# Authentication and Security

## Overview

The Authentication and Security system provides comprehensive protection including JWT-based authentication, role-based access control, encryption, request limiting, and security headers.

## Architecture

### Security Components

1. **JWT Authentication** - Token-based authentication
2. **Role-Based Access Control** - User permissions and roles
3. **Encryption Services** - Data encryption and decryption
4. **Security Middleware** - Request protection and headers
5. **Rate Limiting** - DDoS and abuse prevention
6. **Audit Logging** - Security event tracking

### Security Flow

```
Client Request → Security Headers → Rate Limiting → JWT Validation → RBAC → Endpoint
                      ↓
               Audit Logging → Encryption (if needed) → Response
```

## JWT Authentication

### Token Management

**Source:** `src/auth/jwt_auth.py`

```python
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-here")  # Change in production
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

class JWTAuth:
    """JWT authentication handler with token blacklisting."""

    def __init__(self):
        self.security = HTTPBearer()
        self.token_blacklist = set()

    def create_access_token(self, user_id: str, role: str) -> str:
        """Create a new access token."""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "exp": expire,
            "sub": user_id,    # User identifier
            "role": role,      # User role
            "type": "access"   # Token type
        }
        return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def create_refresh_token(self, user_id: str, role: str) -> str:
        """Create a new refresh token."""
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {
            "exp": expire,
            "sub": user_id,
            "role": role,
            "type": "refresh"
        }
        return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def verify_token(self, token: str) -> Dict:
        """Verify a JWT token."""
        try:
            # Check if token is blacklisted
            if token in self.token_blacklist:
                raise HTTPException(status_code=401, detail="Token has been revoked")

            # Decode and verify token
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    def blacklist_token(self, token: str):
        """Add a token to the blacklist (for logout)."""
        self.token_blacklist.add(token)

    async def __call__(self, credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())) -> Dict:
        """Validate JWT token and return payload."""
        return self.verify_token(credentials.credentials)

# Global JWT auth instance
jwt_auth = JWTAuth()
```

### Role-Based Permissions

The JWT auth system includes built-in role-based permissions:

```python
# Role to permissions mapping
ROLE_PERMISSIONS = {
    "admin": {
        "cameras": ["read", "write", "delete", "control"],
        "users": ["read", "write", "delete"],
        "system": ["read", "write", "delete"],
    },
    "user": {
        "cameras": ["read", "control"],
        "users": ["read"],
        "system": ["read"]
    },
    "viewer": {
        "cameras": ["read"],
        "users": ["read"],
        "system": ["read"]
    },
}

def check_permission(role: str, resource: str, action: str) -> bool:
    """Check if a role has permission for a specific resource and action."""
    if role not in ROLE_PERMISSIONS:
        return False
    resource_permissions = ROLE_PERMISSIONS[role].get(resource, [])
    return action in resource_permissions
```

### Token Structure

**Access Token Payload:**
```json
{
  "exp": 1609459200,        // Expiration timestamp
  "sub": "admin",           // User identifier (username)
  "role": "admin",          // User role
  "type": "access"          // Token type
}
```

**Refresh Token Payload:**
```json
{
  "exp": 1610064000,        // Expiration timestamp (7 days)
  "sub": "admin",           // User identifier
  "role": "admin",          // User role
  "type": "refresh"         // Token type
}
```
            if payload.get("type") != "refresh":
                return None

            return payload

        except JWTError:
            return None

