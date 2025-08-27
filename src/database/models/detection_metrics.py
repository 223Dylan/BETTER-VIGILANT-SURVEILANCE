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


class DetectionMetrics(Base):
    """Model for storing ML detection metrics and predictions."""

    __tablename__ = "detection_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Camera and detection info
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=False, index=True)
    frame_id = Column(String, nullable=True, index=True)  # Reference to frame storage

    # ML Model info
    model_version = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)

    # Detection results
    prediction_label = Column(String(100), nullable=False)
    confidence_score = Column(Float, nullable=False)
    is_shoplifting = Column(Boolean, default=False)
    bounding_box = Column(JSON)  # x, y, width, height
    object_count = Column(Integer, default=1)

    # Performance metrics
    processing_time_ms = Column(Float, nullable=False)
    inference_time_ms = Column(Float, nullable=False)
    preprocess_time_ms = Column(Float, nullable=False)
    postprocess_time_ms = Column(Float, nullable=False)

    # System performance
    fps_actual = Column(Float, nullable=False)
    fps_target = Column(Float, nullable=False, default=30.0)
    latency_ms = Column(Float, nullable=False)
    queue_depth = Column(Integer, default=0)
    dropped_frames = Column(Integer, default=0)

    # Memory and resource usage
    memory_usage_mb = Column(Float, nullable=True)
    gpu_usage_percent = Column(Float, nullable=True)
    cpu_usage_percent = Column(Float, nullable=True)

    # Alert information
    alert_triggered = Column(Boolean, default=False)
    alert_level = Column(String(20), nullable=True)  # low, medium, high, critical
    alert_type = Column(String(50), nullable=True)

    # Metadata
    timestamp = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), index=True
    )
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )

    # Additional context
    location_data = Column(JSON, nullable=True)  # GPS coordinates, location name
    weather_data = Column(JSON, nullable=True)  # Weather conditions
    lighting_conditions = Column(String(50), nullable=True)  # bright, dim, dark

    # Relationships
    camera = relationship("Camera", back_populates="detection_metrics")

    def __repr__(self):
        return f"<DetectionMetrics(id={self.id}, camera_id={self.camera_id}, label={self.prediction_label}, confidence={self.confidence_score})>"
