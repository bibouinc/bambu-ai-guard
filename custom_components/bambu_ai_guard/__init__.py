"""The Bambu AI Guard integration."""
from __future__ import annotations

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, PLATFORMS, SERVICE_INSPECT_NOW, SERVICE_PURGE_HISTORY
from .coordinator import BambuAIGuardCoordinator
from .frontend import BambuAIGuardCardRegistration
from .replay import PrintReplaySimulator, extract_last_frame_thumb_sync


def _get_first_coordinator(hass: HomeAssistant) -> BambuAIGuardCoordinator | None:
    """Return the first active BambuAIGuardCoordinator."""
    for val in hass.data.get(DOMAIN, {}).values():
        if isinstance(val, BambuAIGuardCoordinator):
            return val
    return None


class LiveFrameView(HomeAssistantView):
    """HTTP API serving fresh single-frame live JPEG snapshots from the printer camera."""

    url = "/api/bambu_ai_guard/live_frame"
    name = "api:bambu_ai_guard:live_frame"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        coord = _get_first_coordinator(self.hass)
        if not coord:
            return web.Response(status=404)
        jpg = await coord.async_get_live_frame()
        if not jpg:
            return web.Response(status=503)
        return web.Response(
            body=jpg,
            content_type="image/jpeg",
            headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
        )


class TimelapsesListView(HomeAssistantView):
    """HTTP API to list available previous print timelapses for replay simulation."""

    url = "/api/bambu_ai_guard/timelapses"
    name = "api:bambu_ai_guard:timelapses"
    requires_auth = True

    def __init__(self, hass: HomeAssistant, simulator: PrintReplaySimulator) -> None:
        self.hass = hass
        self.simulator = simulator

    async def get(self, request: web.Request) -> web.Response:
        coord = _get_first_coordinator(self.hass)
        ip = coord.printer_ip if coord else ""
        code = coord.access_code if coord else ""
        items = await self.simulator.async_list_timelapses(self.hass, ip, code)
        return web.json_response({"timelapses": items})


class TimelapseThumbView(HomeAssistantView):
    """HTTP API serving last-frame JPEG thumbnails for the Try on a Previous Print gallery."""

    url = "/api/bambu_ai_guard/timelapse_thumb"
    name = "api:bambu_ai_guard:timelapse_thumb"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        video_id = request.query.get("video_id", "")
        jpg = await self.hass.async_add_executor_job(
            extract_last_frame_thumb_sync, video_id
        )
        if not jpg:
            return web.Response(status=404)
        return web.Response(
            body=jpg,
            content_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=86400"},
        )


class ReplaySimulateView(HomeAssistantView):
    """HTTP API to start and poll a previous-print timelapse AI replay simulation."""

    url = "/api/bambu_ai_guard/simulate"
    name = "api:bambu_ai_guard:simulate"
    requires_auth = True

    def __init__(self, hass: HomeAssistant, simulator: PrintReplaySimulator) -> None:
        self.hass = hass
        self.simulator = simulator

    async def get(self, request: web.Request) -> web.Response:
        return web.json_response(self.simulator.progress)

    async def post(self, request: web.Request) -> web.Response:
        coord = _get_first_coordinator(self.hass)
        if not coord:
            return web.json_response({"error": "No Bambu AI Guard configured"}, status=400)

        body = await request.json()
        video_id = str(body.get("video_id", "")).strip()
        if not video_id:
            return web.json_response({"error": "Missing video_id"}, status=400)

        if not self.simulator.running:
            async def _run_and_persist() -> None:
                res = await self.simulator.async_run_simulation(
                    hass=self.hass,
                    inspector=coord.inspector,
                    video_id=video_id,
                    printer_model=coord.printer_model,
                    kinematics=coord.kinematics,
                    layer_interval=coord.check_interval_layers,
                    auto_pause_threshold=coord.auto_pause_threshold,
                    printer_ip=coord.printer_ip,
                    access_code=coord.access_code,
                    on_api_call=coord.record_api_call_metrics,
                )
                if not res.get("error") and res.get("checked", 0) > 0:
                    await coord.history.async_record_simulation(video_id, res)
                    coord.async_update_listeners()

            self.hass.async_create_task(_run_and_persist())
        return web.json_response({"started": True, "progress": self.simulator.progress})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bambu AI Guard from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    if "card_registered" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["card_registered"] = True
        card_reg = BambuAIGuardCardRegistration(hass)
        await card_reg.async_register()

    if "replay_simulator" not in hass.data[DOMAIN]:
        simulator = PrintReplaySimulator()
        hass.data[DOMAIN]["replay_simulator"] = simulator
        hass.http.register_view(LiveFrameView(hass))
        hass.http.register_view(TimelapsesListView(hass, simulator))
        hass.http.register_view(TimelapseThumbView(hass))
        hass.http.register_view(ReplaySimulateView(hass, simulator))

    coordinator = BambuAIGuardCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    coordinator.async_start_listeners()

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    if not hass.services.has_service(DOMAIN, SERVICE_INSPECT_NOW):

        async def _async_handle_inspect_now(call: ServiceCall) -> None:
            entry_id = call.data.get("entry_id")
            for cid, coord in hass.data.get(DOMAIN, {}).items():
                if isinstance(coord, BambuAIGuardCoordinator) and (
                    not entry_id or cid == entry_id
                ):
                    await coord.async_run_inspection(manual=True)

        hass.services.async_register(
            DOMAIN, SERVICE_INSPECT_NOW, _async_handle_inspect_now
        )

    if not hass.services.has_service(DOMAIN, SERVICE_PURGE_HISTORY):

        async def _async_handle_purge_history(call: ServiceCall) -> None:
            entry_id = call.data.get("entry_id")
            keep_last = call.data.get("keep_last_prints")
            older_days = call.data.get("older_than_days")
            for cid, coord in hass.data.get(DOMAIN, {}).items():
                if isinstance(coord, BambuAIGuardCoordinator) and (
                    not entry_id or cid == entry_id
                ):
                    await coord.async_purge_history(
                        keep_last_prints=int(keep_last) if keep_last is not None else None,
                        older_than_days=int(older_days) if older_days is not None else None,
                    )

        hass.services.async_register(
            DOMAIN, SERVICE_PURGE_HISTORY, _async_handle_purge_history
        )

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if isinstance(coordinator, BambuAIGuardCoordinator):
        coordinator.async_stop_listeners()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
