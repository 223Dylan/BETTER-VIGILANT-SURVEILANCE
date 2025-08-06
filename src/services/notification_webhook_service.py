import asyncio
import json
import ssl
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
from loguru import logger
from sqlalchemy.orm import Session

from src.database.base import get_db
from src.database.models.notification_webhook import (
    NotificationWebhook,
    WebhookDeliveryLog,
)


class NotificationWebhookService:
    """Service for managing notification webhook integrations."""

    def __init__(self):
        self.db: Session = next(get_db())
        self.session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(ssl=False)  # For development
            self.session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self.session

    def create_webhook(self, webhook_data: Dict) -> NotificationWebhook:
        """Create a new notification webhook."""
        try:
            webhook = NotificationWebhook(**webhook_data)
            self.db.add(webhook)
            self.db.commit()
            self.db.refresh(webhook)
            logger.info(f"Created notification webhook: {webhook.name}")
            return webhook
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create notification webhook: {e}")
            raise

    def get_webhook(self, webhook_id: str) -> Optional[NotificationWebhook]:
        """Get a notification webhook by ID."""
        try:
            return (
                self.db.query(NotificationWebhook)
                .filter(NotificationWebhook.id == webhook_id)
                .first()
            )
        except Exception as e:
            logger.error(f"Failed to get notification webhook: {e}")
            return None

    def get_user_webhooks(
        self, user_id: str, is_active: bool = True
    ) -> List[NotificationWebhook]:
        """Get webhooks for a specific user."""
        try:
            return (
                self.db.query(NotificationWebhook)
                .filter(
                    NotificationWebhook.user_id == user_id,
                    NotificationWebhook.is_active == is_active,
                )
                .all()
            )
        except Exception as e:
            logger.error(f"Failed to get user webhooks: {e}")
            return []

    def update_webhook(
        self, webhook_id: str, webhook_data: Dict
    ) -> Optional[NotificationWebhook]:
        """Update a notification webhook."""
        try:
            webhook = self.get_webhook(webhook_id)
            if not webhook:
                return None

            for key, value in webhook_data.items():
                if hasattr(webhook, key):
                    setattr(webhook, key, value)

            self.db.commit()
            self.db.refresh(webhook)
            logger.info(f"Updated notification webhook: {webhook.name}")
            return webhook
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update notification webhook: {e}")
            return None

    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a notification webhook."""
        try:
            webhook = self.get_webhook(webhook_id)
            if not webhook:
                return False

            self.db.delete(webhook)
            self.db.commit()
            logger.info(f"Deleted notification webhook: {webhook.name}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete notification webhook: {e}")
            return False

    async def verify_webhook(self, webhook_id: str) -> bool:
        """Verify a webhook by sending a test request."""
        try:
            webhook = self.get_webhook(webhook_id)
            if not webhook:
                return False

            # Send test payload
            test_payload = {
                "type": "webhook_verification",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "This is a test webhook verification",
            }

            success = await self._send_webhook_request(webhook, test_payload)

            if success:
                webhook.is_verified = True
                self.db.commit()
                logger.info(f"Webhook verified: {webhook.name}")
            else:
                webhook.is_verified = False
                self.db.commit()
                logger.warning(f"Webhook verification failed: {webhook.name}")

            return success

        except Exception as e:
            logger.error(f"Failed to verify webhook: {e}")
            return False

    async def send_webhook_notification(
        self, webhook_id: str, notification_data: Dict
    ) -> bool:
        """Send a notification to a webhook."""
        try:
            webhook = self.get_webhook(webhook_id)
            if not webhook or not webhook.is_active:
                return False

            # Prepare payload
            payload = self._prepare_webhook_payload(webhook, notification_data)

            # Send request
            success = await self._send_webhook_request(webhook, payload)

            # Update webhook statistics
            webhook.update_stats(success)
            webhook.last_sent = datetime.utcnow()
            self.db.commit()

            return success

        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False

    async def _send_webhook_request(
        self, webhook: NotificationWebhook, payload: Dict
    ) -> bool:
        """Send HTTP request to webhook URL."""
        try:
            session = await self.get_session()

            # Prepare headers
            headers = {
                "Content-Type": webhook.content_type,
                "User-Agent": "Better-Vigilant-Surveillance/1.0",
            }

            # Add custom headers
            custom_headers = webhook.get_headers()
            headers.update(custom_headers)

            # Add authentication
            auth_credentials = webhook.get_auth_credentials()
            if webhook.auth_type == "basic" and auth_credentials:
                import base64

                username = auth_credentials.get("username", "")
                password = auth_credentials.get("password", "")
                auth_string = base64.b64encode(
                    f"{username}:{password}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {auth_string}"
            elif webhook.auth_type == "bearer" and auth_credentials:
                token = auth_credentials.get("token", "")
                headers["Authorization"] = f"Bearer {token}"
            elif webhook.auth_type == "custom" and auth_credentials:
                headers.update(auth_credentials)

            # Prepare request data
            if webhook.content_type == "application/json":
                data = json.dumps(payload)
            else:
                data = payload

            # Send request
            start_time = datetime.utcnow()

            async with session.request(
                method=webhook.method,
                url=webhook.url,
                headers=headers,
                data=data,
                timeout=webhook.timeout,
                ssl=webhook.verify_ssl,
            ) as response:
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()

                # Log the delivery
                await self._log_webhook_delivery(
                    webhook_id=str(webhook.id),
                    url=webhook.url,
                    method=webhook.method,
                    payload=payload,
                    headers=headers,
                    status_code=response.status,
                    response_body=await response.text(),
                    response_headers=dict(response.headers),
                    duration=duration,
                    success=response.status < 400,
                )

                return response.status < 400

        except Exception as e:
            logger.error(f"Webhook request failed: {e}")

            # Log failed delivery
            await self._log_webhook_delivery(
                webhook_id=str(webhook.id),
                url=webhook.url,
                method=webhook.method,
                payload=payload,
                headers={},
                status_code=None,
                response_body="",
                response_headers={},
                duration=0,
                success=False,
                error_message=str(e),
            )

            return False

    def _prepare_webhook_payload(
        self, webhook: NotificationWebhook, notification_data: Dict
    ) -> Dict:
        """Prepare webhook payload based on template."""
        try:
            payload_template = webhook.get_payload_template()

            if payload_template:
                # Use custom template
                payload = payload_template.copy()

                # Replace placeholders with actual data
                for key, value in notification_data.items():
                    placeholder = f"{{{key}}}"
                    payload_str = json.dumps(payload)
                    payload_str = payload_str.replace(placeholder, str(value))
                    payload = json.loads(payload_str)

                return payload
            else:
                # Use default payload structure
                return {
                    "notification": notification_data,
                    "timestamp": datetime.utcnow().isoformat(),
                    "webhook_id": str(webhook.id),
                }

        except Exception as e:
            logger.error(f"Failed to prepare webhook payload: {e}")
            return notification_data

    async def _log_webhook_delivery(self, **delivery_data):
        """Log webhook delivery attempt."""
        try:
            log_entry = WebhookDeliveryLog(**delivery_data)
            self.db.add(log_entry)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log webhook delivery: {e}")

    def get_webhook_delivery_logs(self, webhook_id: str, limit: int = 50) -> List[Dict]:
        """Get delivery logs for a webhook."""
        try:
            logs = (
                self.db.query(WebhookDeliveryLog)
                .filter(WebhookDeliveryLog.webhook_id == webhook_id)
                .order_by(WebhookDeliveryLog.request_time.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": str(log.id),
                    "request_time": log.request_time.isoformat(),
                    "response_time": (
                        log.response_time.isoformat() if log.response_time else None
                    ),
                    "status_code": log.status_code,
                    "duration": log.duration,
                    "success": log.success,
                    "error_message": log.error_message,
                }
                for log in logs
            ]

        except Exception as e:
            logger.error(f"Failed to get webhook delivery logs: {e}")
            return []

    def get_webhook_stats(self, user_id: str) -> Dict:
        """Get statistics for user's webhooks."""
        try:
            webhooks = self.get_user_webhooks(user_id)

            stats = {
                "total_webhooks": len(webhooks),
                "active_webhooks": len([w for w in webhooks if w.is_active]),
                "verified_webhooks": len([w for w in webhooks if w.is_verified]),
                "total_sent": sum(w.success_count for w in webhooks),
                "total_failed": sum(w.failure_count for w in webhooks),
            }

            # Calculate overall success rate
            total_attempts = stats["total_sent"] + stats["total_failed"]
            if total_attempts > 0:
                stats["success_rate"] = round(
                    (stats["total_sent"] / total_attempts) * 100, 2
                )
            else:
                stats["success_rate"] = 0.0

            return stats

        except Exception as e:
            logger.error(f"Failed to get webhook stats: {e}")
            return {}

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()


# Global instance
notification_webhook_service = NotificationWebhookService()
