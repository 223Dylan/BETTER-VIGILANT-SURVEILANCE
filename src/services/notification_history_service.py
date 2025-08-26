from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from loguru import logger
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from src.database.models.base import get_db
from src.database.models.notification_history import NotificationHistory
from src.database.models.user import User


class NotificationHistoryService:
    """Service for managing notification history records."""

    def __init__(self):
        pass

    def create_notification_record(
        self,
        db: Session,
        user_id: str,
        notification_type: str,
        title: Optional[str] = None,
        message: Optional[str] = None,
        alert_id: Optional[str] = None,
        channel_data: Optional[Dict] = None,
    ) -> NotificationHistory:
        """Create a new notification history record."""
        try:
            notification = NotificationHistory(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                alert_id=alert_id,
                channel_data=channel_data,
                status="pending",
            )

            db.add(notification)
            db.commit()
            db.refresh(notification)

            logger.debug(f"Created notification history record: {notification.id}")
            return notification

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create notification history record: {e}")
            raise

    def get_notification_by_id(
        self,
        db: Session,
        notification_id: str,
    ) -> Optional[Dict]:
        """Get a specific notification by ID."""
        try:
            notification = (
                db.query(NotificationHistory)
                .filter(NotificationHistory.id == notification_id)
                .first()
            )

            if notification:
                return notification.to_dict()
            return None

        except Exception as e:
            logger.error(f"Failed to get notification {notification_id}: {e}")
            return None

    def update_notification_status(
        self,
        db: Session,
        notification_id: str,
        new_status: str,
        timestamp: Optional[datetime] = None,
        error_message: Optional[str] = None,
        channel_data: Optional[Dict] = None,
    ) -> Optional[NotificationHistory]:
        """Update notification status and related fields."""
        try:
            notification = (
                db.query(NotificationHistory)
                .filter(NotificationHistory.id == notification_id)
                .first()
            )

            if not notification:
                logger.warning(
                    f"Notification history record not found: {notification_id}"
                )
                return None

            notification.update_status(new_status, timestamp)

            if error_message:
                notification.error_message = error_message

            if channel_data:
                if notification.channel_data is None:
                    notification.channel_data = {}
                notification.channel_data.update(channel_data)

            db.commit()
            db.refresh(notification)

            logger.debug(
                f"Updated notification {notification_id} status to {new_status}"
            )
            return notification

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update notification status: {e}")
            raise

    def get_user_notification_history(
        self,
        db: Session,
        user_id: str,
        limit: int = 50,
        notification_type: Optional[str] = None,
        status: Optional[str] = None,
        date_range: Optional[str] = None,
        alert_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get notification history for a specific user with optional filtering."""
        try:
            query = db.query(NotificationHistory).filter(
                NotificationHistory.user_id == user_id
            )

            # Apply filters
            if notification_type and notification_type.lower() != "all":
                query = query.filter(
                    NotificationHistory.notification_type == notification_type
                )

            if status and status.lower() != "all":
                query = query.filter(NotificationHistory.status == status)

            if alert_id:
                query = query.filter(NotificationHistory.alert_id == alert_id)

            # Apply date range filter
            if date_range:
                try:
                    # Handle formats like "7d", "24h", "30d", etc.
                    if isinstance(date_range, str):
                        if date_range.endswith("d"):
                            days = int(date_range[:-1])
                        elif date_range.endswith("h"):
                            days = int(date_range[:-1]) / 24
                        else:
                            days = int(date_range)
                    else:
                        days = int(date_range)

                    cutoff_date = datetime.now() - timedelta(days=days)
                    query = query.filter(NotificationHistory.created_at >= cutoff_date)
                except ValueError:
                    logger.warning(f"Invalid date range format: {date_range}")

            # Order by creation date (newest first) and limit results
            query = query.order_by(desc(NotificationHistory.created_at)).limit(limit)

            notifications = query.all()
            return [notification.to_dict() for notification in notifications]

        except Exception as e:
            logger.error(f"Failed to get notification history for user {user_id}: {e}")
            return []

    def get_system_notification_history(
        self,
        db: Session,
        limit: int = 100,
        notification_type: Optional[str] = None,
        status: Optional[str] = None,
        date_range: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get system-wide notification history with optional filtering."""
        try:
            query = db.query(NotificationHistory)

            # Apply filters
            if notification_type and notification_type.lower() != "all":
                query = query.filter(
                    NotificationHistory.notification_type == notification_type
                )

            if status and status.lower() != "all":
                query = query.filter(NotificationHistory.status == status)

            if user_id and user_id.lower() != "all":
                query = query.filter(NotificationHistory.user_id == user_id)

            # Apply date range filter
            if date_range:
                try:
                    # Handle formats like "7d", "24h", "30d", etc.
                    if isinstance(date_range, str):
                        if date_range.endswith("d"):
                            days = int(date_range[:-1])
                        elif date_range.endswith("h"):
                            days = int(date_range[:-1]) / 24
                        else:
                            days = int(date_range)
                    else:
                        days = int(date_range)

                    cutoff_date = datetime.now() - timedelta(days=days)
                    query = query.filter(NotificationHistory.created_at >= cutoff_date)
                except ValueError:
                    logger.warning(f"Invalid date range format: {date_range}")

            # Order by creation date (newest first) and limit results
            query = query.order_by(desc(NotificationHistory.created_at)).limit(limit)

            notifications = query.all()
            return [notification.to_dict() for notification in notifications]

        except Exception as e:
            logger.error(f"Failed to get system notification history: {e}")
            return []

    def get_notification_statistics(
        self,
        db: Session,
        user_id: Optional[str] = None,
        days: int = 7,
    ) -> Dict:
        """Get notification statistics for the specified period."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            # Base query
            query = db.query(NotificationHistory).filter(
                NotificationHistory.created_at >= cutoff_date
            )

            # Filter by user if specified
            if user_id:
                query = query.filter(NotificationHistory.user_id == user_id)

            # Get total counts
            total_notifications = query.count()

            # Get status breakdown
            status_counts = db.query(
                NotificationHistory.status, func.count(NotificationHistory.id)
            ).filter(NotificationHistory.created_at >= cutoff_date)

            if user_id:
                status_counts = status_counts.filter(
                    NotificationHistory.user_id == user_id
                )

            status_counts = status_counts.group_by(NotificationHistory.status).all()

            # Get type breakdown
            type_counts = db.query(
                NotificationHistory.notification_type,
                func.count(NotificationHistory.id),
            ).filter(NotificationHistory.created_at >= cutoff_date)

            if user_id:
                type_counts = type_counts.filter(NotificationHistory.user_id == user_id)

            type_counts = type_counts.group_by(
                NotificationHistory.notification_type
            ).all()

            # Calculate success rate
            successful = sum(
                count
                for status, count in status_counts
                if status in ["delivered", "opened", "clicked"]
            )
            failed = sum(count for status, count in status_counts if status == "failed")
            success_rate = (
                (successful / total_notifications * 100)
                if total_notifications > 0
                else 0.0
            )

            return {
                "total_notifications": total_notifications,
                "successful_notifications": successful,
                "failed_notifications": failed,
                "success_rate": round(success_rate, 2),
                "status_breakdown": dict(status_counts),
                "type_breakdown": dict(type_counts),
                "period_days": days,
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get notification statistics: {e}")
            return {
                "total_notifications": 0,
                "successful_notifications": 0,
                "failed_notifications": 0,
                "success_rate": 0.0,
                "status_breakdown": {},
                "type_breakdown": {},
                "period_days": days,
                "generated_at": datetime.now().isoformat(),
            }

    def cleanup_old_notifications(self, db: Session, days_to_keep: int = 90) -> int:
        """Clean up old notification history records."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            # Count records to be deleted
            count_query = db.query(func.count(NotificationHistory.id)).filter(
                NotificationHistory.created_at < cutoff_date
            )
            count_to_delete = count_query.scalar()

            if count_to_delete == 0:
                logger.info("No old notification records to clean up")
                return 0

            # Delete old records
            delete_query = db.query(NotificationHistory).filter(
                NotificationHistory.created_at < cutoff_date
            )
            delete_query.delete()

            db.commit()

            logger.info(
                f"Cleaned up {count_to_delete} old notification history records"
            )
            return count_to_delete

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cleanup old notifications: {e}")
            raise


# Global instance
notification_history_service = NotificationHistoryService()
