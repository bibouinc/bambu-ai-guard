"""DataUpdateCoordinator with Layer-1 multi-checks and flexible Layer/Minute scheduling."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import json
import ssl
import time
from typing import Any

from homeassistant.components.camera import async_get_image as async_get_camera_image
from homeassistant.components.image import DOMAIN as IMAGE_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    BRAND,
    CHECK_MODE_BOTH,
    CHECK_MODE_LAYERS,
    CHECK_MODE_MINUTES,
    CONF_ACCESS_CODE,
    CONF_AUTO_PAUSE,
    CONF_AUTO_PAUSE_THRESHOLD,
    CONF_CAMERA_ENTITY,
    CONF_CHECK_INTERVAL_LAYERS,
    CONF_CHECK_INTERVAL_MINUTES,
    CONF_CHECK_MODE,
    CONF_FIRST_LAYER_CHECKS,
    CONF_GEMINI_API_KEY,
    CONF_KINEMATICS,
    CONF_LAYER_ENTITY,
    CONF_NOTIFY_TARGET,
    CONF_PAUSE_ENTITY,
    CONF_PRINTER_DEVICE_ID,
    CONF_PRINTER_IP,
    CONF_PRINTER_MODEL,
    CONF_PRINTER_NAME,
    CONF_PRINTER_SERIAL,
    CONF_STATUS_ENTITY,
    CONF_SUBTASK_ENTITY,
    CONF_TOTAL_LAYERS_ENTITY,
    CONF_USE_MEDIAN_FILTER,
    CRITICAL_CHECKPOINT_LAYERS,
    DEFAULT_AUTO_PAUSE,
    DEFAULT_AUTO_PAUSE_THRESHOLD,
    DEFAULT_CHECK_INTERVAL_LAYERS,
    DEFAULT_CHECK_INTERVAL_MINUTES,
    DEFAULT_CHECK_MODE,
    DEFAULT_FIRST_LAYER_CHECKS,
    DEFAULT_NOTIFY_TARGET,
    DOMAIN,
    KINEMATICS_COREXY,
    LOGGER,
    NOTIFY_TARGET_NONE,
    STATUS_ERROR,
    STATUS_FAILURE,
    STATUS_IDLE,
)
from .history import PrintHistoryStore
from .vision import (
    GeminiDecisionsInspector,
    InspectionVerdict,
    capture_direct_bambu_camera_frame,
    compute_temporal_median_jpeg,
    detect_printer_model_and_kinematics,
)


def resolve_bambu_device_entities(
    hass: HomeAssistant, device_id: str
) -> dict[str, str]:
    """Auto-resolve camera, layer, status, and pause entities for a Bambu Lab HA device."""
    ent_reg = er.async_get(hass)
    entries = er.async_entries_for_device(
        ent_reg, device_id, include_disabled_entities=False
    )

    resolved: dict[str, str] = {}
    for entry in entries:
        uid = (entry.unique_id or "").lower()
        eid = entry.entity_id
        domain = entry.domain

        if domain == "camera" and ("camera" in uid or "camera" in eid):
            resolved[CONF_CAMERA_ENTITY] = eid
        elif domain == "image" and (
            "p1p_camera" in uid or "chamber" in uid or "camera" in eid
        ):
            resolved.setdefault(CONF_CAMERA_ENTITY, eid)
        elif domain == "sensor":
            if uid.endswith("_current_layer") or eid.endswith("_current_layer"):
                resolved[CONF_LAYER_ENTITY] = eid
            elif uid.endswith("_total_layers") or eid.endswith("_total_layers"):
                resolved[CONF_TOTAL_LAYERS_ENTITY] = eid
            elif uid.endswith("_print_status") or eid.endswith("_print_status"):
                resolved[CONF_STATUS_ENTITY] = eid
            elif (
                uid.endswith("_subtask_name")
                or eid.endswith("_subtask_name")
                or uid.endswith("_gcode_file")
                or eid.endswith("_gcode_file")
            ):
                resolved.setdefault(CONF_SUBTASK_ENTITY, eid)
        elif domain == "button":
            if (
                uid.endswith("_pause")
                or eid.endswith("_pause_print")
                or eid.endswith("_pause")
            ):
                resolved[CONF_PAUSE_ENTITY] = eid

    return resolved


class BambuAIGuardCoordinator(DataUpdateCoordinator[InspectionVerdict]):
    """Coordinates Gemini Decisions API inspections on layer transitions, time intervals, and Layer 1."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
        )
        self.entry = entry
        merged_cfg = {**entry.data, **entry.options}

        self.printer_device_id: str | None = merged_cfg.get(CONF_PRINTER_DEVICE_ID)
        self.printer_name: str = merged_cfg.get(CONF_PRINTER_NAME, "Bambu Lab Printer")
        self.printer_serial: str = merged_cfg.get(
            CONF_PRINTER_SERIAL, entry.entry_id[:12]
        )
        raw_model = merged_cfg.get(CONF_PRINTER_MODEL, "P1P")
        detected_model, detected_kinematics = detect_printer_model_and_kinematics(
            raw_model, self.printer_serial
        )
        self.printer_model: str = detected_model
        self.kinematics: str = merged_cfg.get(CONF_KINEMATICS, detected_kinematics)

        self.camera_entity: str | None = merged_cfg.get(CONF_CAMERA_ENTITY)
        self.layer_entity: str | None = merged_cfg.get(CONF_LAYER_ENTITY)
        self.total_layers_entity: str | None = merged_cfg.get(CONF_TOTAL_LAYERS_ENTITY)
        self.status_entity: str | None = merged_cfg.get(CONF_STATUS_ENTITY)
        self.pause_entity: str | None = merged_cfg.get(CONF_PAUSE_ENTITY)
        self.subtask_entity: str | None = merged_cfg.get(CONF_SUBTASK_ENTITY)

        self.printer_ip: str = merged_cfg.get(CONF_PRINTER_IP, "")
        self.access_code: str = merged_cfg.get(CONF_ACCESS_CODE, "")

        self.history = PrintHistoryStore(hass, self.printer_serial)
        self.purge_keep_prints: int = 50

        # Direct LAN MQTT telemetry fallback state (when ha-bambulab entities are not used)
        self._direct_layer: int = 0
        self._direct_total_layers: int = 0
        self._direct_status: str = "idle"
        self._direct_subtask: str = "Bambu Print"
        self._mqtt_client: Any = None

        # Runtime settings
        self.auto_pause_enabled: bool = bool(
            merged_cfg.get(CONF_AUTO_PAUSE, DEFAULT_AUTO_PAUSE)
        )
        self.auto_pause_threshold: int = int(
            merged_cfg.get(CONF_AUTO_PAUSE_THRESHOLD, DEFAULT_AUTO_PAUSE_THRESHOLD)
        )
        self.check_mode: str = str(
            merged_cfg.get(CONF_CHECK_MODE, DEFAULT_CHECK_MODE)
        )
        self.check_interval_layers: int = int(
            merged_cfg.get(CONF_CHECK_INTERVAL_LAYERS, DEFAULT_CHECK_INTERVAL_LAYERS)
        )
        self.check_interval_minutes: int = int(
            merged_cfg.get(CONF_CHECK_INTERVAL_MINUTES, DEFAULT_CHECK_INTERVAL_MINUTES)
        )
        self.first_layer_checks: int = int(
            merged_cfg.get(CONF_FIRST_LAYER_CHECKS, DEFAULT_FIRST_LAYER_CHECKS)
        )
        default_median = self.kinematics == KINEMATICS_COREXY
        self.use_median_filter: bool = bool(
            merged_cfg.get(CONF_USE_MEDIAN_FILTER, default_median)
        )
        self.notify_target: str = str(
            merged_cfg.get(CONF_NOTIFY_TARGET, DEFAULT_NOTIFY_TARGET)
        )

        session = async_get_clientsession(hass)
        self.inspector = GeminiDecisionsInspector(
            session=session,
            api_key=merged_cfg.get(CONF_GEMINI_API_KEY, ""),
        )

        self.latest_composite_jpeg: bytes | None = None
        self.last_checked_layer: int = -1
        self.last_check_monotonic: float = 0.0
        self.layer1_checks_done: int = 0
        self.total_inspections: int = 0
        self.failures_detected: int = 0
        self._inspect_lock = asyncio.Lock()
        self._unsub_state_listener: Any = None
        self._unsub_timer_listener: Any = None
        self._layer1_task: asyncio.Task[None] | None = None

        self.data = InspectionVerdict(
            status=STATUS_IDLE,
            confidence=None,
            failure_type="none",
            recommended_action="continue",
            details=(
                f"Monitoring {self.printer_name} ({self.printer_model}, {self.kinematics}). "
                "Waiting for active print checkpoint."
            ),
        )

    def async_start_listeners(self) -> None:
        """Subscribe to layer changes and periodic timer for minute-based & Layer-1 checks."""
        if self.printer_device_id and not self.layer_entity:
            resolved = resolve_bambu_device_entities(self.hass, self.printer_device_id)
            self.camera_entity = self.camera_entity or resolved.get(CONF_CAMERA_ENTITY)
            self.layer_entity = self.layer_entity or resolved.get(CONF_LAYER_ENTITY)
            self.total_layers_entity = self.total_layers_entity or resolved.get(
                CONF_TOTAL_LAYERS_ENTITY
            )
            self.status_entity = self.status_entity or resolved.get(CONF_STATUS_ENTITY)
            self.pause_entity = self.pause_entity or resolved.get(CONF_PAUSE_ENTITY)
            self.subtask_entity = self.subtask_entity or resolved.get(CONF_SUBTASK_ENTITY)

        self.hass.async_create_task(self.history.async_load())

        tracked_entities = [e for e in (self.layer_entity, self.status_entity) if e]
        if tracked_entities:
            LOGGER.info(
                "Bambu AI Guard (%s) tracking entities: %s",
                self.printer_name,
                tracked_entities,
            )
            self._unsub_state_listener = async_track_state_change_event(
                self.hass, tracked_entities, self._async_on_printer_state_change
            )

        # Periodic 30-second heartbeat to check if `check_interval_minutes` has elapsed while printing
        self._unsub_timer_listener = async_track_time_interval(
            self.hass,
            self._async_on_timer_tick,
            timedelta(seconds=30),
        )

        # If running in Standalone Direct LAN mode (no HA layer entity), start direct MQTT TLS listener on port 8883
        if not self.layer_entity and self.printer_ip and self.access_code:
            self.hass.async_add_executor_job(self._start_direct_mqtt_sync)

    def _start_direct_mqtt_sync(self) -> None:
        """Connect directly to Bambu Lab MQTT over TLS (port 8883) for layer/status telemetry and auto-pause."""
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            LOGGER.warning("paho-mqtt not installed; direct MQTT listener disabled")
            return

        client_id = f"bambu_ai_guard_{self.printer_serial}_{int(time.time())}"
        if hasattr(mqtt, "CallbackAPIVersion"):
            client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2,
                client_id=client_id,
                protocol=mqtt.MQTTv311,
            )
        else:
            client = mqtt.Client(client_id=client_id)

        client.username_pw_set("bblp", self.access_code)
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        client.tls_set_context(ssl_ctx)
        client.tls_insecure_set(True)
        client.reconnect_delay_set(min_delay=10, max_delay=60)

        def _on_connect(cli: Any, _ud: Any, _flags: Any, rc: Any, *_args: Any) -> None:
            if rc == 0:
                topic = (
                    f"device/{self.printer_serial}/report"
                    if self.printer_serial
                    else "device/+/report"
                )
                cli.subscribe(topic)
                if self.printer_serial:
                    cli.publish(
                        f"device/{self.printer_serial}/request",
                        json.dumps({"pushing": {"sequence_id": "1", "command": "pushall"}}),
                    )

        def _on_message(_cli: Any, _ud: Any, msg: Any) -> None:
            try:
                # Extract serial from topic device/<SERIAL>/report if not yet known
                parts = msg.topic.split("/")
                if len(parts) >= 3 and parts[0] == "device":
                    if not self.printer_serial or self.printer_serial == self.printer_ip:
                        self.printer_serial = parts[1]

                payload = json.loads(msg.payload.decode("utf-8", errors="ignore"))
                p = payload.get("print")
                if not isinstance(p, dict):
                    return

                prev_layer = self._direct_layer
                if "gcode_state" in p:
                    self._direct_status = str(p["gcode_state"]).lower()
                if "subtask_name" in p:
                    self._direct_subtask = str(p["subtask_name"])
                if "total_layer_num" in p:
                    self._direct_total_layers = int(p["total_layer_num"])
                if "layer_num" in p:
                    new_layer = int(p["layer_num"])
                    self._direct_layer = new_layer
                    if new_layer != prev_layer:
                        self.hass.loop.call_soon_threadsafe(
                            self._handle_direct_layer_change, new_layer
                        )
            except Exception:  # noqa: BLE001
                pass

        client.on_connect = _on_connect
        client.on_message = _on_message
        try:
            client.connect_async(self.printer_ip, 8883, keepalive=60)
            client.loop_start()
            self._mqtt_client = client
        except Exception as err:  # noqa: BLE001
            LOGGER.warning("Direct MQTT connect error to %s: %s", self.printer_ip, err)

    @callback
    def _handle_direct_layer_change(self, layer: int) -> None:
        """Handle layer transition coming from direct LAN MQTT."""
        if layer < self.last_checked_layer:
            self.last_checked_layer = -1
            self.layer1_checks_done = 0

        if not self.is_printer_running():
            return

        if layer == 1 and self.layer1_checks_done == 0 and self.first_layer_checks > 0:
            if self._layer1_task and not self._layer1_task.done():
                self._layer1_task.cancel()
            self._layer1_task = self.hass.async_create_task(
                self._async_run_layer1_multi_checks()
            )
            return

        if self.should_inspect_layer(layer):
            self.hass.async_create_task(
                self.async_run_inspection(
                    layer=layer,
                    manual=False,
                    trigger_reason=f"layer_{layer}",
                )
            )

    @callback
    def async_stop_listeners(self) -> None:
        """Unsubscribe listeners on unload."""
        if self._unsub_state_listener:
            self._unsub_state_listener()
            self._unsub_state_listener = None
        if self._unsub_timer_listener:
            self._unsub_timer_listener()
            self._unsub_timer_listener = None
        if self._layer1_task and not self._layer1_task.done():
            self._layer1_task.cancel()
            self._layer1_task = None
        if self._mqtt_client is not None:
            try:
                self._mqtt_client.loop_stop()
                self._mqtt_client.disconnect()
            except Exception:  # noqa: BLE001
                pass
            self._mqtt_client = None

    def get_print_name(self) -> str:
        """Read current print subtask or gcode filename from linked HA sensor or direct MQTT."""
        if not self.subtask_entity:
            return self._direct_subtask
        state = self.hass.states.get(self.subtask_entity)
        if not state or state.state in ("unknown", "unavailable", "None", ""):
            return self._direct_subtask
        return state.state

    def get_current_layer(self) -> int:
        """Read current print layer from linked HA sensor or direct MQTT."""
        if not self.layer_entity:
            return self._direct_layer
        state = self.hass.states.get(self.layer_entity)
        if not state or state.state in ("unknown", "unavailable", "None", ""):
            return self._direct_layer
        try:
            return int(float(state.state))
        except (TypeError, ValueError):
            return self._direct_layer

    def get_total_layers(self) -> int:
        """Read total layers from linked HA sensor or direct MQTT."""
        if not self.total_layers_entity:
            return self._direct_total_layers
        state = self.hass.states.get(self.total_layers_entity)
        if not state or state.state in ("unknown", "unavailable", "None", ""):
            return self._direct_total_layers
        try:
            return int(float(state.state))
        except (TypeError, ValueError):
            return self._direct_total_layers

    def is_printer_running(self) -> bool:
        """Return True if the printer is actively printing."""
        if not self.status_entity:
            return self._direct_status in ("running", "printing", "unknown", "idle")
        state = self.hass.states.get(self.status_entity)
        if not state:
            return True
        val = state.state.lower()
        return val in ("running", "printing")

    def should_inspect_layer(self, layer: int) -> bool:
        """Determine if the given layer transition triggers a layer-based inspection."""
        if self.check_mode == CHECK_MODE_MINUTES:
            # In pure minutes mode, still check critical transition layers 2, 3, 5, 25
            return layer in CRITICAL_CHECKPOINT_LAYERS and layer != self.last_checked_layer

        if layer <= 1 or layer == self.last_checked_layer:
            return False
        if layer in CRITICAL_CHECKPOINT_LAYERS:
            return True
        interval = max(1, self.check_interval_layers)
        return (layer % interval) == 0

    async def _async_run_layer1_multi_checks(self) -> None:
        """Run N spaced inspections during Layer 1 while the first layer is actively being laid down."""
        target_checks = max(0, self.first_layer_checks)
        if target_checks == 0:
            return

        # Wait 40s into Layer 1 so initial prime line & first perimeters are visible
        await asyncio.sleep(40)
        while (
            self.layer1_checks_done < target_checks
            and self.is_printer_running()
            and self.get_current_layer() == 1
        ):
            self.layer1_checks_done += 1
            await self.async_run_inspection(
                layer=1,
                manual=False,
                trigger_reason=f"layer_1_check_{self.layer1_checks_done}_of_{target_checks}",
            )
            if self.layer1_checks_done >= target_checks:
                break
            # Space Layer 1 inspections by 60 seconds
            await asyncio.sleep(60)

    @callback
    def _async_on_timer_tick(self, _now: Any) -> None:
        """Periodic check for Every-X-Minutes mode during an active print."""
        if self.check_mode not in (CHECK_MODE_MINUTES, CHECK_MODE_BOTH):
            return
        if not self.is_printer_running():
            return
        layer = self.get_current_layer()
        if layer < 1:
            return

        elapsed_secs = time.monotonic() - self.last_check_monotonic
        target_secs = max(1, self.check_interval_minutes) * 60.0
        if elapsed_secs >= target_secs:
            self.hass.async_create_task(
                self.async_run_inspection(
                    layer=layer,
                    manual=False,
                    trigger_reason=f"timer_{self.check_interval_minutes}m",
                )
            )

    @callback
    def _async_on_printer_state_change(self, event: Event) -> None:
        """Trigger inspection when layer advances to Layer 1 or a checkpoint layer."""
        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")
        if not new_state or new_state.state in ("unknown", "unavailable"):
            return

        if entity_id == self.status_entity:
            status_val = new_state.state.lower()
            if status_val in ("finish", "idle", "failed", "offline"):
                self.last_checked_layer = -1
                self.layer1_checks_done = 0
                if self._layer1_task and not self._layer1_task.done():
                    self._layer1_task.cancel()
                self.hass.async_create_task(
                    self.history.async_finish_active_print(status_val)
                )
            return

        if entity_id == self.layer_entity:
            try:
                layer = int(float(new_state.state))
            except (TypeError, ValueError):
                return

            if layer < self.last_checked_layer:
                # New print started
                self.last_checked_layer = -1
                self.layer1_checks_done = 0

            if not self.is_printer_running():
                return

            if layer == 1 and self.layer1_checks_done == 0 and self.first_layer_checks > 0:
                if self._layer1_task and not self._layer1_task.done():
                    self._layer1_task.cancel()
                self._layer1_task = self.hass.async_create_task(
                    self._async_run_layer1_multi_checks()
                )
                return

            if self.should_inspect_layer(layer):
                self.hass.async_create_task(
                    self.async_run_inspection(
                        layer=layer,
                        manual=False,
                        trigger_reason=f"layer_{layer}",
                    )
                )

    async def _async_capture_single_frame(self) -> bytes | None:
        """Capture a single frame from the linked HA camera/image entity or direct LAN port 6000."""
        if self.printer_device_id and not self.camera_entity:
            resolved = resolve_bambu_device_entities(self.hass, self.printer_device_id)
            self.camera_entity = resolved.get(CONF_CAMERA_ENTITY)

        if self.camera_entity:
            if self.camera_entity.startswith("camera."):
                try:
                    img = await async_get_camera_image(
                        self.hass, self.camera_entity, timeout=10
                    )
                    if img and img.content and len(img.content) > 1000:
                        return img.content
                except Exception as err:  # noqa: BLE001
                    LOGGER.warning(
                        "Failed reading HA camera %s: %s", self.camera_entity, err
                    )
            elif self.camera_entity.startswith("image."):
                try:
                    comp = self.hass.data.get(IMAGE_DOMAIN)
                    if comp:
                        entity = comp.get_entity(self.camera_entity)
                        if entity:
                            raw = await entity.async_image()
                            if raw and len(raw) > 1000:
                                return raw
                except Exception as err:  # noqa: BLE001
                    LOGGER.warning(
                        "Failed reading HA image entity %s: %s", self.camera_entity, err
                    )

        if self.printer_ip and self.access_code:
            return await capture_direct_bambu_camera_frame(
                host=self.printer_ip,
                access_code=self.access_code,
            )

        return None

    async def async_capture_inspection_frame(self) -> tuple[bytes | None, int]:
        """Capture either a 3-frame temporal median composite (CoreXY) or single crisp frame (A1 Bed-Slinger)."""
        use_burst = self.use_median_filter and self.kinematics == KINEMATICS_COREXY
        if not use_burst:
            frame = await self._async_capture_single_frame()
            return (frame, 1 if frame else 0)

        frames: list[bytes] = []
        for idx in range(3):
            if idx > 0:
                await asyncio.sleep(2.5)
            frame = await self._async_capture_single_frame()
            if frame:
                frames.append(frame)

        return await self.hass.async_add_executor_job(
            compute_temporal_median_jpeg, frames
        )

    async def async_run_inspection(
        self,
        layer: int | None = None,
        manual: bool = False,
        trigger_reason: str = "manual",
    ) -> InspectionVerdict:
        """Execute a full camera capture + Gemini Decisions API inspection cycle."""
        if self._inspect_lock.locked() and not manual:
            return self.data

        async with self._inspect_lock:
            curr_layer = layer if layer is not None else self.get_current_layer()
            total_layers = self.get_total_layers()
            self.last_check_monotonic = time.monotonic()

            jpeg_bytes, frames_merged = await self.async_capture_inspection_frame()
            if not jpeg_bytes:
                verdict = InspectionVerdict(
                    status=STATUS_ERROR,
                    confidence=None,
                    failure_type="none",
                    recommended_action="inspect",
                    details=(
                        f"Could not capture camera snapshot from {self.camera_entity or self.printer_ip or 'printer'}. "
                        "Verify that your Bambu Lab camera entity is enabled and streaming."
                    ),
                    layer=curr_layer,
                    total_layers=total_layers,
                    frames_merged=0,
                    trigger_reason=trigger_reason,
                    warnings=["Camera snapshot unavailable"],
                )
                self.async_set_updated_data(verdict)
                return verdict

            self.latest_composite_jpeg = jpeg_bytes
            if not manual and curr_layer > 1:
                self.last_checked_layer = curr_layer

            verdict = await self.inspector.async_inspect_frame(
                jpeg_bytes=jpeg_bytes,
                printer_model=self.printer_model,
                kinematics=self.kinematics,
                layer=curr_layer,
                total_layers=total_layers,
                frames_merged=frames_merged,
                trigger_reason=trigger_reason,
            )

            self.total_inspections += 1
            auto_paused = False
            snapshot_url = await self.history.async_record_inspection(
                print_name=self.get_print_name(),
                verdict=verdict,
                jpeg_bytes=jpeg_bytes,
                auto_paused=False,
            )
            if verdict.status == STATUS_FAILURE:
                self.failures_detected += 1
                auto_paused = await self._async_handle_failure_verdict(
                    verdict, snapshot_url=snapshot_url
                )
            elif verdict.status == "WARNING":
                await self._async_send_warning_notification(
                    verdict, snapshot_url=snapshot_url
                )

            self.hass.bus.async_fire(
                f"{DOMAIN}_event",
                {
                    "printer_name": self.printer_name,
                    "printer_serial": self.printer_serial,
                    "printer_model": self.printer_model,
                    "kinematics": self.kinematics,
                    "trigger_reason": trigger_reason,
                    "status": verdict.status,
                    "failure_type": verdict.failure_type,
                    "recommended_action": verdict.recommended_action,
                    "confidence_pct": round(verdict.confidence * 100.0, 1)
                    if verdict.confidence is not None
                    else None,
                    "spaghetti_pct": round(verdict.spaghetti_prob * 100.0, 1)
                    if verdict.spaghetti_prob is not None
                    else None,
                    "warping_pct": round(verdict.warping_prob * 100.0, 1)
                    if verdict.warping_prob is not None
                    else None,
                    "detachment_pct": round(verdict.detachment_prob * 100.0, 1)
                    if verdict.detachment_prob is not None
                    else None,
                    "first_layer_defect_pct": round(verdict.first_layer_prob * 100.0, 1)
                    if verdict.first_layer_prob is not None
                    else None,
                    "severity": verdict.severity,
                    "layer": verdict.layer,
                    "total_layers": verdict.total_layers,
                    "details": verdict.details,
                },
            )

            self.async_set_updated_data(verdict)
            return verdict

    async def _async_send_push_notification(
        self,
        title: str,
        message: str,
        snapshot_url: str | None = None,
        critical: bool = False,
    ) -> None:
        """Send a Home Assistant Mobile App / Notify push notification with optional snapshot photo."""
        target = (self.notify_target or NOTIFY_TARGET_NONE).strip()
        if not target or target == NOTIFY_TARGET_NONE:
            return

        service_name = target.removeprefix("notify.")
        if not self.hass.services.has_service("notify", service_name):
            LOGGER.debug("Notify service notify.%s not found; skipping push", service_name)
            return

        data_payload: dict[str, Any] = {
            "url": f"/{DOMAIN}",
            "clickAction": f"/{DOMAIN}",
            "tag": f"{DOMAIN}_{self.printer_serial}",
        }
        if snapshot_url:
            data_payload["image"] = snapshot_url
        if critical:
            data_payload["push"] = {"interruption-level": "time-sensitive"}
            data_payload["importance"] = "high"

        try:
            await self.hass.services.async_call(
                "notify",
                service_name,
                {
                    "title": title,
                    "message": message,
                    "data": data_payload,
                },
                blocking=False,
            )
        except Exception as err:  # noqa: BLE001
            LOGGER.warning("Failed sending push notification to notify.%s: %s", service_name, err)

    async def _async_send_warning_notification(
        self, verdict: InspectionVerdict, snapshot_url: str | None = None
    ) -> None:
        """Create a persistent HA notification and optional phone push on warning-level defects."""
        conf_pct = (verdict.confidence or 0.0) * 100.0
        title = f"⚠️ Bambu AI Guard Warning: {verdict.failure_type.upper()} on {self.printer_name}"
        short_msg = f"Layer {verdict.layer}/{verdict.total_layers} ({conf_pct:.0f}%): {verdict.details}"
        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": title,
                "message": (
                    f"**Defect**: `{verdict.failure_type}` ({conf_pct:.0f}% confidence)\n"
                    f"**Layer**: {verdict.layer}/{verdict.total_layers}\n"
                    f"**Details**: {verdict.details}\n"
                    f"**Action**: Visual inspection recommended."
                ),
                "notification_id": f"{DOMAIN}_alert_{self.printer_serial}",
            },
            blocking=False,
        )
        await self._async_send_push_notification(
            title=title, message=short_msg, snapshot_url=snapshot_url, critical=False
        )

    async def _async_handle_failure_verdict(
        self, verdict: InspectionVerdict, snapshot_url: str | None = None
    ) -> bool:
        """Trigger auto-pause and persistent HA notification when spaghetti/warping/detachment is detected."""
        conf_pct = (verdict.confidence or 0.0) * 100.0
        paused = False

        if self.auto_pause_enabled and conf_pct >= self.auto_pause_threshold:
            if self.pause_entity:
                try:
                    await self.hass.services.async_call(
                        "button",
                        "press",
                        {"entity_id": self.pause_entity},
                        blocking=True,
                    )
                    paused = True
                    LOGGER.warning(
                        "Bambu AI Guard AUTO-PAUSED %s via %s (defect=%s, confidence=%.1f%%)",
                        self.printer_name,
                        self.pause_entity,
                        verdict.failure_type,
                        conf_pct,
                    )
                except Exception as err:  # noqa: BLE001
                    LOGGER.error("Failed calling pause entity %s: %s", self.pause_entity, err)
                    verdict.warnings.append(f"Auto-pause call failed: {err}")
            elif self._mqtt_client is not None and self.printer_serial:
                try:
                    pause_payload = json.dumps(
                        {"print": {"sequence_id": "0", "command": "pause"}}
                    )
                    self._mqtt_client.publish(
                        f"device/{self.printer_serial}/request", pause_payload
                    )
                    paused = True
                    LOGGER.warning(
                        "Bambu AI Guard AUTO-PAUSED %s via direct LAN MQTT (defect=%s, confidence=%.1f%%)",
                        self.printer_name,
                        verdict.failure_type,
                        conf_pct,
                    )
                except Exception as err:  # noqa: BLE001
                    LOGGER.error("Direct MQTT auto-pause failed: %s", err)
                    verdict.warnings.append(f"Direct MQTT auto-pause failed: {err}")

        action_msg = (
            "Print automatically PAUSED."
            if paused
            else "Manual inspection recommended."
        )
        title = f"🚨 Bambu AI Guard: {verdict.failure_type.upper()} on {self.printer_name}"
        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": title,
                "message": (
                    f"**Defect**: `{verdict.failure_type}` ({conf_pct:.0f}% confidence)\n"
                    f"**Layer**: {verdict.layer}/{verdict.total_layers}\n"
                    f"**Details**: {verdict.details}\n"
                    f"**Action**: {action_msg}"
                ),
                "notification_id": f"{DOMAIN}_alert_{self.printer_serial}",
            },
            blocking=False,
        )
        await self._async_send_push_notification(
            title=title,
            message=f"Layer {verdict.layer}/{verdict.total_layers} ({conf_pct:.0f}%) — {action_msg} {verdict.details}",
            snapshot_url=snapshot_url,
            critical=True,
        )
        return paused

    async def async_purge_history(
        self, keep_last_prints: int | None = None, older_than_days: int | None = None
    ) -> dict[str, int]:
        """Manually purge print records older than keep_last_prints."""
        keep = (
            keep_last_prints
            if keep_last_prints is not None
            else self.purge_keep_prints
        )
        result = await self.history.async_purge(
            keep_last_prints=keep, older_than_days=older_than_days
        )
        self.async_update_listeners()
        return result

    @property
    def device_info(self) -> DeviceInfo:
        """Return DeviceInfo attached to the existing Bambu Lab printer or standalone."""
        if self.printer_device_id:
            dev_reg = dr.async_get(self.hass)
            linked_dev = dev_reg.async_get(self.printer_device_id)
            if linked_dev and linked_dev.identifiers:
                return DeviceInfo(
                    identifiers=linked_dev.identifiers,
                )

        return DeviceInfo(
            identifiers={(DOMAIN, self.printer_serial)},
            name=f"{self.printer_name} AI Guard",
            manufacturer=BRAND,
            model=f"{self.printer_model} ({self.kinematics.upper()})",
            sw_version="1.1.0",
        )
