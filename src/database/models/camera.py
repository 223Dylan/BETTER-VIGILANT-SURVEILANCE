from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, Integer,
                        String, Text)
from sqlalchemy.sql import func

from .base import Base


class Camera(Base):
    """Camera configuration model."""

    __tablename__ = "cameras"

    # Primary key
    id = Column(String, primary_key=True)  # e.g., "local-webcam", "ip-cam-001"

    # Basic configuration
    name = Column(String(255), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True, nullable=False)

    # Connection details
    source = Column(String(255), nullable=False)  # URL, device index, etc.
    source_type = Column(
        String(50), nullable=False, default="webcam"
    )  # webcam, rtsp, file

    # Video settings
    fps = Column(Integer, default=15, nullable=False)
    resolution_width = Column(Integer, default=640)
    resolution_height = Column(Integer, default=480)
    brightness = Column(
        Float, default=1.0, nullable=False
    )  # Individual camera brightness (0.0 to 2.0)

    # Processing settings
    detection_enabled = Column(Boolean, default=True, nullable=False)
    detection_sensitivity = Column(Float, default=0.5)  # Threshold for ML predictions
    recording_enabled = Column(Boolean, default=False, nullable=False)

    # Location and metadata
    location = Column(String(255))
    zone = Column(String(100))  # e.g., "entrance", "checkout", "aisle-1"

    # Advanced settings (stored as JSON)
    advanced_settings = Column(JSON, default={})

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_online = Column(DateTime(timezone=True))

    # Status tracking
    status = Column(String(50), default="stopped")  # stopped, starting, active, error
    error_message = Column(Text)
    uptime_hours = Column(Float, default=0.0)

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "source": self.source,
            "source_type": self.source_type,
            "fps": self.fps,
            "resolution": {
                "width": self.resolution_width,
                "height": self.resolution_height,
            },
            "brightness": self.brightness,
            "detection_enabled": self.detection_enabled,
            "detection_sensitivity": self.detection_sensitivity,
            "recording_enabled": self.recording_enabled,
            "location": self.location,
            "zone": self.zone,
            "advanced_settings": self.advanced_settings or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_online": self.last_online.isoformat() if self.last_online else None,
            "status": self.status,
            "error_message": self.error_message,
            "uptime_hours": self.uptime_hours,
        }

    @classmethod
    def from_config_dict(cls, camera_id: str, config_dict: dict):
        """Create Camera instance from config dictionary."""
        return cls(
            id=camera_id,
            name=config_dict.get("name", camera_id),
            description=config_dict.get("description", ""),
            enabled=config_dict.get("enabled", True),
            source=config_dict.get("source", 0),
            source_type=config_dict.get("source_type", "webcam"),
            fps=config_dict.get("fps", 15),
            resolution_width=config_dict.get("resolution", {}).get("width", 640),
            resolution_height=config_dict.get("resolution", {}).get("height", 480),
            brightness=config_dict.get("brightness", 1.0),
            detection_enabled=config_dict.get("detection_enabled", True),
            detection_sensitivity=config_dict.get("detection_sensitivity", 0.5),
            recording_enabled=config_dict.get("recording_enabled", False),
            location=config_dict.get("location"),
            zone=config_dict.get("zone"),
            advanced_settings=config_dict.get("advanced_settings", {}),
            status="stopped",
        )
