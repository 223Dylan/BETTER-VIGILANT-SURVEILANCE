from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Index, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Alert(Base):
    """Alert model for storing detection alerts."""

    __tablename__ = "alerts"

    # Primary key
    id = Column(String, primary_key=True)  # UUID string

    # Core alert information
    camera_id = Column(String(255), nullable=False, index=True)
    type = Column(
        String(100), nullable=False, index=True
    )  # shoplifting, suspicious_activity, etc.
    severity = Column(
        String(50), nullable=False, index=True
    )  # low, medium, high, critical
    status = Column(
        String(50), nullable=False, default="active", index=True
    )  # active, acknowledged, resolved, dismissed

    # Detection data
    confidence = Column(Float, nullable=False)
    message = Column(Text, nullable=False)
    source = Column(String(100), default="detection", nullable=False)

    # Detection metadata (stored as JSON)
    detection_data = Column(JSON, default={})

    # Timestamps
    timestamp = Column(
        DateTime(timezone=True), nullable=False
    )  # When the detection occurred
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Acknowledgment and resolution tracking
    acknowledged_by = Column(String(255), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(255), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Additional notes
    notes = Column(Text, nullable=True)

    # Relationships
    notification_history = relationship(
        "NotificationHistory", back_populates="alert", lazy="dynamic"
    )

    # Create indexes for common queries
    __table_args__ = (
        Index("idx_alert_camera_timestamp", "camera_id", "timestamp"),
        Index("idx_alert_severity_status", "severity", "status"),
        Index("idx_alert_type_timestamp", "type", "timestamp"),
        Index("idx_alert_timestamp_desc", "timestamp"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "camera_id": self.camera_id,
            "type": self.type,
            "severity": self.severity,
            "status": self.status,
            "confidence": self.confidence,
            "message": self.message,
            "source": self.source,
            "detection_data": self.detection_data or {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": (
                self.acknowledged_at.isoformat() if self.acknowledged_at else None
            ),
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "notes": self.notes,
        }

    @classmethod
    def from_alert_record(cls, alert_record):
        """Create Alert instance from AlertRecord."""
        return cls(
            id=alert_record.id,
            camera_id=alert_record.camera_id,
            type=alert_record.type,
            severity=alert_record.severity,
            status=alert_record.status,
            confidence=alert_record.confidence,
            message=alert_record.message,
            source=alert_record.source,
            detection_data=alert_record.detection_data,
            timestamp=(
                datetime.fromisoformat(alert_record.timestamp.replace("Z", ""))
                if isinstance(alert_record.timestamp, str)
                else alert_record.timestamp
            ),
            acknowledged_by=alert_record.acknowledged_by,
            acknowledged_at=(
                datetime.fromisoformat(alert_record.acknowledged_at.replace("Z", ""))
                if alert_record.acknowledged_at
                else None
            ),
            resolved_by=alert_record.resolved_by,
            resolved_at=(
                datetime.fromisoformat(alert_record.resolved_at.replace("Z", ""))
                if alert_record.resolved_at
                else None
            ),
            notes=alert_record.notes,
        )

    def update_from_alert_record(self, alert_record):
        """Update this Alert instance from AlertRecord."""
        self.status = alert_record.status
        self.acknowledged_by = alert_record.acknowledged_by
        self.acknowledged_at = (
            datetime.fromisoformat(alert_record.acknowledged_at.replace("Z", ""))
            if alert_record.acknowledged_at
            else None
        )
        self.resolved_by = alert_record.resolved_by
        self.resolved_at = (
            datetime.fromisoformat(alert_record.resolved_at.replace("Z", ""))
            if alert_record.resolved_at
            else None
        )
        self.notes = alert_record.notes
        self.updated_at = datetime.utcnow()
