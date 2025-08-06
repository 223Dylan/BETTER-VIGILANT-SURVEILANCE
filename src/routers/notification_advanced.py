import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.auth.jwt_auth import get_current_user
from src.auth.permission_types import Permission
from src.auth.permissions import require_permission
from src.database.models.user import User
from src.services.notification_analytics_service import notification_analytics_service
from src.services.notification_scheduler_service import notification_scheduler_service
from src.services.notification_template_service import notification_template_service
from src.services.notification_webhook_service import notification_webhook_service

router = APIRouter()


# Pydantic models
class NotificationTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    subject: str
    body: str
    html_body: Optional[str] = None
    template_type: str
    variables: Optional[Dict] = None
    is_default: bool = False
    is_active: bool = True


class NotificationTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    html_body: Optional[str] = None
    template_type: Optional[str] = None
    variables: Optional[Dict] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class NotificationScheduleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    schedule_type: str
    schedule_config: Dict
    timezone: str = "UTC"
    template_id: Optional[str] = None
    custom_subject: Optional[str] = None
    custom_body: Optional[str] = None
    alert_severities: Optional[List[str]] = None
    alert_types: Optional[List[str]] = None
    camera_ids: Optional[List[str]] = None
    max_runs: Optional[int] = None


class NotificationScheduleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    schedule_type: Optional[str] = None
    schedule_config: Optional[Dict] = None
    timezone: Optional[str] = None
    template_id: Optional[str] = None
    custom_subject: Optional[str] = None
    custom_body: Optional[str] = None
    alert_severities: Optional[List[str]] = None
    alert_types: Optional[List[str]] = None
    camera_ids: Optional[List[str]] = None
    is_active: Optional[bool] = None
    max_runs: Optional[int] = None


class NotificationWebhookCreate(BaseModel):
    name: str
    description: Optional[str] = None
    url: str
    method: str = "POST"
    auth_type: str = "none"
    auth_credentials: Optional[Dict] = None
    headers: Optional[Dict] = None
    payload_template: Optional[Dict] = None
    content_type: str = "application/json"
    alert_severities: Optional[List[str]] = None
    alert_types: Optional[List[str]] = None
    camera_ids: Optional[List[str]] = None
    max_retries: int = 3
    retry_delay: int = 60
    timeout: int = 30
    verify_ssl: bool = True


class NotificationWebhookUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None
    auth_type: Optional[str] = None
    auth_credentials: Optional[Dict] = None
    headers: Optional[Dict] = None
    payload_template: Optional[Dict] = None
    content_type: Optional[str] = None
    alert_severities: Optional[List[str]] = None
    alert_types: Optional[List[str]] = None
    camera_ids: Optional[List[str]] = None
    is_active: Optional[bool] = None
    max_retries: Optional[int] = None
    retry_delay: Optional[int] = None
    timeout: Optional[int] = None
    verify_ssl: Optional[bool] = None


# Template endpoints
@router.get("/templates", response_model=List[Dict])
@require_permission(Permission.USER_UPDATE)
async def get_notification_templates(
    template_type: Optional[str] = None, current_user: User = Depends(get_current_user)
):
    """Get notification templates."""
    try:
        templates = notification_template_service.get_templates(
            template_type=template_type
        )
        return [
            {
                "id": str(template.id),
                "name": template.name,
                "description": template.description,
                "template_type": template.template_type,
                "is_default": template.is_default,
                "is_active": template.is_active,
                "variables": template.get_variables(),
                "created_at": template.created_at.isoformat(),
            }
            for template in templates
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get templates: {str(e)}"
        )


