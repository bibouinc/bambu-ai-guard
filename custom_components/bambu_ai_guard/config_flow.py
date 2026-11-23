"""Config flow for Bambu AI Guard integration."""
from __future__ import annotations

import asyncio
from pathlib import Path
import socket
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import ssdp
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import device_registry as dr, entity_registry as er, selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CHECK_MODES,
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
    CONF_PAUSE_ENTITY,
    CONF_PRINTER_DEVICE_ID,
    CONF_PRINTER_IP,
    CONF_PRINTER_MODEL,
    CONF_PRINTER_NAME,
    CONF_PRINTER_SERIAL,
    CONF_STATUS_ENTITY,
    CONF_TOTAL_LAYERS_ENTITY,
    CONF_USE_MEDIAN_FILTER,
    DEFAULT_AUTO_PAUSE,
    DEFAULT_AUTO_PAUSE_THRESHOLD,
    DEFAULT_CHECK_INTERVAL_LAYERS,
    DEFAULT_CHECK_INTERVAL_MINUTES,
    DEFAULT_CHECK_MODE,
    DEFAULT_FIRST_LAYER_CHECKS,
    DOMAIN,
    KINEMATICS_COREXY,
)
from .coordinator import resolve_bambu_device_entities
from .vision import GeminiDecisionsInspector, detect_printer_model_and_kinematics


def _get_bambu_printer_devices(hass: HomeAssistant) -> list[dr.DeviceEntry]:
    """Find all registered Bambu Lab 3D printer devices (excluding AMS/External Spool sub-devices)."""
    dev_reg = dr.async_get(hass)
    printers: list[dr.DeviceEntry] = []
    excluded_models = {
        "AMS",
        "AMS Lite",
        "AMS 2 Pro",
        "AMS HT",
        "External Spool",
        "Hotend Rack",
    }

    for device in dev_reg.devices.values():
        is_bambu = any(domain == "bambu_lab" for domain, _ in device.identifiers) or (
            device.manufacturer and "bambu" in device.manufacturer.lower()
        )
        if not is_bambu:
            continue
        if device.model in excluded_models:
            continue
        printers.append(device)

    return printers


def _discover_bambu_ssdp_sync(timeout: float = 3.5) -> dict[str, str]:
    """Listen on Bambu Lab SSDP multicast (239.255.255.250:2021) for printer IP, Serial & Model."""
    import struct

    discovered: dict[str, str] = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                pass
        sock.bind(("", 2021))
        # Join SSDP multicast group so Bambu broadcasts are received inside Docker/Linux
        mreq = struct.pack("4sl", socket.inet_aton("239.255.255.250"), socket.INADDR_ANY)
        try:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        except OSError:
            pass
        sock.settimeout(timeout)
        data, addr = sock.recvfrom(4096)
        msg = data.decode("utf-8", errors="ignore")
        if "bambulab" in msg.lower():
            discovered["ip"] = addr[0]
            for line in msg.splitlines():
                low = line.lower()
                if low.startswith("usn:"):
                    discovered["serial"] = line.split(":", 1)[1].strip().split("::")[0]
                elif low.startswith("devname.bambu.com:"):
                    discovered["name"] = line.split(":", 1)[1].strip()
                elif low.startswith("devmodel.bambu.com:"):
                    discovered["model"] = line.split(":", 1)[1].strip()
    except Exception:  # noqa: BLE001
        pass
    finally:
        sock.close()

    return discovered


class BambuAIGuardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bambu AI Guard."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._ssdp_ip: str = ""
        self._ssdp_serial: str = ""
        self._ssdp_model: str = "P1P"

    async def async_step_ssdp(
        self, discovery_info: ssdp.SsdpServiceInfo
    ) -> FlowResult:
        """Handle automatic SSDP discovery of a Bambu Lab printer on the LAN."""
        host = discovery_info.ssdp_headers.get("Location", "") or ""
        if not host and discovery_info.upnp:
            host = str(discovery_info.upnp.get("host", ""))
        serial = str(discovery_info.ssdp_usn or "").split("::")[0].strip().upper()
        if serial:
            await self.async_set_unique_id(f"{DOMAIN}_{serial}")
            self._abort_if_unique_id_configured()
            model, _ = detect_printer_model_and_kinematics(None, serial)
            self._ssdp_serial = serial
            self._ssdp_model = model
        if host:
            self._ssdp_ip = host.replace("http://", "").replace("https://", "").split(":")[0].split("/")[0]

        self.context["title_placeholders"] = {
            "name": f"Bambu Lab {self._ssdp_model} ({self._ssdp_ip or self._ssdp_serial})"
        }
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step: select Bambu printer (HA device or Direct LAN) + Gemini API key."""
        errors: dict[str, str] = {}
        bambu_devices = _get_bambu_printer_devices(self.hass)

        if user_input is not None:
            api_key = user_input.get(CONF_GEMINI_API_KEY, "").strip()
            session = async_get_clientsession(self.hass)
            inspector = GeminiDecisionsInspector(session=session, api_key=api_key)
            valid, err_code = await inspector.async_validate_api_key()

            if not valid and err_code:
                errors["base"] = err_code
            else:
                device_id = user_input.get(CONF_PRINTER_DEVICE_ID)
                dev_reg = dr.async_get(self.hass)
                device = dev_reg.async_get(device_id) if device_id else None

                serial = user_input.get(CONF_PRINTER_SERIAL, "").strip().upper()
                printer_ip = user_input.get(CONF_PRINTER_IP, "").strip()
                access_code = user_input.get(CONF_ACCESS_CODE, "").strip()
                camera_entity = user_input.get(CONF_CAMERA_ENTITY)

                if device:
                    for dom, ident in device.identifiers:
                        if dom == "bambu_lab":
                            serial = ident
                            break
                    if not serial and device.serial_number:
                        serial = device.serial_number

                if not device and not camera_entity and (not printer_ip or not access_code):
                    errors["base"] = "missing_printer_connection"
                else:
                    raw_model = (
                        (device.model if device and device.model else None)
                        or user_input.get(CONF_PRINTER_MODEL)
                        or "P1P"
                    )
                    printer_model, kinematics = detect_printer_model_and_kinematics(
                        raw_model, serial
                    )
                    printer_name = (
                        (device.name_by_user or device.name)
                        if device
                        else f"Bambu Lab {printer_model}"
                    )
                    unique_key = serial or device_id or printer_ip or "default"

                    await self.async_set_unique_id(f"{DOMAIN}_{unique_key}")
                    self._abort_if_unique_id_configured()

                    resolved = (
                        resolve_bambu_device_entities(self.hass, device_id)
                        if device_id
                        else {}
                    )

                    entry_data: dict[str, Any] = {
                        CONF_PRINTER_DEVICE_ID: device_id,
                        CONF_PRINTER_NAME: printer_name,
                        CONF_PRINTER_MODEL: printer_model,
                        CONF_PRINTER_SERIAL: serial or unique_key,
                        CONF_KINEMATICS: kinematics,
                        CONF_PRINTER_IP: printer_ip,
                        CONF_ACCESS_CODE: access_code,
                        CONF_GEMINI_API_KEY: api_key,
                        CONF_CAMERA_ENTITY: camera_entity
                        or resolved.get(CONF_CAMERA_ENTITY),
                        CONF_LAYER_ENTITY: resolved.get(CONF_LAYER_ENTITY),
                        CONF_TOTAL_LAYERS_ENTITY: resolved.get(
                            CONF_TOTAL_LAYERS_ENTITY
                        ),
                        CONF_STATUS_ENTITY: resolved.get(CONF_STATUS_ENTITY),
                        CONF_PAUSE_ENTITY: resolved.get(CONF_PAUSE_ENTITY),
                        CONF_AUTO_PAUSE: DEFAULT_AUTO_PAUSE,
                        CONF_AUTO_PAUSE_THRESHOLD: DEFAULT_AUTO_PAUSE_THRESHOLD,
                        CONF_CHECK_MODE: DEFAULT_CHECK_MODE,
                        CONF_CHECK_INTERVAL_LAYERS: DEFAULT_CHECK_INTERVAL_LAYERS,
                        CONF_CHECK_INTERVAL_MINUTES: DEFAULT_CHECK_INTERVAL_MINUTES,
                        CONF_FIRST_LAYER_CHECKS: DEFAULT_FIRST_LAYER_CHECKS,
                        CONF_USE_MEDIAN_FILTER: kinematics == KINEMATICS_COREXY,
                    }

                    return self.async_create_entry(
                        title=f"{printer_name} AI Guard",
                        data=entry_data,
                    )

        schema_fields: dict[Any, Any] = {}
        if bambu_devices:
            # Mode A: ha-bambulab printer device already configured in Home Assistant (1 dropdown + 1 API key)
            default_dev = bambu_devices[0].id
            schema_fields[
                vol.Required(CONF_PRINTER_DEVICE_ID, default=default_dev)
            ] = selector.DeviceSelector(
                selector.DeviceSelectorConfig(
                    integration="bambu_lab",
                )
            )
        else:
            # Mode B: Standalone Direct LAN with automatic SSDP multicast discovery
            ssdp_info: dict[str, str] = {}
            if not self._ssdp_ip:
                ssdp_info = await self.hass.async_add_executor_job(
                    _discover_bambu_ssdp_sync, 3.5
                )
            default_ip = self._ssdp_ip or ssdp_info.get("ip", "")
            default_serial = self._ssdp_serial or ssdp_info.get("serial", "")
            detected_model, _ = detect_printer_model_and_kinematics(
                ssdp_info.get("model") or self._ssdp_model, default_serial
            )
            if detected_model not in ("P1P", "P1S", "A1", "A1 Mini", "X1C", "X1E"):
                detected_model = "P1P"

            schema_fields[
                vol.Required(CONF_PRINTER_MODEL, default=detected_model)
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["P1P", "P1S", "A1", "A1 Mini", "X1C", "X1E"],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
            schema_fields[
                vol.Required(
                    CONF_PRINTER_IP,
                    default=default_ip,
                )
            ] = selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
            )
            schema_fields[
                vol.Required(
                    CONF_ACCESS_CODE,
                    default="",
                )
            ] = selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            )
            schema_fields[
                vol.Optional(
                    CONF_PRINTER_SERIAL,
                    default=default_serial,
                )
            ] = selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
            )

        schema_fields[vol.Required(CONF_GEMINI_API_KEY)] = selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema_fields),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return BambuAIGuardOptionsFlow(config_entry)


class BambuAIGuardOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Bambu AI Guard."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        cfg = {**self._entry.data, **self._entry.options}
        kinematics = cfg.get(CONF_KINEMATICS, KINEMATICS_COREXY)

        schema_dict: dict[Any, Any] = {
            vol.Required(
                CONF_GEMINI_API_KEY,
                default=cfg.get(CONF_GEMINI_API_KEY, ""),
            ): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            ),
        }

        if not cfg.get(CONF_PRINTER_DEVICE_ID):
            schema_dict[
                vol.Required(
                    CONF_PRINTER_IP,
                    default=cfg.get(CONF_PRINTER_IP, ""),
                )
            ] = selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
            )
            schema_dict[
                vol.Required(
                    CONF_ACCESS_CODE,
                    default=cfg.get(CONF_ACCESS_CODE, ""),
                )
            ] = selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            )

        schema_dict.update(
            {
                vol.Required(
                    CONF_CHECK_MODE,
                    default=cfg.get(CONF_CHECK_MODE, DEFAULT_CHECK_MODE),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=CHECK_MODES,
                        translation_key="check_mode",
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_FIRST_LAYER_CHECKS,
                    default=cfg.get(
                        CONF_FIRST_LAYER_CHECKS, DEFAULT_FIRST_LAYER_CHECKS
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=5,
                        step=1,
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Required(
                    CONF_CHECK_INTERVAL_LAYERS,
                    default=cfg.get(
                        CONF_CHECK_INTERVAL_LAYERS, DEFAULT_CHECK_INTERVAL_LAYERS
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=50,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_CHECK_INTERVAL_MINUTES,
                    default=cfg.get(
                        CONF_CHECK_INTERVAL_MINUTES, DEFAULT_CHECK_INTERVAL_MINUTES
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=60,
                        step=1,
                        unit_of_measurement="min",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_AUTO_PAUSE,
                    default=cfg.get(CONF_AUTO_PAUSE, DEFAULT_AUTO_PAUSE),
                ): bool,
                vol.Required(
                    CONF_AUTO_PAUSE_THRESHOLD,
                    default=cfg.get(
                        CONF_AUTO_PAUSE_THRESHOLD, DEFAULT_AUTO_PAUSE_THRESHOLD
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=50,
                        max=99,
                        step=5,
                        unit_of_measurement="%",
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Required(
                    CONF_USE_MEDIAN_FILTER,
                    default=cfg.get(
                        CONF_USE_MEDIAN_FILTER, kinematics == KINEMATICS_COREXY
                    ),
                ): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema_dict))
