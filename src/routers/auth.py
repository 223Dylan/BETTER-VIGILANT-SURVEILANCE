import hashlib
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.auth.jwt_auth import jwt_auth
from src.database.models.audit_log import AuditAction, AuditSeverity
from src.database.models.base import get_db
from src.database.models.user import User
from src.services.audit_logger import audit_logger

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest, request: Request, db: Session = Depends(get_db)
):
    """Login endpoint using database authentication."""
    audit_logger.start_timing()

    try:
        # Find user in database
        user = (
            db.query(User)
            .filter(User.username == login_data.username, User.is_active == True)
            .first()
        )

        # Verify password
        password_hash = hashlib.sha256(login_data.password.encode()).hexdigest()

        if not user or user.password_hash != password_hash:
            # Log failed login attempt
            audit_logger.log_authentication(
                username=login_data.username,
                action=AuditAction.LOGIN_FAILED,
                success=False,
                request=request,
                error_message="Invalid credentials",
            )

            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Update last login time
        user.last_login_at = datetime.utcnow()
        user.last_activity_at = datetime.utcnow()
        db.commit()

        # Create tokens
        access_token = jwt_auth.create_access_token(user.username, user.role)
        refresh_token = jwt_auth.create_refresh_token(user.username, user.role)

        # Log successful login
        audit_logger.log_authentication(
            username=user.username,
            action=AuditAction.LOGIN,
            success=True,
            request=request,
            metadata={
                "user_id": user.id,
                "role": user.role,
                "last_login": (
                    user.last_login_at.isoformat() if user.last_login_at else None
                ),
            },
        )

        logger.info(f"User {user.username} logged in successfully")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    except HTTPException:
        raise
    except Exception as e:
        # Log system error
        audit_logger.log_security_event(
            action="login_system_error",
            severity=AuditSeverity.HIGH,
            request=request,
            error_message=str(e),
            metadata={"username": login_data.username},
        )

        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error during login"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    try:
        # Verify the refresh token directly
        try:
            token_data = jwt_auth.verify_token(refresh_data.refresh_token)
        except HTTPException as e:
            logger.warning(f"Invalid refresh token: {e.detail}")
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if token_data.get("type") != "refresh":
            raise HTTPException(
                status_code=401, detail="Invalid token type - expected refresh token"
            )

        username = token_data.get("sub")
        role = token_data.get("role")

        if not username or not role:
            raise HTTPException(status_code=401, detail="Invalid token data")

        # Verify user still exists and is active
        user = (
            db.query(User)
            .filter(User.username == username, User.is_active == True)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=401, detail="User no longer exists or is inactive"
            )

        # Update activity time
        user.last_activity_at = datetime.utcnow()
        db.commit()

        # Create new tokens
        access_token = jwt_auth.create_access_token(username, role)
        new_refresh_token = jwt_auth.create_refresh_token(username, role)

        logger.info(f"Token refreshed successfully for user {username}")

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.post("/logout")
async def logout(token_data: dict = Depends(jwt_auth)):
    """Logout endpoint to blacklist the current token."""
    jwt_auth.blacklist_token(token_data.get("token"))
    return {"message": "Successfully logged out"}