@router.post("/templates", response_model=Dict)
@require_permission(Permission.USER_UPDATE)
async def create_notification_template(
    template_data: NotificationTemplateCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new notification template."""
    try:
        template = notification_template_service.create_template(template_data.dict())
        return {
            "id": str(template.id),
            "name": template.name,
            "description": template.description,
            "template_type": template.template_type,
            "is_default": template.is_default,
            "is_active": template.is_active,
            "created_at": template.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create template: {str(e)}"
        )


@router.get("/templates/{template_id}", response_model=Dict)
@require_permission(Permission.USER_UPDATE)
async def get_notification_template(
    template_id: str, current_user: User = Depends(get_current_user)
):
    """Get a specific notification template."""
    try:
        template = notification_template_service.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return {
            "id": str(template.id),
            "name": template.name,
            "description": template.description,
            "subject": template.subject,
            "body": template.body,
            "html_body": template.html_body,
            "template_type": template.template_type,
            "variables": template.get_variables(),
            "is_default": template.is_default,
            "is_active": template.is_active,
            "created_at": template.created_at.isoformat(),
            "updated_at": (
                template.updated_at.isoformat() if template.updated_at else None
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")


@router.put("/templates/{template_id}", response_model=Dict)
@require_permission(Permission.USER_UPDATE)
async def update_notification_template(
    template_id: str,
    template_data: NotificationTemplateUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update a notification template."""
    try:
        template = notification_template_service.update_template(
            template_id, template_data.dict(exclude_unset=True)
        )
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return {
            "id": str(template.id),
            "name": template.name,
            "description": template.description,
            "template_type": template.template_type,
            "is_default": template.is_default,
            "is_active": template.is_active,
            "updated_at": (
                template.updated_at.isoformat() if template.updated_at else None
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update template: {str(e)}"
        )


@router.delete("/templates/{template_id}")
@require_permission(Permission.USER_UPDATE)
async def delete_notification_template(
    template_id: str, current_user: User = Depends(get_current_user)
):
    """Delete a notification template."""
    try:
        success = notification_template_service.delete_template(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")

        return {"message": "Template deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete template: {str(e)}"
        )


# Schedule endpoints
@router.get("/schedules", response_model=List[Dict])
@require_permission(Permission.USER_UPDATE)
async def get_notification_schedules(current_user: User = Depends(get_current_user)):
    """Get user's notification schedules."""
    try:
        schedules = notification_scheduler_service.get_user_schedules(
            str(current_user.id)
        )
        return [
            {
                "id": str(schedule.id),
                "name": schedule.name,
                "description": schedule.description,
                "schedule_type": schedule.schedule_type,
                "timezone": schedule.timezone,
                "is_active": schedule.is_active,
                "last_run": (
                    schedule.last_run.isoformat() if schedule.last_run else None
                ),
                "next_run": (
                    schedule.next_run.isoformat() if schedule.next_run else None
                ),
                "run_count": schedule.run_count,
                "max_runs": schedule.max_runs,
            }
            for schedule in schedules
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get schedules: {str(e)}"
        )


@router.post("/schedules", response_model=Dict)
@require_permission(Permission.USER_UPDATE)
async def create_notification_schedule(
    schedule_data: NotificationScheduleCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new notification schedule."""
    try:
        schedule_dict = schedule_data.dict()
        schedule_dict["user_id"] = str(current_user.id)

        schedule = notification_scheduler_service.create_schedule(schedule_dict)
        return {
            "id": str(schedule.id),
            "name": schedule.name,
            "description": schedule.description,
            "schedule_type": schedule.schedule_type,
            "timezone": schedule.timezone,
            "is_active": schedule.is_active,
            "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
            "created_at": schedule.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create schedule: {str(e)}"
        )


@router.get("/schedules/{schedule_id}", response_model=Dict)
@require_permission(Permission.USER_UPDATE)
async def get_notification_schedule(
    schedule_id: str, current_user: User = Depends(get_current_user)
):
    """Get a specific notification schedule."""
    try:
        schedule = notification_scheduler_service.get_schedule(schedule_id)
        if not schedule or str(schedule.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Schedule not found")

        return {
            "id": str(schedule.id),
            "name": schedule.name,
            "description": schedule.description,
            "schedule_type": schedule.schedule_type,
            "schedule_config": schedule.get_schedule_config(),
            "timezone": schedule.timezone,
            "template_id": str(schedule.template_id) if schedule.template_id else None,
            "custom_subject": schedule.custom_subject,
            "custom_body": schedule.custom_body,
            "alert_severities": schedule.alert_severities,
            "alert_types": schedule.alert_types,
            "camera_ids": schedule.camera_ids,
            "is_active": schedule.is_active,
            "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
            "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
            "run_count": schedule.run_count,
            "max_runs": schedule.max_runs,
            "created_at": schedule.created_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get schedule: {str(e)}")


@router.put("/schedules/{schedule_id}", response_model=Dict)
@require_permission(Permission.USER_UPDATE)
async def update_notification_schedule(
    schedule_id: str,
    schedule_data: NotificationScheduleUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update a notification schedule."""
    try:
        schedule = notification_scheduler_service.get_schedule(schedule_id)
        if not schedule or str(schedule.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Schedule not found")

        updated_schedule = notification_scheduler_service.update_schedule(
            schedule_id, schedule_data.dict(exclude_unset=True)
        )

        return {
            "id": str(updated_schedule.id),
            "name": updated_schedule.name,
            "description": updated_schedule.description,
            "schedule_type": updated_schedule.schedule_type,
            "is_active": updated_schedule.is_active,
            "next_run": (
                updated_schedule.next_run.isoformat()
                if updated_schedule.next_run
                else None
            ),
            "updated_at": (
                updated_schedule.updated_at.isoformat()
                if updated_schedule.updated_at
                else None
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update schedule: {str(e)}"
        )


@router.delete("/schedules/{schedule_id}")
@require_permission(Permission.USER_UPDATE)
async def delete_notification_schedule(
    schedule_id: str, current_user: User = Depends(get_current_user)
):
    """Delete a notification schedule."""
    try:
        schedule = notification_scheduler_service.get_schedule(schedule_id)
        if not schedule or str(schedule.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Schedule not found")

        success = notification_scheduler_service.delete_schedule(schedule_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete schedule")

        return {"message": "Schedule deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete schedule: {str(e)}"
        )


# Analytics endpoints
@router.get("/analytics/summary", response_model=Dict)
@require_permission(Permission.USER_UPDATE)
async def get_notification_analytics_summary(
    days: int = 30, current_user: User = Depends(get_current_user)
):
    """Get notification analytics summary."""
    try:
        summary = notification_analytics_service.get_analytics_summary(
            str(current_user.id), days
        )
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get analytics: {str(e)}"
        )


@router.get("/analytics/hourly", response_model=Dict)
@require_permission(Permission.USER_UPDATE)
async def get_notification_hourly_breakdown(
    days: int = 7, current_user: User = Depends(get_current_user)
):
    """Get hourly breakdown of notification activity."""
    try:
        breakdown = notification_analytics_service.get_hourly_breakdown(
            str(current_user.id), days
        )
        return breakdown
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get hourly breakdown: {str(e)}"
        )


@router.get("/analytics/channels", response_model=Dict)
@require_permission(Permission.USER_UPDATE)
async def get_notification_channel_performance(
    days: int = 30, current_user: User = Depends(get_current_user)
):
    """Get performance metrics by channel."""
    try:
        performance = notification_analytics_service.get_channel_performance(
            str(current_user.id), days
        )
        return performance
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get channel performance: {str(e)}"
        )


@router.get("/analytics/timeline", response_model=List[Dict])
@require_permission(Permission.USER_UPDATE)
async def get_notification_event_timeline(
    limit: int = 100, current_user: User = Depends(get_current_user)
):
    """Get recent notification events timeline."""
    try:
        timeline = notification_analytics_service.get_event_timeline(
            str(current_user.id), limit
        )
        return timeline
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get event timeline: {str(e)}"
        )


# Webhook endpoints
@router.get("/webhooks", response_model=List[Dict])
@require_permission(Permission.USER_UPDATE)
async def get_notification_webhooks(current_user: User = Depends(get_current_user)):
    """Get user's notification webhooks."""
    try:
        webhooks = notification_webhook_service.get_user_webhooks(str(current_user.id))
        return [
            {
                "id": str(webhook.id),
                "name": webhook.name,
                "description": webhook.description,
                "url": webhook.url,
                "method": webhook.method,
                "auth_type": webhook.auth_type,
                "is_active": webhook.is_active,
                "is_verified": webhook.is_verified,
                "success_count": webhook.success_count,
                "failure_count": webhook.failure_count,
                "success_rate": webhook.get_success_rate(),
                "last_sent": (
                    webhook.last_sent.isoformat() if webhook.last_sent else None
                ),
            }
            for webhook in webhooks
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get webhooks: {str(e)}")


@router.post("/webhooks", response_model=Dict)
@require_permission(Permission.USER_UPDATE)
async def create_notification_webhook(
    webhook_data: NotificationWebhookCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new notification webhook."""
    try:
        webhook_dict = webhook_data.dict()
        webhook_dict["user_id"] = str(current_user.id)

        webhook = notification_webhook_service.create_webhook(webhook_dict)
        return {
            "id": str(webhook.id),
            "name": webhook.name,
            "description": webhook.description,
            "url": webhook.url,
            "method": webhook.method,
            "auth_type": webhook.auth_type,
            "is_active": webhook.is_active,
            "is_verified": webhook.is_verified,
            "created_at": webhook.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create webhook: {str(e)}"
        )


@router.post("/webhooks/{webhook_id}/verify")
@require_permission(Permission.USER_UPDATE)
async def verify_notification_webhook(
    webhook_id: str, current_user: User = Depends(get_current_user)
):
    """Verify a notification webhook."""
    try:
        webhook = notification_webhook_service.get_webhook(webhook_id)
        if not webhook or str(webhook.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Webhook not found")

        success = await notification_webhook_service.verify_webhook(webhook_id)
        return {
            "success": success,
            "message": (
                "Webhook verified successfully"
                if success
                else "Webhook verification failed"
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to verify webhook: {str(e)}"
        )


@router.get("/webhooks/{webhook_id}/logs", response_model=List[Dict])
@require_permission(Permission.USER_UPDATE)
async def get_webhook_delivery_logs(
    webhook_id: str, limit: int = 50, current_user: User = Depends(get_current_user)
):
    """Get delivery logs for a webhook."""
    try:
        webhook = notification_webhook_service.get_webhook(webhook_id)
        if not webhook or str(webhook.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Webhook not found")

        logs = notification_webhook_service.get_webhook_delivery_logs(webhook_id, limit)
        return logs
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get webhook logs: {str(e)}"
        )


@router.get("/webhooks/stats", response_model=Dict)
@require_permission(Permission.USER_UPDATE)
async def get_webhook_stats(current_user: User = Depends(get_current_user)):
    """Get webhook statistics for the user."""
    try:
        stats = notification_webhook_service.get_webhook_stats(str(current_user.id))
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get webhook stats: {str(e)}"
        )


@router.get("/schedules/stats", response_model=Dict)
@require_permission(Permission.USER_UPDATE)
async def get_schedule_stats(current_user: User = Depends(get_current_user)):
    """Get schedule statistics for the user."""
    try:
        stats = notification_scheduler_service.get_schedule_stats(str(current_user.id))
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get schedule stats: {str(e)}"
        )
