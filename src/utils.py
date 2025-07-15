import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import yaml
from loguru import logger


class Config:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._config:
            self.load_config()

    def load_config(self, config_path: str = "config/config.yaml") -> None:
        """Load configuration from YAML file."""
        try:
            with open(config_path, "r") as f:
                self._config = yaml.safe_load(f)
            self._setup_logging()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_config = self._config.get("logging", {})
        log_file = log_config.get("file", "logs/app.log")

        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # Configure logger
        logger.remove()  # Clear default handler
        logger.add(
            log_file,
            rotation=log_config.get("rotation", "1 day"),
            retention=log_config.get("retention", "7 days"),
            level=log_config.get("level", "INFO"),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        )
        logger.add(lambda msg: print(msg), level=log_config.get("level", "INFO"))

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self._config.copy()


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def ensure_directory(directory: str) -> None:
    """Ensure directory exists, create if it doesn't."""
    os.makedirs(directory, exist_ok=True)


def validate_global_config(config: dict):
    required_sections = ["model", "processing", "logging", "preprocessing"]
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Global config missing required section: {section}")

    # Model section
    model = config["model"]
    for field in ["path", "sequence_length", "frame_size"]:
        if field not in model:
            raise ValueError(f"Global config 'model' missing field: {field}")

    # Processing section
    processing = config["processing"]
    if "probability_thresholds" not in processing:
        raise ValueError("Global config 'processing' missing 'probability_thresholds'")

    # Preprocessing section
    preprocessing = config["preprocessing"]
    required_preprocessing = ["grayscale"]
    for field in required_preprocessing:
        if field not in preprocessing:
            raise ValueError(f"Global config 'preprocessing' missing field: {field}")

    # Logging section
    logging = config["logging"]
    for field in ["level", "file"]:
        if field not in logging:
            raise ValueError(f"Global config 'logging' missing field: {field}")


def load_config(config_path: str = None) -> dict:
    if config_path is None:
        config_path = get_config_path()
    try:
        with open(config_path, "r") as f:
            if config_path.endswith(".yaml") or config_path.endswith(".yml"):
                config = yaml.safe_load(f)
            else:
                config = json.load(f)
        validate_global_config(config)
        logger.info("Configuration loaded and validated successfully")
        return config
    except Exception as e:
        logger.error(f"Failed to load or validate configuration: {e}")
        raise


def setup_environment():
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
    os.environ["TF_ENABLE_AUTO_MIXED_PRECISION"] = "1"
    os.environ["TF_ENABLE_ONEDNN_OPTS"] = "1"
    cv2.setNumThreads(4)


# Function removed - camera configs now loaded from unified config.yaml


# --- ENV VAR OVERRIDES ---
def get_config_path():
    return os.environ.get("APP_CONFIG_PATH", "config/config.yaml")


def get_camera_config_path():
    # Camera configs moved to main config.yaml
    return os.environ.get("APP_CONFIG_PATH", "config/config.yaml")


