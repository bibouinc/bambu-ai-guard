"""Camera entity showing the latest AI-inspected (or 3-frame median composite) snapshot."""
from __future__ import annotations

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BambuAIGuardCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Bambu AI Guard composite snapshot camera."""
    coordinator: BambuAIGuardCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BambuAIGuardCompositeCamera(coordinator)])


class BambuAIGuardCompositeCamera(
    CoordinatorEntity[BambuAIGuardCoordinator], Camera
):
    """Camera displaying the latest inspected (or nozzle-erased median) print snapshot."""

    _attr_has_entity_name = True
    _attr_translation_key = "ai_composite_camera"
    _attr_icon = "mdi:camera-enhance"

    def __init__(self, coordinator: BambuAIGuardCoordinator) -> None:
        """Initialize the camera."""
        super().__init__(coordinator)
        Camera.__init__(self)
        self._attr_unique_id = f"{coordinator.printer_serial}_ai_composite_camera"
        self._attr_device_info = coordinator.device_info

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return bytes of the latest composite camera image (or fast single-frame live preview)."""
        if self.coordinator.latest_composite_jpeg:
            return self.coordinator.latest_composite_jpeg
        frame = await self.coordinator._async_capture_single_frame()
        if frame:
            self.coordinator.latest_composite_jpeg = frame
        return frame
