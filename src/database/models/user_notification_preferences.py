import uuid
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class UserNotificationPreferences(Base):
    """User notification preferences model."""

    __tablename__ = "user_notification_preferences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String, ForeignKey("users.id"), unique=True, nullable=False, index=True
    )

    # Notification channels
    email_enabled = Column(Boolean, default=True, nullable=False)
    push_enabled = Column(Boolean, default=True, nullable=False)
    webhook_enabled = Column(Boolean, default=False, nullable=False)
    webhook_url = Column(String(500), nullable=True)

    # Alert filtering
    alert_severities = Column(
        JSON, default=["critical", "high", "medium"]
    )  # List of severities to receive
    alert_types = Column(
        JSON, default=["shoplifting", "suspicious_activity", "system_alert"]
    )  # List of types to receive
    assigned_cameras = Column(
        JSON, default=[]
    )  # List of camera IDs user monitors (empty = all cameras)

    # Notification timing
    cooldown_minutes = Column(
        Integer, default=5, nullable=False
    )  # Minimum time between notifications
    quiet_hours_enabled = Column(Boolean, default=False, nullable=False)
    quiet_hours_start = Column(String(5), default="22:00")  # HH:MM format
    quiet_hours_end = Column(String(5), default="08:00")  # HH:MM format

    # Custom settings
    custom_filters = Column(JSON, default={})  # Additional custom filtering rules

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    user = relationship("User", backref="notification_preferences")

    def should_receive_alert(
        self, alert_severity: str, alert_type: str, camera_id: str
    ) -> bool:
        """Check if user should receive this alert based on preferences."""

        # Check if user is assigned to this camera (if camera-specific assignments exist)
        if self.assigned_cameras and camera_id not in self.assigned_cameras:
            return False

        # Check severity filter
        if alert_severity not in (self.alert_severities or []):
            return False

        # Check type filter
        if alert_type not in (self.alert_types or []):
            return False

        # Check quiet hours
        if self.is_in_quiet_hours():
            return False

        return True

    def is_in_quiet_hours(self) -> bool:
        """Check if current time is within user's quiet hours."""
        if not self.quiet_hours_enabled:
            return False

        now = datetime.now().time()

        try:
            start_time = datetime.strptime(self.quiet_hours_start, "%H:%M").time()
            end_time = datetime.strptime(self.quiet_hours_end, "%H:%M").time()
        except (ValueError, TypeError):
            return False

        if start_time <= end_time:
            # Same day quiet hours (e.g., 22:00 - 08:00 next day is not this case)
            return start_time <= now <= end_time
        else:
            # Overnight quiet hours (e.g., 22:00 - 08:00)
            return now >= start_time or now <= end_time

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email_enabled": self.email_enabled,
            "push_enabled": self.push_enabled,
            "webhook_enabled": self.webhook_enabled,
            "webhook_url": self.webhook_url,
            "alert_severities": self.alert_severities,
            "alert_types": self.alert_types,
            "assigned_cameras": self.assigned_cameras,
            "cooldown_minutes": self.cooldown_minutes,
            "quiet_hours_enabled": self.quiet_hours_enabled,
            "quiet_hours_start": self.quiet_hours_start,
            "quiet_hours_end": self.quiet_hours_end,
            "custom_filters": self.custom_filters,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_default_preferences(cls) -> Dict:
        """Get default notification preferences for new users."""
        return {
            "email_enabled": True,
            "push_enabled": True,
            "webhook_enabled": False,
            "alert_severities": ["critical", "high", "medium"],
            "alert_types": ["shoplifting", "suspicious_activity", "system_alert"],
            "assigned_cameras": [],
            "cooldown_minutes": 5,
            "quiet_hours_enabled": False,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00",
            "custom_filters": {},
        }
