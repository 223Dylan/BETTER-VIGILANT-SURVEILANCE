"""Add push_subscriptions table

Revision ID: add_push_subscriptions_table
Revises: notification_history_001
Create Date: 2025-01-26 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_push_subscriptions_table"
down_revision = "notification_history_001"
branch_labels = None
depends_on = None


def upgrade():
    """Create push_subscriptions table."""
    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh_key", sa.Text(), nullable=False),
        sa.Column("auth_key", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # Create index on user_id for faster lookups
    op.create_index("ix_push_subscriptions_user_id", "push_subscriptions", ["user_id"])

    # Create index on is_active for filtering active subscriptions
    op.create_index(
        "ix_push_subscriptions_is_active", "push_subscriptions", ["is_active"]
    )


def downgrade():
    """Drop push_subscriptions table."""
    op.drop_index("ix_push_subscriptions_is_active", table_name="push_subscriptions")
    op.drop_index("ix_push_subscriptions_user_id", table_name="push_subscriptions")
    op.drop_table("push_subscriptions")
