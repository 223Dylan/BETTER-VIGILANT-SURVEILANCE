import asyncio
import json
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional, Set

import requests
from loguru import logger
from sqlalchemy.orm import Session

from src.database.models.alert import Alert
from src.database.models.user import User
from src.database.models.user_notification_preferences import (
    UserNotificationPreferences,
)
from src.services.notification_history_service import notification_history_service
from src.websocket_manager import websocket_manager


class UserNotificationService:
    """Service for sending user-specific alert notifications."""

    def __init__(self):
        self.last_notification_time: Dict[str, datetime] = {}
        self.notification_history: List[Dict] = []
        self.max_history_size = 1000

        # Load SMTP configuration
        self.smtp_config = self._load_smtp_config()

        logger.info("[INIT] User Notification Service initialized")

    def _load_smtp_config(self) -> Optional[Dict]:
        """Load SMTP configuration from environment variables."""
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = os.getenv("SMTP_PORT", "587")
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_from = os.getenv("SMTP_FROM_ADDRESS")

        if not all([smtp_host, smtp_username, smtp_password, smtp_from]):
            logger.warning(
                "[SMTP] SMTP configuration incomplete - email notifications disabled"
            )
            return None

        try:
            config = {
                "host": smtp_host,
                "port": int(smtp_port),
                "username": smtp_username,
                "password": smtp_password,
                "from_address": smtp_from,
                "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            }
            logger.info(f"[SMTP] SMTP configured for {smtp_host}:{smtp_port}")
            return config
        except ValueError as e:
            logger.error(f"[SMTP] Invalid SMTP configuration: {e}")
            return None

    async def send_alert_to_users(self, alert_data: Dict, db: Session) -> int:
        """Send alert notification to all eligible users."""
        try:
            # Get all active users with their notification preferences
            users_with_prefs = (
                db.query(User, UserNotificationPreferences)
                .outerjoin(
                    UserNotificationPreferences,
                    User.id == UserNotificationPreferences.user_id,
                )
                .filter(User.is_active == True)
                .all()
            )

            eligible_users = []
            for user, prefs in users_with_prefs:
                # Create default preferences if none exist
                if not prefs:
                    prefs = self._create_default_preferences(user.id, db)

                # Check if user should receive this alert
                if prefs.should_receive_alert(
                    alert_data.get("severity"),
                    alert_data.get("type"),
                    alert_data.get("camera_id"),
                ):
                    eligible_users.append((user, prefs))

            if not eligible_users:
                logger.info(
                    f"[NOTIFICATIONS] No eligible users for alert {alert_data.get('id')}"
                )
                return 0

            # Send notifications to eligible users
            notification_tasks = []
            for user, prefs in eligible_users:
                if self._can_send_notification(user.id, prefs.cooldown_minutes):
                    task = self._send_user_notification(user, prefs, alert_data)
                    notification_tasks.append(task)

            if not notification_tasks:
                logger.info(
                    f"[NOTIFICATIONS] All users in cooldown for alert {alert_data.get('id')}"
                )
                return 0

            # Execute all notifications concurrently
            results = await asyncio.gather(*notification_tasks, return_exceptions=True)

            # Count successful notifications
            successful = sum(1 for r in results if r is True)
            failed = len(results) - successful

            logger.info(
                f"[NOTIFICATIONS] Alert {alert_data.get('id')}: "
                f"Sent to {successful} users, {failed} failed"
            )

            # Record in history
            self._record_notification(
                alert_data, len(eligible_users), successful, failed
            )

            return successful

        except Exception as e:
            logger.error(f"[NOTIFICATIONS] Error sending alert notifications: {e}")
            return 0

    async def _send_user_notification(
        self, user: User, prefs: UserNotificationPreferences, alert_data: Dict
    ) -> bool:
        """Send notification to a specific user through their preferred channels."""
        try:
            notification_data = self._prepare_notification_data(alert_data, user)

            success = False

            # Send email notification
            if prefs.email_enabled and self.smtp_config:
                email_success = await self._send_email_notification(
                    user, notification_data
                )
                success = success or email_success

            # Send WebSocket notification (real-time)
            if prefs.push_enabled:
                ws_success = await self._send_websocket_notification(
                    user, notification_data
                )
                success = success or ws_success

            # Send webhook notification
            if prefs.webhook_enabled and prefs.webhook_url:
                webhook_success = await self._send_webhook_notification(
                    user, prefs.webhook_url, notification_data
                )
                success = success or webhook_success

            # Update last notification time if any channel succeeded
            if success:
                self.last_notification_time[user.id] = datetime.now()

            return success

        except Exception as e:
            logger.error(
                f"[NOTIFICATIONS] Error sending notification to user {user.id}: {e}"
            )
            return False

    def _prepare_notification_data(self, alert_data: Dict, user: User) -> Dict:
        """Prepare notification data for user."""
        return {
            "alert_id": alert_data.get("id"),
            "camera_id": alert_data.get("camera_id"),
            "type": alert_data.get("type"),
            "severity": alert_data.get("severity"),
            "message": alert_data.get("message"),
            "confidence": alert_data.get("confidence"),
            "timestamp": alert_data.get("timestamp"),
            "user_id": user.id,
            "username": user.username,
            "user_email": user.email,
        }

    async def _send_email_notification(
        self, user: User, notification_data: Dict
    ) -> bool:
        """Send email notification to user."""
        if not self.smtp_config:
            return False

        try:
            # Create email message
            msg = MIMEMultipart("alternative")
            msg["From"] = self.smtp_config["from_address"]
            msg["To"] = user.email
            msg["Subject"] = (
                f"Security Alert: {notification_data['type'].replace('_', ' ').title()}"
            )

            # Create HTML body
            html_body = self._create_email_html(notification_data)
            text_body = self._create_email_text(notification_data)

            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            # Send email
            with smtplib.SMTP(
                self.smtp_config["host"], self.smtp_config["port"]
            ) as server:
                if self.smtp_config["use_tls"]:
                    server.starttls()
                server.login(self.smtp_config["username"], self.smtp_config["password"])
                server.send_message(msg)

            logger.info(f"[EMAIL] Notification sent to {user.email}")
            return True

        except Exception as e:
            logger.error(f"[EMAIL] Failed to send email to {user.email}: {e}")
            return False

    async def _send_websocket_notification(
        self, user: User, notification_data: Dict
    ) -> bool:
        """Send real-time notification via WebSocket."""
        try:
            message = {
                "type": "user_alert_notification",
                "user_id": user.id,
                "data": notification_data,
            }

            # Send to user's WebSocket connection if they're connected
            await websocket_manager.send_to_user(user.id, message)

            logger.info(f"[WEBSOCKET] Notification sent to user {user.id}")
            return True

        except Exception as e:
            logger.error(
                f"[WEBSOCKET] Failed to send WebSocket notification to user {user.id}: {e}"
            )
            return False

    async def _send_webhook_notification(
        self, user: User, webhook_url: str, notification_data: Dict
    ) -> bool:
        """Send webhook notification."""
        try:
            payload = {
                "type": "security_alert",
                "user": {"id": user.id, "username": user.username, "email": user.email},
                "alert": notification_data,
                "timestamp": datetime.now().isoformat(),
            }

            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            logger.info(f"[WEBHOOK] Notification sent for user {user.id}")
            return True

        except Exception as e:
            logger.error(
                f"[WEBHOOK] Failed to send webhook notification for user {user.id}: {e}"
            )
            return False

    def _create_email_html(self, notification_data: Dict) -> str:
        """Create HTML email body for alert notification."""
        severity_colors = {
            "critical": "#dc2626",
            "high": "#ea580c",
            "medium": "#d97706",
            "low": "#059669",
        }

        color = severity_colors.get(
            notification_data.get("severity", "medium"), "#6b7280"
        )
        confidence = notification_data.get("confidence", 0)

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Security Alert</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f9fafb;">
            <div style="background-color: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h2 style="margin: 0; font-size: 24px;">🚨 Security Alert</h2>
            </div>
            <div style="padding: 30px; background-color: white; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
                <h3 style="color: {color}; margin-top: 0; font-size: 20px;">
                    {notification_data.get('type', 'Unknown').replace('_', ' ').title()}
                </h3>

                <div style="margin: 20px 0;">
                    <div style="margin: 10px 0;">
                        <strong>Camera:</strong> {notification_data.get('camera_id', 'Unknown')}
                    </div>
                    <div style="margin: 10px 0;">
                        <strong>Severity:</strong>
                        <span style="color: {color}; font-weight: bold;">
                            {notification_data.get('severity', 'Unknown').title()}
                        </span>
                    </div>
                    <div style="margin: 10px 0;">
                        <strong>Confidence:</strong> {confidence:.1%}
                    </div>
                    <div style="margin: 10px 0;">
                        <strong>Time:</strong> {notification_data.get('timestamp', 'Unknown')}
                    </div>
                </div>

                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <strong>Details:</strong><br>
                    {notification_data.get('message', 'No additional details available.')}
                </div>

                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                    <p style="font-size: 12px; color: #6b7280; margin: 0;">
                        This is an automated alert from your surveillance system.
                        You received this notification because you have email alerts enabled in your preferences.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

    def _create_email_text(self, notification_data: Dict) -> str:
        """Create plain text email body for alert notification."""
        confidence = notification_data.get("confidence", 0)

        return f"""
SECURITY ALERT

Type: {notification_data.get('type', 'Unknown').replace('_', ' ').title()}
Camera: {notification_data.get('camera_id', 'Unknown')}
Severity: {notification_data.get('severity', 'Unknown').title()}
Confidence: {confidence:.1%}
Time: {notification_data.get('timestamp', 'Unknown')}

Details:
{notification_data.get('message', 'No additional details available.')}

---
This is an automated alert from your surveillance system.
        """

    def _can_send_notification(self, user_id: str, cooldown_minutes: int) -> bool:
        """Check if enough time has passed since last notification to this user."""
        if user_id not in self.last_notification_time:
            return True

        time_since_last = datetime.now() - self.last_notification_time[user_id]
        return time_since_last.total_seconds() >= (cooldown_minutes * 60)

    def _create_default_preferences(
        self, user_id: str, db: Session
    ) -> UserNotificationPreferences:
        """Create default notification preferences for a user."""
        try:
            prefs = UserNotificationPreferences(
                user_id=user_id, **UserNotificationPreferences.get_default_preferences()
            )
            db.add(prefs)
            db.commit()
            db.refresh(prefs)

            logger.info(
                f"[PREFS] Created default notification preferences for user {user_id}"
            )
            return prefs

        except Exception as e:
            logger.error(
                f"[PREFS] Failed to create default preferences for user {user_id}: {e}"
            )
            db.rollback()
            # Return a temporary preferences object with defaults
            return UserNotificationPreferences(
                user_id=user_id, **UserNotificationPreferences.get_default_preferences()
            )

    def _record_notification(
        self, alert_data: Dict, eligible_users: int, successful: int, failed: int
    ):
        """Record notification attempt in history."""
        # Keep in-memory record for backward compatibility
        record = {
            "timestamp": datetime.now().isoformat(),
            "alert_id": alert_data.get("id"),
            "alert_type": alert_data.get("type"),
            "alert_severity": alert_data.get("severity"),
            "camera_id": alert_data.get("camera_id"),
            "eligible_users": eligible_users,
            "successful_deliveries": successful,
            "failed_deliveries": failed,
        }

        self.notification_history.append(record)

        # Keep history size manageable
        if len(self.notification_history) > self.max_history_size:
            self.notification_history = self.notification_history[
                -self.max_history_size :
            ]

        # Also record in database for persistent storage
        try:
            # Create a summary record in the database
            notification_history_service.create_notification_record(
                user_id="system",  # System-wide record
                notification_type="alert_broadcast",
                title=f"Alert Broadcast: {alert_data.get('type', 'Unknown')}",
                message=f"Alert {alert_data.get('id')} sent to {eligible_users} users. Success: {successful}, Failed: {failed}",
                alert_id=alert_data.get("id"),
                channel_data={
                    "alert_type": alert_data.get("type"),
                    "alert_severity": alert_data.get("severity"),
                    "camera_id": alert_data.get("camera_id"),
                    "eligible_users": eligible_users,
                    "successful_deliveries": successful,
                    "failed_deliveries": failed,
                },
            )
        except Exception as e:
            logger.error(f"Failed to record notification in database: {e}")

    def get_notification_stats(self, days: int = 7) -> Dict:
        """Get notification statistics for the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)

        recent_notifications = [
            n
            for n in self.notification_history
            if datetime.fromisoformat(n["timestamp"]) >= cutoff_date
        ]

        if not recent_notifications:
            return {
                "total_notifications": 0,
                "total_alerts": 0,
                "total_users_notified": 0,
                "successful_deliveries": 0,
                "failed_deliveries": 0,
                "delivery_success_rate": 0.0,
            }

        total_deliveries = sum(
            n["successful_deliveries"] + n["failed_deliveries"]
            for n in recent_notifications
        )
        successful_deliveries = sum(
            n["successful_deliveries"] for n in recent_notifications
        )

        return {
            "total_notifications": len(recent_notifications),
            "total_alerts": len(set(n["alert_id"] for n in recent_notifications)),
            "total_users_notified": sum(
                n["eligible_users"] for n in recent_notifications
            ),
            "successful_deliveries": successful_deliveries,
            "failed_deliveries": sum(
                n["failed_deliveries"] for n in recent_notifications
            ),
            "delivery_success_rate": (
                (successful_deliveries / total_deliveries * 100)
                if total_deliveries > 0
                else 0.0
            ),
        }


# Global instance
user_notification_service = UserNotificationService()
