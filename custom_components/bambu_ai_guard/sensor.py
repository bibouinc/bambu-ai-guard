"""Sensors for Bambu AI Guard (Status, Confidence, Probabilities, Latency)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STATUS_IDLE
from .coordinator import BambuAIGuardCoordinator
from .vision import InspectionVerdict


def _build_ai_status_attrs(
    c: BambuAIGuardCoordinator, v: InspectionVerdict
) -> dict[str, Any]:
    """Build attributes for the primary AI Guard status sensor, preserving last check across restarts."""
    last_hist = c.history.recent_inspections[-1] if c.history.recent_inspections else None
    has_live_verdict = v.status != STATUS_IDLE
    last_check_ts = (
        v.last_updated
        if has_live_verdict
        else (last_hist.get("timestamp") if last_hist else None)
    )
    last_check_layer = (
        v.layer
        if has_live_verdict and v.layer is not None
        else (last_hist.get("layer") if last_hist else None)
    )
    last_check_total = (
        v.total_layers
        if has_live_verdict and v.total_layers
        else (last_hist.get("total_layers") if last_hist else None)
    )
    last_check_trigger = (
        v.trigger_reason
        if has_live_verdict
        else (last_hist.get("trigger") if last_hist else None)
    )
    last_check_latency = (
        v.latency_ms
        or c.last_api_latency_ms
        or (last_hist.get("latency_ms") if last_hist else None)
    )
    return {
        "printer_model": c.printer_model,
        "kinematics": c.kinematics,
        "failure_type": v.failure_type,
        "recommended_action": v.recommended_action,
        "details": v.details,
        "confidence_pct": round(v.confidence * 100.0, 1)
        if v.confidence is not None
        else None,
        "spaghetti_pct": round(v.spaghetti_prob * 100.0, 1)
        if v.spaghetti_prob is not None
        else (last_hist.get("spaghetti_pct") if last_hist else None),
        "warping_pct": round(v.warping_prob * 100.0, 1)
        if v.warping_prob is not None
        else (last_hist.get("warping_pct") if last_hist else None),
        "detachment_pct": round(v.detachment_prob * 100.0, 1)
        if v.detachment_prob is not None
        else (last_hist.get("detachment_pct") if last_hist else None),
        "first_layer_defect_pct": round(v.first_layer_prob * 100.0, 1)
        if v.first_layer_prob is not None
        else (last_hist.get("first_layer_pct") if last_hist else None),
        "severity": v.severity,
        "provider": v.provider,
        "model": v.model,
        "latency_ms": last_check_latency,
        "layer": last_check_layer,
        "total_layers": last_check_total,
        "current_layer": c.get_current_layer(),
        "current_total_layers": c.get_total_layers(),
        "is_printing": c.is_printer_running(),
        "print_name": c.get_subtask_name(),
        "trigger_reason": last_check_trigger,
        "frames_merged": v.frames_merged,
        "total_inspections": c.total_inspections,
        "calls_today": c.calls_today,
        "rate_limited": c.rate_limited,
        "failures_detected": c.failures_detected,
        "warnings": v.warnings,
        "last_updated": last_check_ts,
        "last_check_timestamp": last_check_ts,
    }


@dataclass(frozen=True, kw_only=True)
class BambuAIGuardSensorDescription(SensorEntityDescription):
    """Describes a Bambu AI Guard sensor."""

    value_fn: Callable[[BambuAIGuardCoordinator, InspectionVerdict], Any]
    attr_fn: Callable[[BambuAIGuardCoordinator, InspectionVerdict], dict[str, Any]] = (
        lambda _c, _v: {}
    )


SENSORS: tuple[BambuAIGuardSensorDescription, ...] = (
    BambuAIGuardSensorDescription(
        key="ai_status",
        translation_key="ai_status",
        icon="mdi:shield-Search",
        value_fn=lambda _c, v: v.status,
        attr_fn=_build_ai_status_attrs,
    ),
    BambuAIGuardSensorDescription(
        key="ai_confidence",
        translation_key="ai_confidence",
        icon="mdi:percent-circle",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda _c, v: round(v.confidence * 100.0, 1)
        if v.confidence is not None
        else None,
    ),
    BambuAIGuardSensorDescription(
        key="spaghetti_probability",
        translation_key="spaghetti_probability",
        icon="mdi:pasta",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda _c, v: round(v.spaghetti_prob * 100.0, 1)
        if v.spaghetti_prob is not None
        else None,
    ),
    BambuAIGuardSensorDescription(
        key="warping_probability",
        translation_key="warping_probability",
        icon="mdi:angle-acute",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda _c, v: round(v.warping_prob * 100.0, 1)
        if v.warping_prob is not None
        else None,
    ),
    BambuAIGuardSensorDescription(
        key="api_latency",
        translation_key="api_latency",
        icon="mdi:speedometer",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda _c, v: v.latency_ms,
    ),
    BambuAIGuardSensorDescription(
        key="print_history",
        translation_key="print_history",
        icon="mdi:history",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c, _v: len(c.history.prints),
        attr_fn=lambda c, _v: {
            "total_prints_recorded": len(c.history.prints),
            "purge_keep_prints_setting": c.purge_keep_prints,
            "recent_prints": list(reversed(c.history.prints[-50:])),
            "recent_inspections": list(reversed(c.history.recent_inspections[-30:])),
            "simulations": c.history.simulations,
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bambu AI Guard sensors."""
    coordinator: BambuAIGuardCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(BambuAIGuardSensor(coordinator, desc) for desc in SENSORS)


class BambuAIGuardSensor(CoordinatorEntity[BambuAIGuardCoordinator], SensorEntity):
    """Representation of a Bambu AI Guard sensor."""

    _attr_has_entity_name = True
    entity_description: BambuAIGuardSensorDescription

    def __init__(
        self,
        coordinator: BambuAIGuardCoordinator,
        description: BambuAIGuardSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.printer_serial}_ai_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> Any:
        """Return the value reported by the AI inspector (or None when not yet evaluated)."""
        return self.entity_description.value_fn(self.coordinator, self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return self.entity_description.attr_fn(self.coordinator, self.coordinator.data)
