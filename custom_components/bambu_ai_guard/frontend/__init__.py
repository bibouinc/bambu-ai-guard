"""Auto-register the Bambu AI Guard custom Lovelace card in Home Assistant."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from homeassistant.components import panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later

from ..const import DOMAIN, LOGGER

URL_BASE = "/bambu_ai_guard_frontend"
CARD_FILENAME = "bambu-ai-guard-card.js"
PANEL_FILENAME = "bambu-ai-guard-panel.js"
CARD_VERSION = "1.7.4"


class BambuAIGuardCardRegistration:
    """Registers /bambu_ai_guard_frontend/bambu-ai-guard-card.js as a Lovelace module resource."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize card registration."""
        self.hass = hass

    @property
    def _lovelace(self) -> Any:
        return self.hass.data.get("lovelace")

    @property
    def _resource_mode(self) -> str:
        ll = self._lovelace
        if ll is None:
            return "yaml"
        if hasattr(ll, "resource_mode"):
            return str(ll.resource_mode)
        if hasattr(ll, "mode"):
            return str(ll.mode)
        if isinstance(ll, dict):
            return str(ll.get("mode", "yaml"))
        return "yaml"

    @property
    def _resources(self) -> Any:
        ll = self._lovelace
        if ll is None:
            return None
        if hasattr(ll, "resources"):
            return ll.resources
        if isinstance(ll, dict):
            return ll.get("resources")
        return None

    async def async_register(self) -> None:
        """Register static path, sidebar panel, and Lovelace card resource."""
        try:
            await self.hass.http.async_register_static_paths(
                [StaticPathConfig(URL_BASE, str(Path(__file__).parent), False)]
            )
        except RuntimeError:
            pass

        # Register dedicated Home Assistant Sidebar Panel ("Bambu AI Guard")
        try:
            await panel_custom.async_register_panel(
                self.hass,
                frontend_url_path=DOMAIN,
                webcomponent_name="bambu-ai-guard-panel",
                sidebar_title="Bambu AI Guard",
                sidebar_icon="mdi:printer-3d-nozzle-alert",
                module_url=f"{URL_BASE}/{PANEL_FILENAME}?v={CARD_VERSION}",
                require_admin=False,
            )
            LOGGER.info("Registered Bambu AI Guard sidebar panel at /%s", DOMAIN)
        except Exception as err:  # noqa: BLE001
            LOGGER.debug("Sidebar panel registration skipped/already exists: %s", err)

        if self._resource_mode == "storage":
            await self._async_wait_and_register_resource()

    async def _async_wait_and_register_resource(self) -> None:
        async def _check_loaded(_now: Any) -> None:
            res = self._resources
            if res is None:
                return
            if getattr(res, "loaded", True):
                await self._async_upsert_lovelace_resource()
            else:
                async_call_later(self.hass, 5, _check_loaded)

        await _check_loaded(0)

    async def _async_upsert_lovelace_resource(self) -> None:
        res = self._resources
        if res is None:
            return
        target_path = f"{URL_BASE}/{CARD_FILENAME}"
        target_url = f"{target_path}?v={CARD_VERSION}"

        existing = [
            item
            for item in res.async_items()
            if str(item.get("url", "")).split("?")[0] == target_path
        ]

        if existing:
            item = existing[0]
            if item.get("url") != target_url:
                await res.async_update_item(
                    item["id"], {"res_type": "module", "url": target_url}
                )
                LOGGER.info("Updated Bambu AI Guard Lovelace card to %s", CARD_VERSION)
        else:
            await res.async_create_item({"res_type": "module", "url": target_url})
            LOGGER.info("Registered Bambu AI Guard Lovelace card (%s)", target_url)
