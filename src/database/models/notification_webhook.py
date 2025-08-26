import uuid

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


class NotificationWebhook(Base):
    """Model for notification webhook integrations."""

    __tablename__ = "notification_webhooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Match users.id which is a String/VARCHAR
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Webhook configuration
    name = Column(String(255), nullable=False)
    description = Column(Text)
    url = Column(String(500), nullable=False)
    method = Column(String(10), default="POST")  # GET, POST, PUT, PATCH

    # Authentication
    auth_type = Column(String(50), default="none")  # none, basic, bearer, custom
    auth_credentials = Column(JSON)  # Encrypted credentials

    # Headers and payload
    headers = Column(JSON)  # Custom headers
    payload_template = Column(JSON)  # Template for payload structure
    content_type = Column(String(100), default="application/json")

    # Filtering and targeting
    alert_severities = Column(JSON)  # List of severities to include
    alert_types = Column(JSON)  # List of alert types to include
    camera_ids = Column(JSON)  # List of camera IDs to include

    # Status and monitoring
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_sent = Column(DateTime(timezone=True))
    last_response = Column(JSON)  # Last response from webhook
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)

    # Retry configuration
    max_retries = Column(Integer, default=3)
    retry_delay = Column(Integer, default=60)  # Seconds
    timeout = Column(Integer, default=30)  # Seconds

    # Security
    verify_ssl = Column(Boolean, default=True)
    custom_ca_cert = Column(Text)  # Custom CA certificate

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="notification_webhooks")
    delivery_logs = relationship(
        "WebhookDeliveryLog",
        back_populates="webhook",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<NotificationWebhook(name='{self.name}', url='{self.url}')>"

    def get_auth_credentials(self) -> dict:
        """Get authentication credentials."""
        return self.auth_credentials or {}

    def get_headers(self) -> dict:
        """Get custom headers."""
        return self.headers or {}

    def get_payload_template(self) -> dict:
        """Get payload template."""
        return self.payload_template or {}

    def get_last_response(self) -> dict:
        """Get last response data."""
        return self.last_response or {}

    def update_stats(self, success: bool):
        """Update success/failure statistics."""
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

    def get_success_rate(self) -> float:
        """Calculate success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return (self.success_count / total) * 100


class WebhookDeliveryLog(Base):
    """Model for webhook delivery logs."""

    __tablename__ = "webhook_delivery_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webhook_id = Column(
        UUID(as_uuid=True), ForeignKey("notification_webhooks.id"), nullable=False
    )
    notification_id = Column(String(255))  # Reference to notification

    # Delivery details
    url = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)
    payload = Column(JSON)
    headers = Column(JSON)

    # Response details
    status_code = Column(Integer)
    response_body = Column(Text)
    response_headers = Column(JSON)

    # Timing and performance
    request_time = Column(DateTime(timezone=True), nullable=False)
    response_time = Column(DateTime(timezone=True))
    duration = Column(Float)  # Request duration in seconds

    # Status
    success = Column(Boolean, nullable=False)
    error_message = Column(String(500))

    # Retry information
    attempt_number = Column(Integer, default=1)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    webhook = relationship("NotificationWebhook", back_populates="delivery_logs")

    def __repr__(self):
        return f"<WebhookDeliveryLog(webhook_id='{self.webhook_id}', success={self.success})>"

    def get_payload(self) -> dict:
        """Get request payload."""
        return self.payload or {}

    def get_headers(self) -> dict:
        """Get request headers."""
        return self.headers or {}

    def get_response_headers(self) -> dict:
        """Get response headers."""
        return self.response_headers or {}
