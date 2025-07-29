import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from fastapi import Request
from loguru import logger
from sqlalchemy.orm import Session

from src.database.models.audit_log import AuditAction, AuditLog, AuditSeverity
from src.database.models.base import get_db
from src.database.models.user import User


class AuditLogger:
    """Service for comprehensive audit logging of permission and security events."""

    def __init__(self):
        self.start_time = None

    def start_timing(self):
        """Start timing for request duration tracking."""
        self.start_time = time.time()

    def get_duration_ms(self) -> Optional[int]:
        """Get request duration in milliseconds."""
        if self.start_time:
            return int((time.time() - self.start_time) * 1000)
        return None

    def log_permission_check(
        self,
        user: Optional[User],
        permission: Union[str, "Permission"],
        granted: bool,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        request: Optional[Request] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log a permission check event."""
        try:
            db: Session = next(get_db())

            action = (
                AuditAction.PERMISSION_GRANTED
                if granted
                else AuditAction.PERMISSION_DENIED
            )
            severity = AuditSeverity.LOW if granted else AuditSeverity.MEDIUM

            audit_log = AuditLog(
                user_id=user.id if user else None,
                username=user.username if user else "anonymous",
                user_role=user.role if user else None,
                action=action.value,
                action_category="permission",
                resource_type=resource_type,
                resource_id=resource_id,
                permission_required=(
                    permission.value
                    if hasattr(permission, "value")
                    else str(permission)
                ),
                permission_granted=granted,
                request_method=request.method if request else None,
                endpoint=str(request.url) if request else None,
                ip_address=self._get_client_ip(request) if request else None,
                user_agent=request.headers.get("user-agent") if request else None,
                success=granted,
                severity=severity.value,
                metadata_json=metadata or {},
                duration_ms=self.get_duration_ms(),
            )

            db.add(audit_log)
            db.commit()

            # Log to application logger as well
            log_level = "info" if granted else "warning"
            permission_value = (
                permission.value if hasattr(permission, "value") else str(permission)
            )
            getattr(logger, log_level)(
                f"Permission {permission_value} {'granted' if granted else 'denied'} "
                f"for user {user.username if user else 'anonymous'} "
                f"on {resource_type or 'unknown'}"
            )

        except Exception as e:
            logger.error(f"Failed to log permission check: {e}")
        finally:
            if "db" in locals():
                db.close()

    def log_authentication(
        self,
        username: str,
        action: AuditAction,
        success: bool,
        request: Optional[Request] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log authentication events."""
        try:
            db: Session = next(get_db())

            severity = AuditSeverity.LOW if success else AuditSeverity.HIGH

            audit_log = AuditLog(
                username=username,
                action=action.value,
                action_category="authentication",
                request_method=request.method if request else None,
                endpoint=str(request.url) if request else None,
                ip_address=self._get_client_ip(request) if request else None,
                user_agent=request.headers.get("user-agent") if request else None,
                success=success,
                severity=severity.value,
                error_message=error_message,
                metadata_json=metadata or {},
                duration_ms=self.get_duration_ms(),
            )

            db.add(audit_log)
            db.commit()

            # Log to application logger
            log_level = "info" if success else "warning"
            getattr(logger, log_level)(
                f"Authentication {action.value} for user {username}: "
                f"{'success' if success else 'failed'}"
            )

        except Exception as e:
            logger.error(f"Failed to log authentication event: {e}")
        finally:
            if "db" in locals():
                db.close()

    def log_resource_access(
        self,
        user: Optional[User],
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        success: bool = True,
        request: Optional[Request] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log resource access events."""
        try:
            db: Session = next(get_db())

            severity = AuditSeverity.LOW if success else AuditSeverity.MEDIUM

            audit_log = AuditLog(
                user_id=user.id if user else None,
                username=user.username if user else "anonymous",
                user_role=user.role if user else None,
                action=action.value,
                action_category=AuditLog.get_action_category(action.value),
                resource_type=resource_type,
                resource_id=resource_id,
                request_method=request.method if request else None,
                endpoint=str(request.url) if request else None,
                ip_address=self._get_client_ip(request) if request else None,
                user_agent=request.headers.get("user-agent") if request else None,
                success=success,
                severity=severity.value,
                error_message=error_message,
                metadata_json=metadata or {},
                duration_ms=self.get_duration_ms(),
            )

            db.add(audit_log)
            db.commit()

            # Log to application logger
            log_level = "info" if success else "warning"
            getattr(logger, log_level)(
                f"Resource access {action.value} by user {user.username if user else 'anonymous'} "
                f"on {resource_type} {resource_id or ''}: {'success' if success else 'failed'}"
            )

        except Exception as e:
            logger.error(f"Failed to log resource access: {e}")
        finally:
            if "db" in locals():
                db.close()

    def log_administrative_action(
        self,
        user: User,
        action: AuditAction,
        target_user_id: Optional[str] = None,
        target_username: Optional[str] = None,
        request: Optional[Request] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log administrative actions like user management."""
        try:
            db: Session = next(get_db())

            # Administrative actions are generally more sensitive
            severity = AuditSeverity.MEDIUM
            if action in [
                AuditAction.USER_DELETED,
                AuditAction.ROLE_CHANGED,
                AuditAction.PERMISSIONS_MODIFIED,
            ]:
                severity = AuditSeverity.HIGH

            # Combine changes and metadata
            combined_metadata = metadata or {}
            if changes:
                combined_metadata["changes"] = changes
            if target_username:
                combined_metadata["target_username"] = target_username

            audit_log = AuditLog(
                user_id=user.id,
                username=user.username,
                user_role=user.role,
                action=action.value,
                action_category="administration",
                resource_type="user",
                resource_id=target_user_id,
                request_method=request.method if request else None,
                endpoint=str(request.url) if request else None,
                ip_address=self._get_client_ip(request) if request else None,
                user_agent=request.headers.get("user-agent") if request else None,
                success=True,
                severity=severity.value,
                metadata_json=combined_metadata,
                duration_ms=self.get_duration_ms(),
            )

            db.add(audit_log)
            db.commit()

            logger.info(
                f"Administrative action {action.value} by {user.username} "
                f"on user {target_username or target_user_id or 'unknown'}"
            )

        except Exception as e:
            logger.error(f"Failed to log administrative action: {e}")
        finally:
            if "db" in locals():
                db.close()

    def log_security_event(
        self,
        action: str,
        severity: AuditSeverity,
        user: Optional[User] = None,
        request: Optional[Request] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log general security events."""
        try:
            db: Session = next(get_db())

            audit_log = AuditLog(
                user_id=user.id if user else None,
                username=user.username if user else "system",
                user_role=user.role if user else None,
                action=action,
                action_category="security",
                request_method=request.method if request else None,
                endpoint=str(request.url) if request else None,
                ip_address=self._get_client_ip(request) if request else None,
                user_agent=request.headers.get("user-agent") if request else None,
                success=severity in [AuditSeverity.LOW, AuditSeverity.MEDIUM],
                severity=severity.value,
                error_message=error_message,
                metadata_json=metadata or {},
                duration_ms=self.get_duration_ms(),
            )

            db.add(audit_log)
            db.commit()

            # Log to application logger with appropriate level
            if severity == AuditSeverity.CRITICAL:
                logger.critical(
                    f"Security event: {action} - {error_message or 'No details'}"
                )
            elif severity == AuditSeverity.HIGH:
                logger.error(
                    f"Security event: {action} - {error_message or 'No details'}"
                )
            elif severity == AuditSeverity.MEDIUM:
                logger.warning(
                    f"Security event: {action} - {error_message or 'No details'}"
                )
            else:
                logger.info(f"Security event: {action}")

        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
        finally:
            if "db" in locals():
                db.close()

    def get_audit_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        action_category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        severity: Optional[str] = None,
        success: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve audit logs with filtering."""
        try:
            db: Session = next(get_db())

            query = db.query(AuditLog)

            # Apply filters
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if action:
                query = query.filter(AuditLog.action == action)
            if action_category:
                query = query.filter(AuditLog.action_category == action_category)
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            if severity:
                query = query.filter(AuditLog.severity == severity)
            if success is not None:
                query = query.filter(AuditLog.success == success)

            # Order by timestamp (newest first) and apply pagination
            logs = (
                query.order_by(AuditLog.timestamp.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            return [log.to_dict() for log in logs]

        except Exception as e:
            logger.error(f"Failed to retrieve audit logs: {e}")
            return []
        finally:
            if "db" in locals():
                db.close()

    def get_audit_statistics(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get audit log statistics."""
        try:
            db: Session = next(get_db())

            query = db.query(AuditLog)

            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)

            # Get basic counts
            total_events = query.count()
            failed_events = query.filter(AuditLog.success == False).count()

            # Get counts by category
            category_stats = {}
            for category in [
                "authentication",
                "permission",
                "resource",
                "administration",
                "security",
            ]:
                count = query.filter(AuditLog.action_category == category).count()
                category_stats[category] = count

            # Get counts by severity
            severity_stats = {}
            for severity in ["low", "medium", "high", "critical"]:
                count = query.filter(AuditLog.severity == severity).count()
                severity_stats[severity] = count

            return {
                "total_events": total_events,
                "failed_events": failed_events,
                "success_rate": (
                    (total_events - failed_events) / total_events * 100
                    if total_events > 0
                    else 0
                ),
                "category_breakdown": category_stats,
                "severity_breakdown": severity_stats,
            }

        except Exception as e:
            logger.error(f"Failed to get audit statistics: {e}")
            return {}
        finally:
            if "db" in locals():
                db.close()

    def cleanup_old_logs(self, retention_days: int = 90):
        """Clean up old audit logs based on retention policy."""
        try:
            db: Session = next(get_db())

            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            # Delete logs older than retention period
            deleted_count = (
                db.query(AuditLog).filter(AuditLog.timestamp < cutoff_date).delete()
            )

            db.commit()

            logger.info(
                f"Cleaned up {deleted_count} audit logs older than {retention_days} days"
            )
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup audit logs: {e}")
            return 0
        finally:
            if "db" in locals():
                db.close()

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request."""
        if not request:
            return None

        # Check for forwarded IP first (behind proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Check for real IP
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        return request.client.host if request.client else None


# Global audit logger instance
audit_logger = AuditLogger()
