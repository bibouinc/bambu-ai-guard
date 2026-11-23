"""Select entity for Bambu AI Guard inspection frequency mode (Layers, Minutes, Both)."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CHECK_MODES, DOMAIN
from .coordinator import BambuAIGuardCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bambu AI Guard select entities."""
    coordinator: BambuAIGuardCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BambuAIGuardCheckModeSelect(coordinator)])


class BambuAIGuardCheckModeSelect(
    CoordinatorEntity[BambuAIGuardCoordinator], SelectEntity
):
    """Select entity to choose between Layer-based, Minute-based, or Combined inspection schedule."""

    _attr_has_entity_name = True
    _attr_translation_key = "check_mode"
    _attr_icon = "mdi:calendar-clock"
    _attr_options = CHECK_MODES
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: BambuAIGuardCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.printer_serial}_ai_check_mode"
        self._attr_device_info = coordinator.device_info

    @property
    def current_option(self) -> str:
        """Return the current check mode."""
        return self.coordinator.check_mode

    async def async_select_option(self, option: str) -> None:
        """Change the selected check mode."""
        if option in CHECK_MODES:
            self.coordinator.check_mode = option
            self.async_write_ha_state()
