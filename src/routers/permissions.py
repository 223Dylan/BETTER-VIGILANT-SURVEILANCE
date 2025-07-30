from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.auth.permissions import (
    ROLE_PERMISSIONS,
    Permission,
    UserRole,
    get_current_user,
    require_permission,
)
from src.database.models.base import get_db
from src.database.models.user import User

router = APIRouter()


class PermissionInfo(BaseModel):
    """Permission information model."""

    name: str
    value: str
    description: str
    category: str


class RoleInfo(BaseModel):
    """Role information model."""

    name: str
    display_name: str
    description: str
    permissions: List[str]
    user_count: int


class PermissionSummary(BaseModel):
    """Permission summary for a user."""

    user_id: str
    username: str
    role: str
    role_permissions: List[str]
    custom_permissions: List[str]
    effective_permissions: List[str]
    total_permissions: int


# Permission definitions with categories and descriptions
PERMISSION_DEFINITIONS = {
    # Camera permissions
    Permission.CAMERA_VIEW: {
        "description": "View camera feeds and status information",
        "category": "Camera Management",
    },
    Permission.CAMERA_CREATE: {
        "description": "Add new cameras to the system",
        "category": "Camera Management",
    },
    Permission.CAMERA_UPDATE: {
        "description": "Modify camera settings and configuration",
        "category": "Camera Management",
    },
    Permission.CAMERA_DELETE: {
        "description": "Remove cameras from the system",
        "category": "Camera Management",
    },
    Permission.CAMERA_CONTROL: {
        "description": "Start, stop, and control camera operations",
        "category": "Camera Management",
    },
    Permission.CAMERA_STREAM: {
        "description": "Access live camera streams",
        "category": "Camera Management",
    },
    Permission.CAMERA_CONFIG: {
        "description": "Configure camera parameters and settings",
        "category": "Camera Management",
    },
    # Alert permissions
    Permission.ALERT_VIEW: {
        "description": "View alerts and notifications",
        "category": "Alert Management",
    },
    Permission.ALERT_CREATE: {
        "description": "Create new alerts manually",
        "category": "Alert Management",
    },
    Permission.ALERT_ACKNOWLEDGE: {
        "description": "Acknowledge and mark alerts as seen",
        "category": "Alert Management",
    },
    Permission.ALERT_RESOLVE: {
        "description": "Resolve and close alerts",
        "category": "Alert Management",
    },
    Permission.ALERT_DELETE: {
        "description": "Delete alerts from the system",
        "category": "Alert Management",
    },
    Permission.ALERT_EXPORT: {
        "description": "Export alert data and reports",
        "category": "Alert Management",
    },
    # User permissions
    Permission.USER_VIEW: {
        "description": "View user accounts and profiles",
        "category": "User Management",
    },
    Permission.USER_CREATE: {
        "description": "Create new user accounts",
        "category": "User Management",
    },
    Permission.USER_UPDATE: {
        "description": "Modify existing user accounts",
        "category": "User Management",
    },
    Permission.USER_DELETE: {
        "description": "Delete user accounts",
        "category": "User Management",
    },
    Permission.USER_MANAGE_ROLES: {
        "description": "Assign and modify user roles",
        "category": "User Management",
    },
    Permission.USER_MANAGE_PERMISSIONS: {
        "description": "Grant and revoke individual permissions",
        "category": "User Management",
    },
    # System permissions
    Permission.SYSTEM_CONFIG: {
        "description": "Configure system settings and parameters",
        "category": "System Administration",
    },
    Permission.SYSTEM_LOGS: {
        "description": "Access system logs and audit trails",
        "category": "System Administration",
    },
    Permission.SYSTEM_METRICS: {
        "description": "View system performance metrics",
        "category": "System Administration",
    },
    Permission.SYSTEM_BACKUP: {
        "description": "Create and manage system backups",
        "category": "System Administration",
    },
    Permission.SYSTEM_MAINTENANCE: {
        "description": "Perform system maintenance tasks",
        "category": "System Administration",
    },
    # Analytics permissions
    Permission.ANALYTICS_VIEW: {
        "description": "View analytics dashboards and reports",
        "category": "Analytics",
    },
    Permission.ANALYTICS_EXPORT: {
        "description": "Export analytics data",
        "category": "Analytics",
    },
    Permission.ANALYTICS_REPORTS: {
        "description": "Generate and schedule analytics reports",
        "category": "Analytics",
    },
    # Security permissions
    Permission.SECURITY_AUDIT: {
        "description": "Access security audit logs and reports",
        "category": "Security",
    },
    Permission.SECURITY_CONFIG: {
        "description": "Configure security settings and policies",
        "category": "Security",
    },
}

ROLE_DESCRIPTIONS = {
    UserRole.VIEWER: "Read-only access to cameras and basic alerts",
    UserRole.USER: "Standard user with camera viewing and alert management",
    UserRole.OPERATOR: "Advanced user with camera control and system monitoring",
    UserRole.ADMIN: "Full system access including user and system management",
}