# --- CAMERA CONFIG VALIDATION ---
def validate_camera_config(cam: dict):
    required_fields = [
        "id",
        "name",
        "location_id",
        "zone_name",
        "source",
        "camera_type",
        "fps",
    ]
    for field in required_fields:
        if field not in cam:
            raise ValueError(f"Camera config missing required field: {field}")

    # Add default enabled status if not provided
    if "enabled" not in cam:
        cam["enabled"] = True

    # Handle resolution field - convert from nested format to flat format for compatibility
    if "resolution" in cam and isinstance(cam["resolution"], dict):
        cam["resolution_width"] = cam["resolution"]["width"]
        cam["resolution_height"] = cam["resolution"]["height"]
    elif "resolution_width" not in cam or "resolution_height" not in cam:
        # Set defaults if neither format is provided
        cam["resolution_width"] = 640
        cam["resolution_height"] = 480

    # Add more checks as needed (e.g., type checks, value ranges)
    if cam["camera_type"] not in ("usb", "ip"):
        raise ValueError(f"Invalid camera_type: {cam['camera_type']}")
    if not isinstance(cam["enabled"], bool):
        raise ValueError(f"'enabled' must be a boolean in camera config: {cam['id']}")
    if not isinstance(cam["fps"], int) or cam["fps"] <= 0:
        raise ValueError(
            f"'fps' must be a positive integer in camera config: {cam['id']}"
        )
    if not isinstance(cam["resolution_width"], int) or cam["resolution_width"] <= 0:
        raise ValueError(
            f"'resolution_width' must be a positive integer in camera config: {cam['id']}"
        )
    if not isinstance(cam["resolution_height"], int) or cam["resolution_height"] <= 0:
        raise ValueError(
            f"'resolution_height' must be a positive integer in camera config: {cam['id']}"
        )
    if "logging_level" in cam and cam["logging_level"] not in (
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ):
        raise ValueError(
            f"Invalid logging_level: {cam['logging_level']}. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL"
        )
    # Validate alert configuration
    if "alerts" in cam:
        alerts = cam["alerts"]
        if not isinstance(alerts, dict):
            raise ValueError(
                f"'alerts' must be a dictionary in camera config: {cam['id']}"
            )
        # Validate webhooks
        if "webhooks" in alerts:
            webhooks = alerts["webhooks"]
            if not isinstance(webhooks, list):
                raise ValueError(
                    f"'alerts.webhooks' must be a list in camera config: {cam['id']}"
                )
            for webhook in webhooks:
                if not isinstance(webhook, dict):
                    raise ValueError(
                        f"Each webhook must be a dictionary in camera config: {cam['id']}"
                    )
                if "url" not in webhook:
                    raise ValueError(
                        f"Webhook missing required 'url' field in camera config: {cam['id']}"
                    )
        # Validate email
        if "email" in alerts:
            email = alerts["email"]
            if not isinstance(email, dict):
                raise ValueError(
                    f"'alerts.email' must be a dictionary in camera config: {cam['id']}"
                )
            if "recipients" not in email:
                raise ValueError(
                    f"'alerts.email' missing required 'recipients' field in camera config: {cam['id']}"
                )
            if not isinstance(email["recipients"], list):
                raise ValueError(
                    f"'alerts.email.recipients' must be a list in camera config: {cam['id']}"
                )
        # Validate cooldown
        if "cooldown" in alerts:
            cooldown = alerts["cooldown"]
            if not isinstance(cooldown, (int, float)) or cooldown < 0:
                raise ValueError(
                    f"'alerts.cooldown' must be a positive number in camera config: {cam['id']}"
                )
    # Validate ROIs
    if "rois" in cam:
        rois = cam["rois"]
        if not isinstance(rois, list):
            raise ValueError(f"'rois' must be a list in camera config: {cam['id']}")
        for roi in rois:
            if not isinstance(roi, dict):
                raise ValueError(
                    f"Each ROI must be a dictionary in camera config: {cam['id']}"
                )
            required_roi_fields = ["name", "points"]
            for field in required_roi_fields:
                if field not in roi:
                    raise ValueError(
                        f"ROI missing required field '{field}' in camera config: {cam['id']}"
                    )
            if not isinstance(roi["points"], list) or len(roi["points"]) < 3:
                raise ValueError(
                    f"ROI 'points' must be a list of at least 3 points in camera config: {cam['id']}"
                )
            for point in roi["points"]:
                if not isinstance(point, list) or len(point) != 2:
                    raise ValueError(
                        f"ROI point must be a list of 2 coordinates [x,y] in camera config: {cam['id']}"
                    )
                if not all(isinstance(coord, (int, float)) for coord in point):
                    raise ValueError(
                        f"ROI coordinates must be numbers in camera config: {cam['id']}"
                    )
    # Validate model parameters
    if "model_params" in cam:
        model_params = cam["model_params"]
        if not isinstance(model_params, dict):
            raise ValueError(
                f"'model_params' must be a dictionary in camera config: {cam['id']}"
            )
        # Validate sequence_length
        if "sequence_length" in model_params:
            seq_len = model_params["sequence_length"]
            if not isinstance(seq_len, int) or seq_len <= 0:
                raise ValueError(
                    f"'model_params.sequence_length' must be a positive integer in camera config: {cam['id']}"
                )
        # Validate frame_size
        if "frame_size" in model_params:
            frame_size = model_params["frame_size"]
            if not isinstance(frame_size, (list, tuple)) or len(frame_size) != 2:
                raise ValueError(
                    f"'model_params.frame_size' must be a list/tuple of 2 integers in camera config: {cam['id']}"
                )
            if not all(isinstance(dim, int) and dim > 0 for dim in frame_size):
                raise ValueError(
                    f"'model_params.frame_size' dimensions must be positive integers in camera config: {cam['id']}"
                )
        # Validate batch_size
        if "batch_size" in model_params:
            batch_size = model_params["batch_size"]
            if not isinstance(batch_size, int) or batch_size <= 0:
                raise ValueError(
                    f"'model_params.batch_size' must be a positive integer in camera config: {cam['id']}"
                )
        # Validate inference_mode
        if "inference_mode" in model_params:
            inference_mode = model_params["inference_mode"]
            if inference_mode not in ("cpu", "gpu", "tpu"):
                raise ValueError(
                    f"'model_params.inference_mode' must be one of: cpu, gpu, tpu in camera config: {cam['id']}"
                )


