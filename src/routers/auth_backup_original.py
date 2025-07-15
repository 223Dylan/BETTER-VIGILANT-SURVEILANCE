from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import hashlib
from datetime import datetime

from src.auth.jwt_auth import jwt_auth
from src.database.models.user import User
from src.database.models.base import get_db
from loguru import logger

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_info: dict


class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == hashed_password


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint using database authentication."""
    try:
        # Find user in database
        user = (
            db.query(User)
            .filter(User.username == login_data.username, User.is_active == True)
            .first()
        )

        if not user or not verify_password(login_data.password, user.password_hash):
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

        logger.info(f"User {user.username} logged in successfully")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_info": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "permissions": user.permissions,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error during login"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: dict = Depends(jwt_auth), db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    try:
        if token_data.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

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

        access_token = jwt_auth.create_access_token(username, role)
        refresh_token = jwt_auth.create_refresh_token(username, role)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_info": user.to_dict(),
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
