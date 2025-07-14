import cv2
import numpy as np
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from src.database.models.frame import Frame
import json
from datetime import datetime, timedelta
from loguru import logger

class FrameService:
    def __init__(self, db: Session):
        """Initialize the frame service with a database session."""
        self.db = db
        logger.info("FrameService initialized")

    def _compress_frame(self, frame: np.ndarray) -> bytes:
        """Compress a frame using JPEG encoding."""
        success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            raise ValueError("Failed to compress frame")
        return buffer.tobytes()

    def _decompress_frame(self, frame_data: bytes) -> np.ndarray:
        """Decompress a frame from bytes to numpy array."""
        nparr = np.frombuffer(frame_data, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    def store_frame(self, frame: bytes, sequence_number: int = None, metadata: dict = None) -> int:
        """Store a frame in the database."""
        try:
            frame_record = Frame(
                frame_data=frame,
                sequence_number=sequence_number,
                timestamp=datetime.utcnow(),
                frame_metadata=metadata or {}
            )
            self.db.add(frame_record)
            self.db.commit()
            self.db.refresh(frame_record)
            logger.info(f"Stored frame {frame_record.id}")
            return frame_record.id
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing frame: {e}")
            raise

    def get_frame(self, frame_id: int) -> Optional[Frame]:
        """Get a frame by ID."""
        try:
            frame = self.db.query(Frame).filter(Frame.id == frame_id).first()
            if frame:
                logger.info(f"Retrieved frame {frame_id}")
            return frame
        except Exception as e:
            logger.error(f"Error retrieving frame {frame_id}: {e}")
            raise

    def get_frames_by_sequence(self, start: int, end: int) -> List[Frame]:
        """Get frames within a sequence range."""
        try:
            frames = self.db.query(Frame)\
                .filter(Frame.sequence_number >= start)\
                .filter(Frame.sequence_number <= end)\
                .order_by(Frame.sequence_number)\
                .all()
            logger.info(f"Retrieved {len(frames)} frames in sequence range {start}-{end}")
            return frames
        except Exception as e:
            logger.error(f"Error retrieving frames by sequence: {e}")
            raise

    def get_frames_by_timestamp(self, start_time: datetime, end_time: datetime) -> List[Frame]:
        """Get frames within a time range."""
        try:
            frames = self.db.query(Frame)\
                .filter(Frame.timestamp >= start_time)\
                .filter(Frame.timestamp <= end_time)\
                .order_by(Frame.timestamp)\
                .all()
            logger.info(f"Retrieved {len(frames)} frames in time range {start_time}-{end_time}")
            return frames
        except Exception as e:
            logger.error(f"Error retrieving frames by timestamp: {e}")
            raise

    def get_frames_batch(self, frame_ids: List[int]) -> List[Frame]:
        """Get multiple frames by their IDs in a single query."""
        try:
            frames = self.db.query(Frame)\
                .filter(Frame.id.in_(frame_ids))\
                .all()
            logger.info(f"Retrieved {len(frames)} frames in batch")
            return frames
        except Exception as e:
            logger.error(f"Error retrieving frames batch: {e}")
            raise

    def get_frames_by_sequence_batch(self, sequence_ranges: List[tuple]) -> Dict[int, List[Frame]]:
        """Get multiple sequence ranges in a single query."""
        try:
            result = {}
            for i, (start, end) in enumerate(sequence_ranges):
                frames = self.db.query(Frame)\
                    .filter(Frame.sequence_number >= start)\
                    .filter(Frame.sequence_number <= end)\
                    .order_by(Frame.sequence_number)\
                    .all()
                result[i] = frames
            logger.info(f"Retrieved {sum(len(frames) for frames in result.values())} frames in {len(sequence_ranges)} sequence ranges")
            return result
        except Exception as e:
            logger.error(f"Error retrieving frames by sequence batch: {e}")
            raise

    def get_frames_by_timestamp_batch(self, time_ranges: List[tuple]) -> Dict[int, List[Frame]]:
        """Get multiple time ranges in a single query."""
        try:
            result = {}
            for i, (start_time, end_time) in enumerate(time_ranges):
                frames = self.db.query(Frame)\
                    .filter(Frame.timestamp >= start_time)\
                    .filter(Frame.timestamp <= end_time)\
                    .order_by(Frame.timestamp)\
                    .all()
                result[i] = frames
            logger.info(f"Retrieved {sum(len(frames) for frames in result.values())} frames in {len(time_ranges)} time ranges")
            return result
        except Exception as e:
            logger.error(f"Error retrieving frames by timestamp batch: {e}")
            raise

    def update_frame_metadata(self, frame_id: int, metadata: dict) -> bool:
        """Update metadata for a frame."""
        try:
            frame = self.db.query(Frame).filter(Frame.id == frame_id).first()
            if frame:
                frame.frame_metadata.update(metadata)
                self.db.commit()
                logger.info(f"Updated metadata for frame {frame_id}")
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating frame metadata: {e}")
            raise

    def delete_old_frames(self, days: int) -> int:
        """Delete frames older than specified days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            result = self.db.query(Frame)\
                .filter(Frame.timestamp < cutoff_date)\
                .delete()
            self.db.commit()
            logger.info(f"Deleted {result} frames older than {days} days")
            return result
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting old frames: {e}")
            raise

    def get_latest_frames(self, limit: int = 10) -> List[Frame]:
        """Get the most recent frames."""
        try:
            frames = self.db.query(Frame)\
                .order_by(desc(Frame.timestamp))\
                .limit(limit)\
                .all()
            logger.info(f"Retrieved {len(frames)} latest frames")
            return frames
        except Exception as e:
            logger.error(f"Error retrieving latest frames: {e}")
            raise

    def get_frame_count(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> int:
        """Get total count of frames, optionally filtered by time range."""
        try:
            query = self.db.query(Frame)
            if start_time:
                query = query.filter(Frame.timestamp >= start_time)
            if end_time:
                query = query.filter(Frame.timestamp <= end_time)
            count = query.count()
            logger.info(f"Retrieved frame count: {count}")
            return count
        except Exception as e:
            logger.error(f"Error getting frame count: {e}")
            raise 