import uuid

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database.base import Base


class NotificationAnalytics(Base):
    """Model for notification analytics and metrics."""

    __tablename__ = "notification_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Metrics
    total_sent = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)
    total_clicked = Column(Integer, default=0)

    # Channel-specific metrics
    email_sent = Column(Integer, default=0)
    email_failed = Column(Integer, default=0)
    email_delivered = Column(Integer, default=0)
    email_opened = Column(Integer, default=0)

    push_sent = Column(Integer, default=0)
    push_failed = Column(Integer, default=0)
    push_delivered = Column(Integer, default=0)
    push_clicked = Column(Integer, default=0)

    webhook_sent = Column(Integer, default=0)
    webhook_failed = Column(Integer, default=0)
    webhook_delivered = Column(Integer, default=0)

    # Performance metrics
    avg_delivery_time = Column(Float)  # Average delivery time in seconds
    avg_open_time = Column(Float)  # Average time to open in seconds
    avg_click_time = Column(Float)  # Average time to click in seconds

    # Engagement metrics
    open_rate = Column(Float)  # Percentage of opened notifications
    click_rate = Column(Float)  # Percentage of clicked notifications
    bounce_rate = Column(Float)  # Percentage of failed deliveries

    # Time-based metrics
    date = Column(DateTime(timezone=True), nullable=False)
    hour = Column(Integer)  # Hour of day (0-23)
    day_of_week = Column(Integer)  # Day of week (0-6, Monday=0)

    # Additional data
    metadata = Column(JSON)  # Additional analytics data

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="notification_analytics")

    def __repr__(self):
        return f"<NotificationAnalytics(user_id='{self.user_id}', date='{self.date}')>"

    def calculate_rates(self):
        """Calculate engagement rates."""
        if self.total_sent > 0:
            self.open_rate = (self.total_opened / self.total_sent) * 100
            self.click_rate = (self.total_clicked / self.total_sent) * 100
            self.bounce_rate = (self.total_failed / self.total_sent) * 100
        else:
            self.open_rate = 0.0
            self.click_rate = 0.0
            self.bounce_rate = 0.0

    def get_metadata(self) -> dict:
        """Get additional analytics data."""
        return self.metadata or {}

    def update_metadata(self, data: dict):
        """Update metadata with new data."""
        current_metadata = self.get_metadata()
        current_metadata.update(data)
        self.metadata = current_metadata


class NotificationEvent(Base):
    """Model for individual notification events for detailed analytics."""

    __tablename__ = "notification_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    notification_id = Column(String(255))  # Reference to actual notification

    # Event details
    event_type = Column(
        String(50), nullable=False
    )  # sent, delivered, opened, clicked, failed
    channel = Column(String(50), nullable=False)  # email, push, webhook
    timestamp = Column(DateTime(timezone=True), nullable=False)

    # Event data
    event_data = Column(JSON)  # Additional event-specific data
    error_message = Column(String(500))  # For failed events

    # Performance metrics
    delivery_time = Column(Float)  # Time to deliver in seconds
    processing_time = Column(Float)  # Time to process in seconds

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="notification_events")

    def __repr__(self):
        return (
            f"<NotificationEvent(type='{self.event_type}', channel='{self.channel}')>"
        )

    def get_event_data(self) -> dict:
        """Get event-specific data."""
        return self.event_data or {}
