import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class CameraMetrics(Base):
    """Model for storing camera performance metrics."""

    __tablename__ = "camera_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Camera identification
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=False, index=True)

    # Connection metrics
    connection_status = Column(
        String(20), nullable=False, default="connected"
    )  # connected, disconnected, error
    connection_latency_ms = Column(Float, nullable=True)
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)

    # Video stream metrics
    fps_actual = Column(Float, nullable=False)
    fps_target = Column(Float, nullable=False, default=30.0)
    resolution_width = Column(Integer, nullable=True)
    resolution_height = Column(Integer, nullable=True)
    bitrate_kbps = Column(Integer, nullable=True)

    # Performance metrics
    frame_processing_time_ms = Column(Float, nullable=True)
    queue_depth = Column(Integer, default=0)
    dropped_frames = Column(Integer, default=0)
    total_frames_processed = Column(Integer, default=0)

    # Quality metrics
    signal_strength = Column(Float, nullable=True)  # 0-100%
    noise_level = Column(Float, nullable=True)  # 0-100%
    brightness_level = Column(Float, nullable=True)  # 0-100%
    contrast_level = Column(Float, nullable=True)  # 0-100%

    # Storage metrics
    recording_status = Column(Boolean, default=False)
    storage_used_gb = Column(Float, nullable=True)
    storage_available_gb = Column(Float, nullable=True)

    # Network metrics
    bandwidth_usage_mbps = Column(Float, nullable=True)
    packet_loss_percent = Column(Float, nullable=True)
    jitter_ms = Column(Float, nullable=True)

    # Error tracking
    error_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    error_timestamp = Column(DateTime(timezone=True), nullable=True)

    # Timestamp and metadata
    timestamp = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), index=True
    )
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )

    # Additional context
    location_data = Column(JSON, nullable=True)  # GPS coordinates, location name
    environmental_data = Column(JSON, nullable=True)  # temperature, humidity, lighting

    # Relationships
    camera = relationship("Camera", back_populates="camera_metrics")

    def __repr__(self):
        return f"<CameraMetrics(id={self.id}, camera_id={self.camera_id}, fps={self.fps_actual}, status={self.connection_status})>"
