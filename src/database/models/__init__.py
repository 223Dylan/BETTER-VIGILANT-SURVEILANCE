"""Database models package."""

from .alert import Alert
from .analytics_aggregates import AnalyticsAggregates
from .audit_log import AuditLog
from .base import Base, engine, get_db
from .camera import Camera
from .camera_metrics import CameraMetrics
from .detection_metrics import DetectionMetrics
from .frame import Frame
from .notification_analytics import NotificationAnalytics, NotificationEvent
from .notification_history import NotificationHistory
from .notification_schedule import NotificationSchedule
from .notification_template import NotificationTemplate
from .notification_webhook import NotificationWebhook, WebhookDeliveryLog
from .push_subscription import PushSubscription
from .system_metrics import SystemMetrics
from .user import User
from .user_notification_preferences import UserNotificationPreferences

__all__ = [
    "Base",
    "get_db",
    "engine",
    "User",
    "UserNotificationPreferences",
    "NotificationAnalytics",
    "NotificationEvent",
    "NotificationHistory",
    "NotificationSchedule",
    "NotificationTemplate",
    "NotificationWebhook",
    "WebhookDeliveryLog",
    "PushSubscription",
    "Camera",
    "Alert",
    "AuditLog",
    "Frame",
    "DetectionMetrics",
    "SystemMetrics",
    "CameraMetrics",
    "AnalyticsAggregates",
]
