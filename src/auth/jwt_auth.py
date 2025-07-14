from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-here')  # Change in production
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Role to permissions mapping
ROLE_PERMISSIONS = {
    'admin': {
        'cameras': ['read', 'write', 'delete', 'control'],
        'users': ['read', 'write', 'delete'],
        'system': ['read', 'write', 'delete']
    },
    'user': {
        'cameras': ['read', 'control'],
        'users': ['read'],
        'system': ['read']
    },
    'viewer': {
        'cameras': ['read'],
        'users': ['read'],
        'system': ['read']
    }
}

class JWTAuth:
    def __init__(self):
        self.security = HTTPBearer()
        self.token_blacklist = set()

    def create_access_token(self, user_id: str, role: str) -> str:
        """Create a new access token."""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "exp": expire,
            "sub": user_id,
            "role": role,
            "type": "access"
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
            if token in self.token_blacklist:
                raise HTTPException(status_code=401, detail="Token has been revoked")
            
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    def blacklist_token(self, token: str):
        """Add a token to the blacklist."""
        self.token_blacklist.add(token)

    def check_permission(self, role: str, resource: str, action: str) -> bool:
        """Check if a role has permission for a specific resource and action."""
        if role not in ROLE_PERMISSIONS:
            return False
        
        resource_permissions = ROLE_PERMISSIONS[role].get(resource, [])
        return action in resource_permissions

    async def __call__(self, credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())) -> Dict:
        """Validate JWT token and return payload."""
        return self.verify_token(credentials.credentials)

# Create singleton instance
jwt_auth = JWTAuth() 