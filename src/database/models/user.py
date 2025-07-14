from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
import uuid
from .base import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default='user')
    permissions = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    last_activity_at = Column(DateTime(timezone=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'permissions': self.permissions or {},
            'is_active': self.is_active,
            'is_verified': self.is_verified
        }
    
    def has_permission(self, permission_key):
        if self.role == 'admin':
            return True
        return self.permissions.get(permission_key, False) if self.permissions else False

