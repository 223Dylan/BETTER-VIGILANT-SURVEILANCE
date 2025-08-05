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


@router.get("/users/me/notification-stats")
async def get_my_notification_stats(
    days: int = 7, current_user: User = Depends(get_current_user)
):
    """Get notification statistics for current user."""
    # For now, return basic stats
    # TODO: Implement per-user notification tracking
    return {
        "message": "Personal notification statistics coming soon",
        "days": days,
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
