"""Add advanced notification features

Revision ID: add_advanced_notification_features
Revises: add_user_notification_preferences
Create Date: 2024-01-01 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_advanced_notification_features"
down_revision = "add_user_notification_preferences"
branch_labels = None
depends_on = None


def upgrade():
    # Create notification_templates table
    op.create_table(
        "notification_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("html_body", sa.Text(), nullable=True),
        sa.Column("template_type", sa.String(length=50), nullable=False),
        sa.Column("variables", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create notification_schedules table
    op.create_table(
        "notification_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("schedule_type", sa.String(length=50), nullable=False),
        sa.Column(
            "schedule_config", postgresql.JSON(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("timezone", sa.String(length=50), nullable=True),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("custom_subject", sa.String(length=500), nullable=True),
        sa.Column("custom_body", sa.Text(), nullable=True),
        sa.Column(
            "alert_severities", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("alert_types", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("camera_ids", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("last_run", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_runs", sa.Integer(), nullable=True),
        sa.Column("run_count", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["notification_templates.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create notification_analytics table
    op.create_table(
        "notification_analytics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_sent", sa.Integer(), nullable=True),
        sa.Column("total_failed", sa.Integer(), nullable=True),
        sa.Column("total_delivered", sa.Integer(), nullable=True),
        sa.Column("total_opened", sa.Integer(), nullable=True),
        sa.Column("total_clicked", sa.Integer(), nullable=True),
        sa.Column("email_sent", sa.Integer(), nullable=True),
        sa.Column("email_failed", sa.Integer(), nullable=True),
        sa.Column("email_delivered", sa.Integer(), nullable=True),
        sa.Column("email_opened", sa.Integer(), nullable=True),
        sa.Column("push_sent", sa.Integer(), nullable=True),
        sa.Column("push_failed", sa.Integer(), nullable=True),
        sa.Column("push_delivered", sa.Integer(), nullable=True),
        sa.Column("push_clicked", sa.Integer(), nullable=True),
        sa.Column("webhook_sent", sa.Integer(), nullable=True),
        sa.Column("webhook_failed", sa.Integer(), nullable=True),
        sa.Column("webhook_delivered", sa.Integer(), nullable=True),
        sa.Column("avg_delivery_time", sa.Float(), nullable=True),
        sa.Column("avg_open_time", sa.Float(), nullable=True),
        sa.Column("avg_click_time", sa.Float(), nullable=True),
        sa.Column("open_rate", sa.Float(), nullable=True),
        sa.Column("click_rate", sa.Float(), nullable=True),
        sa.Column("bounce_rate", sa.Float(), nullable=True),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hour", sa.Integer(), nullable=True),
        sa.Column("day_of_week", sa.Integer(), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create notification_events table
    op.create_table(
        "notification_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("notification_id", sa.String(length=255), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("delivery_time", sa.Float(), nullable=True),
        sa.Column("processing_time", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create notification_webhooks table
    op.create_table(
        "notification_webhooks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=True),
        sa.Column("auth_type", sa.String(length=50), nullable=True),
        sa.Column(
            "auth_credentials", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("headers", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "payload_template", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("content_type", sa.String(length=100), nullable=True),
        sa.Column(
            "alert_severities", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("alert_types", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("camera_ids", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=True),
        sa.Column("last_sent", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_response", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("success_count", sa.Integer(), nullable=True),
        sa.Column("failure_count", sa.Integer(), nullable=True),
        sa.Column("max_retries", sa.Integer(), nullable=True),
        sa.Column("retry_delay", sa.Integer(), nullable=True),
        sa.Column("timeout", sa.Integer(), nullable=True),
        sa.Column("verify_ssl", sa.Boolean(), nullable=True),
        sa.Column("custom_ca_cert", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
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
        sa.Column("attempt_number", sa.Integer(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["webhook_id"],
            ["notification_webhooks.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(
        op.f("ix_notification_templates_template_type"),
        "notification_templates",
        ["template_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_templates_is_active"),
        "notification_templates",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_schedules_user_id"),
        "notification_schedules",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_schedules_is_active"),
        "notification_schedules",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_schedules_next_run"),
        "notification_schedules",
        ["next_run"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_analytics_user_id"),
        "notification_analytics",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_analytics_date"),
        "notification_analytics",
        ["date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_events_user_id"),
        "notification_events",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_events_timestamp"),
        "notification_events",
        ["timestamp"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_events_event_type"),
        "notification_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_events_channel"),
        "notification_events",
        ["channel"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_webhooks_user_id"),
        "notification_webhooks",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_webhooks_is_active"),
        "notification_webhooks",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        op.f("ix_webhook_delivery_logs_webhook_id"),
        "webhook_delivery_logs",
        ["webhook_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_webhook_delivery_logs_request_time"),
        "webhook_delivery_logs",
        ["request_time"],
        unique=False,
    )


def downgrade():
    # Drop indexes
    op.drop_index(
        op.f("ix_webhook_delivery_logs_request_time"),
        table_name="webhook_delivery_logs",
    )
    op.drop_index(
        op.f("ix_webhook_delivery_logs_webhook_id"), table_name="webhook_delivery_logs"
    )
    op.drop_index(
        op.f("ix_notification_webhooks_is_active"), table_name="notification_webhooks"
    )
    op.drop_index(
        op.f("ix_notification_webhooks_user_id"), table_name="notification_webhooks"
    )
    op.drop_index(
        op.f("ix_notification_events_channel"), table_name="notification_events"
    )
    op.drop_index(
        op.f("ix_notification_events_event_type"), table_name="notification_events"
    )
    op.drop_index(
        op.f("ix_notification_events_timestamp"), table_name="notification_events"
    )
    op.drop_index(
        op.f("ix_notification_events_user_id"), table_name="notification_events"
    )
    op.drop_index(
        op.f("ix_notification_analytics_date"), table_name="notification_analytics"
    )
    op.drop_index(
        op.f("ix_notification_analytics_user_id"), table_name="notification_analytics"
    )
    op.drop_index(
        op.f("ix_notification_schedules_next_run"), table_name="notification_schedules"
    )
    op.drop_index(
        op.f("ix_notification_schedules_is_active"), table_name="notification_schedules"
    )
    op.drop_index(
        op.f("ix_notification_schedules_user_id"), table_name="notification_schedules"
    )
    op.drop_index(
        op.f("ix_notification_templates_is_active"), table_name="notification_templates"
    )
    op.drop_index(
        op.f("ix_notification_templates_template_type"),
        table_name="notification_templates",
    )

    # Drop tables
    op.drop_table("webhook_delivery_logs")
    op.drop_table("notification_webhooks")
    op.drop_table("notification_events")
    op.drop_table("notification_analytics")
    op.drop_table("notification_schedules")
    op.drop_table("notification_templates")
