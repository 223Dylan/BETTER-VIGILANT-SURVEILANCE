"""Fix notification_events columns to match model

Revision ID: notif_events_002
Revises: adv_notifications_001
Create Date: 2025-08-12 13:05:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "notif_events_002"
down_revision = "adv_notifications_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    table = "notification_events"

    # Add missing columns if they don't exist
    # channel
    try:
        op.add_column(table, sa.Column("channel", sa.String(length=50), nullable=True))
    except Exception:
        pass

    # error_message
    try:
        op.add_column(
            table, sa.Column("error_message", sa.String(length=500), nullable=True)
        )
    except Exception:
        pass

    # delivery_time
    try:
        op.add_column(table, sa.Column("delivery_time", sa.Float(), nullable=True))
    except Exception:
        pass

    # processing_time
    try:
        op.add_column(table, sa.Column("processing_time", sa.Float(), nullable=True))
    except Exception:
        pass

    # event_data (rename from event_metadata if present)
    conn = op.get_bind()

    # Check existing columns
    existing_cols = set()
    res = conn.execute(
        sa.text(
            """
        SELECT column_name FROM information_schema.columns
        WHERE table_name = :tbl
        """
        ),
        {"tbl": table},
    ).fetchall()
    existing_cols = {r[0] for r in res}

    if "event_metadata" in existing_cols and "event_data" not in existing_cols:
        op.alter_column(table, "event_metadata", new_column_name="event_data")

    # timestamp (rename from event_timestamp if present)
    if "event_timestamp" in existing_cols and "timestamp" not in existing_cols:
        op.alter_column(table, "event_timestamp", new_column_name="timestamp")

    # Make channel non-nullable only after adding; keep nullable for safety
    # If you want non-null, uncomment the following line after backfilling values
    # op.alter_column(table, "channel", existing_type=sa.String(length=50), nullable=False)


def downgrade() -> None:
    table = "notification_events"

    # Reverse renames if the new names exist
    conn = op.get_bind()
    res = conn.execute(
        sa.text(
            """
        SELECT column_name FROM information_schema.columns
        WHERE table_name = :tbl
        """
        ),
        {"tbl": table},
    ).fetchall()
    existing_cols = {r[0] for r in res}

    if "timestamp" in existing_cols and "event_timestamp" not in existing_cols:
        op.alter_column(table, "timestamp", new_column_name="event_timestamp")

    if "event_data" in existing_cols and "event_metadata" not in existing_cols:
        op.alter_column(table, "event_data", new_column_name="event_metadata")

    # Drop added columns if present
    for col in ["channel", "error_message", "delivery_time", "processing_time"]:
        if col in existing_cols:
            try:
                op.drop_column(table, col)
            except Exception:
                pass
