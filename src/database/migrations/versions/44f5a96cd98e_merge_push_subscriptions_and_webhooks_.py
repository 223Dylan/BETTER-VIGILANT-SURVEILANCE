"""merge push subscriptions and webhooks heads

Revision ID: 44f5a96cd98e
Revises: add_push_subscriptions_table, notif_webhooks_001
Create Date: 2025-08-26 16:01:31.681982

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "44f5a96cd98e"
down_revision = ("add_push_subscriptions_table", "notif_webhooks_001")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
