import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from .base import Base


class NotificationTemplate(Base):
    """Model for notification templates."""

    __tablename__ = "notification_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    html_body = Column(Text)
    template_type = Column(String(50), nullable=False)  # email, push, webhook
    variables = Column(JSON)  # Available template variables
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return (
            f"<NotificationTemplate(name='{self.name}', type='{self.template_type}')>"
        )

    def get_variables(self) -> dict:
        """Get available template variables."""
        return self.variables or {}

    def render_template(self, context: dict) -> dict:
        """Render template with given context."""
        rendered_subject = self._render_text(self.subject, context)
        rendered_body = self._render_text(self.body, context)
        rendered_html = (
            self._render_text(self.html_body, context) if self.html_body else None
        )

        return {
            "subject": rendered_subject,
            "body": rendered_body,
            "html_body": rendered_html,
        }

    def _render_text(self, text: str, context: dict) -> str:
        """Render template text with context variables."""
        if not text:
            return ""

        # Simple template variable replacement
        # In production, you might want to use a proper templating engine like Jinja2
        rendered = text
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, str(value))

        return rendered
