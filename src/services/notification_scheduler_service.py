import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pytz
from loguru import logger
from sqlalchemy.orm import Session

from src.database.models.base import get_db
from src.database.models.notification_schedule import NotificationSchedule
from src.database.models.notification_template import NotificationTemplate
from src.services.user_notification_service import user_notification_service


class NotificationSchedulerService:
    """Service for managing scheduled notifications."""

    def __init__(self):
        self.db: Session = next(get_db())
        self.scheduler_running = False

    def create_schedule(self, schedule_data: Dict) -> NotificationSchedule:
        """Create a new notification schedule."""
        try:
            schedule = NotificationSchedule(**schedule_data)
            self.db.add(schedule)
            self.db.commit()
            self.db.refresh(schedule)

            # Set initial next_run time
            schedule.update_next_run()
            self.db.commit()

            logger.info(f"Created notification schedule: {schedule.name}")
            return schedule
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create notification schedule: {e}")
            raise

    def get_schedule(self, schedule_id: str) -> Optional[NotificationSchedule]:
        """Get a notification schedule by ID."""
        try:
            return (
                self.db.query(NotificationSchedule)
                .filter(NotificationSchedule.id == schedule_id)
                .first()
            )
        except Exception as e:
            logger.error(f"Failed to get notification schedule: {e}")
            return None

    def get_user_schedules(
        self, user_id: str, is_active: bool = True
    ) -> List[NotificationSchedule]:
        """Get schedules for a specific user."""
        try:
            return (
                self.db.query(NotificationSchedule)
                .filter(
                    NotificationSchedule.user_id == user_id,
                    NotificationSchedule.is_active == is_active,
                )
                .all()
            )
        except Exception as e:
            logger.error(f"Failed to get user schedules: {e}")
            return []

    def update_schedule(
        self, schedule_id: str, schedule_data: Dict
    ) -> Optional[NotificationSchedule]:
        """Update a notification schedule."""
        try:
            schedule = self.get_schedule(schedule_id)
            if not schedule:
                return None

            for key, value in schedule_data.items():
                if hasattr(schedule, key):
                    setattr(schedule, key, value)

            # Update next_run time if schedule config changed
            if "schedule_config" in schedule_data:
                schedule.update_next_run()

            self.db.commit()
            self.db.refresh(schedule)
            logger.info(f"Updated notification schedule: {schedule.name}")
            return schedule
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update notification schedule: {e}")
            return None

    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a notification schedule."""
        try:
            schedule = self.get_schedule(schedule_id)
            if not schedule:
                return False

            self.db.delete(schedule)
            self.db.commit()
            logger.info(f"Deleted notification schedule: {schedule.name}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete notification schedule: {e}")
            return False

    def get_due_schedules(self) -> List[NotificationSchedule]:
        """Get all schedules that are due to run."""
        try:
            now = datetime.utcnow()
            return (
                self.db.query(NotificationSchedule)
                .filter(
                    NotificationSchedule.is_active == True,
                    NotificationSchedule.next_run <= now,
                )
                .all()
            )
        except Exception as e:
            logger.error(f"Failed to get due schedules: {e}")
            return []

    async def run_scheduled_notifications(self):
        """Run all due scheduled notifications."""
        try:
            due_schedules = self.get_due_schedules()

            for schedule in due_schedules:
                await self._execute_schedule(schedule)

        except Exception as e:
            logger.error(f"Failed to run scheduled notifications: {e}")

    async def _execute_schedule(self, schedule: NotificationSchedule):
        """Execute a single scheduled notification."""
        try:
            logger.info(f"Executing scheduled notification: {schedule.name}")

            # Get alert data based on schedule filters
            alert_data = await self._get_filtered_alerts(schedule)

            if not alert_data:
                logger.info(f"No alerts found for schedule: {schedule.name}")
                return

            # Prepare notification content
            notification_content = await self._prepare_notification_content(
                schedule, alert_data
            )

            # Send notification
            await user_notification_service.send_notification_to_user(
                user_id=str(schedule.user_id),
                notification_type="scheduled",
                content=notification_content,
                channels=["email"],  # Default to email for scheduled notifications
            )

            # Update schedule statistics
            schedule.last_run = datetime.utcnow()
            schedule.run_count += 1
            schedule.update_next_run()

            self.db.commit()
            logger.info(
                f"Successfully executed scheduled notification: {schedule.name}"
            )

        except Exception as e:
            logger.error(
                f"Failed to execute scheduled notification {schedule.name}: {e}"
            )

    async def _get_filtered_alerts(self, schedule: NotificationSchedule) -> List[Dict]:
        """Get alerts filtered by schedule criteria."""
        try:
            # This is a simplified implementation
            # In production, you'd query the actual alerts database
            from datetime import datetime, timedelta

            # Mock alert data for demonstration
            alerts = []

            # Filter by severity
            severities = schedule.alert_severities or ["critical", "high", "medium"]

            # Filter by alert types
            alert_types = schedule.alert_types or ["shoplifting", "suspicious_activity"]

            # Filter by cameras
            camera_ids = schedule.camera_ids or ["CAM-1", "CAM-2", "CAM-3"]

            # Generate mock alerts based on filters
            for i in range(5):  # Generate 5 mock alerts
                alert = {
                    "id": f"alert-{i}",
                    "type": alert_types[i % len(alert_types)],
                    "severity": severities[i % len(severities)],
                    "camera_id": camera_ids[i % len(camera_ids)],
                    "timestamp": datetime.utcnow() - timedelta(hours=i),
                    "description": f"Mock alert {i} for scheduled notification",
                }
                alerts.append(alert)

            return alerts

        except Exception as e:
            logger.error(f"Failed to get filtered alerts: {e}")
            return []

    async def _prepare_notification_content(
        self, schedule: NotificationSchedule, alerts: List[Dict]
    ) -> Dict:
        """Prepare notification content based on schedule configuration."""
        try:
            if schedule.template_id:
                # Use custom template
                template = (
                    self.db.query(NotificationTemplate)
                    .filter(NotificationTemplate.id == schedule.template_id)
                    .first()
                )

                if template:
                    # Render template with alert data
                    context = {
                        "alert_count": len(alerts),
                        "alerts": alerts,
                        "schedule_name": schedule.name,
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                    rendered = template.render_template(context)
                    return {
                        "subject": rendered["subject"],
                        "body": rendered["body"],
                        "html_body": rendered.get("html_body"),
                    }

            # Use custom content if no template
            if schedule.custom_subject and schedule.custom_body:
                return {
                    "subject": schedule.custom_subject,
                    "body": schedule.custom_body,
                }

            # Default content
            return {
                "subject": f"Scheduled Security Report - {schedule.name}",
                "body": f"Security report for {schedule.name}\n\nFound {len(alerts)} alerts in the specified time period.",
            }

        except Exception as e:
            logger.error(f"Failed to prepare notification content: {e}")
            return {
                "subject": "Scheduled Security Report",
                "body": "Security report generated by scheduled notification.",
            }

    async def start_scheduler(self):
        """Start the notification scheduler."""
        if self.scheduler_running:
            return

        self.scheduler_running = True
        logger.info("Starting notification scheduler")

        while self.scheduler_running:
            try:
                await self.run_scheduled_notifications()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)

    def stop_scheduler(self):
        """Stop the notification scheduler."""
        self.scheduler_running = False
        logger.info("Stopping notification scheduler")

    def get_schedule_stats(self, user_id: str) -> Dict:
        """Get statistics for user's schedules."""
        try:
            schedules = self.get_user_schedules(user_id)

            stats = {
                "total_schedules": len(schedules),
                "active_schedules": len([s for s in schedules if s.is_active]),
                "total_runs": sum(s.run_count for s in schedules),
                "next_run": None,
            }

            # Find next scheduled run
            active_schedules = [s for s in schedules if s.is_active and s.next_run]
            if active_schedules:
                # Ensure next_run values are datetime objects
                next_run_times = [
                    s.next_run for s in active_schedules if s.next_run is not None
                ]
                if next_run_times:
                    next_run = min(next_run_times)
                    stats["next_run"] = next_run.isoformat()

            return stats

        except Exception as e:
            logger.error(f"Failed to get schedule stats: {e}")
            return {}


# Global instance
notification_scheduler_service = NotificationSchedulerService()
