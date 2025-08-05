"""add_user_notification_preferences

Revision ID: user_notifications_001
Revises: 455924c09f24
Create Date: 2024-01-01 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "user_notifications_001"
down_revision = "455924c09f24"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_notification_preferences table
    op.create_table(
        "user_notification_preferences",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, default=True),
        sa.Column("push_enabled", sa.Boolean(), nullable=False, default=True),
        sa.Column("webhook_enabled", sa.Boolean(), nullable=False, default=False),
        sa.Column("webhook_url", sa.String(length=500), nullable=True),
        sa.Column("alert_severities", sa.JSON(), nullable=True),
        sa.Column("alert_types", sa.JSON(), nullable=True),
        sa.Column("assigned_cameras", sa.JSON(), nullable=True),
        sa.Column("cooldown_minutes", sa.Integer(), nullable=False, default=5),
        sa.Column("quiet_hours_enabled", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "quiet_hours_start", sa.String(length=5), nullable=True, default="22:00"
        ),
        sa.Column(
            "quiet_hours_end", sa.String(length=5), nullable=True, default="08:00"
        ),
        sa.Column("custom_filters", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(
        "ix_user_notification_preferences_user_id",
        "user_notification_preferences",
        ["user_id"],
    )

    # Create foreign key constraint
    op.create_foreign_key(
        "fk_user_notification_preferences_user_id",
        "user_notification_preferences",
        "users",
        ["user_id"],
        ["id"],
    )

    # Create unique constraint on user_id
    op.create_unique_constraint(
        "uq_user_notification_preferences_user_id",
        "user_notification_preferences",
        ["user_id"],
    )


def downgrade() -> None:
    # Drop the table and all its constraints/indexes
    op.drop_table("user_notification_preferences")
