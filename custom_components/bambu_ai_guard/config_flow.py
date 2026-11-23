"""Config flow for Bambu AI Guard integration."""
from __future__ import annotations

import asyncio
from pathlib import Path
import socket
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import device_registry as dr, entity_registry as er, selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CHECK_MODES,
    CONF_ACCESS_CODE,
    CONF_AUTO_PAUSE,
    CONF_AUTO_PAUSE_THRESHOLD,
    CONF_CAMERA_ENTITY,
    CONF_CHECK_INTERVAL_LAYERS,
    CONF_CHECK_INTERVAL_MINUTES,
    CONF_CHECK_MODE,
    CONF_FIRST_LAYER_CHECKS,
    CONF_GEMINI_API_KEY,
    CONF_KINEMATICS,
    CONF_LAYER_ENTITY,
    CONF_PAUSE_ENTITY,
    CONF_PRINTER_DEVICE_ID,
    CONF_PRINTER_IP,
    CONF_PRINTER_MODEL,
    CONF_PRINTER_NAME,
    CONF_PRINTER_SERIAL,
    CONF_STATUS_ENTITY,
    CONF_TOTAL_LAYERS_ENTITY,
    CONF_USE_MEDIAN_FILTER,
    DEFAULT_AUTO_PAUSE,
    DEFAULT_AUTO_PAUSE_THRESHOLD,
    DEFAULT_CHECK_INTERVAL_LAYERS,
    DEFAULT_CHECK_INTERVAL_MINUTES,
    DEFAULT_CHECK_MODE,
    DEFAULT_FIRST_LAYER_CHECKS,
    DOMAIN,
    KINEMATICS_COREXY,
)
from .coordinator import resolve_bambu_device_entities
from .vision import GeminiDecisionsInspector, detect_printer_model_and_kinematics


def _get_bambu_printer_devices(hass: HomeAssistant) -> list[dr.DeviceEntry]:
    """Find all registered Bambu Lab 3D printer devices (excluding AMS/External Spool sub-devices)."""
    dev_reg = dr.async_get(hass)
    printers: list[dr.DeviceEntry] = []
    excluded_models = {
        "AMS",
        "AMS Lite",
        "AMS 2 Pro",
        "AMS HT",
        "External Spool",
        "Hotend Rack",
    }

    for device in dev_reg.devices.values():
        is_bambu = any(domain == "bambu_lab" for domain, _ in device.identifiers) or (
            device.manufacturer and "bambu" in device.manufacturer.lower()
        )
        if not is_bambu:
            continue
        if device.model in excluded_models:
            continue
        printers.append(device)

    return printers


def _discover_bambu_ssdp_sync(timeout: float = 1.5) -> dict[str, str]:
    """Quick UDP SSDP probe / listener on port 2021 for Bambu Lab printers on LAN."""
    discovered: dict[str, str] = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", 2021))
        sock.settimeout(timeout)
        data, addr = sock.recvfrom(4096)
        msg = data.decode("utf-8", errors="ignore")
        if "bambulab" in msg.lower():
            discovered["ip"] = addr[0]
            for line in msg.splitlines():
                low = line.lower()
                if low.startswith("usn:"):
                    discovered["serial"] = line.split(":", 1)[1].strip().split("::")[0]
                elif low.startswith("devname.bambu.com:"):
                    discovered["name"] = line.split(":", 1)[1].strip()
    except Exception:  # noqa: BLE001
        pass
    finally:
        sock.close()

    return discovered


class BambuAIGuardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bambu AI Guard."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step: select Bambu printer (HA device or Direct LAN) + Gemini API key."""
        errors: dict[str, str] = {}
        bambu_devices = _get_bambu_printer_devices(self.hass)

        if user_input is not None:
            api_key = user_input.get(CONF_GEMINI_API_KEY, "").strip()
            session = async_get_clientsession(self.hass)
            inspector = GeminiDecisionsInspector(session=session, api_key=api_key)
            valid, err_code = await inspector.async_validate_api_key()

            if not valid and err_code:
                errors["base"] = err_code
            else:
                device_id = user_input.get(CONF_PRINTER_DEVICE_ID)
                dev_reg = dr.async_get(self.hass)
                device = dev_reg.async_get(device_id) if device_id else None

                serial = user_input.get(CONF_PRINTER_SERIAL, "").strip().upper()
                printer_ip = user_input.get(CONF_PRINTER_IP, "").strip()
                access_code = user_input.get(CONF_ACCESS_CODE, "").strip()
                camera_entity = user_input.get(CONF_CAMERA_ENTITY)

                if device:
                    for dom, ident in device.identifiers:
                        if dom == "bambu_lab":
                            serial = ident
                            break
                    if not serial and device.serial_number:
                        serial = device.serial_number

                if not device and not camera_entity and (not printer_ip or not access_code):
                    errors["base"] = "missing_printer_connection"
                else:
                    raw_model = (
                        (device.model if device and device.model else None)
                        or user_input.get(CONF_PRINTER_MODEL)
                        or "P1P"
                    )
                    printer_model, kinematics = detect_printer_model_and_kinematics(
                        raw_model, serial
                    )
                    printer_name = (
                        (device.name_by_user or device.name)
                        if device
                        else f"Bambu Lab {printer_model}"
                    )
                    unique_key = serial or device_id or printer_ip or "default"

                    await self.async_set_unique_id(f"{DOMAIN}_{unique_key}")
                    self._abort_if_unique_id_configured()

                    resolved = (
                        resolve_bambu_device_entities(self.hass, device_id)
                        if device_id
                        else {}
                    )

                    entry_data: dict[str, Any] = {
                        CONF_PRINTER_DEVICE_ID: device_id,
                        CONF_PRINTER_NAME: printer_name,
                        CONF_PRINTER_MODEL: printer_model,
                        CONF_PRINTER_SERIAL: serial or unique_key,
                        CONF_KINEMATICS: kinematics,
                        CONF_PRINTER_IP: printer_ip,
                        CONF_ACCESS_CODE: access_code,
                        CONF_GEMINI_API_KEY: api_key,
                        CONF_CAMERA_ENTITY: camera_entity
                        or resolved.get(CONF_CAMERA_ENTITY),
                        CONF_LAYER_ENTITY: resolved.get(CONF_LAYER_ENTITY),
                        CONF_TOTAL_LAYERS_ENTITY: resolved.get(
                            CONF_TOTAL_LAYERS_ENTITY
                        ),
                        CONF_STATUS_ENTITY: resolved.get(CONF_STATUS_ENTITY),
                        CONF_PAUSE_ENTITY: resolved.get(CONF_PAUSE_ENTITY),
                        CONF_AUTO_PAUSE: DEFAULT_AUTO_PAUSE,
                        CONF_AUTO_PAUSE_THRESHOLD: DEFAULT_AUTO_PAUSE_THRESHOLD,
                        CONF_CHECK_MODE: DEFAULT_CHECK_MODE,
                        CONF_CHECK_INTERVAL_LAYERS: DEFAULT_CHECK_INTERVAL_LAYERS,
                        CONF_CHECK_INTERVAL_MINUTES: DEFAULT_CHECK_INTERVAL_MINUTES,
                        CONF_FIRST_LAYER_CHECKS: DEFAULT_FIRST_LAYER_CHECKS,
                        CONF_USE_MEDIAN_FILTER: kinematics == KINEMATICS_COREXY,
                    }

                    return self.async_create_entry(
                        title=f"{printer_name} AI Guard",
                        data=entry_data,
                    )

        schema_fields: dict[Any, Any] = {}
        if bambu_devices:
            # Mode A: ha-bambulab printer device already configured in Home Assistant (1 dropdown + 1 API key)
            default_dev = bambu_devices[0].id
            schema_fields[
                vol.Required(CONF_PRINTER_DEVICE_ID, default=default_dev)
            ] = selector.DeviceSelector(
                selector.DeviceSelectorConfig(
                    integration="bambu_lab",
                )
            )
        else:
            # Mode B: Check if any camera.* entity exists in Home Assistant, or fallback to auto-discovered LAN
            ent_reg = er.async_get(self.hass)
            has_cameras = any(
                e.domain in ("camera", "image") for e in ent_reg.entities.values()
            )
            ssdp_info = await self.hass.async_add_executor_job(
                _discover_bambu_ssdp_sync, 0.8
            )
            schema_fields[
                vol.Required(CONF_PRINTER_MODEL, default="P1P")
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["P1P", "P1S", "A1", "A1 Mini", "X1C", "X1E"],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
            if has_cameras:
                schema_fields[
                    vol.Optional(CONF_CAMERA_ENTITY)
                ] = selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["camera", "image"])
                )
            schema_fields[
                vol.Optional(
                    CONF_PRINTER_IP,
                    default=ssdp_info.get("ip", ""),
                )
            ] = selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
            )
            schema_fields[
                vol.Optional(
                    CONF_ACCESS_CODE,
                    default=ssdp_info.get("access_code", ""),
                )
            ] = selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            )
            schema_fields[
                vol.Optional(
                    CONF_PRINTER_SERIAL,
                    default=ssdp_info.get("serial", ""),
                )
            ] = selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
            )

        schema_fields[vol.Required(CONF_GEMINI_API_KEY)] = selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema_fields),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return BambuAIGuardOptionsFlow(config_entry)


class BambuAIGuardOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Bambu AI Guard."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        cfg = {**self._entry.data, **self._entry.options}
        kinematics = cfg.get(CONF_KINEMATICS, KINEMATICS_COREXY)

        schema_dict: dict[Any, Any] = {
            vol.Required(
                CONF_GEMINI_API_KEY,
                default=cfg.get(CONF_GEMINI_API_KEY, ""),
            ): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            ),
        }

        if not cfg.get(CONF_PRINTER_DEVICE_ID):
            schema_dict[
                vol.Required(
                    CONF_PRINTER_IP,
                    default=cfg.get(CONF_PRINTER_IP, ""),
                )
            ] = selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
            )
            schema_dict[
                vol.Required(
                    CONF_ACCESS_CODE,
                    default=cfg.get(CONF_ACCESS_CODE, ""),
                )
            ] = selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            )

        schema_dict.update(
            {
                vol.Required(
                    CONF_CHECK_MODE,
                    default=cfg.get(CONF_CHECK_MODE, DEFAULT_CHECK_MODE),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=CHECK_MODES,
                        translation_key="check_mode",
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_FIRST_LAYER_CHECKS,
                    default=cfg.get(
                        CONF_FIRST_LAYER_CHECKS, DEFAULT_FIRST_LAYER_CHECKS
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=5,
                        step=1,
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Required(
                    CONF_CHECK_INTERVAL_LAYERS,
                    default=cfg.get(
                        CONF_CHECK_INTERVAL_LAYERS, DEFAULT_CHECK_INTERVAL_LAYERS
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=50,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_CHECK_INTERVAL_MINUTES,
                    default=cfg.get(
                        CONF_CHECK_INTERVAL_MINUTES, DEFAULT_CHECK_INTERVAL_MINUTES
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=60,
                        step=1,
                        unit_of_measurement="min",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_AUTO_PAUSE,
                    default=cfg.get(CONF_AUTO_PAUSE, DEFAULT_AUTO_PAUSE),
                ): bool,
                vol.Required(
                    CONF_AUTO_PAUSE_THRESHOLD,
                    default=cfg.get(
                        CONF_AUTO_PAUSE_THRESHOLD, DEFAULT_AUTO_PAUSE_THRESHOLD
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=50,
                        max=99,
                        step=5,
                        unit_of_measurement="%",
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Required(
                    CONF_USE_MEDIAN_FILTER,
                    default=cfg.get(
                        CONF_USE_MEDIAN_FILTER, kinematics == KINEMATICS_COREXY
                    ),
                ): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema_dict))