def resize_frame(frame, target_size):
    """Resize frame to target size while maintaining aspect ratio."""
    if frame is None:
        return None
    h, w = frame.shape[:2]
    target_w, target_h = target_size

    # Calculate aspect ratios
    aspect_ratio = w / h
    target_ratio = target_w / target_h

    if aspect_ratio > target_ratio:
        # Width is larger relative to height
        new_w = target_w
        new_h = int(target_w / aspect_ratio)
    else:
        # Height is larger relative to width
        new_h = target_h
        new_w = int(target_h * aspect_ratio)

    # Resize
    resized = cv2.resize(frame, (new_w, new_h))

    # Create black canvas of target size
    canvas = np.zeros((target_h, target_w, frame.shape[2]), dtype=frame.dtype)

    # Calculate position to paste resized image
    x_offset = (target_w - new_w) // 2
    y_offset = (target_h - new_h) // 2

    # Paste resized image onto canvas
    canvas[y_offset : y_offset + new_h, x_offset : x_offset + new_w] = resized

    return canvas


@dataclass
class CameraConfig:
    id: str
    name: str
    location_id: str
    zone_name: str
    source: object  # int for USB, str for IP
    camera_type: str  # 'usb' or 'ip'
    enabled: bool
    fps: int
    resolution_width: int
    resolution_height: int
    ip_address: Optional[str] = None
    port: Optional[int] = None
    credentials: Optional[str] = None
    model_path: Optional[str] = None
    preprocessing: Optional[dict] = None
    thresholds: Optional[dict] = None
    output_path: Optional[str] = None
    logging_level: Optional[str] = None
    alerts: Optional[dict] = None
    rois: Optional[List[dict]] = None
    model_params: Optional[dict] = None


def load_camera_configs(path=None) -> List[CameraConfig]:
    if path is None:
        path = get_camera_config_path()

    # Load cameras from the unified config.yaml file
    with open(path, "r") as f:
        if path.endswith(".yaml") or path.endswith(".yml"):
            config = yaml.safe_load(f)
        else:
            config = json.load(f)

    # Extract cameras section from config
    cameras_data = config.get("cameras", [])

    for cam in cameras_data:
        validate_camera_config(cam)
    return [CameraConfig(**cam) for cam in cameras_data]
