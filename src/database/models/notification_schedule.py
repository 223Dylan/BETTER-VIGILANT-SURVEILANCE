import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database.models.base import Base


class NotificationSchedule(Base):
    """Model for scheduled notifications."""

    __tablename__ = "notification_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Schedule configuration
    schedule_type = Column(String(50), nullable=False)  # daily, weekly, monthly, custom
    schedule_config = Column(JSON, nullable=False)  # Cron-like configuration
    timezone = Column(String(50), default="UTC")

    # Notification content
    template_id = Column(UUID(as_uuid=True), ForeignKey("notification_templates.id"))
    custom_subject = Column(String(500))
    custom_body = Column(Text)

    # Filtering and targeting
    alert_severities = Column(JSON)  # List of severities to include
    alert_types = Column(JSON)  # List of alert types to include
    camera_ids = Column(JSON)  # List of camera IDs to include

    # Status and timing
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime(timezone=True))
    next_run = Column(DateTime(timezone=True))
    max_runs = Column(Integer)  # None for unlimited
    run_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="notification_schedules")
    template = relationship("NotificationTemplate")

    def __repr__(self):
        return (
            f"<NotificationSchedule(name='{self.name}', type='{self.schedule_type}')>"
        )

    def get_schedule_config(self) -> dict:
        """Get schedule configuration."""
        return self.schedule_config or {}

    def should_run(self, current_time=None) -> bool:
        """Check if the schedule should run at the given time."""
        if not self.is_active:
            return False

        if self.max_runs and self.run_count >= self.max_runs:
            return False

        if not current_time:
            from datetime import datetime

            current_time = datetime.utcnow()

        # Simple implementation - in production, use a proper scheduler like APScheduler
        if not self.next_run:
            return False

        return current_time >= self.next_run

    def update_next_run(self):
        """Update the next run time based on schedule configuration."""
        from datetime import datetime, timedelta

        import pytz

        tz = pytz.timezone(self.timezone or "UTC")
        now = datetime.now(tz)

        config = self.get_schedule_config()

        if self.schedule_type == "daily":
            # Run daily at specified time
            hour = config.get("hour", 9)
            minute = config.get("minute", 0)
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            if next_run <= now:
                next_run += timedelta(days=1)

        elif self.schedule_type == "weekly":
            # Run weekly on specified day and time
            weekday = config.get("weekday", 0)  # Monday = 0
            hour = config.get("hour", 9)
            minute = config.get("minute", 0)

            days_ahead = weekday - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7

            next_run = now.replace(
                hour=hour, minute=minute, second=0, microsecond=0
            ) + timedelta(days=days_ahead)

        elif self.schedule_type == "monthly":
            # Run monthly on specified day and time
            day = config.get("day", 1)
            hour = config.get("hour", 9)
            minute = config.get("minute", 0)

            next_run = now.replace(
                day=day, hour=hour, minute=minute, second=0, microsecond=0
            )

            if next_run <= now:
                # Move to next month
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)

        else:
            # Custom schedule - use cron-like configuration
            # This is a simplified implementation
            interval_minutes = config.get("interval_minutes", 60)
            next_run = now + timedelta(minutes=interval_minutes)

        self.next_run = next_run
        return next_run
