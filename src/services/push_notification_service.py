import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from src.database.models.push_subscription import PushSubscription
from src.database.models.user import User


class PushNotificationService:
    """Service for managing push notification subscriptions and sending push notifications."""

    def __init__(self):
        self.vapid_private_key = self._get_vapid_private_key()
        self.vapid_public_key = self._get_vapid_public_key()
        self.vapid_claims = self._get_vapid_claims()

    async def subscribe_user(
        self, db: Session, user_id: str, subscription_data: Dict[str, Any]
    ) -> bool:
        """Subscribe a user to push notifications."""
        try:
            # Check if user already has a subscription
            existing_subscription = (
                db.query(PushSubscription)
                .filter(PushSubscription.user_id == user_id)
                .first()
            )

            if existing_subscription:
                # Update existing subscription
                existing_subscription.endpoint = subscription_data["endpoint"]
                existing_subscription.p256dh_key = subscription_data["keys"]["p256dh"]
                existing_subscription.auth_key = subscription_data["keys"]["auth"]
                existing_subscription.updated_at = datetime.now()
                existing_subscription.is_active = True
            else:
                # Create new subscription
                new_subscription = PushSubscription(
                    user_id=user_id,
                    endpoint=subscription_data["endpoint"],
                    p256dh_key=subscription_data["keys"]["p256dh"],
                    auth_key=subscription_data["keys"]["auth"],
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.add(new_subscription)

            db.commit()
            logger.info(f"[PUSH] User {user_id} subscribed to push notifications")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"[PUSH] Failed to subscribe user {user_id}: {e}")
            return False

    async def unsubscribe_user(self, db: Session, user_id: str) -> bool:
        """Unsubscribe a user from push notifications."""
        try:
            subscription = (
                db.query(PushSubscription)
                .filter(PushSubscription.user_id == user_id)
                .first()
            )

            if subscription:
                subscription.is_active = False
                subscription.updated_at = datetime.now()
                db.commit()
                logger.info(
                    f"[PUSH] User {user_id} unsubscribed from push notifications"
                )
                return True
            else:
                logger.warning(f"[PUSH] No subscription found for user {user_id}")
                return False

        except Exception as e:
            db.rollback()
            logger.error(f"[PUSH] Failed to unsubscribe user {user_id}: {e}")
            return False

    async def get_user_subscription(
        self, db: Session, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a user's push subscription details."""
        try:
            subscription = (
                db.query(PushSubscription)
                .filter(
                    PushSubscription.user_id == user_id,
                    PushSubscription.is_active == True,
                )
                .first()
            )

            if subscription:
                return {
                    "id": subscription.id,
                    "user_id": subscription.user_id,
                    "endpoint": subscription.endpoint,
                    "is_active": subscription.is_active,
                    "created_at": (
                        subscription.created_at.isoformat()
                        if subscription.created_at
                        else None
                    ),
                    "updated_at": (
                        subscription.updated_at.isoformat()
                        if subscription.updated_at
                        else None
                    ),
                }
            return None

        except Exception as e:
            logger.error(f"[PUSH] Failed to get subscription for user {user_id}: {e}")
            return None

    async def get_all_active_subscriptions(self, db: Session) -> List[Dict[str, Any]]:
        """Get all active push subscriptions."""
        try:
            subscriptions = (
                db.query(PushSubscription)
                .filter(PushSubscription.is_active == True)
                .all()
            )

            return [
                {
                    "id": sub.id,
                    "user_id": sub.user_id,
                    "endpoint": sub.endpoint,
                    "p256dh_key": sub.p256dh_key,
                    "auth_key": sub.auth_key,
                    "created_at": (
                        sub.created_at.isoformat() if sub.created_at else None
                    ),
                    "updated_at": (
                        sub.updated_at.isoformat() if sub.updated_at else None
                    ),
                }
                for sub in subscriptions
            ]

        except Exception as e:
            logger.error(f"[PUSH] Failed to get active subscriptions: {e}")
            return []

    async def send_push_notification(
        self, db: Session, user_ids: List[str], notification_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """Send push notifications to multiple users."""
        try:
            # Get active subscriptions for the specified users
            subscriptions = (
                db.query(PushSubscription)
                .filter(
                    PushSubscription.user_id.in_(user_ids),
                    PushSubscription.is_active == True,
                )
                .all()
            )

            if not subscriptions:
                logger.warning(
                    "[PUSH] No active subscriptions found for the specified users"
                )
                return {"sent": 0, "failed": 0, "total": 0}

            # Send notifications to each subscription
            sent_count = 0
            failed_count = 0

            for subscription in subscriptions:
                try:
                    success = await self._send_single_push_notification(
                        subscription, notification_data
                    )
                    if success:
                        sent_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(
                        f"[PUSH] Failed to send notification to subscription {subscription.id}: {e}"
                    )
                    failed_count += 1

            total_count = len(subscriptions)
            logger.info(
                f"[PUSH] Sent {sent_count}/{total_count} push notifications successfully"
            )

            return {"sent": sent_count, "failed": failed_count, "total": total_count}

        except Exception as e:
            logger.error(f"[PUSH] Failed to send push notifications: {e}")
            return {"sent": 0, "failed": 0, "total": 0}

    async def send_push_notification_to_all(
        self, db: Session, notification_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """Send push notifications to all active subscribers."""
        try:
            # Get all active subscriptions
            subscriptions = await self.get_all_active_subscriptions(db)

            if not subscriptions:
                logger.warning("[PUSH] No active subscriptions found")
                return {"sent": 0, "failed": 0, "total": 0}

            # Extract user IDs
            user_ids = [sub["user_id"] for sub in subscriptions]

            # Send notifications
            return await self.send_push_notification(db, user_ids, notification_data)

        except Exception as e:
            logger.error(f"[PUSH] Failed to send push notifications to all users: {e}")
            return {"sent": 0, "failed": 0, "total": 0}

    async def _send_single_push_notification(
        self, subscription: PushSubscription, notification_data: Dict[str, Any]
    ) -> bool:
        """Send a single push notification to a specific subscription."""
        try:
            # This is a simplified implementation
            # In a real-world scenario, you would use a library like pywebpush
            # or make HTTP requests to the push service (FCM, etc.)

            # For now, we'll just log the attempt
            logger.info(f"[PUSH] Would send notification to {subscription.endpoint}")
            logger.info(
                f"[PUSH] Notification data: {json.dumps(notification_data, indent=2)}"
            )

            # Simulate async delay
            await asyncio.sleep(0.1)

            # In a real implementation, you would:
            # 1. Encrypt the payload using the subscription keys
            # 2. Send HTTP POST to the endpoint
            # 3. Handle the response

            return True

        except Exception as e:
            logger.error(f"[PUSH] Failed to send single push notification: {e}")
            return False

    def _get_vapid_private_key(self) -> str:
        """Get VAPID private key from environment or configuration."""
        # This should come from your environment variables
        import os

        return os.getenv("VAPID_PRIVATE_KEY", "your-vapid-private-key-here")

    def _get_vapid_public_key(self) -> str:
        """Get VAPID public key from environment or configuration."""
        # This should come from your environment variables
        import os

        return os.getenv("VAPID_PUBLIC_KEY", "your-vapid-public-key-here")

    def _get_vapid_claims(self) -> Dict[str, str]:
        """Get VAPID claims for push notifications."""
        return {
            "sub": "mailto:admin@yourdomain.com",  # Your contact email
            "aud": "https://yourdomain.com",  # Your domain
            "exp": str(
                int(datetime.now().timestamp()) + 12 * 3600
            ),  # 12 hours from now
        }

    async def cleanup_inactive_subscriptions(self, db: Session) -> int:
        """Remove inactive push subscriptions older than 30 days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)

            deleted_count = (
                db.query(PushSubscription)
                .filter(
                    PushSubscription.is_active == False,
                    PushSubscription.updated_at < cutoff_date,
                )
                .delete()
            )

            db.commit()
            logger.info(f"[PUSH] Cleaned up {deleted_count} inactive subscriptions")
            return deleted_count

        except Exception as e:
            db.rollback()
            logger.error(f"[PUSH] Failed to cleanup inactive subscriptions: {e}")
            return 0


# Create singleton instance
push_notification_service = PushNotificationService()
