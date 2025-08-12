"""Add advanced notification features

Revision ID: adv_notifications_001
Revises: 0bf1432298e3
Create Date: 2024-01-01 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "adv_notifications_001"
down_revision = "0bf1432298e3"
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
        sa.Column("user_id", sa.String(), nullable=False),
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
        sa.Column("user_id", sa.String(), nullable=False),
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
        sa.Column(
            "analytics_data", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create notification_events table
    op.create_table(
        "notification_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )

    # Create foreign keys
    op.create_foreign_key(
        "fk_notification_analytics_user_id",
        "notification_analytics",
        "users",
        ["user_id"],
        ["id"],
    )

    op.create_foreign_key(
        "fk_notification_events_user_id",
        "notification_events",
        "users",
        ["user_id"],
        ["id"],
    )


def downgrade():
    op.drop_table("notification_events")
    op.drop_table("notification_analytics")
    op.drop_table("notification_schedules")
    op.drop_table("notification_templates")
