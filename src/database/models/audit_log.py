import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class AuditAction(str, Enum):
    """Enum for different types of audit actions."""

    # Authentication actions
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    TOKEN_REFRESH = "token_refresh"

    # Permission checks
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    ROLE_CHECK = "role_check"

    # Resource access
    RESOURCE_ACCESS = "resource_access"
    RESOURCE_ACCESS_DENIED = "resource_access_denied"

    # Administrative actions
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    ROLE_CHANGED = "role_changed"
    PERMISSIONS_MODIFIED = "permissions_modified"

    # Camera actions
    CAMERA_VIEWED = "camera_viewed"
    CAMERA_CONTROLLED = "camera_controlled"
    CAMERA_CREATED = "camera_created"
    CAMERA_UPDATED = "camera_updated"
    CAMERA_DELETED = "camera_deleted"

    # Alert actions
    ALERT_VIEWED = "alert_viewed"
    ALERT_ACKNOWLEDGED = "alert_acknowledged"
    ALERT_RESOLVED = "alert_resolved"
    ALERT_DELETED = "alert_deleted"
    ALERT_EXPORTED = "alert_exported"

    # System actions
    SYSTEM_CONFIG_VIEWED = "system_config_viewed"
    SYSTEM_CONFIG_MODIFIED = "system_config_modified"
    SYSTEM_LOGS_ACCESSED = "system_logs_accessed"
    ANALYTICS_ACCESSED = "analytics_accessed"


class AuditSeverity(str, Enum):
    """Enum for audit log severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLog(Base):
    """Audit log model for tracking all security and permission-related events."""

    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Who performed the action
    user_id = Column(String, index=True)  # Can be null for anonymous actions
    username = Column(String(50), index=True)  # Denormalized for performance
    user_role = Column(String(20), index=True)

    # What action was performed
    action = Column(String(50), nullable=False, index=True)
    action_category = Column(
        String(20), index=True
    )  # auth, permission, resource, admin, etc.

    # Where the action occurred
    resource_type = Column(String(50), index=True)  # camera, user, alert, system, etc.
    resource_id = Column(String, index=True)
    endpoint = Column(String(255))

    # Context and details
    permission_required = Column(String(50))  # Which permission was checked
    permission_granted = Column(Boolean, default=False)
    request_method = Column(String(10))  # GET, POST, PUT, DELETE

    # Request details
    ip_address = Column(String(45), index=True)  # IPv6 support
    user_agent = Column(Text)
    session_id = Column(String)

    # Result and metadata
    success = Column(Boolean, default=True, index=True)
    severity = Column(String(20), default=AuditSeverity.LOW, index=True)
    error_message = Column(Text)

    # Additional context as JSON
    metadata_json = Column(JSON, default=dict)

    # Timing
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    duration_ms = Column(Integer)  # Request duration in milliseconds

    # Data retention
    retention_date = Column(DateTime(timezone=True))  # For automatic cleanup

    def to_dict(self):
        """Convert audit log to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "user_role": self.user_role,
            "action": self.action,
            "action_category": self.action_category,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "endpoint": self.endpoint,
            "permission_required": self.permission_required,
            "permission_granted": self.permission_granted,
            "request_method": self.request_method,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "success": self.success,
            "severity": self.severity,
            "error_message": self.error_message,
            "metadata": self.metadata_json or {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "duration_ms": self.duration_ms,
            "retention_date": (
                self.retention_date.isoformat() if self.retention_date else None
            ),
        }

    @classmethod
    def get_action_category(cls, action: str) -> str:
        """Get the category for an action."""
        auth_actions = [
            AuditAction.LOGIN,
            AuditAction.LOGOUT,
            AuditAction.LOGIN_FAILED,
            AuditAction.TOKEN_REFRESH,
        ]
        permission_actions = [
            AuditAction.PERMISSION_GRANTED,
            AuditAction.PERMISSION_DENIED,
            AuditAction.ROLE_CHECK,
        ]
        resource_actions = [
            AuditAction.RESOURCE_ACCESS,
            AuditAction.RESOURCE_ACCESS_DENIED,
        ]
        admin_actions = [
            AuditAction.USER_CREATED,
            AuditAction.USER_UPDATED,
            AuditAction.USER_DELETED,
            AuditAction.ROLE_CHANGED,
            AuditAction.PERMISSIONS_MODIFIED,
        ]

        if action in auth_actions:
            return "authentication"
        elif action in permission_actions:
            return "permission"
        elif action in resource_actions:
            return "resource"
        elif action in admin_actions:
            return "administration"
        elif action.startswith("camera_"):
            return "camera"
        elif action.startswith("alert_"):
            return "alert"
        elif action.startswith("system_"):
            return "system"
        else:
            return "other"
