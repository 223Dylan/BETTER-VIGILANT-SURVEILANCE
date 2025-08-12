"""Create notification_webhooks and webhook_delivery_logs tables

Revision ID: notif_webhooks_001
Revises: notif_events_002
Create Date: 2025-08-12 13:10:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "notif_webhooks_001"
down_revision = "notif_events_002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create notification_webhooks table
    op.create_table(
        "notification_webhooks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),  # FK to users.id (String)
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=True, server_default="POST"),
        sa.Column(
            "auth_type", sa.String(length=50), nullable=True, server_default="none"
        ),
        sa.Column(
            "auth_credentials", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("headers", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "payload_template", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "content_type",
            sa.String(length=100),
            nullable=True,
            server_default="application/json",
        ),
        sa.Column(
            "alert_severities", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("alert_types", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("camera_ids", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")
        ),
        sa.Column(
            "is_verified", sa.Boolean(), nullable=True, server_default=sa.text("false")
        ),
        sa.Column("last_sent", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_response", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("success_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("failure_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=True, server_default="3"),
        sa.Column("retry_delay", sa.Integer(), nullable=True, server_default="60"),
        sa.Column("timeout", sa.Integer(), nullable=True, server_default="30"),
        sa.Column(
            "verify_ssl", sa.Boolean(), nullable=True, server_default=sa.text("true")
        ),
        sa.Column("custom_ca_cert", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_foreign_key(
        "fk_notification_webhooks_user_id",
        "notification_webhooks",
        "users",
        ["user_id"],
        ["id"],
    )

    # Create webhook_delivery_logs table
    op.create_table(
        "webhook_delivery_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("webhook_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("notification_id", sa.String(length=255), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("payload", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("headers", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column(
            "response_headers", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("request_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("response_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("attempt_number", sa.Integer(), nullable=True, server_default="1"),
        sa.Column("retry_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_foreign_key(
        "fk_webhook_delivery_logs_webhook_id",
        "webhook_delivery_logs",
        "notification_webhooks",
        ["webhook_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_webhook_delivery_logs_webhook_id",
        "webhook_delivery_logs",
        type_="foreignkey",
    )
    op.drop_table("webhook_delivery_logs")
    op.drop_constraint(
        "fk_notification_webhooks_user_id", "notification_webhooks", type_="foreignkey"
    )
    op.drop_table("notification_webhooks")
