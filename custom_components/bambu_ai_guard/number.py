"""Number entities for Bambu AI Guard (Threshold, Layer Interval, Minute Interval, Layer 1 Checks)."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
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
    """Set up Bambu AI Guard number entities."""
    coordinator: BambuAIGuardCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            BambuAIGuardThresholdNumber(coordinator),
            BambuAIGuardFirstLayerChecksNumber(coordinator),
            BambuAIGuardLayerIntervalNumber(coordinator),
            BambuAIGuardMinuteIntervalNumber(coordinator),
            BambuAIGuardPurgeKeepPrintsNumber(coordinator),
        ]
    )


class BambuAIGuardThresholdNumber(
    CoordinatorEntity[BambuAIGuardCoordinator], NumberEntity
):
    """Number entity for the confidence threshold required to auto-pause a print."""

    _attr_has_entity_name = True
    _attr_translation_key = "auto_pause_threshold"
    _attr_icon = "mdi:tune-vertical"
    _attr_native_min_value = 50
    _attr_native_max_value = 99
    _attr_native_step = 5
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: BambuAIGuardCoordinator) -> None:
        """Initialize the threshold number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.printer_serial}_ai_auto_pause_threshold"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float:
        """Return current threshold."""
        return float(self.coordinator.auto_pause_threshold)

    async def async_set_native_value(self, value: float) -> None:
        """Update current threshold."""
        self.coordinator.auto_pause_threshold = int(value)
        self.async_write_ha_state()


class BambuAIGuardFirstLayerChecksNumber(
    CoordinatorEntity[BambuAIGuardCoordinator], NumberEntity
):
    """Number entity for how many inspections (0-5) to run during Layer 1."""

    _attr_has_entity_name = True
    _attr_translation_key = "first_layer_checks"
    _attr_icon = "mdi:numeric-1-box-multiple-outline"
    _attr_native_min_value = 0
    _attr_native_max_value = 5
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: BambuAIGuardCoordinator) -> None:
        """Initialize the Layer 1 checks number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.printer_serial}_ai_first_layer_checks"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float:
        """Return number of Layer 1 checks."""
        return float(self.coordinator.first_layer_checks)

    async def async_set_native_value(self, value: float) -> None:
        """Update number of Layer 1 checks."""
        self.coordinator.first_layer_checks = int(value)
        self.async_write_ha_state()


class BambuAIGuardLayerIntervalNumber(
    CoordinatorEntity[BambuAIGuardCoordinator], NumberEntity
):
    """Number entity for how often (every X layers) to run AI inspection."""

    _attr_has_entity_name = True
    _attr_translation_key = "check_interval_layers"
    _attr_icon = "mdi:layers-triple"
    _attr_native_min_value = 1
    _attr_native_max_value = 50
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: BambuAIGuardCoordinator) -> None:
        """Initialize the layer interval number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.printer_serial}_ai_check_interval_layers"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float:
        """Return current layer interval."""
        return float(self.coordinator.check_interval_layers)

    async def async_set_native_value(self, value: float) -> None:
        """Update current layer interval."""
        self.coordinator.check_interval_layers = int(value)
        self.async_write_ha_state()


class BambuAIGuardMinuteIntervalNumber(
    CoordinatorEntity[BambuAIGuardCoordinator], NumberEntity
):
    """Number entity for how often (every X minutes) to run AI inspection."""

    _attr_has_entity_name = True
    _attr_translation_key = "check_interval_minutes"
    _attr_icon = "mdi:timer-cog-outline"
    _attr_native_min_value = 1
    _attr_native_max_value = 60
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_mode = NumberMode.BOX
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: BambuAIGuardCoordinator) -> None:
        """Initialize the minute interval number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.printer_serial}_ai_check_interval_minutes"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float:
        """Return current minute interval."""
        return float(self.coordinator.check_interval_minutes)

    async def async_set_native_value(self, value: float) -> None:
        """Update current minute interval."""
        self.coordinator.check_interval_minutes = int(value)
        self.async_write_ha_state()


class BambuAIGuardPurgeKeepPrintsNumber(
    CoordinatorEntity[BambuAIGuardCoordinator], NumberEntity
):
    """Number entity for how many recent prints (X) to keep when clicking Manual Purge."""

    _attr_has_entity_name = True
    _attr_translation_key = "purge_keep_prints"
    _attr_icon = "mdi:database-cog-outline"
    _attr_native_min_value = 0
    _attr_native_max_value = 1000
    _attr_native_step = 5
    _attr_mode = NumberMode.BOX
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: BambuAIGuardCoordinator) -> None:
        """Initialize the purge keep prints number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.printer_serial}_ai_purge_keep_prints"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float:
        """Return number of prints to keep on manual purge."""
        return float(self.coordinator.purge_keep_prints)

    async def async_set_native_value(self, value: float) -> None:
        """Update number of prints to keep on manual purge."""
        self.coordinator.purge_keep_prints = int(value)
        self.async_write_ha_state()