class PasswordHandler:
    """Password hashing and verification."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def generate_password_reset_token(user_id: str) -> str:
        """Generate password reset token."""
        data = {
            "sub": user_id,
            "type": "password_reset",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
```

### Authentication Dependencies

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verify token
    payload = JWTHandler.verify_token(token)
    if not payload:
        raise credentials_exception

    # Get user
    username = payload.get("sub")
    if not username:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise credentials_exception

    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(required_role: str):
    """Dependency to require specific role."""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

def require_permissions(required_permissions: list):
    """Dependency to require specific permissions."""
    def permission_checker(current_user: User = Depends(get_current_user)):
        user_permissions = current_user.permissions or {}

        for permission in required_permissions:
            if not user_permissions.get(permission, False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing permission: {permission}"
                )
        return current_user
    return permission_checker
```

## Role-Based Access Control

### User Roles and Permissions

```python
from enum import Enum
from typing import Dict, List

class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    USER = "user"

class Permission(str, Enum):
    """Permission enumeration."""
    # Camera permissions
    CAMERA_VIEW = "camera:view"
    CAMERA_CREATE = "camera:create"
    CAMERA_UPDATE = "camera:update"
    CAMERA_DELETE = "camera:delete"
    CAMERA_CONTROL = "camera:control"

    # Alert permissions
    ALERT_VIEW = "alert:view"
    ALERT_ACKNOWLEDGE = "alert:acknowledge"
    ALERT_RESOLVE = "alert:resolve"
    ALERT_DELETE = "alert:delete"

    # User permissions
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # System permissions
    SYSTEM_CONFIG = "system:config"
    SYSTEM_LOGS = "system:logs"
    SYSTEM_METRICS = "system:metrics"

# Role permission mappings
ROLE_PERMISSIONS: Dict[UserRole, List[Permission]] = {
    UserRole.ADMIN: [
        # All permissions
        Permission.CAMERA_VIEW, Permission.CAMERA_CREATE, Permission.CAMERA_UPDATE,
        Permission.CAMERA_DELETE, Permission.CAMERA_CONTROL,
        Permission.ALERT_VIEW, Permission.ALERT_ACKNOWLEDGE, Permission.ALERT_RESOLVE,
        Permission.ALERT_DELETE,
        Permission.USER_VIEW, Permission.USER_CREATE, Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.SYSTEM_CONFIG, Permission.SYSTEM_LOGS, Permission.SYSTEM_METRICS
    ],
    UserRole.OPERATOR: [
        # Camera and alert management
        Permission.CAMERA_VIEW, Permission.CAMERA_UPDATE, Permission.CAMERA_CONTROL,
        Permission.ALERT_VIEW, Permission.ALERT_ACKNOWLEDGE, Permission.ALERT_RESOLVE,
        Permission.SYSTEM_METRICS
    ],
    UserRole.VIEWER: [
        # Read-only access
        Permission.CAMERA_VIEW,
        Permission.ALERT_VIEW,
        Permission.SYSTEM_METRICS
    ],
    UserRole.USER: [
        # Basic access
        Permission.CAMERA_VIEW,
        Permission.ALERT_VIEW
    ]
}

def get_user_permissions(role: UserRole) -> List[Permission]:
    """Get permissions for user role."""
    return ROLE_PERMISSIONS.get(role, [])

def has_permission(user: User, permission: Permission) -> bool:
    """Check if user has specific permission."""
    # Admin has all permissions
    if user.role == UserRole.ADMIN:
        return True

    # Check role-based permissions
    role_permissions = get_user_permissions(UserRole(user.role))
    if permission in role_permissions:
        return True

    # Check custom user permissions
    user_permissions = user.permissions or {}
    return user_permissions.get(permission.value, False)
```

## Encryption Services

### Data Encryption

**Source:** `src/security/encryption.py`

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import base64
import os

class SymmetricEncryption:
    """Symmetric encryption using Fernet."""

    def __init__(self, key: bytes = None):
        if key is None:
            key = self._derive_key_from_password(
                os.getenv("ENCRYPTION_PASSWORD", "default-password").encode(),
                os.getenv("ENCRYPTION_SALT", "default-salt").encode()
            )
        self.fernet = Fernet(key)

    @staticmethod
    def _derive_key_from_password(password: bytes, salt: bytes) -> bytes:
        """Derive encryption key from password."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key

    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        encrypted_data = self.fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data."""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception:
            raise ValueError("Failed to decrypt data")

class AsymmetricEncryption:
    """Asymmetric encryption using RSA."""

    def __init__(self, private_key_path: str = None, public_key_path: str = None):
        self.private_key_path = private_key_path or "keys/private_key.pem"
        self.public_key_path = public_key_path or "keys/public_key.pem"

        self.private_key = self._load_private_key()
        self.public_key = self._load_public_key()

    def _load_private_key(self):
        """Load private key from file."""
        try:
            with open(self.private_key_path, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None
                )
            return private_key
        except FileNotFoundError:
            # Generate new key pair if not found
            return self._generate_key_pair()

    def _load_public_key(self):
        """Load public key from file."""
        try:
            with open(self.public_key_path, "rb") as key_file:
                public_key = serialization.load_pem_public_key(key_file.read())
            return public_key
        except FileNotFoundError:
            return self.private_key.public_key()

    def _generate_key_pair(self):
        """Generate new RSA key pair."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        # Save private key
        os.makedirs(os.path.dirname(self.private_key_path), exist_ok=True)
        with open(self.private_key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

        # Save public key
        public_key = private_key.public_key()
        with open(self.public_key_path, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

        return private_key

    def encrypt(self, data: str) -> str:
        """Encrypt data with public key."""
        encrypted_data = self.public_key.encrypt(
            data.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.urlsafe_b64encode(encrypted_data).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data with private key."""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.private_key.decrypt(
                decoded_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted_data.decode()
        except Exception:
            raise ValueError("Failed to decrypt data")

# Global encryption instances
symmetric_encryption = SymmetricEncryption()
asymmetric_encryption = AsymmetricEncryption()
```

## Security Middleware

### Security Headers Middleware

**Source:** `src/middleware/security_headers.py`

```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self'; "
            "connect-src 'self' ws: wss:; "
            "media-src 'self' blob:; "
            "object-src 'none'; "
            "frame-src 'none'"
        )
        response.headers["Content-Security-Policy"] = csp_policy

        return response
```

### Rate Limiting Middleware

**Source:** `src/middleware/request_limits.py`

```python
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Optional
import time
from collections import defaultdict, deque

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using sliding window."""

    def __init__(self, app, requests_per_minute: int = 60, requests_per_second: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_second = requests_per_second
        self.minute_windows: Dict[str, deque] = defaultdict(deque)
        self.second_windows: Dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # Check rate limits
        if self._is_rate_limited(client_ip, current_time):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )

        # Record request
        self._record_request(client_ip, current_time)

        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host

    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """Check if client is rate limited."""
        # Clean old entries
        self._clean_old_entries(client_ip, current_time)

        # Check per-second limit
        second_window = self.second_windows[client_ip]
        if len(second_window) >= self.requests_per_second:
            return True

        # Check per-minute limit
        minute_window = self.minute_windows[client_ip]
        if len(minute_window) >= self.requests_per_minute:
            return True

        return False

    def _record_request(self, client_ip: str, current_time: float):
        """Record request timestamp."""
        self.second_windows[client_ip].append(current_time)
        self.minute_windows[client_ip].append(current_time)

    def _clean_old_entries(self, client_ip: str, current_time: float):
        """Remove old entries from sliding windows."""
        # Clean second window (keep last second)
        second_window = self.second_windows[client_ip]
        while second_window and current_time - second_window[0] > 1:
            second_window.popleft()

        # Clean minute window (keep last minute)
        minute_window = self.minute_windows[client_ip]
        while minute_window and current_time - minute_window[0] > 60:
            minute_window.popleft()
```

## Audit Logging

### Security Event Logging

**Source:** `src/middleware/audit_logger.py`

```python
import json
import logging
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional

# Setup audit logger
audit_logger = logging.getLogger("audit")
audit_handler = logging.FileHandler("logs/audit.log")
audit_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
audit_handler.setFormatter(audit_formatter)
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)

class AuditLoggerMiddleware(BaseHTTPMiddleware):
    """Log security-relevant events."""

    SENSITIVE_ENDPOINTS = {
        "/api/v1/auth/token",
        "/api/v1/auth/refresh",
        "/api/v1/users",
        "/api/v1/cameras",
        "/api/v1/alerts"
    }

    async def dispatch(self, request: Request, call_next):
        start_time = datetime.utcnow()

        # Extract request info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")
        method = request.method
        path = request.url.path

        # Get user info if available
        user_id = None
        username = None
        try:
            # Try to extract user from token
            authorization = request.headers.get("Authorization")
            if authorization and authorization.startswith("Bearer "):
                token = authorization.split(" ")[1]
                payload = JWTHandler.verify_token(token)
                if payload:
                    username = payload.get("sub")
        except:
            pass

        # Process request
        response = await call_next(request)

        # Calculate response time
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds()

        # Log if sensitive endpoint or error
        if (path in self.SENSITIVE_ENDPOINTS or
            response.status_code >= 400 or
            method in ["POST", "PUT", "DELETE"]):

            audit_event = {
                "timestamp": start_time.isoformat(),
                "event_type": "api_request",
                "client_ip": client_ip,
                "user_agent": user_agent,
                "username": username,
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code < 400
            }

            # Add extra context for failures
            if response.status_code >= 400:
                audit_event["event_type"] = "api_error"
                audit_event["error_category"] = self._categorize_error(response.status_code)

            # Log authentication events
            if path == "/api/v1/auth/token":
                if response.status_code == 200:
                    audit_event["event_type"] = "login_success"
                else:
                    audit_event["event_type"] = "login_failure"

            audit_logger.info(json.dumps(audit_event))

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _categorize_error(self, status_code: int) -> str:
        """Categorize error by status code."""
        if status_code == 401:
            return "authentication_error"
        elif status_code == 403:
            return "authorization_error"
        elif status_code == 404:
            return "not_found"
        elif status_code == 422:
            return "validation_error"
        elif status_code == 429:
            return "rate_limit_exceeded"
        elif 400 <= status_code < 500:
            return "client_error"
        else:
            return "server_error"

def log_security_event(event_type: str, details: dict, user_id: Optional[str] = None):
    """Log custom security event."""
    audit_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        **details
    }

    audit_logger.warning(json.dumps(audit_event))
```

## Security Configuration

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Encryption Configuration
ENCRYPTION_PASSWORD=your-encryption-password
ENCRYPTION_SALT=your-encryption-salt

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_SECOND=10

# Security Headers
FORCE_HTTPS=true
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database Security
DB_SSL_MODE=require
DB_SSL_CERT=/path/to/server-ca.pem
DB_SSL_KEY=/path/to/client-key.pem
DB_SSL_ROOT_CERT=/path/to/ca-cert.pem
```

## Best Practices

1. **Password Security**
   - Enforce strong password policies
   - Use bcrypt for password hashing
   - Implement password history
   - Force password changes periodically

2. **Token Management**
   - Use short-lived access tokens
   - Implement refresh token rotation
   - Store tokens securely on client
   - Revoke tokens on logout

3. **Access Control**
   - Implement principle of least privilege
   - Use role-based permissions
   - Regularly audit user permissions
   - Log all access attempts

4. **Data Protection**
   - Encrypt sensitive data at rest
   - Use HTTPS for all communications
   - Implement proper key management
   - Regular security audits