@router.get("/permissions", response_model=List[PermissionInfo])
@require_permission(Permission.USER_VIEW)
async def get_all_permissions(current_user: User = Depends(get_current_user)):
    """Get all available permissions with descriptions."""
    permissions = []

    for permission in Permission:
        definition = PERMISSION_DEFINITIONS.get(permission, {})
        permissions.append(
            PermissionInfo(
                name=permission.name,
                value=permission.value,
                description=definition.get("description", ""),
                category=definition.get("category", "Uncategorized"),
            )
        )

    return sorted(permissions, key=lambda x: (x.category, x.name))


@router.get("/roles", response_model=List[RoleInfo])
@require_permission(Permission.USER_VIEW)
async def get_all_roles(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get all available roles with their permissions and user counts."""
    roles = []

    for role in UserRole:
        # Count users with this role
        user_count = db.query(User).filter(User.role == role.value).count()

        role_permissions = ROLE_PERMISSIONS.get(role, [])

        roles.append(
            RoleInfo(
                name=role.value,
                display_name=role.value.title(),
                description=ROLE_DESCRIPTIONS.get(role, ""),
                permissions=[p.value for p in role_permissions],
                user_count=user_count,
            )
        )

    return roles


@router.get("/roles/{role_name}/permissions")
@require_permission(Permission.USER_VIEW)
async def get_role_permissions(
    role_name: str, current_user: User = Depends(get_current_user)
):
    """Get permissions for a specific role."""
    try:
        role = UserRole(role_name)
    except ValueError:
        raise HTTPException(status_code=404, detail="Role not found")

    permissions = ROLE_PERMISSIONS.get(role, [])

    return {
        "role": role.value,
        "permissions": [p.value for p in permissions],
        "permission_count": len(permissions),
        "permission_details": [
            {
                "name": p.value,
                "description": PERMISSION_DEFINITIONS.get(p, {}).get("description", ""),
                "category": PERMISSION_DEFINITIONS.get(p, {}).get("category", ""),
            }
            for p in permissions
        ],
    }


@router.get("/users/{user_id}/permissions", response_model=PermissionSummary)
@require_permission(Permission.USER_VIEW)
async def get_user_permissions(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get comprehensive permission summary for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        user_role = UserRole(user.role)
    except ValueError:
        user_role = UserRole.USER  # Default fallback

    # Get role permissions
    role_permissions = ROLE_PERMISSIONS.get(user_role, [])
    role_permission_values = [p.value for p in role_permissions]

    # Get custom permissions (stored in user.permissions JSON field)
    custom_permissions = user.permissions or []
    if isinstance(custom_permissions, dict):
        # Handle legacy permission format
        custom_permissions = [
            perm
            for perm, enabled in custom_permissions.items()
            if enabled and perm not in role_permission_values
        ]

    # Calculate effective permissions (role + custom, removing duplicates)
    effective_permissions = list(set(role_permission_values + custom_permissions))

    return PermissionSummary(
        user_id=user.id,
        username=user.username,
        role=user.role,
        role_permissions=role_permission_values,
        custom_permissions=custom_permissions,
        effective_permissions=sorted(effective_permissions),
        total_permissions=len(effective_permissions),
    )


@router.get("/matrix")
@require_permission(Permission.USER_VIEW)
async def get_permission_matrix(current_user: User = Depends(get_current_user)):
    """Get a complete permission matrix showing which roles have which permissions."""
    matrix = {}

    # Build matrix for each role
    for role in UserRole:
        role_permissions = ROLE_PERMISSIONS.get(role, [])
        permission_map = {}

        # Check each permission against this role
        for permission in Permission:
            permission_map[permission.value] = permission in role_permissions

        matrix[role.value] = {
            "display_name": role.value.title(),
            "description": ROLE_DESCRIPTIONS.get(role, ""),
            "permissions": permission_map,
            "total_permissions": len(role_permissions),
        }

    # Also provide permission details
    permission_details = {}
    for permission in Permission:
        definition = PERMISSION_DEFINITIONS.get(permission, {})
        permission_details[permission.value] = {
            "name": permission.value,
            "description": definition.get("description", ""),
            "category": definition.get("category", "Uncategorized"),
        }

    return {
        "roles": matrix,
        "permissions": permission_details,
        "categories": list(
            set(
                PERMISSION_DEFINITIONS.get(p, {}).get("category", "Uncategorized")
                for p in Permission
            )
        ),
    }


@router.post("/validate")
@require_permission(Permission.USER_VIEW)
async def validate_permissions(
    permissions: List[str], current_user: User = Depends(get_current_user)
):
    """Validate a list of permissions and return validation results."""
    valid_permissions = [p.value for p in Permission]
    results = []

    for perm in permissions:
        is_valid = perm in valid_permissions
        definition = None

        if is_valid:
            # Find the permission enum to get definition
            for p in Permission:
                if p.value == perm:
                    definition = PERMISSION_DEFINITIONS.get(p, {})
                    break

        results.append(
            {
                "permission": perm,
                "valid": is_valid,
                "description": (
                    definition.get("description", "") if definition else None
                ),
                "category": definition.get("category", "") if definition else None,
            }
        )

    valid_count = sum(1 for r in results if r["valid"])

    return {
        "permissions": results,
        "total_checked": len(permissions),
        "valid_count": valid_count,
        "invalid_count": len(permissions) - valid_count,
        "all_valid": valid_count == len(permissions),
    }
