import logging
import os
import time
from collections import defaultdict
from typing import Dict, List, Optional

import jwt
from dotenv import load_dotenv
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.utils.secrets import secrets_manager

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Rate limiting configuration from environment variables
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 60))  # 1 minute
RATE_LIMIT_MAX_REQUESTS = int(
    os.getenv("RATE_LIMIT_MAX_REQUESTS", 100)
)  # 100 requests per minute

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-here")
JWT_ALGORITHM = "HS256"

# Role-based access control configuration
ROLE_PERMISSIONS = {
    "admin": ["*"],  # Admin can do everything
    "user": ["read", "write"],
    "viewer": ["read"],
}

# API Key to Role mapping
API_KEY_ROLES = {
    os.getenv("API_KEY_ADMIN"): "admin",
    os.getenv("API_KEY_USER"): "user",
    os.getenv("API_KEY_VIEWER"): "viewer",
}

# Public endpoints that don't require API keys
PUBLIC_ENDPOINTS = [
    "/",
    "/favicon.ico",
    "/api/health",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/refresh",
    "/docs",
    "/openapi.json",
    "/redoc",
    # Camera endpoints (temporarily public for development)
    "/cameras/available",
    "/cameras/status",
    "/cameras/upload-video",
    # Metrics endpoints (public for monitoring)
    "/api/metrics/health",
    "/api/metrics/summary",
    "/api/metrics/system",
    "/api/metrics/cameras",
    "/api/metrics/detections",
    "/api/metrics/alerts/recent",
    # Dashboard endpoints (public for dashboard display)
    "/api/audit/recent-events",
    "/api/audit/frontend-events",
]

# Video streaming endpoints that should be public
VIDEO_STREAMING_PATTERNS = [
    "/api/video/hls/",
    "/api/video/mjpeg/",
    "/api/video/stream/",
    "/api/test/hls/",
    "/api/simple/hls/",
    # Camera control endpoints (temporarily public for development)
    "/cameras/",
    # Metrics endpoints patterns (public for monitoring)
    "/api/metrics/",
    # WebSocket endpoints patterns (public for real-time updates)
    "/ws/",
]


class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)

    def is_rate_limited(self, client_id: str) -> bool:
        """Check if a client has exceeded their rate limit"""
        now = time.time()
        # Remove old requests outside the window
        self.requests[client_id] = [
            req_time
            for req_time in self.requests[client_id]
            if now - req_time < RATE_LIMIT_WINDOW
        ]

        # Check if limit is exceeded
        if len(self.requests[client_id]) >= RATE_LIMIT_MAX_REQUESTS:
            return True

        # Add new request
        self.requests[client_id].append(now)
        return False


class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = RateLimiter()

    async def dispatch(self, request: Request, call_next):
        # Skip security checks for public endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)

        # Allow OPTIONS requests for CORS preflight without authentication
        if request.method == "OPTIONS":
            return await call_next(request)

        # Rate limiting for all requests
        client_id = request.client.host if request.client else "unknown"
        if self.rate_limiter.is_rate_limited(client_id):
            return Response(
                content='{"detail": "Too many requests. Please try again later."}',
                status_code=429,
                media_type="application/json",
            )

        # Try to authenticate with JWT token first, then API key
        role = None

        # Check for JWT token in Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                role = payload.get("role")
                request.state.user_id = payload.get("sub")
            except jwt.ExpiredSignatureError:
                return Response(
                    content='{"detail": "Token has expired"}',
                    status_code=401,
                    media_type="application/json",
                )
            except jwt.PyJWTError as e:
                logger.debug(f"JWT token validation failed: {e}")
                # Token is invalid, try API key authentication
                pass

        # If JWT authentication failed, try API key authentication
        if not role:
            api_key = request.headers.get("X-API-Key")
            if api_key and api_key in API_KEY_ROLES:
                role = API_KEY_ROLES[api_key]
            else:
                return Response(
                    content='{"detail": "Invalid or missing authentication credentials"}',
                    status_code=401,
                    media_type="application/json",
                )

        # Check permissions based on role
        if not self._has_permission(role, request.method):
            return Response(
                content='{"detail": "Insufficient permissions for this operation"}',
                status_code=403,
                media_type="application/json",
            )

        # Add role to request state for use in route handlers
        request.state.role = role

        # Continue with the request
        response = await call_next(request)
        return response

    def _is_public_endpoint(self, path: str) -> bool:
        """Check if an endpoint is public (doesn't require API key)"""
        # Check exact matches first
        if (
            path in PUBLIC_ENDPOINTS
            or path.startswith("/static/")
            or path.endswith(".png")
            or path.endswith(".ico")
            or path.endswith(".jpg")
            or path.endswith(".jpeg")
            or path.endswith(".svg")
        ):
            return True

        # Check video streaming patterns
        for pattern in VIDEO_STREAMING_PATTERNS:
            if path.startswith(pattern):
                return True

        return False

    def _has_permission(self, role: str, method: str) -> bool:
        """Check if a role has permission for a given HTTP method"""
        if role not in ROLE_PERMISSIONS:
            return False

        permissions = ROLE_PERMISSIONS[role]
        if "*" in permissions:  # Admin role
            return True

        # Map HTTP methods to permissions
        method_permissions = {
            "GET": "read",
            "POST": "write",
            "PUT": "write",
            "DELETE": "write",
            "PATCH": "write",
        }

        required_permission = method_permissions.get(method, "read")
        return required_permission in permissions


# For backwards compatibility, create a function that can be used as middleware
async def security_middleware(request: Request):
    """Legacy function for direct middleware usage - deprecated"""
    logger.warning(
        "Using deprecated security_middleware function. Use SecurityMiddleware class instead."
    )
    return True
