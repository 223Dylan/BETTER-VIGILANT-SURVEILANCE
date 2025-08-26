"""add_notification_history_table

Revision ID: notification_history_001
Revises: user_notifications_001
Create Date: 2024-01-01 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "notification_history_001"
down_revision = "user_notifications_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create notification_history table
    op.create_table(
        "notification_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("alert_id", sa.String(), nullable=True),
        sa.Column("notification_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="pending"
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("clicked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("channel_data", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.String(length=10), server_default="0"),
        sa.Column("delivery_time", sa.String(length=10), nullable=True),
        sa.Column("processing_time", sa.String(length=10), nullable=True),
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
        "idx_notification_history_user_id", "notification_history", ["user_id"]
    )
    op.create_index(
        "idx_notification_history_alert_id", "notification_history", ["alert_id"]
    )
    op.create_index(
        "idx_notification_history_status", "notification_history", ["status"]
    )
    op.create_index(
        "idx_notification_history_type", "notification_history", ["notification_type"]
    )
    op.create_index(
        "idx_notification_history_created_at", "notification_history", ["created_at"]
    )

    # Create foreign key constraints
    op.create_foreign_key(
        "fk_notification_history_user_id",
        "notification_history",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_notification_history_alert_id",
        "notification_history",
        "alerts",
        ["alert_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Drop foreign key constraints
    op.drop_constraint(
        "fk_notification_history_alert_id", "notification_history", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_notification_history_user_id", "notification_history", type_="foreignkey"
    )

    # Drop indexes
    op.drop_index("idx_notification_history_created_at", "notification_history")
    op.drop_index("idx_notification_history_type", "notification_history")
    op.drop_index("idx_notification_history_status", "notification_history")
    op.drop_index("idx_notification_history_alert_id", "notification_history")
    op.drop_index("idx_notification_history_user_id", "notification_history")

    # Drop table
    op.drop_table("notification_history")
