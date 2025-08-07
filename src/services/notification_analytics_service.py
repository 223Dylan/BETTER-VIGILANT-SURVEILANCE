from datetime import datetime, timedelta
from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from src.database.models.base import get_db
from src.database.models.notification_analytics import (
    NotificationAnalytics,
    NotificationEvent,
)


class NotificationAnalyticsService:
    """Service for notification analytics and reporting."""

    def __init__(self):
        self.db: Session = next(get_db())

    def record_event(self, event_data: Dict) -> NotificationEvent:
        """Record a notification event."""
        try:
            event = NotificationEvent(**event_data)
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            logger.debug(f"Recorded notification event: {event.event_type}")
            return event
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to record notification event: {e}")
            raise

    def update_analytics(self, user_id: str, date: datetime, analytics_data: Dict):
        """Update analytics for a specific user and date."""
        try:
            # Get or create analytics record
            analytics = (
                self.db.query(NotificationAnalytics)
                .filter(
                    and_(
                        NotificationAnalytics.user_id == user_id,
                        func.date(NotificationAnalytics.date) == func.date(date),
                    )
                )
                .first()
            )

            if not analytics:
                analytics = NotificationAnalytics(
                    user_id=user_id,
                    date=date,
                    hour=date.hour,
                    day_of_week=date.weekday(),
                )
                self.db.add(analytics)

            # Update metrics
            for key, value in analytics_data.items():
                if hasattr(analytics, key):
                    current_value = getattr(analytics, key) or 0
                    setattr(analytics, key, current_value + value)

            # Recalculate rates
            analytics.calculate_rates()

            self.db.commit()
            logger.debug(f"Updated analytics for user {user_id} on {date.date()}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update analytics: {e}")

    def get_user_analytics(
        self, user_id: str, start_date: datetime, end_date: datetime
    ) -> List[NotificationAnalytics]:
        """Get analytics for a user within a date range."""
        try:
            return (
                self.db.query(NotificationAnalytics)
                .filter(
                    and_(
                        NotificationAnalytics.user_id == user_id,
                        NotificationAnalytics.date >= start_date,
                        NotificationAnalytics.date <= end_date,
                    )
                )
                .order_by(NotificationAnalytics.date)
                .all()
            )
        except Exception as e:
            logger.error(f"Failed to get user analytics: {e}")
            return []

    def get_analytics_summary(self, user_id: str, days: int = 30) -> Dict:
        """Get analytics summary for a user."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            analytics = self.get_user_analytics(user_id, start_date, end_date)

            if not analytics:
                return self._get_empty_summary()

            # Calculate totals
            total_sent = sum(a.total_sent for a in analytics)
            total_failed = sum(a.total_failed for a in analytics)
            total_delivered = sum(a.total_delivered for a in analytics)
            total_opened = sum(a.total_opened for a in analytics)
            total_clicked = sum(a.total_clicked for a in analytics)

            # Calculate averages
            avg_delivery_time = sum(a.avg_delivery_time or 0 for a in analytics) / len(
                analytics
            )
            avg_open_time = sum(a.avg_open_time or 0 for a in analytics) / len(
                analytics
            )
            avg_click_time = sum(a.avg_click_time or 0 for a in analytics) / len(
                analytics
            )

            # Calculate rates
            open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
            click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
            bounce_rate = (total_failed / total_sent * 100) if total_sent > 0 else 0

            # Channel breakdown
            email_sent = sum(a.email_sent for a in analytics)
            push_sent = sum(a.push_sent for a in analytics)
            webhook_sent = sum(a.webhook_sent for a in analytics)

            return {
                "period_days": days,
                "total_sent": total_sent,
                "total_failed": total_failed,
                "total_delivered": total_delivered,
                "total_opened": total_opened,
                "total_clicked": total_clicked,
                "open_rate": round(open_rate, 2),
                "click_rate": round(click_rate, 2),
                "bounce_rate": round(bounce_rate, 2),
                "avg_delivery_time": round(avg_delivery_time, 2),
                "avg_open_time": round(avg_open_time, 2),
                "avg_click_time": round(avg_click_time, 2),
                "channel_breakdown": {
                    "email": email_sent,
                    "push": push_sent,
                    "webhook": webhook_sent,
                },
                "daily_data": [
                    {
                        "date": a.date.isoformat(),
                        "sent": a.total_sent,
                        "delivered": a.total_delivered,
                        "opened": a.total_opened,
                        "clicked": a.total_clicked,
                    }
                    for a in analytics
                ],
            }

        except Exception as e:
            logger.error(f"Failed to get analytics summary: {e}")
            return self._get_empty_summary()

    def get_hourly_breakdown(self, user_id: str, days: int = 7) -> Dict:
        """Get hourly breakdown of notification activity."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            events = (
                self.db.query(NotificationEvent)
                .filter(
                    and_(
                        NotificationEvent.user_id == user_id,
                        NotificationEvent.timestamp >= start_date,
                        NotificationEvent.timestamp <= end_date,
                    )
                )
                .all()
            )

            # Group by hour
            hourly_data = {}
            for hour in range(24):
                hourly_data[hour] = {
                    "sent": 0,
                    "delivered": 0,
                    "opened": 0,
                    "clicked": 0,
                    "failed": 0,
                }

            for event in events:
                hour = event.timestamp.hour
                if event.event_type in hourly_data[hour]:
                    hourly_data[hour][event.event_type] += 1

            return {"hourly_breakdown": hourly_data, "total_events": len(events)}

        except Exception as e:
            logger.error(f"Failed to get hourly breakdown: {e}")
            return {"hourly_breakdown": {}, "total_events": 0}

    def get_channel_performance(self, user_id: str, days: int = 30) -> Dict:
        """Get performance metrics by channel."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            events = (
                self.db.query(NotificationEvent)
                .filter(
                    and_(
                        NotificationEvent.user_id == user_id,
                        NotificationEvent.timestamp >= start_date,
                        NotificationEvent.timestamp <= end_date,
                    )
                )
                .all()
            )

            # Group by channel
            channel_data = {
                "email": {"sent": 0, "delivered": 0, "opened": 0, "failed": 0},
                "push": {"sent": 0, "delivered": 0, "clicked": 0, "failed": 0},
                "webhook": {"sent": 0, "delivered": 0, "failed": 0},
            }

            for event in events:
                if event.channel in channel_data:
                    if event.event_type in channel_data[event.channel]:
                        channel_data[event.channel][event.event_type] += 1

            # Calculate success rates
            for channel, data in channel_data.items():
                total_sent = sum(data.values())
                if total_sent > 0:
                    data["success_rate"] = round(
                        (data.get("delivered", 0) / total_sent) * 100, 2
                    )
                else:
                    data["success_rate"] = 0

            return {"channel_performance": channel_data, "period_days": days}

        except Exception as e:
            logger.error(f"Failed to get channel performance: {e}")
            return {"channel_performance": {}, "period_days": days}

    def get_event_timeline(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Get recent notification events timeline."""
        try:
            events = (
                self.db.query(NotificationEvent)
                .filter(NotificationEvent.user_id == user_id)
                .order_by(NotificationEvent.timestamp.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": str(event.id),
                    "event_type": event.event_type,
                    "channel": event.channel,
                    "timestamp": event.timestamp.isoformat(),
                    "duration": event.delivery_time,
                    "success": event.event_type != "failed",
                    "error_message": event.error_message,
                }
                for event in events
            ]

        except Exception as e:
            logger.error(f"Failed to get event timeline: {e}")
            return []

    def _get_empty_summary(self) -> Dict:
        """Get empty analytics summary."""
        return {
            "period_days": 30,
            "total_sent": 0,
            "total_failed": 0,
            "total_delivered": 0,
            "total_opened": 0,
            "total_clicked": 0,
            "open_rate": 0.0,
            "click_rate": 0.0,
            "bounce_rate": 0.0,
            "avg_delivery_time": 0.0,
            "avg_open_time": 0.0,
            "avg_click_time": 0.0,
            "channel_breakdown": {"email": 0, "push": 0, "webhook": 0},
            "daily_data": [],
        }


# Global instance
notification_analytics_service = NotificationAnalyticsService()
