import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class SystemMetrics(Base):
    """Model for storing system performance metrics."""

    __tablename__ = "system_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # System identification
    hostname = Column(String(100), nullable=False)
    system_type = Column(String(50), nullable=False, default="surveillance_system")

    # CPU metrics
    cpu_usage_percent = Column(Float, nullable=False)
    cpu_count = Column(Integer, nullable=False)
    cpu_frequency_mhz = Column(Float, nullable=True)
    cpu_temperature_celsius = Column(Float, nullable=True)

    # Memory metrics
    memory_usage_percent = Column(Float, nullable=False)
    memory_total_gb = Column(Float, nullable=False)
    memory_available_gb = Column(Float, nullable=False)
    memory_used_gb = Column(Float, nullable=False)
    swap_usage_percent = Column(Float, nullable=True)

    # Disk metrics
    disk_usage_percent = Column(Float, nullable=False)
    disk_total_gb = Column(Float, nullable=False)
    disk_used_gb = Column(Float, nullable=False)
    disk_free_gb = Column(Float, nullable=False)
    disk_read_mbps = Column(Float, nullable=True)
    disk_write_mbps = Column(Float, nullable=True)

    # Network metrics
    network_in_mbps = Column(Float, nullable=True)
    network_out_mbps = Column(Float, nullable=True)
    network_connections = Column(Integer, nullable=True)

    # GPU metrics (if available)
    gpu_usage_percent = Column(Float, nullable=True)
    gpu_memory_usage_percent = Column(Float, nullable=True)
    gpu_temperature_celsius = Column(Float, nullable=True)

    # Application-specific metrics
    active_cameras = Column(Integer, nullable=False, default=0)
    active_detections = Column(Integer, nullable=False, default=0)
    active_alerts = Column(Integer, nullable=False, default=0)

    # Performance metrics
    system_load_1min = Column(Float, nullable=True)
    system_load_5min = Column(Float, nullable=True)
    system_load_15min = Column(Float, nullable=True)

    # Process metrics
    total_processes = Column(Integer, nullable=True)
    zombie_processes = Column(Integer, nullable=True)

    # Timestamp and metadata
    timestamp = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), index=True
    )
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )

    # Additional context
    uptime_seconds = Column(Integer, nullable=True)
    last_boot_time = Column(DateTime(timezone=True), nullable=True)
    system_info = Column(JSON, nullable=True)  # OS version, kernel, etc.

    def __repr__(self):
        return f"<SystemMetrics(id={self.id}, hostname={self.hostname}, cpu={self.cpu_usage_percent}%, memory={self.memory_usage_percent}%)>"
