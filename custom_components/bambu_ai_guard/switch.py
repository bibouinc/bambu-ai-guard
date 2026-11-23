"""Switches for Bambu AI Guard (Auto-Pause on Defect, 3-Frame Median Nozzle Filter)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up Bambu AI Guard switches."""
    coordinator: BambuAIGuardCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            BambuAIGuardAutoPauseSwitch(coordinator),
            BambuAIGuardMedianFilterSwitch(coordinator),
        ]
    )


class BambuAIGuardAutoPauseSwitch(
    CoordinatorEntity[BambuAIGuardCoordinator], SwitchEntity
):
    """Switch to enable/disable automatic print pause on high-confidence failure."""

    _attr_has_entity_name = True
    _attr_translation_key = "auto_pause"
    _attr_icon = "mdi:pause-octagon"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: BambuAIGuardCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.printer_serial}_ai_auto_pause"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool:
        """Return true if auto-pause is enabled."""
        return self.coordinator.auto_pause_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable auto-pause."""
        self.coordinator.auto_pause_enabled = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable auto-pause."""
        self.coordinator.auto_pause_enabled = False
        self.async_write_ha_state()


class BambuAIGuardMedianFilterSwitch(
    CoordinatorEntity[BambuAIGuardCoordinator], SwitchEntity
):
    """Switch to enable/disable the 3-frame temporal median nozzle-erasing filter."""

    _attr_has_entity_name = True
    _attr_translation_key = "median_filter"
    _attr_icon = "mdi:image-filter-center-focus"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: BambuAIGuardCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.printer_serial}_ai_median_filter"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool:
        """Return true if 3-frame median filter is enabled."""
        return self.coordinator.use_median_filter

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable 3-frame median filter."""
        self.coordinator.use_median_filter = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable 3-frame median filter."""
        self.coordinator.use_median_filter = False
        self.async_write_ha_state()
