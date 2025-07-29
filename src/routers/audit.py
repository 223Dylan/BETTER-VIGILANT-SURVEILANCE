from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.auth.permissions import Permission, get_current_user, require_permission
from src.database.models.audit_log import AuditAction, AuditSeverity
from src.database.models.base import get_db
from src.database.models.user import User
from src.services.audit_logger import audit_logger

router = APIRouter(prefix="/api/audit", tags=["audit"])


class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str]
    username: str
    user_role: Optional[str]
    action: str
    action_category: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    endpoint: Optional[str]
    permission_required: Optional[str]
    permission_granted: bool
    request_method: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    success: bool
    severity: str
    error_message: Optional[str]
    metadata: dict
    timestamp: str
    duration_ms: Optional[int]


class AuditLogListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class AuditStatsResponse(BaseModel):
    total_events: int
    failed_events: int
    success_rate: float
    category_breakdown: dict
    severity_breakdown: dict


@router.get("/logs", response_model=AuditLogListResponse)
@require_permission(Permission.SECURITY_AUDIT)
async def get_audit_logs(
    request: Request,
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    action_category: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    severity: Optional[str] = Query(None),
    success: Optional[bool] = Query(None),
):
    """Get audit logs with filtering and pagination."""
    try:
        # Log this audit access
        audit_logger.log_resource_access(
            user=current_user,
            action=AuditAction.SYSTEM_LOGS_ACCESSED,
            resource_type="audit_logs",
            request=request,
        )

        # Calculate offset
        offset = (page - 1) * per_page

        # Get logs with filters
        logs_data = audit_logger.get_audit_logs(
            limit=per_page,
            offset=offset,
            user_id=user_id,
            action=action,
            action_category=action_category,
            start_date=start_date,
            end_date=end_date,
            severity=severity,
            success=success,
        )

        # Get total count for pagination (simplified - in production you'd want a proper count query)
        all_logs = audit_logger.get_audit_logs(
            limit=10000,  # Large number to get approximate total
            user_id=user_id,
            action=action,
            action_category=action_category,
            start_date=start_date,
            end_date=end_date,
            severity=severity,
            success=success,
        )
        total = len(all_logs)

        # Calculate pagination
        total_pages = (total + per_page - 1) // per_page

        # Convert to response format
        logs = [AuditLogResponse(**log_data) for log_data in logs_data]

        return AuditLogListResponse(
            logs=logs,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )

    except Exception as e:
        audit_logger.log_security_event(
            action="audit_logs_access_failed",
            severity=AuditSeverity.MEDIUM,
            user=current_user,
            request=request,
            error_message=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")


@router.get("/stats", response_model=AuditStatsResponse)
@require_permission(Permission.SECURITY_AUDIT)
async def get_audit_statistics(
    request: Request,
    current_user: User = Depends(get_current_user),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
):
    """Get audit log statistics."""
    try:
        # Log this audit access
        audit_logger.log_resource_access(
            user=current_user,
            action=AuditAction.ANALYTICS_ACCESSED,
            resource_type="audit_stats",
            request=request,
        )

        stats = audit_logger.get_audit_statistics(
            start_date=start_date, end_date=end_date
        )

        return AuditStatsResponse(**stats)

    except Exception as e:
        audit_logger.log_security_event(
            action="audit_stats_access_failed",
            severity=AuditSeverity.MEDIUM,
            user=current_user,
            request=request,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve audit statistics"
        )


@router.post("/cleanup")
@require_permission(Permission.SYSTEM_MAINTENANCE)
async def cleanup_old_logs(
    request: Request,
    current_user: User = Depends(get_current_user),
    retention_days: int = Query(90, ge=1, le=365),
):
    """Clean up old audit logs."""
    try:
        deleted_count = audit_logger.cleanup_old_logs(retention_days)

        # Log this administrative action
        audit_logger.log_administrative_action(
            user=current_user,
            action=AuditAction.SYSTEM_CONFIG_MODIFIED,
            request=request,
            metadata={
                "action": "cleanup_audit_logs",
                "retention_days": retention_days,
                "deleted_count": deleted_count,
            },
        )

        return {
            "success": True,
            "message": f"Cleaned up {deleted_count} old audit logs",
            "deleted_count": deleted_count,
        }

    except Exception as e:
        audit_logger.log_security_event(
            action="audit_cleanup_failed",
            severity=AuditSeverity.HIGH,
            user=current_user,
            request=request,
            error_message=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to cleanup audit logs")


@router.get("/actions")
@require_permission(Permission.SECURITY_AUDIT)
async def get_available_actions(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Get list of all available audit actions for filtering."""
    try:
        actions = [action.value for action in AuditAction]

        return {
            "actions": actions,
            "categories": [
                "authentication",
                "permission",
                "resource",
                "administration",
                "camera",
                "alert",
                "system",
                "security",
                "other",
            ],
            "severities": [severity.value for severity in AuditSeverity],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve audit actions")


@router.get("/user/{user_id}/logs")
@require_permission(Permission.SECURITY_AUDIT)
async def get_user_audit_logs(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
):
    """Get audit logs for a specific user."""
    try:
        # Log this user-specific audit access
        audit_logger.log_resource_access(
            user=current_user,
            action=AuditAction.USER_VIEWED,
            resource_type="user_audit_logs",
            resource_id=user_id,
            request=request,
        )

        offset = (page - 1) * per_page

        logs_data = audit_logger.get_audit_logs(
            limit=per_page,
            offset=offset,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Get total count
        all_logs = audit_logger.get_audit_logs(
            limit=10000, user_id=user_id, start_date=start_date, end_date=end_date
        )
        total = len(all_logs)
        total_pages = (total + per_page - 1) // per_page

        logs = [AuditLogResponse(**log_data) for log_data in logs_data]

        return AuditLogListResponse(
            logs=logs,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )

    except Exception as e:
        audit_logger.log_security_event(
            action="user_audit_logs_access_failed",
            severity=AuditSeverity.MEDIUM,
            user=current_user,
            request=request,
            error_message=str(e),
            metadata={"target_user_id": user_id},
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve user audit logs"
        )


@router.get("/recent-failures")
@require_permission(Permission.SECURITY_AUDIT)
async def get_recent_failures(
    request: Request,
    current_user: User = Depends(get_current_user),
    hours: int = Query(24, ge=1, le=168),  # Last 1-168 hours
    limit: int = Query(100, ge=1, le=500),
):
    """Get recent failed events for security monitoring."""
    try:
        start_date = datetime.utcnow() - timedelta(hours=hours)

        logs_data = audit_logger.get_audit_logs(
            limit=limit, start_date=start_date, success=False
        )

        # Log this security monitoring access
        audit_logger.log_resource_access(
            user=current_user,
            action=AuditAction.SECURITY_AUDIT,
            resource_type="security_failures",
            request=request,
            metadata={"hours": hours, "limit": limit},
        )

        logs = [AuditLogResponse(**log_data) for log_data in logs_data]

        return {"failures": logs, "count": len(logs), "time_range_hours": hours}

    except Exception as e:
        audit_logger.log_security_event(
            action="security_failures_access_failed",
            severity=AuditSeverity.HIGH,
            user=current_user,
            request=request,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve recent failures"
        )
