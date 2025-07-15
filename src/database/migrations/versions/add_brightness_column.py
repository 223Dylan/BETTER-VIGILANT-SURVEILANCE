"""Add brightness column to cameras table

Revision ID: brightness_001
Revises: 455924c09f24
Create Date: 2025-01-20 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "brightness_001"
down_revision = "455924c09f24"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add brightness column to cameras table
    op.add_column(
        "cameras",
        sa.Column("brightness", sa.Float(), nullable=False, server_default="1.0"),
    )


def downgrade() -> None:
    # Remove brightness column from cameras table
    op.drop_column("cameras", "brightness")
