#!/usr/bin/env python3
"""
Simple script to check the notification history table.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import func

from database.models.base import get_db
from database.models.notification_history import NotificationHistory


def check_notification_history():
    """Check the notification history table."""
    db = next(get_db())

    try:
        # Count total records
        total_count = db.query(func.count(NotificationHistory.id)).scalar()
        print(f"Total notification history records: {total_count}")

        # Count by notification type
        type_counts = (
            db.query(
                NotificationHistory.notification_type,
                func.count(NotificationHistory.id),
            )
            .group_by(NotificationHistory.notification_type)
            .all()
        )

        print("\nRecords by notification type:")
        for notification_type, count in type_counts:
            print(f"  {notification_type}: {count}")

        # Count by user
        user_counts = (
            db.query(NotificationHistory.user_id, func.count(NotificationHistory.id))
            .group_by(NotificationHistory.user_id)
            .all()
        )

        print("\nRecords by user:")
        for user_id, count in user_counts:
            print(f"  {user_id}: {count}")

        # Show some sample records
        print("\nSample records:")
        sample_records = db.query(NotificationHistory).limit(5).all()
        for record in sample_records:
            print(f"  ID: {record.id}")
            print(f"    User: {record.user_id}")
            print(f"    Type: {record.notification_type}")
            print(f"    Title: {record.title}")
            print(f"    Created: {record.created_at}")
            print(f"    Channel Data: {record.channel_data}")
            print()

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    check_notification_history()
