import threading
import time
from collections import deque
from queue import Empty, Full, Queue
from threading import Event, Thread
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from loguru import logger

from src.detection_metrics import log_camera_health_metrics, log_system_metrics
from src.services.frame_storage_service import FrameStorageService

from .base import BaseComponent
from .utils import resize_frame


class FrameProcessor(BaseComponent):
    """Processes and buffers frames for model prediction.
    Per-camera preprocessing options (from config):
      - preprocessing.grayscale: bool (default True)
      - preprocessing.crop: [x, y, w, h] (crop rectangle before resize)
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.sequence_length = config.get("model", {}).get("sequence_length", 160)
        frame_size = config.get("model", {}).get("frame_size", 90)
        # Support list or integer frame_size
        self.frame_size = frame_size[0] if isinstance(frame_size, list) else frame_size
        self.lock = threading.Lock()
        self.running = False
        self.processing_thread = None
        self.last_processed_time = time.time()
        self.fps_target = config.get("camera", {}).get("fps", 30)
        self.fps_window = 10  # Window size for FPS calculation
        self.fps_history = deque(maxlen=self.fps_window)

        # Use notebook's fixed preprocessing approach - no configuration needed
        # The preprocessing steps are: frame_diff -> blur -> resize -> grayscale -> normalize

        # Performance optimization flags
        self.use_gpu = config.get("processing", {}).get("use_gpu", False)
        self.skip_frames = config.get("processing", {}).get("skip_frames", 0)
        self.frame_counter = 0

        # Initialize OpenCV optimizations
        cv2.setUseOptimized(True)
        cv2.ocl.setUseOpenCL(self.use_gpu)

        # Pre-allocate sequence buffer for better performance
        self.sequence_buffer = np.zeros(
            (self.sequence_length, self.frame_size, self.frame_size, 1),
            dtype=np.float32,
        )
        self.buffer_position = 0  # Track position in sequence buffer
        self.sequence_complete = False  # Track if we have a complete sequence
        self.frames_collected = 0  # Track total frames collected

        # Add frame queue for processing with larger maxlen
        self.frame_queue = deque(
            maxlen=10
        )  # Increased from 5 to 10 to prevent frame drops

        # Pre-allocate frame buffers for better performance
        self.frame_buffer = Queue(maxsize=self.sequence_length)
        self.processed_frames = Queue(maxsize=self.sequence_length)

        # Add frame dropping logic - reduce queue size for faster processing
        self.max_queue_size = 20  # Reduced from 50 to 20 for faster sequence building
        self.drop_frames = True  # Enable frame dropping when queue is full

        # Performance monitoring
        self.processing_times = []
        self.total_frames_processed = 0
        self.start_time = None

        # Initialize frame storage service
        # self.frame_storage = FrameStorageService()  # Temporarily disabled to test predictions
        self.camera_id = config.get("camera", {}).get("id", "local-webcam")

        # Initialize previous frame for background removal
        self._previous_frame = None

        logger.info(
            f"FrameProcessor initialized with sequence length {self.sequence_length}"
        )
        logger.info(
            f"Using notebook's preprocessing: frame_diff -> blur(3x3) -> resize -> grayscale -> normalize"
        )

    def initialize(self) -> bool:
        """Initialize the frame processor."""
        try:
            # Reset all buffers and counters
            self.sequence_buffer.fill(0)
            self.buffer_position = 0
            self.sequence_complete = False
            self.fps_history.clear()
            self.frame_counter = 0
            self.total_frames_processed = 0
            self.start_time = None
            self.processing_times = []

            # Reset previous frame for background removal
            self._previous_frame = None

            # Initialize frame queue
            self.frame_queue.clear()

            # Set initialized flag
            self._initialized = True

            logger.info(
                f"FrameProcessor initialized with sequence length {self.sequence_length} and frame size {self.frame_size}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize frame processor: {e}")
            self._initialized = False
            return False

    def start(self) -> bool:
        """Start the frame processor."""
        if not self._initialized:
            logger.error("Frame processor not initialized")
            return False

        self.running = True
        self.processing_thread = Thread(target=self._process_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        self.start_time = time.time()
        logger.info("Frame processor started")
        return True

    def stop(self) -> bool:
        """Stop the frame processor."""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join()
        logger.info("Frame processor stopped")
        return True

    def cleanup(self) -> None:
        """Clean up frame processor resources."""
        self.stop()
        self.sequence_buffer.fill(0)
        self.buffer_position = 0
        self.fps_history.clear()
        self._initialized = False
        logger.info("FrameProcessor cleaned up")

    def _process_loop(self):
        """Main processing loop."""
        logger.info("Starting frame processing loop")

        while self.running:
            try:
                # Get frame from buffer with shorter timeout for faster processing
                frame = self.frame_buffer.get(
                    timeout=0.05
                )  # Reduced from 0.1 to 0.05 for faster processing

                # Process frame
                start_time = time.time()
                processed_frame = self._process_frame(frame)
                processing_time = time.time() - start_time

                # Update performance tracking
                self.processing_times.append(processing_time)
                if len(self.processing_times) > 10:
                    self.processing_times.pop(0)
                self.total_frames_processed += 1

                # Calculate performance metrics
                avg_processing_time = (
                    sum(self.processing_times) / len(self.processing_times)
                    if self.processing_times
                    else 0
                )
                processing_fps = (
                    1.0 / avg_processing_time if avg_processing_time > 0 else 0
                )

                # Log performance stats with corrected sequence count
                with self.lock:
                    current_sequence_count = self.frames_collected

                if (
                    self.total_frames_processed % 100 == 0
                ):  # Reduced from 20 to 100 frames
                    logger.debug(
                        f"Performance stats - FPS: {processing_fps:.1f}, Avg processing time: {avg_processing_time*1000:.1f}ms"
                    )
                    logger.debug(
                        f"Processing stats - FPS: {processing_fps:.1f}, Queue: {current_sequence_count}/{self.sequence_length}, Total frames: {self.total_frames_processed}"
                    )

            except Empty:
                # Normal timeout when no frames are available - don't log as error
                continue
            except Exception as e:
                # Log other genuine errors
                logger.error(f"Error in processing loop: {type(e).__name__}: {e}")
                time.sleep(0.1)

    def _process_frame(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Process a single frame using the exact preprocessing from the notebook."""
        try:
            # Step 1: Frame differencing (background subtraction)
            if self._previous_frame is not None:
                # Use frame differencing as in the notebook
                diff = cv2.absdiff(frame, self._previous_frame)
            else:
                # For the first frame, use the original frame
                diff = frame.copy()

            # Update previous frame for next iteration
            self._previous_frame = frame.copy()

            # Step 2: Gaussian blur (exactly as in notebook: kernel (3,3), sigma 0)
            diff = cv2.GaussianBlur(diff, (3, 3), 0)

            # Step 3: Resize (exactly as in notebook: to frame_height, frame_width)
            resized_frame = cv2.resize(diff, (self.frame_size, self.frame_size))

            # Step 4: Convert to grayscale (exactly as in notebook)
            gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)

            # Step 5: Normalize (exactly as in notebook: divide by 255)
            normalized_frame = gray_frame / 255.0

            # Reshape for model input (add channel dimension)
            normalized_frame = normalized_frame.reshape(
                self.frame_size, self.frame_size, 1
            ).astype(np.float32)

            # Store in sequence buffer
            with self.lock:
                if self.sequence_complete:
                    return

                self.sequence_buffer[self.buffer_position] = normalized_frame
                self.frames_collected += 1
                self.buffer_position += 1

                # Check if sequence is complete
                if self.frames_collected == self.sequence_length:
                    self.sequence_complete = True
                    self.buffer_position = 0

            return True

        except Exception as e:
            logger.error(f"Error processing frame: {str(e)}")
            return None

    def process_frame(self, frame: np.ndarray) -> bool:
        """Add a frame to the processing queue."""
        if not self.running:
            return False
        try:
            if frame is None:
                logger.warning("Received None frame")
                return False

            # Note: Streaming injection now handled directly in camera pipeline

            # Frame dropping logic
            if self.drop_frames and self.frame_buffer.qsize() >= self.max_queue_size:
                # Drop oldest frame if queue is full
                self.frame_buffer.get_nowait()
                logger.debug("Dropped frame due to queue being full")

            # Make a copy of the frame to prevent memory issues
            frame_copy = frame.copy()
            self.frame_buffer.put(frame_copy)

            if self.frame_buffer.qsize() % 10 == 0:  # Log every 10 frames
                # Get sequence count safely with lock
                with self.lock:
                    current_sequence_count = self.frames_collected
                logger.info(
                    f"Queue status: {self.frame_buffer.qsize()}/{self.max_queue_size} frames (Sequence: {current_sequence_count}/{self.sequence_length})"
                )
            return True
        except Exception as e:
            logger.error(f"Error adding frame to queue: {e}")
            return False

    def is_sequence_ready(self) -> bool:
        """Check if we have a complete sequence ready for prediction."""
        with self.lock:
            return self.sequence_complete

    def get_sequence(self) -> Optional[np.ndarray]:
        """Get the current sequence for prediction."""
        with self.lock:
            if not self.sequence_complete:
                return None

            # Log before clearing
            logger.info(
                f"[SEQUENCE] RETRIEVING SEQUENCE: {self.frames_collected} frames, clearing buffer for next cycle"
            )

            # Make a copy of the sequence buffer before clearing
            sequence_copy = self.sequence_buffer.copy()

            # Reset sequence state for next 160-frame collection
            self.sequence_complete = False
            self.frames_collected = 0
            self.buffer_position = 0
            self.sequence_buffer.fill(0)  # Clear the buffer

            logger.info(f"BUFFER RESET: Ready for next {self.sequence_length} frames")

            # Return a copy of the sequence buffer
            return sequence_copy

    def update_brightness(self, new_brightness: float) -> bool:
        """Brightness adjustment not supported in notebook preprocessing mode."""
        logger.warning(
            f"Brightness adjustment not supported in notebook preprocessing mode for {self.camera_id}"
        )
        return False

    def get_stats(self) -> dict:
        """Get frame processing statistics."""
        try:
            if not self.fps_history:
                return {
                    "avg_processing_time": 0,
                    "processing_fps": 0,
                    "buffer_position": self.buffer_position,
                }

            avg_time = sum(self.fps_history) / len(self.fps_history)
            return {
                "avg_processing_time": avg_time,
                "processing_fps": 1.0 / avg_time if avg_time > 0 else 0,
                "buffer_position": self.buffer_position,
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"avg_processing_time": 0, "processing_fps": 0, "buffer_position": 0}
