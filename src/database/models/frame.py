from sqlalchemy import Column, Integer, String, DateTime, JSON, LargeBinary
from sqlalchemy.sql import func
from .base import Base

class Frame(Base):
    __tablename__ = "frames"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    sequence_number = Column(Integer, index=True)
    frame_data = Column(LargeBinary)  # For storing compressed frame data
    frame_metadata = Column(JSON)  # For storing predictions, annotations, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Frame(id={self.id}, sequence={self.sequence_number}, timestamp={self.timestamp})>" 