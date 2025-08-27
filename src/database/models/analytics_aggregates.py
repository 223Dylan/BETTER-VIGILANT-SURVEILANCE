import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class AnalyticsAggregates(Base):
    """Model for storing pre-computed analytics aggregates for fast dashboard queries."""

    __tablename__ = "analytics_aggregates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Aggregation metadata
    aggregation_type = Column(
        String(50), nullable=False, index=True
    )  # hourly, daily, weekly, monthly
    time_period = Column(
        String(20), nullable=False, index=True
    )  # 2024-01-15, 2024-W03, 2024-01
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)

    # Scope (optional - for camera-specific or system-wide aggregates)
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)

    # Detection aggregates
    total_detections = Column(Integer, default=0)
    shoplifting_detections = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    average_confidence = Column(Float, default=0.0)
    detection_rate_per_hour = Column(Float, default=0.0)

    # Alert aggregates
    total_alerts = Column(Integer, default=0)
    alerts_by_severity = Column(
        JSON, nullable=True
    )  # {"low": 10, "medium": 5, "high": 2, "critical": 1}
    alerts_by_type = Column(
        JSON, nullable=True
    )  # {"shoplifting": 15, "loitering": 2, "vandalism": 1}

    # Performance aggregates
    average_processing_time_ms = Column(Float, default=0.0)
    average_fps = Column(Float, default=0.0)
    average_latency_ms = Column(Float, default=0.0)
    system_uptime_percent = Column(Float, default=0.0)

    # System resource aggregates
    average_cpu_usage = Column(Float, default=0.0)
    average_memory_usage = Column(Float, default=0.0)
    average_disk_usage = Column(Float, default=0.0)
    peak_cpu_usage = Column(Float, default=0.0)
    peak_memory_usage = Column(Float, default=0.0)

    # Camera aggregates
    active_cameras_count = Column(Integer, default=0)
    cameras_by_status = Column(
        JSON, nullable=True
    )  # {"connected": 8, "disconnected": 2, "error": 1}
    average_camera_uptime = Column(Float, default=0.0)

    # Notification aggregates
    notifications_sent = Column(Integer, default=0)
    notifications_delivered = Column(Integer, default=0)
    notifications_failed = Column(Integer, default=0)
    average_delivery_time_ms = Column(Float, default=0.0)

    # Business metrics
    incidents_resolved = Column(Integer, default=0)
    average_response_time_minutes = Column(Float, default=0.0)
    cost_savings_estimate = Column(
        Float, default=0.0
    )  # Estimated cost savings from prevented incidents

    # Time-based breakdowns
    hourly_breakdown = Column(JSON, nullable=True)  # {"00": 5, "01": 3, "02": 0, ...}
    daily_breakdown = Column(JSON, nullable=True)  # {"Monday": 25, "Tuesday": 30, ...}

    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )
    last_calculated = Column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    # Data quality indicators
    data_completeness_percent = Column(Float, default=100.0)
    sample_count = Column(
        Integer, default=0
    )  # Number of raw data points used for aggregation

    # Relationships
    camera = relationship("Camera", back_populates="analytics_aggregates")
    user = relationship("User", back_populates="analytics_aggregates")

    def __repr__(self):
        return f"<AnalyticsAggregates(id={self.id}, type={self.aggregation_type}, period={self.time_period}, detections={self.total_detections})>"
