import sys
import time
from collections import deque
from typing import Optional, Tuple

import cv2
import numpy as np
from loguru import logger

from src.utils import CameraConfig

from .base import BaseComponent


class FrameCapture(BaseComponent):
    """Handles frame capture from camera."""

    def __init__(self, config: CameraConfig):
        super().__init__(config)
        self.camera: Optional[cv2.VideoCapture] = None
        self.config = config
        self.camera_type = config.camera_type
        self.source = config.source
        self.width = config.resolution_width
        self.height = config.resolution_height
        self.fps = config.fps
        self.buffer_size = getattr(config, "buffer_size", 160)
        self._last_frame_time = 0
        self._frame_count = 0
        self._start_time = 0
        self._last_frame = None
        self._frame_timeout = 1.0  # 1 second timeout for frame read
        self._min_frame_interval = 1.0 / self.fps  # Minimum time between frames

        # Video file specific attributes
        self._is_video_file = False
        self._video_frame_count = 0
        self._total_video_frames = 0

        # Performance monitoring
        self._read_times = deque(maxlen=100)  # Track last 100 read times
        self._last_stats_time = time.time()
        self._frames_captured = 0

    def initialize(self) -> bool:
        """Initialize the camera."""
        try:
            # Release any existing camera
            if self.camera is not None:
                self.camera.release()

            # Initialize camera based on type
            if self.camera_type == "usb":
                # Prefer Windows-friendly backends with graceful fallback
                self.camera = self._open_usb_camera(self.source)
            elif self.camera_type == "ip":
                self.camera = cv2.VideoCapture(str(self.source))
            elif self.camera_type == "file":
                # For video files, use the file path directly
                self.camera = cv2.VideoCapture(str(self.source))
                # For video files, we want to loop the video when it ends
                self._is_video_file = True
                self._video_frame_count = 0
                self._total_video_frames = int(
                    self.camera.get(cv2.CAP_PROP_FRAME_COUNT)
                )
                logger.info(
                    f"Video file loaded: {self.source} ({self._total_video_frames} frames)"
                )
            else:
                logger.error(f"Unknown camera type: {self.camera_type}")
                return False

            if not self.camera.isOpened():
                logger.error(f"Failed to open camera source: {self.source}")
                return False

            # Set only essential camera properties, safely (some backends ignore/err)
            self._safe_set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self._safe_set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            # Setting FPS and BUFFERSIZE can be flaky on Windows backends; do it best-effort
            self._safe_set(cv2.CAP_PROP_FPS, self.fps)
            self._safe_set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Verify camera settings
            actual_width = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)

            logger.info(
                f"Camera initialized: {int(actual_width)}x{int(actual_height)} @ {actual_fps:.1f}fps (type: {self.camera_type}, source: {self.source})"
            )

            # Warm up the camera and read a test frame to ensure camera is working
            self._warmup_camera(num_frames=5, delay_seconds=0.05)
            ret, frame = self.camera.read()
            if not ret or frame is None:
                logger.error("Failed to read test frame from camera")
                return False

            self._start_time = time.time()
            self._initialized = True  # Set initialized flag
            return True

        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            self._initialized = False  # Ensure initialized flag is False on error
            return False

    def _open_usb_camera(self, source) -> Optional[cv2.VideoCapture]:
        """Open a USB camera with backend fallbacks that work better on Windows.

        Order: DirectShow -> MSMF -> ANY
        """
        backends_to_try = (
            [
                cv2.CAP_DSHOW,
                cv2.CAP_MSMF,
                cv2.CAP_ANY,
            ]
            if sys.platform == "win32"
            else [cv2.CAP_ANY]
        )

        # Normalize source to int index if possible
        index_or_path = None
        try:
            index_or_path = int(source)
        except (ValueError, TypeError):
            index_or_path = str(source)

        for backend in backends_to_try:
            try:
                cap = (
                    cv2.VideoCapture(index_or_path, backend)
                    if isinstance(index_or_path, int)
                    else cv2.VideoCapture(index_or_path, backend)
                )
                if cap.isOpened():
                    logger.info(f"Opened USB camera using backend={backend}")
                    return cap
                cap.release()
            except Exception as backend_err:
                logger.debug(f"Backend {backend} failed to open camera: {backend_err}")

        # Last resort: try default constructor once more
        cap = (
            cv2.VideoCapture(index_or_path)
            if isinstance(index_or_path, int)
            else cv2.VideoCapture(index_or_path)
        )
        return cap

    def _warmup_camera(self, num_frames: int = 3, delay_seconds: float = 0.03) -> None:
        """Read and discard a few frames to allow auto-exposure/focus to settle."""
        try:
            for _ in range(max(0, num_frames)):
                _ = self.camera.read()
                if delay_seconds > 0:
                    time.sleep(delay_seconds)
        except Exception:
            # Non-fatal; simply proceed
            pass

    def _safe_set(self, prop: int, value: float) -> None:
        """Attempt to set a camera property; ignore failures but log at debug."""
        try:
            ok = self.camera.set(prop, value)
            if not ok:
                logger.debug(
                    f"Camera property set ignored/failed: prop={prop}, value={value}"
                )
        except Exception as set_err:
            logger.debug(
                f"Camera property set error: prop={prop}, value={value}, err={set_err}"
            )

    def start(self) -> bool:
        """Start frame capture."""
        if not self._initialized or self.camera is None:
            logger.error("Camera not initialized")
            return False

        self._running = True
        self._frame_count = 0
        self._start_time = time.time()
        logger.info("Frame capture started")
        return True

    def stop(self) -> bool:
        """Stop frame capture."""
        self._running = False
        logger.info("Frame capture stopped")
        return True

    def cleanup(self) -> None:
        """Clean up camera resources."""
        if self.camera is not None:
            self.camera.release()
            self.camera = None
        self._initialized = False
        self._running = False
        logger.info("Camera resources cleaned up")

    def get_frame(self) -> Optional[np.ndarray]:
        """Get a frame from the camera. Returns the frame if available, or None. Only increments frame count for new frames."""
        if not self._running or self.camera is None:
            return None

        try:
            current_time = time.time()
            # Check if we need to drop this frame
            elapsed_since_last = current_time - self._last_frame_time
            if elapsed_since_last < self._min_frame_interval:
                # Sleep for the remaining time to enforce FPS
                time.sleep(self._min_frame_interval - elapsed_since_last)
                current_time = time.time()

            # Read frame with timeout
            start_read = time.time()
            ret, frame = self.camera.read()
            read_time = time.time() - start_read
            self._read_times.append(read_time)
            self._frames_captured += 1

            # Log performance stats every 5 seconds (reduced from 1 second)
            if current_time - self._last_stats_time >= 5.0:
                avg_read_time = sum(self._read_times) / len(self._read_times)
                fps = self._frames_captured / (current_time - self._last_stats_time)
                logger.debug(
                    f"Camera stats - FPS: {fps:.1f}, Avg read time: {avg_read_time*1000:.1f}ms"
                )  # Changed to debug level
                self._frames_captured = 0
                self._last_stats_time = current_time

            if read_time > self._frame_timeout:
                logger.warning(f"Frame read timeout: {read_time:.2f}s")
                return self._last_frame

            if not ret or frame is None:
                # If this is a video file and we've reached the end, loop back to beginning
                if (
                    self._is_video_file
                    and self._video_frame_count >= self._total_video_frames - 1
                ):
                    logger.debug(f"Video file reached end, looping back to beginning")
                    self.camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self._video_frame_count = 0
                    ret, frame = self.camera.read()

                if not ret or frame is None:
                    logger.warning("Failed to read frame from camera/video file")
                    return self._last_frame

            # New frame captured successfully
            self._frame_count += 1
            self._last_frame_time = current_time
            self._last_frame = frame.copy()  # Make a copy to prevent memory issues

            # Increment video frame counter for video files
            if self._is_video_file:
                self._video_frame_count += 1

            # Calculate actual FPS
            elapsed = current_time - self._start_time
            if elapsed > 0:
                actual_fps = self._frame_count / elapsed
                if actual_fps < self.fps * 0.5:  # If FPS is less than 50% of target
                    logger.warning(
                        f"Low FPS detected: {actual_fps:.1f} (target: {self.fps})"
                    )
                    logger.debug(f"Frame read time: {read_time*1000:.1f}ms")

            return frame

        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
            return self._last_frame

    def get_stats(self) -> dict:
        """Get frame capture statistics."""
        if not self._initialized:
            return {"fps": 0, "frame_count": 0}

        current_time = time.time()
        elapsed = current_time - self._start_time
        fps = self._frame_count / elapsed if elapsed > 0 else 0

        return {"fps": fps, "frame_count": self._frame_count}
