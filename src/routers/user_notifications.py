from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session

from src.auth.permission_types import Permission
from src.auth.permissions import get_current_user, require_permission
from src.database.models.base import get_db
from src.database.models.user import User
from src.database.models.user_notification_preferences import (
    UserNotificationPreferences,
)
from src.services.alert_manager import AlertRecord
from src.services.notification_history_service import notification_history_service
from src.services.push_notification_service import push_notification_service
from src.services.user_notification_service import user_notification_service

router = APIRouter()


class NotificationPreferencesResponse(BaseModel):
    """Response model for notification preferences."""

    id: str
    user_id: str
    email_enabled: bool
    push_enabled: bool
    webhook_enabled: bool
    webhook_url: Optional[str] = None
    alert_severities: List[str]
    alert_types: List[str]
    assigned_cameras: List[str]
    cooldown_minutes: int
    quiet_hours_enabled: bool
    quiet_hours_start: str
    quiet_hours_end: str
    custom_filters: Dict
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class NotificationPreferencesUpdate(BaseModel):
    """Request model for updating notification preferences."""

    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    webhook_enabled: Optional[bool] = None
    webhook_url: Optional[str] = None
    alert_severities: Optional[List[str]] = None
    alert_types: Optional[List[str]] = None
    assigned_cameras: Optional[List[str]] = None
    cooldown_minutes: Optional[int] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    custom_filters: Optional[Dict] = None

    @validator("alert_severities")
    def validate_severities(cls, v):
        if v is not None:
            valid_severities = {"critical", "high", "medium", "low"}
            if not all(severity in valid_severities for severity in v):
                raise ValueError(
                    f"Invalid severity levels. Must be one of: {valid_severities}"
                )
        return v

    @validator("alert_types")
    def validate_types(cls, v):
        if v is not None:
            valid_types = {
                "shoplifting",
                "suspicious_activity",
                "object_detection",
                "motion",
                "system_alert",
            }
            if not all(alert_type in valid_types for alert_type in v):
                raise ValueError(f"Invalid alert types. Must be one of: {valid_types}")
        return v

    @validator("cooldown_minutes")
    def validate_cooldown(cls, v):
        if v is not None and (v < 1 or v > 1440):  # 1 minute to 24 hours
            raise ValueError("Cooldown must be between 1 and 1440 minutes")
        return v

    @validator("quiet_hours_start", "quiet_hours_end")
    def validate_time_format(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, "%H:%M")
            except ValueError:
                raise ValueError("Time must be in HH:MM format")
        return v


