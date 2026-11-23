"""The Bambu AI Guard integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, PLATFORMS, SERVICE_INSPECT_NOW, SERVICE_PURGE_HISTORY
from .coordinator import BambuAIGuardCoordinator
from .frontend import BambuAIGuardCardRegistration


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bambu AI Guard from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    if "card_registered" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["card_registered"] = True
        card_reg = BambuAIGuardCardRegistration(hass)
        await card_reg.async_register()

    coordinator = BambuAIGuardCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    coordinator.async_start_listeners()

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    if not hass.services.has_service(DOMAIN, SERVICE_INSPECT_NOW):

        async def _async_handle_inspect_now(call: ServiceCall) -> None:
            entry_id = call.data.get("entry_id")
            for cid, coord in hass.data.get(DOMAIN, {}).items():
                if not entry_id or cid == entry_id:
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
                if not entry_id or cid == entry_id:
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
    coordinator: BambuAIGuardCoordinator | None = hass.data.get(DOMAIN, {}).get(
        entry.entry_id
    )
    if coordinator:
        coordinator.async_stop_listeners()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
