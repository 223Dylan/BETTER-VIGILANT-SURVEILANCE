from enum import Enum
from functools import wraps
from typing import Dict, List, Set

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.auth.jwt_auth import jwt_auth
from src.auth.permission_types import Permission
from src.database.models.base import get_db
from src.database.models.user import User
from src.services.audit_logger import audit_logger


class UserRole(str, Enum):
    """User role enumeration."""

    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    OPERATOR = "operator"


# Role permission mappings
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: {
        # All permissions for admin
        Permission.CAMERA_VIEW,
        Permission.CAMERA_CREATE,
        Permission.CAMERA_UPDATE,
        Permission.CAMERA_DELETE,
        Permission.CAMERA_CONTROL,
        Permission.CAMERA_STREAM,
        Permission.CAMERA_CONFIG,
        Permission.ALERT_VIEW,
        Permission.ALERT_CREATE,
        Permission.ALERT_ACKNOWLEDGE,
        Permission.ALERT_RESOLVE,
        Permission.ALERT_DELETE,
        Permission.ALERT_EXPORT,
        Permission.USER_VIEW,
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.USER_MANAGE_ROLES,
        Permission.USER_MANAGE_PERMISSIONS,
        Permission.SYSTEM_CONFIG,
        Permission.SYSTEM_LOGS,
        Permission.SYSTEM_METRICS,
        Permission.SYSTEM_BACKUP,
        Permission.SYSTEM_MAINTENANCE,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
        Permission.ANALYTICS_REPORTS,
        Permission.SECURITY_AUDIT,
        Permission.SECURITY_CONFIG,
    },
    UserRole.OPERATOR: {
        # Camera and alert management, limited user access
        Permission.CAMERA_VIEW,
        Permission.CAMERA_UPDATE,
        Permission.CAMERA_CONTROL,
        Permission.CAMERA_STREAM,
        Permission.CAMERA_CONFIG,
        Permission.ALERT_VIEW,
        Permission.ALERT_ACKNOWLEDGE,
        Permission.ALERT_RESOLVE,
        Permission.ALERT_EXPORT,
        Permission.USER_VIEW,
        Permission.SYSTEM_METRICS,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
    },
    UserRole.USER: {
        # Basic camera and alert access
        Permission.CAMERA_VIEW,
        Permission.CAMERA_STREAM,
        Permission.ALERT_VIEW,
        Permission.ALERT_ACKNOWLEDGE,
        Permission.USER_VIEW,
        Permission.SYSTEM_METRICS,
        Permission.ANALYTICS_VIEW,
    },
    UserRole.VIEWER: {
        # Read-only access
        Permission.CAMERA_VIEW,
        Permission.CAMERA_STREAM,
        Permission.ALERT_VIEW,
        Permission.USER_VIEW,
        Permission.ANALYTICS_VIEW,
    },
}


class PermissionChecker:
    """Utility class for checking permissions."""

    @staticmethod
    def user_has_permission(
        user: User,
        permission: Permission,
        request: Request = None,
        resource_type: str = None,
        resource_id: str = None,
    ) -> bool:
        """Check if a user has a specific permission."""
        # Admin always has all permissions
        if user.role == UserRole.ADMIN:
            granted = True
        else:
            # Check role-based permissions
            role_permissions = ROLE_PERMISSIONS.get(UserRole(user.role), set())
            if permission in role_permissions:
                granted = True
            # Check custom user permissions
            elif user.permissions and permission.value in user.permissions:
                granted = user.permissions[permission.value]
            else:
                granted = False

        # Log the permission check
        audit_logger.log_permission_check(
            user=user,
            permission=permission,
            granted=granted,
            resource_type=resource_type,
            resource_id=resource_id,
            request=request,
        )

        return granted

    @staticmethod
    def user_has_any_permission(user: User, permissions: List[Permission]) -> bool:
        """Check if a user has any of the specified permissions."""
        return any(
            PermissionChecker.user_has_permission(user, perm) for perm in permissions
        )

    @staticmethod
    def user_has_all_permissions(user: User, permissions: List[Permission]) -> bool:
        """Check if a user has all of the specified permissions."""
        return all(
            PermissionChecker.user_has_permission(user, perm) for perm in permissions
        )

    @staticmethod
    def get_user_permissions(user: User) -> Set[Permission]:
        """Get all permissions for a user."""
        if user.role == UserRole.ADMIN:
            return set(Permission)

        # Get role-based permissions
        permissions = ROLE_PERMISSIONS.get(UserRole(user.role), set()).copy()

        # Add custom user permissions
        if user.permissions:
            for perm_key, has_perm in user.permissions.items():
                try:
                    permission = Permission(perm_key)
                    if has_perm:
                        permissions.add(permission)
                    else:
                        permissions.discard(permission)
                except ValueError:
                    # Invalid permission key, skip
                    continue

        return permissions


async def get_current_user(
    token_data: dict = Depends(jwt_auth), db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from token."""
    username = token_data.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = (
        db.query(User).filter(User.username == username, User.is_active == True).first()
    )
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


def require_permission(permission: Permission):
    """Decorator to require specific permission for an endpoint."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs if it exists
            current_user = kwargs.get("current_user")
            request = kwargs.get("request")

            if not current_user:
                # If not in kwargs, it should be in args (dependency injection)
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                    elif isinstance(arg, Request):
                        request = arg

            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")

            # Start timing for audit log
            audit_logger.start_timing()

            if not PermissionChecker.user_has_permission(
                current_user,
                permission,
                request=request,
                resource_type=func.__name__.replace("_", " ").title(),
            ):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied. Required permission: {permission.value}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_any_permission(permissions: List[Permission]):
    """Decorator to require any of the specified permissions for an endpoint."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break

            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")

            if not PermissionChecker.user_has_any_permission(current_user, permissions):
                perm_names = [p.value for p in permissions]
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied. Required permissions (any): {perm_names}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_all_permissions(permissions: List[Permission]):
    """Decorator to require all of the specified permissions for an endpoint."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break

            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")

            if not PermissionChecker.user_has_all_permissions(
                current_user, permissions
            ):
                perm_names = [p.value for p in permissions]
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied. Required permissions (all): {perm_names}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(role: UserRole):
    """Decorator to require specific role for an endpoint."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break

            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")

            if (
                current_user.role != role.value
                and current_user.role != UserRole.ADMIN.value
            ):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied. Required role: {role.value}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
