from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from src.database.models.base import get_db
from src.database.models.notification_template import NotificationTemplate


class NotificationTemplateService:
    """Service for managing notification templates."""

    def __init__(self):
        self.db: Session = next(get_db())

    def create_template(self, template_data: Dict) -> NotificationTemplate:
        """Create a new notification template."""
        try:
            template = NotificationTemplate(**template_data)
            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)
            logger.info(f"Created notification template: {template.name}")
            return template
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create notification template: {e}")
            raise

    def get_template(self, template_id: str) -> Optional[NotificationTemplate]:
        """Get a notification template by ID."""
        try:
            return (
                self.db.query(NotificationTemplate)
                .filter(NotificationTemplate.id == template_id)
                .first()
            )
        except Exception as e:
            logger.error(f"Failed to get notification template: {e}")
            return None

    def get_templates(
        self, template_type: Optional[str] = None, is_active: bool = True
    ) -> List[NotificationTemplate]:
        """Get notification templates with optional filtering."""
        try:
            query = self.db.query(NotificationTemplate)

            if template_type:
                query = query.filter(
                    NotificationTemplate.template_type == template_type
                )

            if is_active is not None:
                query = query.filter(NotificationTemplate.is_active == is_active)

            return query.all()
        except Exception as e:
            logger.error(f"Failed to get notification templates: {e}")
            return []

    def get_default_template(
        self, template_type: str
    ) -> Optional[NotificationTemplate]:
        """Get the default template for a specific type."""
        try:
            return (
                self.db.query(NotificationTemplate)
                .filter(
                    NotificationTemplate.template_type == template_type,
                    NotificationTemplate.is_default == True,
                    NotificationTemplate.is_active == True,
                )
                .first()
            )
        except Exception as e:
            logger.error(f"Failed to get default template: {e}")
            return None

    def update_template(
        self, template_id: str, template_data: Dict
    ) -> Optional[NotificationTemplate]:
        """Update a notification template."""
        try:
            template = self.get_template(template_id)
            if not template:
                return None

            for key, value in template_data.items():
                if hasattr(template, key):
                    setattr(template, key, value)

            self.db.commit()
            self.db.refresh(template)
            logger.info(f"Updated notification template: {template.name}")
            return template
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update notification template: {e}")
            return None

    def delete_template(self, template_id: str) -> bool:
        """Delete a notification template."""
        try:
            template = self.get_template(template_id)
            if not template:
                return False

            self.db.delete(template)
            self.db.commit()
            logger.info(f"Deleted notification template: {template.name}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete notification template: {e}")
            return False

    def render_template(self, template_id: str, context: Dict) -> Optional[Dict]:
        """Render a template with given context."""
        try:
            template = self.get_template(template_id)
            if not template:
                return None

            return template.render_template(context)
        except Exception as e:
            logger.error(f"Failed to render template: {e}")
            return None

    def get_template_variables(self, template_id: str) -> Dict:
        """Get available variables for a template."""
        try:
            template = self.get_template(template_id)
            if not template:
                return {}

            return template.get_variables()
        except Exception as e:
            logger.error(f"Failed to get template variables: {e}")
            return {}

    def create_default_templates(self):
        """Create default notification templates."""
        default_templates = [
            {
                "name": "Security Alert - Email",
                "description": "Default email template for security alerts",
                "subject": "Security Alert: {alert_type} detected on {camera_id}",
                "body": """
Security Alert Notification

Alert Type: {alert_type}
Severity: {severity}
Camera: {camera_id}
Timestamp: {timestamp}
Location: {location}

Description: {description}

Please review this alert immediately.
                """,
                "html_body": """
<h2>Security Alert Notification</h2>
<p><strong>Alert Type:</strong> {alert_type}</p>
<p><strong>Severity:</strong> {severity}</p>
<p><strong>Camera:</strong> {camera_id}</p>
<p><strong>Timestamp:</strong> {timestamp}</p>
<p><strong>Location:</strong> {location}</p>
<p><strong>Description:</strong> {description}</p>
<p>Please review this alert immediately.</p>
                """,
                "template_type": "email",
                "variables": {
                    "alert_type": "Type of security alert",
                    "severity": "Alert severity level",
                    "camera_id": "Camera identifier",
                    "timestamp": "Alert timestamp",
                    "location": "Camera location",
                    "description": "Alert description",
                },
                "is_default": True,
                "is_active": True,
            },
            {
                "name": "Security Alert - Push",
                "description": "Default push notification template for security alerts",
                "subject": "Security Alert",
                "body": "{alert_type} detected on {camera_id} - {severity} severity",
                "template_type": "push",
                "variables": {
                    "alert_type": "Type of security alert",
                    "severity": "Alert severity level",
                    "camera_id": "Camera identifier",
                },
                "is_default": True,
                "is_active": True,
            },
            {
                "name": "Security Alert - Webhook",
                "description": "Default webhook template for security alerts",
                "subject": "Security Alert",
                "body": """
{
  "alert_type": "{alert_type}",
  "severity": "{severity}",
  "camera_id": "{camera_id}",
  "timestamp": "{timestamp}",
  "location": "{location}",
  "description": "{description}"
}
                """,
                "template_type": "webhook",
                "variables": {
                    "alert_type": "Type of security alert",
                    "severity": "Alert severity level",
                    "camera_id": "Camera identifier",
                    "timestamp": "Alert timestamp",
                    "location": "Camera location",
                    "description": "Alert description",
                },
                "is_default": True,
                "is_active": True,
            },
        ]

        for template_data in default_templates:
            try:
                self.create_template(template_data)
            except Exception as e:
                logger.error(
                    f"Failed to create default template {template_data['name']}: {e}"
                )


# Global instance
notification_template_service = NotificationTemplateService()
