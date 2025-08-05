"""merge multiple heads

Revision ID: 0bf1432298e3
Revises: audit_logs_001, brightness_001, user_notifications_001
Create Date: 2025-08-05 13:18:31.539831

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0bf1432298e3"
down_revision = ("audit_logs_001", "brightness_001", "user_notifications_001")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
