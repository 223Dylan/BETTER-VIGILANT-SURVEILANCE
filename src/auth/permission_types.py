from enum import Enum


class Permission(str, Enum):
    """Permission enumeration for granular access control."""

    # Camera permissions
    CAMERA_VIEW = "camera:view"
    CAMERA_CREATE = "camera:create"
    CAMERA_UPDATE = "camera:update"
    CAMERA_DELETE = "camera:delete"
    CAMERA_CONTROL = "camera:control"
    CAMERA_STREAM = "camera:stream"
    CAMERA_CONFIG = "camera:config"

    # Alert permissions
    ALERT_VIEW = "alert:view"
    ALERT_CREATE = "alert:create"
    ALERT_ACKNOWLEDGE = "alert:acknowledge"
    ALERT_RESOLVE = "alert:resolve"
    ALERT_DELETE = "alert:delete"
    ALERT_EXPORT = "alert:export"

    # User permissions
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_MANAGE_ROLES = "user:manage_roles"
    USER_MANAGE_PERMISSIONS = "user:manage_permissions"

    # System permissions
    SYSTEM_CONFIG = "system:config"
    SYSTEM_LOGS = "system:logs"
    SYSTEM_METRICS = "system:metrics"
    SYSTEM_BACKUP = "system:backup"
    SYSTEM_MAINTENANCE = "system:maintenance"

    # Analytics permissions
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"
    ANALYTICS_REPORTS = "analytics:reports"

    # Security permissions
    SECURITY_AUDIT = "security:audit"
    SECURITY_CONFIG = "security:config"
