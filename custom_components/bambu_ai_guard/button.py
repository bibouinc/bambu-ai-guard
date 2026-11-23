"""Button entity to trigger an immediate on-demand Gemini AI inspection."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BambuAIGuardCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bambu AI Guard buttons."""
    coordinator: BambuAIGuardCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            BambuAIGuardInspectButton(coordinator),
            BambuAIGuardPurgeHistoryButton(coordinator),
        ]
    )


class BambuAIGuardInspectButton(
    CoordinatorEntity[BambuAIGuardCoordinator], ButtonEntity
):
    """Button to trigger an immediate AI snapshot and defect check."""

    _attr_has_entity_name = True
    _attr_translation_key = "inspect_now"
    _attr_icon = "mdi:camera-iris"

    def __init__(self, coordinator: BambuAIGuardCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.printer_serial}_ai_inspect_now"
        self._attr_device_info = coordinator.device_info

    async def async_press(self) -> None:
        """Run an immediate AI inspection."""
        await self.coordinator.async_run_inspection(manual=True)


class BambuAIGuardPurgeHistoryButton(
    CoordinatorEntity[BambuAIGuardCoordinator], ButtonEntity
):
    """Button to manually purge print history records older than the last X prints."""

    _attr_has_entity_name = True
    _attr_translation_key = "purge_history"
    _attr_icon = "mdi:delete-sweep-outline"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: BambuAIGuardCoordinator) -> None:
        """Initialize the purge button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.printer_serial}_ai_purge_history"
        self._attr_device_info = coordinator.device_info

    async def async_press(self) -> None:
        """Purge print records older than keep_last_prints."""
        await self.coordinator.async_purge_history()
