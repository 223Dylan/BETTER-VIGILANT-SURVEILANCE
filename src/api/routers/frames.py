"""
NOTICE: This frames API router exists but is NOT currently being used in the system.
- Router registration is disabled in main.py
- Frame storage service is disabled in frame_processor.py  
- No frontend components call these endpoints
- System currently operates in real-time mode without persistent frame storage
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import numpy as np
import cv2
import base64
from io import BytesIO

from src.database.models.base import get_db
from src.services.frame_service import FrameService
from pydantic import BaseModel

router = APIRouter(prefix="/frames", tags=["frames"])

class FrameResponse(BaseModel):
    id: int
    sequence_number: int
    timestamp: datetime
    frame_data: str  # base64 encoded
    frame_metadata: dict
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True

class FrameMetadataUpdate(BaseModel):
    metadata: dict

class FrameCreate(BaseModel):
    frame_data: str  # base64 encoded image
    sequence_number: int
    metadata: Optional[dict] = None

@router.post("/", response_model=FrameResponse)
async def store_frame(
    frame_create: FrameCreate,
    db: Session = Depends(get_db)
):
    """Store a new frame in the database."""
    try:
        # Decode base64 image
        image_data = base64.b64decode(frame_create.frame_data)
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image data")
        
        # Store frame
        frame_service = FrameService(db)
        frame_record = frame_service.store_frame(frame, frame_create.sequence_number, frame_create.metadata)
        
        # Convert frame data to base64 for response
        frame_record.frame_data = frame_create.frame_data  # Already base64 encoded
        
        return frame_record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{frame_id}", response_model=FrameResponse)
async def get_frame(
    frame_id: int,
    db: Session = Depends(get_db)
):
    """Retrieve a frame by ID."""
    frame_service = FrameService(db)
    frame = frame_service.get_frame(frame_id)
    
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")
    
    # Convert frame data to base64
    frame.frame_data = base64.b64encode(frame.frame_data).decode('utf-8')
    
    return frame

@router.get("/sequence/{start}/{end}", response_model=List[FrameResponse])
async def get_frames_by_sequence(
    start: int,
    end: int,
    db: Session = Depends(get_db)
):
    """Retrieve frames within a sequence range."""
    frame_service = FrameService(db)
    frames = frame_service.get_frames_by_sequence(start, end)
    
    # Convert frame data to base64
    for frame in frames:
        frame.frame_data = base64.b64encode(frame.frame_data).decode('utf-8')
    
    return frames

@router.get("/time-range/", response_model=List[FrameResponse])
async def get_frames_by_timestamp(
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    db: Session = Depends(get_db)
):
    """Retrieve frames within a time range."""
    frame_service = FrameService(db)
    frames = frame_service.get_frames_by_timestamp(start_time, end_time)
    
    # Convert frame data to base64
    for frame in frames:
        frame.frame_data = base64.b64encode(frame.frame_data).decode('utf-8')
    
    return frames

@router.patch("/{frame_id}/metadata", response_model=FrameResponse)
async def update_frame_metadata(
    frame_id: int,
    metadata_update: FrameMetadataUpdate,
    db: Session = Depends(get_db)
):
    """Update metadata for a specific frame."""
    frame_service = FrameService(db)
    frame = frame_service.update_frame_metadata(frame_id, metadata_update.metadata)
    
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")
    
    # Convert frame data to base64
    frame.frame_data = base64.b64encode(frame.frame_data).decode('utf-8')
    
    return frame

@router.delete("/old/{days}")
async def delete_old_frames(
    days: int,
    db: Session = Depends(get_db)
):
    """Delete frames older than specified days."""
    frame_service = FrameService(db)
    deleted_count = frame_service.delete_old_frames(days)
    return {"deleted_count": deleted_count} 