import hashlib
import secrets
import string
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.auth.jwt_auth import jwt_auth
from src.auth.permissions import (
    Permission,
    PermissionChecker,
    UserRole,
    get_current_user,
    require_any_permission,
    require_permission,
)
from src.database.models.base import get_db
from src.database.models.user import User

router = APIRouter()


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    permissions: dict
    created_at: str
    updated_at: str
    last_login_at: Optional[str] = None
    last_activity_at: Optional[str] = None
    avatar_url: Optional[str] = None


class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "user"
    permissions: Optional[dict] = None


class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    permissions: Optional[dict] = None


class PasswordChangeRequest(BaseModel):
    new_password: str


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


def get_default_permissions(role: str) -> dict:
    """Get default permissions based on role."""
    default_permissions = {
        "canViewCameras": False,
        "canControlCameras": False,
        "canViewAlerts": False,
        "canManageAlerts": False,
        "canViewAnalytics": False,
        "canManageUsers": False,
        "canManageSystem": False,
        "canExportData": False,
    }

    if role == "admin":
        return {key: True for key in default_permissions.keys()}
    elif role == "user":
        return {
            **default_permissions,
            "canViewCameras": True,
            "canViewAlerts": True,
            "canManageAlerts": True,
            "canExportData": True,
        }
    elif role == "viewer":
        return {
            **default_permissions,
            "canViewCameras": True,
            "canViewAlerts": True,
        }

    return default_permissions


def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_random_password(length: int = 12) -> str:
    """Generate a random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def user_to_response(user: User) -> UserResponse:
    """Convert User model to UserResponse."""
    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        first_name=getattr(user, "first_name", None),
        last_name=getattr(user, "last_name", None),
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        permissions=user.permissions or {},
        created_at=user.created_at.isoformat() if user.created_at else "",
        updated_at=user.updated_at.isoformat() if user.updated_at else "",
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        last_activity_at=(
            user.last_activity_at.isoformat() if user.last_activity_at else None
        ),
        avatar_url=getattr(user, "avatar_url", None),
    )


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/users/", response_model=UserListResponse)
@require_permission(Permission.USER_VIEW)
async def get_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get paginated list of users (admin only)."""
    query = db.query(User)

    # Apply filters
    if search:
        search_filter = or_(
            User.username.ilike(f"%{search}%"), User.email.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    if role:
        query = query.filter(User.role == role)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * per_page
    users = query.offset(offset).limit(per_page).all()

    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page

    return UserListResponse(
        users=[user_to_response(user) for user in users],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.post("/users/", response_model=UserResponse)
@require_permission(Permission.USER_CREATE)
async def create_user(
    user_data: CreateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new user (admin only)."""
    # Check if username or email already exists
    existing_user = (
        db.query(User)
        .filter(or_(User.username == user_data.username, User.email == user_data.email))
        .first()
    )

    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        else:
            raise HTTPException(status_code=400, detail="Email already exists")

    # Set permissions based on role if not provided
    permissions = user_data.permissions or get_default_permissions(user_data.role)

    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        is_active=True,
        is_verified=True,
        permissions=permissions,
    )

    # Set optional fields if the model supports them
    if hasattr(new_user, "first_name") and user_data.first_name:
        new_user.first_name = user_data.first_name
    if hasattr(new_user, "last_name") and user_data.last_name:
        new_user.last_name = user_data.last_name

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return user_to_response(new_user)


@router.get("/users/{user_id}", response_model=UserResponse)
@require_permission(Permission.USER_VIEW)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user by ID (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user_to_response(user)


@router.patch("/users/{user_id}", response_model=UserResponse)
@require_permission(Permission.USER_UPDATE)
async def update_user(
    user_id: str,
    user_data: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if username or email conflicts with other users
    if user_data.username and user_data.username != user.username:
        existing = (
            db.query(User)
            .filter(User.username == user_data.username, User.id != user_id)
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")

    if user_data.email and user_data.email != user.email:
        existing = (
            db.query(User)
            .filter(User.email == user_data.email, User.id != user_id)
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")

    # Update fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        # Only set attributes that exist on the User model
        if hasattr(user, field):
            setattr(user, field, value)

    # If role changed and no custom permissions provided, update permissions
    if user_data.role and user_data.role != user.role and not user_data.permissions:
        user.permissions = get_default_permissions(user_data.role)

    db.commit()
    db.refresh(user)

    return user_to_response(user)


@router.delete("/users/{user_id}")
@require_permission(Permission.USER_DELETE)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete user (admin only)."""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}


@router.post("/users/{user_id}/change-password")
async def change_user_password(
    user_id: str,
    password_data: PasswordChangeRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Change user password (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(password_data.new_password)
    db.commit()

    return {"message": "Password updated successfully"}


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reset user password to a random one (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate random password
    new_password = generate_random_password()
    user.password_hash = hash_password(new_password)
    db.commit()

    return {
        "message": "Password reset successfully",
        "temporary_password": new_password,
    }
