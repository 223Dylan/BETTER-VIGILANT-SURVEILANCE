from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.sql import func

from .base import Base


class PushSubscription(Base):
    """Model for storing push notification subscriptions."""

    __tablename__ = "push_subscriptions"

    id = Column(String, primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(String, nullable=False, index=True)
    endpoint = Column(Text, nullable=False)  # Push service endpoint URL
    p256dh_key = Column(Text, nullable=False)  # P-256 ECDH public key
    auth_key = Column(Text, nullable=False)  # Authentication secret
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<PushSubscription(id={self.id}, user_id={self.user_id}, endpoint={self.endpoint[:50]}...)>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "endpoint": self.endpoint,
            "p256dh_key": self.p256dh_key,
            "auth_key": self.auth_key,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_by_user_id(cls, db, user_id: str):
        """Get active subscription for a user."""
        return (
            db.query(cls).filter(cls.user_id == user_id, cls.is_active == True).first()
        )

    @classmethod
    def get_all_active(cls, db):
        """Get all active subscriptions."""
        return db.query(cls).filter(cls.is_active == True).all()

    @classmethod
    def deactivate_by_user_id(cls, db, user_id: str):
        """Deactivate all subscriptions for a user."""
        subscriptions = db.query(cls).filter(cls.user_id == user_id).all()
        for subscription in subscriptions:
            subscription.is_active = False
        db.commit()
        return len(subscriptions)
