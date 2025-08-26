#!/usr/bin/env python3
"""
Script to populate notification history table with sample data for testing.
"""

import os
import random
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from database.models.alert import Alert
from database.models.base import SessionLocal
from database.models.notification_history import NotificationHistory
from database.models.user import User


def create_sample_notification_history():
    """Create sample notification history records."""
    print("Creating sample notification history...")

    with SessionLocal() as db:
        # Get existing users and alerts
        users = db.query(User).limit(5).all()
        alerts = db.query(Alert).limit(10).all()

        if not users:
            print("No users found. Please create users first.")
            return

        if not alerts:
            print("No alerts found. Please create alerts first.")
            return

        # Sample notification types and statuses
        notification_types = ["email", "push", "webhook", "alert_broadcast"]
        statuses = ["pending", "sent", "delivered", "failed", "opened", "clicked"]
        severities = ["critical", "high", "medium", "low"]

        # Create sample notifications for the last 30 days
        base_time = datetime.now()

        for i in range(100):  # Create 100 sample notifications
            # Random timestamp within last 30 days
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)

            timestamp = base_time - timedelta(
                days=days_ago, hours=hours_ago, minutes=minutes_ago
            )

            # Random user and alert
            user = random.choice(users)
            alert = random.choice(alerts) if alerts else None

            # Random notification type and status
            notification_type = random.choice(notification_types)
            status = random.choice(statuses)

            # Create notification record
            notification = NotificationHistory(
                user_id=user.id,
                notification_type=notification_type,
                title=f"Security Alert - {random.choice(severities).title()} Severity",
                message=f"Suspicious activity detected on camera {alert.camera_id if alert else 'CAM-001'}",
                alert_id=alert.id if alert else None,
                status=status,
                channel_data={
                    "severity": random.choice(severities),
                    "camera_id": alert.camera_id if alert else "CAM-001",
                    "confidence": round(random.uniform(0.6, 0.95), 3),
                },
                retry_count=random.randint(0, 3),
                created_at=timestamp,
                updated_at=timestamp,
            )

            # Add timestamps based on status
            if status in ["sent", "delivered", "opened", "clicked"]:
                notification.sent_at = timestamp + timedelta(
                    seconds=random.randint(1, 30)
                )

            if status in ["delivered", "opened", "clicked"]:
                notification.delivered_at = timestamp + timedelta(
                    seconds=random.randint(31, 60)
                )

            if status == "opened":
                notification.opened_at = timestamp + timedelta(
                    seconds=random.randint(61, 120)
                )

            if status == "clicked":
                notification.clicked_at = timestamp + timedelta(
                    seconds=random.randint(121, 180)
                )

            if status == "failed":
                notification.error_message = "Delivery failed: Network timeout"

            db.add(notification)

        try:
            db.commit()
            print(f"✅ Successfully created 100 sample notification history records")
        except Exception as e:
            db.rollback()
            print(f"❌ Error creating notification history: {e}")


def main():
    """Main function."""
    print("=" * 60)
    print("POPULATING NOTIFICATION HISTORY TABLE")
    print("=" * 60)

    try:
        create_sample_notification_history()
        print("\n✅ Notification history population completed!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
