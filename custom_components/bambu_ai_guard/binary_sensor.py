"""Binary sensors for Bambu AI Guard (Spaghetti, Warping, Detachment, First-Layer Defect)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STATUS_FAILURE, STATUS_WARNING
from .coordinator import BambuAIGuardCoordinator
from .vision import InspectionVerdict


@dataclass(frozen=True, kw_only=True)
class BambuAIGuardBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a Bambu AI Guard binary sensor."""

    is_on_fn: Callable[[InspectionVerdict], bool]
    prob_fn: Callable[[InspectionVerdict], float | None]


BINARY_SENSORS: tuple[BambuAIGuardBinarySensorDescription, ...] = (
    BambuAIGuardBinarySensorDescription(
        key="defect_detected",
        translation_key="defect_detected",
        icon="mdi:alert-circle",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda v: (
            v.status in (STATUS_FAILURE, STATUS_WARNING)
            or any(
                p is not None and p >= 0.50
                for p in (
                    v.spaghetti_prob,
                    v.warping_prob,
                    v.detachment_prob,
                    v.first_layer_prob,
                )
            )
        ),
        prob_fn=lambda v: max(
            (
                p
                for p in (
                    v.spaghetti_prob,
                    v.warping_prob,
                    v.detachment_prob,
                    v.first_layer_prob,
                    v.confidence if v.status in (STATUS_FAILURE, STATUS_WARNING) else None,
                )
                if p is not None
            ),
            default=None,
        ),
    ),
    BambuAIGuardBinarySensorDescription(
        key="spaghetti_detected",
        translation_key="spaghetti_detected",
        icon="mdi:pasta",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda v: (
            (v.status in (STATUS_FAILURE, STATUS_WARNING) and v.failure_type == "spaghetti")
            or (v.spaghetti_prob is not None and v.spaghetti_prob >= 0.50)
        ),
        prob_fn=lambda v: v.spaghetti_prob,
    ),
    BambuAIGuardBinarySensorDescription(
        key="warping_detected",
        translation_key="warping_detected",
        icon="mdi:angle-acute",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda v: (
            (v.status in (STATUS_FAILURE, STATUS_WARNING) and v.failure_type == "warping")
            or (v.warping_prob is not None and v.warping_prob >= 0.50)
        ),
        prob_fn=lambda v: v.warping_prob,
    ),
    BambuAIGuardBinarySensorDescription(
        key="detachment_detected",
        translation_key="detachment_detected",
        icon="mdi:cube-Off-outline",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda v: (
            (v.status in (STATUS_FAILURE, STATUS_WARNING) and v.failure_type == "detachment")
            or (v.detachment_prob is not None and v.detachment_prob >= 0.50)
        ),
        prob_fn=lambda v: v.detachment_prob,
    ),
    BambuAIGuardBinarySensorDescription(
        key="first_layer_defect",
        translation_key="first_layer_defect",
        icon="mdi:layers-off",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda v: (
            (
                v.status in (STATUS_FAILURE, STATUS_WARNING)
                and v.failure_type == "first_layer_defect"
            )
            or (v.first_layer_prob is not None and v.first_layer_prob >= 0.50)
        ),
        prob_fn=lambda v: v.first_layer_prob,
    ),
    BambuAIGuardBinarySensorDescription(
        key="any_failure_detected",
        translation_key="any_failure_detected",
        icon="mdi:alert-octagon",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda v: v.status == STATUS_FAILURE,
        prob_fn=lambda v: v.confidence,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bambu AI Guard binary sensors."""
    coordinator: BambuAIGuardCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        BambuAIGuardBinarySensor(coordinator, desc) for desc in BINARY_SENSORS
    )


class BambuAIGuardBinarySensor(
    CoordinatorEntity[BambuAIGuardCoordinator], BinarySensorEntity
):
    """Representation of a Bambu AI Guard defect binary sensor."""

    _attr_has_entity_name = True
    entity_description: BambuAIGuardBinarySensorDescription

    def __init__(
        self,
        coordinator: BambuAIGuardCoordinator,
        description: BambuAIGuardBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.printer_serial}_ai_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool:
        """Return true if the defect is detected."""
        return self.entity_description.is_on_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return live inspection attributes for automations."""
        v = self.coordinator.data
        prob = self.entity_description.prob_fn(v)
        return {
            "probability_pct": round(prob * 100.0, 1) if prob is not None else None,
            "status": v.status,
            "failure_type": v.failure_type,
            "recommended_action": v.recommended_action,
            "severity": v.severity,
            "spaghetti_pct": round(v.spaghetti_prob * 100.0, 1)
            if v.spaghetti_prob is not None
            else None,
            "warping_pct": round(v.warping_prob * 100.0, 1)
            if v.warping_prob is not None
            else None,
            "detachment_pct": round(v.detachment_prob * 100.0, 1)
            if v.detachment_prob is not None
            else None,
            "first_layer_defect_pct": round(v.first_layer_prob * 100.0, 1)
            if v.first_layer_prob is not None
            else None,
            "details": v.details,
            "layer": v.layer,
            "total_layers": v.total_layers,
            "printer_name": self.coordinator.printer_name,
            "printer_model": self.coordinator.printer_model,
            "last_updated": v.last_updated,
            "warnings": v.warnings,
        }
