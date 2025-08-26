import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database.models.base import Base


class NotificationHistory(Base):
    """Model for storing individual notification history records."""

    __tablename__ = "notification_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    alert_id = Column(String, ForeignKey("alerts.id"), nullable=True, index=True)

    # Notification details
    notification_type = Column(String(50), nullable=False)  # email, push, webhook
    title = Column(String(500), nullable=True)
    message = Column(Text, nullable=True)

    # Status tracking
    status = Column(
        String(50), nullable=False, default="pending"
    )  # pending, sent, delivered, failed, opened, clicked
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)

    # Channel-specific data
    channel_data = Column(
        JSON
    )  # Email headers, webhook response, push notification data

    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(String(10), default="0")

    # Performance metrics
    delivery_time = Column(String(10), nullable=True)  # Time to deliver in seconds
    processing_time = Column(String(10), nullable=True)  # Time to process in seconds

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="notification_history")
    alert = relationship("Alert", back_populates="notification_history")

    def __repr__(self):
        return f"<NotificationHistory(id='{self.id}', user_id='{self.user_id}', type='{self.notification_type}', status='{self.status}')>"

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "alert_id": self.alert_id,
            "notification_type": self.notification_type,
            "title": self.title,
            "message": self.message,
            "status": self.status,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": (
                self.delivered_at.isoformat() if self.delivered_at else None
            ),
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "clicked_at": self.clicked_at.isoformat() if self.clicked_at else None,
            "channel_data": self.channel_data,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "delivery_time": self.delivery_time,
            "processing_time": self.processing_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def update_status(self, new_status: str, timestamp: Optional[datetime] = None):
        """Update notification status and relevant timestamp."""
        self.status = new_status
        self.updated_at = datetime.now()

        if timestamp is None:
            timestamp = datetime.now()

        if new_status == "sent":
            self.sent_at = timestamp
        elif new_status == "delivered":
            self.delivered_at = timestamp
        elif new_status == "opened":
            self.opened_at = timestamp
        elif new_status == "clicked":
            self.clicked_at = timestamp