@router.get(
    "/users/me/notification-preferences", response_model=NotificationPreferencesResponse
)
async def get_my_notification_preferences(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get current user's notification preferences."""
    try:
        prefs = (
            db.query(UserNotificationPreferences)
            .filter(UserNotificationPreferences.user_id == current_user.id)
            .first()
        )

        if not prefs:
            # Create default preferences
            prefs = UserNotificationPreferences(
                user_id=current_user.id,
                **UserNotificationPreferences.get_default_preferences(),
            )
            db.add(prefs)
            db.commit()
            db.refresh(prefs)
            logger.info(
                f"[PREFS] Created default notification preferences for user {current_user.id}"
            )

        return NotificationPreferencesResponse(**prefs.to_dict())
    except Exception as e:
        logger.error(
            f"[PREFS] Error getting preferences for user {current_user.id}: {e}"
        )
        # Return default preferences if database error
        default_prefs = UserNotificationPreferences.get_default_preferences()
        default_prefs["id"] = "default"
        default_prefs["user_id"] = current_user.id
        return NotificationPreferencesResponse(**default_prefs)


@router.put(
    "/users/me/notification-preferences", response_model=NotificationPreferencesResponse
)
async def update_my_notification_preferences(
    preferences: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user's notification preferences."""
    try:
        prefs = (
            db.query(UserNotificationPreferences)
            .filter(UserNotificationPreferences.user_id == current_user.id)
            .first()
        )

        if not prefs:
            # Create new preferences
            prefs = UserNotificationPreferences(
                user_id=current_user.id,
                **UserNotificationPreferences.get_default_preferences(),
            )
            db.add(prefs)

        # Update only provided fields
        update_data = preferences.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(prefs, field):
                setattr(prefs, field, value)

        try:
            db.commit()
            db.refresh(prefs)
            logger.info(
                f"[PREFS] Updated notification preferences for user {current_user.id}"
            )
            return NotificationPreferencesResponse(**prefs.to_dict())
        except Exception as e:
            db.rollback()
            logger.error(
                f"[PREFS] Failed to update preferences for user {current_user.id}: {e}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to update notification preferences"
            )
    except Exception as e:
        logger.error(
            f"[PREFS] Error updating preferences for user {current_user.id}: {e}"
        )
        # Return default preferences if database error
        default_prefs = UserNotificationPreferences.get_default_preferences()
        default_prefs["id"] = "default"
        default_prefs["user_id"] = current_user.id
        return NotificationPreferencesResponse(**default_prefs)


@router.post("/users/me/test-notification")
async def send_test_notification(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Send a test notification to current user."""
    try:
        # Get user's notification preferences
        try:
            prefs = (
                db.query(UserNotificationPreferences)
                .filter(UserNotificationPreferences.user_id == current_user.id)
                .first()
            )

            if not prefs:
                # Create default preferences if not found
                prefs = UserNotificationPreferences(
                    user_id=current_user.id,
                    **UserNotificationPreferences.get_default_preferences(),
                )
        except Exception as db_error:
            logger.warning(
                f"[TEST] Database error, using default preferences: {db_error}"
            )
            # Use default preferences if database fails
            prefs = UserNotificationPreferences(
                user_id=current_user.id,
                **UserNotificationPreferences.get_default_preferences(),
            )

        # Create a test alert data
        test_alert_data = {
            "id": f"test-{datetime.now().isoformat()}",
            "camera_id": "test-camera",
            "timestamp": datetime.now().isoformat(),
            "type": "test",
            "severity": "medium",
            "status": "active",
            "confidence": 0.85,
            "message": "This is a test notification to verify your alert settings are working correctly.",
            "source": "test",
            "detection_data": {"test": True},
        }

        # Send test notification
        success = await user_notification_service._send_user_notification(
            current_user, prefs, test_alert_data
        )

        if success:
            return {"message": "Test notification sent successfully"}
        else:
            return {
                "message": "Test notification failed - check your notification settings"
            }

    except Exception as e:
        logger.error(
            f"[TEST] Failed to send test notification to user {current_user.id}: {e}"
        )
        raise HTTPException(status_code=500, detail="Failed to send test notification")


@router.get("/users/me/notification-history")
async def get_my_notification_history(
    limit: int = 50,
    type: Optional[str] = None,
    status: Optional[str] = None,
    date_range: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's notification history."""
    try:
        logger.info(
            f"[HISTORY] Getting notification history for user {current_user.id}"
        )

        # Get notification history from the database
        notifications = notification_history_service.get_user_notification_history(
            db=db,
            user_id=current_user.id,
            limit=limit,
            notification_type=type,
            status=status,
            date_range=date_range,
        )

        return {"notifications": notifications}
    except Exception as e:
        logger.error(
            f"[HISTORY] Error getting notification history for user {current_user.id}: {e}"
        )
        return {"notifications": []}


@router.put("/users/me/notifications/{notification_id}/status")
async def update_my_notification_status(
    notification_id: str,
    status_update: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the status of a specific notification for the current user."""
    try:
        # Verify the notification belongs to the current user
        notification = notification_history_service.get_notification_by_id(
            db, notification_id
        )

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        if notification.get("user_id") != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Update the notification status
        updated_notification = notification_history_service.update_notification_status(
            db=db,
            notification_id=notification_id,
            new_status=status_update.get("status"),
            timestamp=datetime.now(),
            channel_data=status_update.get("channel_data"),
        )

        if updated_notification:
            return {
                "message": "Notification status updated successfully",
                "notification": updated_notification,
            }
        else:
            raise HTTPException(
                status_code=500, detail="Failed to update notification status"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[STATUS_UPDATE] Error updating notification {notification_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to update notification status"
        )


@router.put("/users/me/notifications/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all pending notifications as read for the current user."""
    try:
        # Get all pending notifications for the user
        pending_notifications = (
            notification_history_service.get_user_notification_history(
                db=db,
                user_id=current_user.id,
                status="pending",
                limit=1000,  # Get all pending notifications
            )
        )

        updated_count = 0
        for notification in pending_notifications:
            try:
                notification_history_service.update_notification_status(
                    db=db,
                    notification_id=notification["id"],
                    new_status="delivered",
                    timestamp=datetime.now(),
                )
                updated_count += 1
            except Exception as e:
                logger.warning(
                    f"Failed to update notification {notification['id']}: {e}"
                )
                continue

        return {
            "message": f"Marked {updated_count} notifications as read",
            "updated_count": updated_count,
        }

    except Exception as e:
        logger.error(f"[MARK_ALL_READ] Error marking notifications as read: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to mark notifications as read"
        )


@router.get("/users/me/notification-stats")
async def get_my_notification_stats(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get notification statistics for current user."""
    try:
        stats = notification_history_service.get_notification_statistics(
            db=db,
            user_id=current_user.id,
            days=days,
        )
        return stats
    except Exception as e:
        logger.error(f"Failed to get user notification stats: {e}")
        return {
            "total_notifications": 0,
            "successful_notifications": 0,
            "failed_notifications": 0,
            "success_rate": 0.0,
            "status_breakdown": {},
            "type_breakdown": {},
            "period_days": days,
            "user_id": current_user.id,
        }


@router.get("/admin/notification-stats")
@require_permission(Permission.SYSTEM_METRICS)
async def get_system_notification_stats(
    days: int = 7, current_user: User = Depends(get_current_user)
):
    """Get system-wide notification statistics (admin only)."""
    try:
        stats = user_notification_service.get_notification_stats(days)
        return {
            "stats": stats,
            "period_days": days,
            "generated_at": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"[STATS] Failed to get notification stats: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve notification statistics"
        )


@router.get("/admin/users/notification-preferences")
@require_permission(Permission.USER_VIEW)
async def get_all_user_notification_preferences(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get notification preferences for all users (admin only)."""
    try:
        # Get users with their notification preferences
        query = (
            db.query(User, UserNotificationPreferences)
            .outerjoin(
                UserNotificationPreferences,
                User.id == UserNotificationPreferences.user_id,
            )
            .filter(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )

        results = query.all()

        user_preferences = []
        for user, prefs in results:
            if prefs:
                prefs_data = prefs.to_dict()
            else:
                prefs_data = {
                    "user_id": user.id,
                    **UserNotificationPreferences.get_default_preferences(),
                    "id": None,
                    "created_at": None,
                    "updated_at": None,
                }

            user_preferences.append(
                {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                        "is_active": user.is_active,
                    },
                    "preferences": prefs_data,
                }
            )

        # Get total count
        total_count = db.query(User).filter(User.is_active == True).count()

        return {
            "users": user_preferences,
            "total": total_count,
            "skip": skip,
            "limit": limit,
        }

    except Exception as e:
        logger.error(f"[ADMIN] Failed to get user notification preferences: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve user notification preferences"
        )


@router.get("/admin/notification-history")
@require_permission(Permission.SYSTEM_METRICS)
async def get_system_notification_history(
    limit: int = 100,
    notification_type: Optional[str] = None,
    status: Optional[str] = None,
    date_range: Optional[str] = None,
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Get system-wide notification history (admin only)."""
    try:
        notifications = notification_history_service.get_system_notification_history(
            db=db,
            limit=limit,
            notification_type=notification_type,
            status=status,
            date_range=date_range,
            user_id=user_id,
        )

        return {
            "notifications": notifications,
            "total": len(notifications),
            "limit": limit,
            "filters": {
                "notification_type": notification_type,
                "status": status,
                "date_range": date_range,
                "user_id": user_id,
            },
            "generated_at": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"[ADMIN] Failed to get system notification history: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve system notification history"
        )


@router.put(
    "/admin/users/{user_id}/notification-preferences",
    response_model=NotificationPreferencesResponse,
)
@require_permission(Permission.USER_UPDATE)
async def update_user_notification_preferences(
    user_id: str,
    preferences: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update notification preferences for a specific user (admin only)."""
    # Check if target user exists
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get or create preferences
    prefs = (
        db.query(UserNotificationPreferences)
        .filter(UserNotificationPreferences.user_id == user_id)
        .first()
    )

    if not prefs:
        prefs = UserNotificationPreferences(
            user_id=user_id, **UserNotificationPreferences.get_default_preferences()
        )
        db.add(prefs)

    # Update only provided fields
    update_data = preferences.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(prefs, field):
            setattr(prefs, field, value)

    try:
        db.commit()
        db.refresh(prefs)
        logger.info(
            f"[ADMIN] Updated notification preferences for user {user_id} by admin {current_user.id}"
        )
        return NotificationPreferencesResponse(**prefs.to_dict())
    except Exception as e:
        db.rollback()
        logger.error(f"[ADMIN] Failed to update preferences for user {user_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to update notification preferences"
        )


# Push Notification Subscription Endpoints
class PushSubscriptionRequest(BaseModel):
    """Request model for push subscription."""

    endpoint: str
    keys: Dict[str, str]


@router.post("/users/me/push-subscription")
async def subscribe_to_push_notifications(
    subscription: PushSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Subscribe current user to push notifications."""
    try:
        # Store push subscription in database
        success = await push_notification_service.subscribe_user(
            db=db, user_id=current_user.id, subscription_data=subscription.dict()
        )

        if success:
            logger.info(
                f"[PUSH] User {current_user.id} subscribed to push notifications"
            )
            return {"message": "Successfully subscribed to push notifications"}
        else:
            raise HTTPException(
                status_code=500, detail="Failed to subscribe to push notifications"
            )

    except Exception as e:
        logger.error(f"[PUSH] Failed to subscribe user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to subscribe to push notifications"
        )


@router.delete("/users/me/push-subscription")
async def unsubscribe_from_push_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unsubscribe current user from push notifications."""
    try:
        # Remove push subscription from database
        success = await push_notification_service.unsubscribe_user(
            db=db, user_id=current_user.id
        )

        if success:
            logger.info(
                f"[PUSH] User {current_user.id} unsubscribed from push notifications"
            )
            return {"message": "Successfully unsubscribed from push notifications"}
        else:
            raise HTTPException(
                status_code=500, detail="Failed to unsubscribe from push notifications"
            )

    except Exception as e:
        logger.error(f"[PUSH] Failed to unsubscribe user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to unsubscribe from push notifications"
        )


@router.get("/users/me/push-subscription")
async def get_push_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's push subscription status."""
    try:
        subscription = await push_notification_service.get_user_subscription(
            db=db, user_id=current_user.id
        )

        return {"subscribed": subscription is not None, "subscription": subscription}

    except Exception as e:
        logger.error(
            f"[PUSH] Failed to get subscription for user {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve push subscription status"
        )
