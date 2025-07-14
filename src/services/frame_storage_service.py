from typing import Optional, Dict, Any
import base64
import cv2
import numpy as np
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.orm import Session
import redis
import json
import pickle
import os
from urllib.parse import urlparse

from src.database.models.base import get_db
from src.services.frame_service import FrameService

class FrameStorageService:
    """Service for storing frames with metadata."""
    
    def __init__(self):
        """Initialize the frame storage service."""
        self.db = next(get_db())
        self.frame_service = FrameService(self.db)
        
        # Initialize Redis connection from environment variable
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            parsed_url = urlparse(redis_url)
            
            self.redis_client = redis.Redis(
                host=parsed_url.hostname or 'localhost',
                port=parsed_url.port or 6379,
                db=int(parsed_url.path[1:]) if parsed_url.path else 0,
                decode_responses=False,  # Keep binary data as is
                socket_timeout=5,  # Add timeout
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            logger.info(f"Redis connection established at {redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
        
        # Cache configuration
        self.cache_ttl = int(os.getenv('REDIS_CACHE_TTL', '3600'))  # Default 1 hour
        self.cache_prefix = os.getenv('REDIS_CACHE_PREFIX', 'frame:')
        
        # Frame processing configuration
        self.target_width = int(os.getenv('FRAME_WIDTH', '320'))
        self.target_height = int(os.getenv('FRAME_HEIGHT', '240'))
        self.jpeg_quality = int(os.getenv('JPEG_QUALITY', '85'))
        
        logger.info("FrameStorageService initialized")
    
    def _compress_frame(self, frame: np.ndarray) -> bytes:
        """Compress frame to reduce storage size."""
        try:
            # Resize frame
            if frame.shape[1] > self.target_width or frame.shape[0] > self.target_height:
                frame = cv2.resize(frame, (self.target_width, self.target_height))
            
            # Encode as JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
            _, buffer = cv2.imencode('.jpg', frame, encode_param)
            return buffer.tobytes()
        except Exception as e:
            logger.error(f"Error compressing frame: {e}")
            raise

    def _decompress_frame(self, frame_data: bytes) -> np.ndarray:
        """Decompress frame data."""
        try:
            nparr = np.frombuffer(frame_data, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as e:
            logger.error(f"Error decompressing frame: {e}")
            raise

    def _get_cache_key(self, frame_id: int) -> str:
        """Generate Redis cache key for a frame."""
        return f"{self.cache_prefix}{frame_id}"

    def _cache_frame(self, frame_id: int, frame_data: dict):
        """Cache frame data in Redis."""
        if not self.redis_client:
            return
            
        try:
            cache_key = self._get_cache_key(frame_id)
            # Serialize frame data
            serialized_data = pickle.dumps(frame_data)
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                serialized_data
            )
            logger.debug(f"Cached frame {frame_id}")
        except redis.RedisError as e:
            logger.error(f"Redis error caching frame {frame_id}: {e}")
        except Exception as e:
            logger.error(f"Failed to cache frame {frame_id}: {e}")

    def _get_cached_frame(self, frame_id: int) -> Optional[dict]:
        """Retrieve frame data from Redis cache."""
        if not self.redis_client:
            return None
            
        try:
            cache_key = self._get_cache_key(frame_id)
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                # Deserialize frame data
                frame_data = pickle.loads(cached_data)
                logger.debug(f"Retrieved frame {frame_id} from cache")
                return frame_data
        except redis.RedisError as e:
            logger.error(f"Redis error retrieving frame {frame_id}: {e}")
        except Exception as e:
            logger.error(f"Failed to retrieve frame {frame_id} from cache: {e}")
        return None

    def store_processed_frame(
        self,
        frame: np.ndarray,
        camera_id: str,
        processing_metadata: dict,
        sequence_number: int = None
    ) -> int:
        """Store a processed frame with metadata.
        
        Args:
            frame: The processed frame as a numpy array
            camera_id: ID of the camera that captured the frame
            processing_metadata: Additional metadata from processing
            sequence_number: Optional sequence number (auto-incremented if not provided)
            
        Returns:
            The ID of the stored frame
        """
        try:
            # Compress frame
            compressed_data = self._compress_frame(frame)
            
            # Create frame data
            frame_data = {
                'frame_data': compressed_data,
                'camera_id': camera_id,
                'timestamp': datetime.utcnow(),
                'sequence_number': sequence_number,
                'metadata': processing_metadata
            }
            
            # Store in database
            frame_id = self.frame_service.store_frame(
                frame=compressed_data,
                sequence_number=sequence_number,
                metadata=processing_metadata
            )
            
            # Cache the frame
            self._cache_frame(frame_id, frame_data)
            
            logger.info(f"Stored frame {frame_id} from camera {camera_id}")
            return frame_id
            
        except Exception as e:
            logger.error(f"Error storing frame: {e}")
            raise
    
    def get_frame(self, frame_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a stored frame by ID."""
        try:
            # Try to get from cache first
            cached_frame = self._get_cached_frame(frame_id)
            if cached_frame:
                return cached_frame
                
            # If not in cache, get from database
            frame = self.frame_service.get_frame(frame_id)
            if frame:
                # Decompress frame
                frame_data = self._decompress_frame(frame.frame_data)
                frame_dict = {
                    "id": frame.id,
                    "sequence_number": frame.sequence_number,
                    "timestamp": frame.timestamp,
                    "frame_data": base64.b64encode(frame_data).decode('utf-8'),
                    "metadata": frame.frame_metadata
                }
                # Cache the frame
                self._cache_frame(frame_id, frame_dict)
                return frame_dict
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving frame {frame_id}: {e}")
            raise
    
    def get_frames_by_sequence(self, start: int, end: int) -> list:
        """Retrieve frames within a sequence range."""
        try:
            frames = self.frame_service.get_frames_by_sequence(start, end)
            result = []
            
            for frame in frames:
                # Try cache first
                cached_frame = self._get_cached_frame(frame.id)
                if cached_frame:
                    result.append(cached_frame)
                    continue
                    
                # If not in cache, process and cache
                frame_data = self._decompress_frame(frame.frame_data)
                frame_dict = {
                    "id": frame.id,
                    "sequence_number": frame.sequence_number,
                    "timestamp": frame.timestamp,
                    "frame_data": base64.b64encode(frame_data).decode('utf-8'),
                    "metadata": frame.frame_metadata
                }
                self._cache_frame(frame.id, frame_dict)
                result.append(frame_dict)
                
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving frames by sequence: {e}")
            raise
    
    def get_frames_by_timestamp(self, start_time: datetime, end_time: datetime) -> list:
        """Retrieve frames within a time range."""
        try:
            frames = self.frame_service.get_frames_by_timestamp(start_time, end_time)
            result = []
            
            for frame in frames:
                # Try cache first
                cached_frame = self._get_cached_frame(frame.id)
                if cached_frame:
                    result.append(cached_frame)
                    continue
                    
                # If not in cache, process and cache
                frame_data = self._decompress_frame(frame.frame_data)
                frame_dict = {
                    "id": frame.id,
                    "sequence_number": frame.sequence_number,
                    "timestamp": frame.timestamp,
                    "frame_data": base64.b64encode(frame_data).decode('utf-8'),
                    "metadata": frame.frame_metadata
                }
                self._cache_frame(frame.id, frame_dict)
                result.append(frame_dict)
                
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving frames by timestamp: {e}")
            raise
    
    def update_frame_metadata(self, frame_id: int, metadata: dict) -> bool:
        """Update metadata for a stored frame."""
        try:
            success = self.frame_service.update_frame_metadata(frame_id, metadata)
            if success:
                # Invalidate cache
                if self.redis_client:
                    self.redis_client.delete(self._get_cache_key(frame_id))
            return success
            
        except Exception as e:
            logger.error(f"Error updating frame metadata: {e}")
            raise
    
    def delete_old_frames(self, days: int) -> int:
        """Delete frames older than specified days."""
        try:
            count = self.frame_service.delete_old_frames(days)
            # Note: Cache will expire automatically
            return count
        except Exception as e:
            logger.error(f"Error deleting old frames: {e}")
            raise

    def cleanup(self):
        """Clean up resources."""
        try:
            if self.redis_client:
                self.redis_client.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}") 