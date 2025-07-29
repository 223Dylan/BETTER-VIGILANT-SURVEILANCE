"""Add audit logs table

Revision ID: audit_logs_001
Revises: 455924c09f24
Create Date: 2025-01-29 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "audit_logs_001"
down_revision = "455924c09f24"
branch_labels = None
depends_on = None


def upgrade():
    """Create audit logs table."""
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(), nullable=False, primary_key=True),
        # Who performed the action
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("username", sa.String(length=50), nullable=True),
        sa.Column("user_role", sa.String(length=20), nullable=True),
        # What action was performed
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("action_category", sa.String(length=20), nullable=True),
        # Where the action occurred
        sa.Column("resource_type", sa.String(length=50), nullable=True),
        sa.Column("resource_id", sa.String(), nullable=True),
        sa.Column("endpoint", sa.String(length=255), nullable=True),
        # Context and details
        sa.Column("permission_required", sa.String(length=50), nullable=True),
        sa.Column("permission_granted", sa.Boolean(), nullable=True, default=False),
        sa.Column("request_method", sa.String(length=10), nullable=True),
        # Request details
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("session_id", sa.String(), nullable=True),
        # Result and metadata
        sa.Column("success", sa.Boolean(), nullable=True, default=True),
        sa.Column("severity", sa.String(length=20), nullable=True, default="low"),
        sa.Column("error_message", sa.Text(), nullable=True),
        # Additional context as JSON
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        # Timing
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        # Data retention
        sa.Column("retention_date", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes for better query performance
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_username", "audit_logs", ["username"])
    op.create_index("ix_audit_logs_user_role", "audit_logs", ["user_role"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_action_category", "audit_logs", ["action_category"])
    op.create_index("ix_audit_logs_resource_type", "audit_logs", ["resource_type"])
    op.create_index("ix_audit_logs_resource_id", "audit_logs", ["resource_id"])
    op.create_index("ix_audit_logs_ip_address", "audit_logs", ["ip_address"])
    op.create_index("ix_audit_logs_success", "audit_logs", ["success"])
    op.create_index("ix_audit_logs_severity", "audit_logs", ["severity"])
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])

    # Composite indexes for common query patterns
    op.create_index(
        "ix_audit_logs_user_timestamp", "audit_logs", ["user_id", "timestamp"]
    )
    op.create_index(
        "ix_audit_logs_action_timestamp", "audit_logs", ["action", "timestamp"]
    )
    op.create_index(
        "ix_audit_logs_category_timestamp",
        "audit_logs",
        ["action_category", "timestamp"],
    )
    op.create_index(
        "ix_audit_logs_success_timestamp", "audit_logs", ["success", "timestamp"]
    )


def downgrade():
    """Drop audit logs table."""
    # Drop indexes
    op.drop_index("ix_audit_logs_success_timestamp", table_name="audit_logs")
    op.drop_index("ix_audit_logs_category_timestamp", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action_timestamp", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_timestamp", table_name="audit_logs")
    op.drop_index("ix_audit_logs_timestamp", table_name="audit_logs")
    op.drop_index("ix_audit_logs_severity", table_name="audit_logs")
    op.drop_index("ix_audit_logs_success", table_name="audit_logs")
    op.drop_index("ix_audit_logs_ip_address", table_name="audit_logs")
    op.drop_index("ix_audit_logs_resource_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_resource_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action_category", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_role", table_name="audit_logs")
    op.drop_index("ix_audit_logs_username", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")

    # Drop table
    op.drop_table("audit_logs")
