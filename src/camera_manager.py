from typing import Dict, List, Optional
import numpy as np
from loguru import logger
from .frame_capture import FrameCapture
from .utils import CameraConfig
import time
from collections import deque


class CameraManager:
    """Manages multiple camera instances."""

    def __init__(self):
        self.cameras: Dict[str, FrameCapture] = {}
        self._initialized = False
        self._running = False
        self._frame_times: Dict[str, deque] = (
            {}
        )  # Track frame times for FPS calculation
        self._fps_window = 30  # Number of frames to average FPS over
        self._last_error_time: Dict[str, float] = {}  # Track last error time per camera
        self._error_cooldown = 5.0  # Seconds to wait before retrying failed camera
        self._init_retries = 3  # Number of times to retry camera initialization
        self._init_retry_delay = 1.0  # Seconds to wait between retries
        self._failed_cameras: Dict[str, str] = (
            {}
        )  # Track failed cameras and their error messages

    def initialize_cameras(self, camera_configs: List[CameraConfig]) -> bool:
        """Initialize all enabled cameras."""
        try:
            # Clean up any existing cameras
            self.cleanup()

            # Initialize only enabled cameras
            success = False
            for config in camera_configs:
                if not config.enabled:
                    logger.info(f"Skipping disabled camera: {config.name}")
                    continue

                # Try to initialize camera with retries
                for attempt in range(self._init_retries):
                    try:
                        camera = FrameCapture(config)
                        if camera.initialize():
                            self.cameras[config.id] = camera
                            self._frame_times[config.id] = deque(
                                maxlen=self._fps_window
                            )
                            self._last_error_time[config.id] = 0
                            logger.info(
                                f"Initialized camera: {config.name} ({config.id})"
                            )
                            success = True
                            break
                        else:
                            error_msg = f"Failed to initialize camera: {config.name} (attempt {attempt + 1}/{self._init_retries})"
                            logger.warning(error_msg)
                            if attempt < self._init_retries - 1:
                                time.sleep(self._init_retry_delay)
                    except Exception as e:
                        error_msg = f"Error initializing camera {config.name}: {str(e)}"
                        logger.warning(
                            f"{error_msg} (attempt {attempt + 1}/{self._init_retries})"
                        )
                        if attempt < self._init_retries - 1:
                            time.sleep(self._init_retry_delay)
                else:
                    # All retries failed
                    self._failed_cameras[config.id] = error_msg
                    logger.error(
                        f"All initialization attempts failed for camera: {config.name}"
                    )

            if not self.cameras:
                logger.error("No cameras could be initialized")
                return False

            self._initialized = True
            return success

        except Exception as e:
            logger.error(f"Error in camera initialization: {e}")
            self.cleanup()
            return False

    def start(self) -> bool:
        """Start all cameras."""
        if not self._initialized:
            logger.error("Cameras not initialized")
            return False

        try:
            for camera_id, camera in self.cameras.items():
                if not camera.start():
                    logger.error(f"Failed to start camera: {camera_id}")
                    return False

            self._running = True
            return True

        except Exception as e:
            logger.error(f"Error starting cameras: {e}")
            return False

    def stop(self) -> bool:
        """Stop all cameras."""
        self._running = False
        for camera in self.cameras.values():
            camera.stop()
        return True

    def cleanup(self) -> None:
        """Clean up all camera resources."""
        self.stop()
        for camera in self.cameras.values():
            camera.cleanup()
        self.cameras.clear()
        self._frame_times.clear()
        self._last_error_time.clear()
        self._failed_cameras.clear()
        self._initialized = False
        self._running = False

    def get_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """Get a frame from a specific camera. Only update FPS if a new frame is captured."""
        if not self._running:
            return None

        camera = self.cameras.get(camera_id)
        if camera is None:
            logger.error(f"Camera not found: {camera_id}")
            return None

        try:
            prev_last_frame = camera._last_frame
            frame = camera.get_frame()
            # Only count as new if the returned frame is not the same object as the previous _last_frame
            if frame is not None and frame is not prev_last_frame:
                current_time = time.time()
                self._frame_times[camera_id].append(current_time)
                self._last_error_time[camera_id] = (
                    0  # Reset error time on successful frame
                )
            return frame

        except Exception as e:
            current_time = time.time()
            if (
                current_time - self._last_error_time.get(camera_id, 0)
                > self._error_cooldown
            ):
                logger.error(f"Error getting frame from camera {camera_id}: {e}")
                self._last_error_time[camera_id] = current_time
            return None

    def get_all_frames(self) -> Dict[str, Optional[np.ndarray]]:
        """Get frames from all cameras."""
        return {
            camera_id: self.get_frame(camera_id) for camera_id in self.cameras.keys()
        }

    def get_camera_status(self, camera_id: str) -> dict:
        """Get status information for a specific camera."""
        if camera_id not in self.cameras:
            if camera_id in self._failed_cameras:
                return {
                    "id": camera_id,
                    "error": self._failed_cameras[camera_id],
                    "status": "failed",
                }
            return {"error": "Camera not found"}

        camera = self.cameras[camera_id]
        frame_times = self._frame_times[camera_id]

        # Calculate FPS
        fps = 0
        if len(frame_times) >= 2:
            time_diff = frame_times[-1] - frame_times[0]
            if time_diff > 0:
                fps = (len(frame_times) - 1) / time_diff

        return {
            "id": camera_id,
            "name": camera.config.name,
            "location": camera.config.location_id,
            "zone": camera.config.zone_name,
            "type": camera.camera_type,
            "fps": round(fps, 1),
            "resolution": f"{camera.width}x{camera.height}",
            "running": camera.is_running,
            "error_time": self._last_error_time.get(camera_id, 0),
            "status": "active",
        }

    def get_all_status(self) -> Dict[str, dict]:
        """Get status information for all cameras."""
        status = {
            camera_id: self.get_camera_status(camera_id)
            for camera_id in self.cameras.keys()
        }
        # Add failed cameras to status
        status.update(
            {
                camera_id: self.get_camera_status(camera_id)
                for camera_id in self._failed_cameras.keys()
            }
        )
        return status

    @property
    def is_running(self) -> bool:
        """Check if cameras are running."""
        return self._running

    @property
    def camera_count(self) -> int:
        """Get the number of active cameras."""
        return len(self.cameras)

    @property
    def failed_camera_count(self) -> int:
        """Get the number of failed cameras."""
        return len(self._failed_cameras)
