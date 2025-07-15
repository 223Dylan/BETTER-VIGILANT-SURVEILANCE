"""
Configuration management module.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import yaml

logger = logging.getLogger(__name__)


@dataclass
class CameraConfig:
    """Camera configuration data class."""

    id: str
    name: str
    location_id: str
    zone_name: str
    source: Any  # Can be int (for USB) or str (for IP)
    camera_type: str
    enabled: bool = True
    fps: int = 30
    resolution_width: int = 640
    resolution_height: int = 480
    ip_address: Optional[str] = None
    port: Optional[int] = None
    credentials: Optional[Dict[str, str]] = None
    model_path: Optional[str] = None
    model: Optional[str] = None
    preprocessing: Optional[Dict[str, Any]] = None
    thresholds: Optional[Dict[str, Any]] = None
    output_path: Optional[str] = None
    logging_level: str = "INFO"
    alerts: Optional[Dict[str, Any]] = None
    rois: Optional[List[Dict[str, Any]]] = None
    model_params: Optional[Dict[str, Any]] = None

    @property
    def url(self) -> str:
        """Get camera URL based on type."""
        if self.camera_type == "usb":
            return str(self.source)
        elif self.camera_type == "ip":
            protocol = "rtsp" if self.port == 554 else "http"
            auth = (
                f"{self.credentials['username']}:{self.credentials['password']}@"
                if self.credentials
                else ""
            )
            return f"{protocol}://{auth}{self.ip_address}:{self.port}"
        else:
            raise ValueError(f"Unsupported camera type: {self.camera_type}")

    @property
    def resolution(self) -> tuple:
        """Get resolution as tuple."""
        return (self.resolution_width, self.resolution_height)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CameraConfig":
        """Create CameraConfig from dictionary."""
        try:
            # Ensure required fields are present
            required_fields = [
                "id",
                "name",
                "location_id",
                "zone_name",
                "source",
                "camera_type",
            ]
            if not all(k in data for k in required_fields):
                missing = [k for k in required_fields if k not in data]
                raise ValueError(f"Missing required fields: {', '.join(missing)}")

            # Handle resolution field
            resolution_width = data.get("resolution_width", 640)
            resolution_height = data.get("resolution_height", 480)
            if "resolution" in data:
                resolution = data["resolution"]
                if isinstance(resolution, dict):
                    resolution_width = resolution.get("width", resolution_width)
                    resolution_height = resolution.get("height", resolution_height)

            return cls(
                id=str(data["id"]),
                name=str(data["name"]),
                location_id=str(data["location_id"]),
                zone_name=str(data["zone_name"]),
                source=data["source"],
                camera_type=str(data["camera_type"]),
                enabled=bool(data.get("enabled", True)),
                fps=int(data.get("fps", 30)),
                resolution_width=int(resolution_width),
                resolution_height=int(resolution_height),
                ip_address=data.get("ip_address"),
                port=data.get("port"),
                credentials=data.get("credentials"),
                model_path=data.get("model_path"),
                model=data.get("model"),
                preprocessing=data.get("preprocessing"),
                thresholds=data.get("thresholds"),
                output_path=data.get("output_path"),
                logging_level=str(data.get("logging_level", "INFO")),
                alerts=data.get("alerts"),
                rois=data.get("rois"),
                model_params=data.get("model_params"),
            )
        except Exception as e:
            logger.error(f"Error creating CameraConfig from data: {str(e)}")
            raise

    def to_dict(self) -> Dict[str, Any]:
        """Convert CameraConfig to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "location_id": self.location_id,
            "zone_name": self.zone_name,
            "source": self.source,
            "camera_type": self.camera_type,
            "enabled": self.enabled,
            "fps": self.fps,
            "resolution_width": self.resolution_width,
            "resolution_height": self.resolution_height,
            "ip_address": self.ip_address,
            "port": self.port,
            "credentials": self.credentials,
            "model_path": self.model_path,
            "model": self.model,
            "preprocessing": self.preprocessing,
            "thresholds": self.thresholds,
            "output_path": self.output_path,
            "logging_level": self.logging_level,
            "alerts": self.alerts,
            "rois": self.rois,
            "model_params": self.model_params,
        }


class Config:
    """Configuration management class."""

    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize configuration."""
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    if self.config_path.endswith(".yaml") or self.config_path.endswith(
                        ".yml"
                    ):
                        self.config = yaml.safe_load(f)
                    else:
                        self.config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.warning(f"Configuration file {self.config_path} not found")
                self.config = {}
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            self.config = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-like access to configuration."""
        return self.config[key]

    def __contains__(self, key: str) -> bool:
        """Allow 'in' operator to check if key exists."""
        return key in self.config


def ensure_directory(path: str) -> None:
    """Ensure directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)


def load_config(config_path: str = "config/config.yaml") -> Config:
    """Load configuration from file."""
    return Config(config_path)


def setup_environment() -> None:
    """Set up environment variables and directories."""
    # Create necessary directories
    ensure_directory("logs")
    ensure_directory("data")
    ensure_directory("models")


def load_camera_configs(
    config_path: str = "config/config.yaml",
) -> Dict[str, CameraConfig]:
    """Load camera configurations from unified config.yaml."""
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                if config_path.endswith(".yaml") or config_path.endswith(".yml"):
                    full_config = yaml.safe_load(f)
                else:
                    full_config = json.load(f)

            # Extract cameras section from unified config
            cameras_data = full_config.get("cameras", [])

            # Convert list to dictionary format
            if isinstance(cameras_data, list):
                return {
                    config["id"]: CameraConfig.from_dict(config)
                    for config in cameras_data
                }
            else:
                return {
                    cam_id: CameraConfig.from_dict(config)
                    for cam_id, config in cameras_data.items()
                }
        logger.warning(f"Configuration file {config_path} not found")
        return {}
    except Exception as e:
        logger.error(f"Error loading camera configurations: {str(e)}")
        return {}
