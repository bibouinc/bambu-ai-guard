"""Constants for the Bambu AI Guard integration."""
from __future__ import annotations

import logging
from homeassistant.const import Platform

DOMAIN = "bambu_ai_guard"
BRAND = "Bambu Lab"
LOGGER = logging.getLogger(__package__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.CAMERA,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.BUTTON,
]

# Configuration keys
CONF_GEMINI_API_KEY = "gemini_api_key"
CONF_PRINTER_DEVICE_ID = "printer_device_id"
CONF_PRINTER_NAME = "printer_name"
CONF_PRINTER_MODEL = "printer_model"
CONF_PRINTER_SERIAL = "printer_serial"
CONF_KINEMATICS = "kinematics"

# Entity links (auto-discovered from ha-bambulab or manual)
CONF_CAMERA_ENTITY = "camera_entity"
CONF_LAYER_ENTITY = "layer_entity"
CONF_TOTAL_LAYERS_ENTITY = "total_layers_entity"
CONF_STATUS_ENTITY = "status_entity"
CONF_PAUSE_ENTITY = "pause_entity"
CONF_SUBTASK_ENTITY = "subtask_entity"

# Optional direct LAN fallback (if ha-bambulab camera is not used)
CONF_PRINTER_IP = "printer_ip"
CONF_ACCESS_CODE = "access_code"

# Runtime inspection & scheduling options
CONF_AUTO_PAUSE = "auto_pause"
CONF_AUTO_PAUSE_THRESHOLD = "auto_pause_threshold"
CONF_CHECK_MODE = "check_mode"
CONF_CHECK_INTERVAL_LAYERS = "check_interval_layers"
CONF_CHECK_INTERVAL_MINUTES = "check_interval_minutes"
CONF_FIRST_LAYER_CHECKS = "first_layer_checks"
CONF_USE_MEDIAN_FILTER = "use_median_filter"
CONF_NOTIFY_TARGET = "notify_target"

# Notification defaults
NOTIFY_TARGET_NONE = "none"
NOTIFY_TARGET_ALL = "notify.notify"
DEFAULT_NOTIFY_TARGET = NOTIFY_TARGET_ALL

# Schedule modes
CHECK_MODE_LAYERS = "layers"
CHECK_MODE_MINUTES = "minutes"
CHECK_MODE_BOTH = "both"
CHECK_MODES: list[str] = [
    CHECK_MODE_LAYERS,
    CHECK_MODE_MINUTES,
    CHECK_MODE_BOTH,
]

# Defaults
DEFAULT_AUTO_PAUSE = True
DEFAULT_AUTO_PAUSE_THRESHOLD = 80
DEFAULT_CHECK_MODE = CHECK_MODE_BOTH
DEFAULT_CHECK_INTERVAL_LAYERS = 10
DEFAULT_CHECK_INTERVAL_MINUTES = 5
DEFAULT_FIRST_LAYER_CHECKS = 3

# Critical checkpoints always inspected on layer transition
CRITICAL_CHECKPOINT_LAYERS: tuple[int, ...] = (2, 3, 5, 25)

# Kinematics classification
KINEMATICS_COREXY = "corexy"
KINEMATICS_BEDSLINGER = "bedslinger"

BEDSLINGER_MODELS = {"A1", "A1 MINI", "A1MINI", "A1_MINI"}
COREXY_MODELS = {"P1P", "P1S", "X1C", "X1", "X1E", "H2D", "H2C"}

# Serial prefix mapping for automatic model detection
SERIAL_PREFIX_TO_MODEL: dict[str, tuple[str, str]] = {
    "01S": ("P1P", KINEMATICS_COREXY),
    "01P": ("P1S", KINEMATICS_COREXY),
    "00M": ("X1C", KINEMATICS_COREXY),
    "00W": ("X1E", KINEMATICS_COREXY),
    "039": ("A1", KINEMATICS_BEDSLINGER),
    "030": ("A1 Mini", KINEMATICS_BEDSLINGER),
}

# Status values
STATUS_IDLE = "IDLE"
STATUS_OK = "OK"
STATUS_WARNING = "WARNING"
STATUS_FAILURE = "FAILURE"
STATUS_ERROR = "API_ERROR"

# Services
SERVICE_INSPECT_NOW = "inspect_now"
SERVICE_PURGE_HISTORY = "purge_history"
