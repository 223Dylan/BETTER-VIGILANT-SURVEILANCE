import multiprocessing
import time
import cv2
import numpy as np
from loguru import logger
from src.camera_manager import CameraManager
from src.frame_processor import FrameProcessor
from src.tasks import celery_predict
from src.utils import CameraConfig
from src.utils.config import load_config


class CameraPipelineProcess(multiprocessing.Process):
    """Process for handling camera pipeline."""

    def __init__(self, camera_config: CameraConfig, shared_data: dict):
        super().__init__()
        self.camera_config = camera_config
        self.shared_data = shared_data
        self.camera_manager = None
        self.frame_processor = None
        self._stop_event = multiprocessing.Event()
        self._last_frame_time = time.time()
        self._min_frame_interval = 1.0 / self.camera_config.fps
        self._last_prediction_check = time.time()
        self._prediction_check_interval = 0.5

    def run(self):
        """Run the camera pipeline process."""
        try:
            # Load global configuration from config.yaml
            global_config = load_config("config/config.yaml")

            # Initialize components
            self.camera_manager = CameraManager()
            if not self.camera_manager.initialize_cameras([self.camera_config]):
                logger.error(f"Failed to initialize camera {self.camera_config.id}")
                return

            # Use global config from config.yaml combined with camera-specific settings from database
            preprocessing_config = global_config.get("preprocessing", {}).copy()

            # Override global brightness with individual camera brightness if available
            if (
                hasattr(self.camera_config, "preprocessing")
                and self.camera_config.preprocessing
            ):
                if "brightness" in self.camera_config.preprocessing:
                    preprocessing_config["brightness"] = (
                        self.camera_config.preprocessing["brightness"]
                    )

            model_params = {
                "model": global_config.get("model", {}),
                "camera": {"fps": self.camera_config.fps, "id": self.camera_config.id},
                "preprocessing": preprocessing_config,
                "processing": global_config.get("processing", {}),
            }

            logger.info(
                f"Using global config for camera {self.camera_config.id}: preprocessing={model_params['preprocessing']}"
            )

            self.frame_processor = FrameProcessor(model_params)
            if not self.frame_processor.initialize():
                logger.error(
                    f"Failed to initialize frame processor for {self.camera_config.id}"
                )
                return

            if not self.camera_manager.start() or not self.frame_processor.start():
                logger.error(f"Failed to start components for {self.camera_config.id}")
                return

            logger.info(f"Camera pipeline started for {self.camera_config.id}")

            while not self._stop_event.is_set():
                current_time = time.time()
                elapsed = current_time - self._last_frame_time

                if elapsed < self._min_frame_interval:
                    time.sleep(self._min_frame_interval - elapsed)
                    continue

                frame = self.camera_manager.get_frame(self.camera_config.id)

                if frame is not None:
                    self._handle_frame(frame)
                else:
                    if self.camera_config.id in self.shared_data["frames"]:
                        self.shared_data["frames"][self.camera_config.id] = None

                self._last_frame_time = current_time

        except Exception as e:
            logger.error(
                f"Fatal error in camera pipeline for {self.camera_config.id}: {e}",
                exc_info=True,
            )
        finally:
            self.cleanup()

    def _handle_frame(self, frame: np.ndarray):
        """Handle processing and streaming of a single frame."""
        # Stream frame via manager
        from src.api.video_stream import stream_manager

        if stream_manager:
            success, buffer = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85]
            )
            if success:
                stream_manager.process_frame(self.camera_config.id, buffer.tobytes())

        # Store for other uses
        self.shared_data["frames"][self.camera_config.id] = frame

        # Process for predictions
        if self.frame_processor:
            self.frame_processor.process_frame(frame)
            self._check_and_trigger_predictions()

        # Update stats
        if self.camera_config.id in self.shared_data["stats"]:
            stats = self.shared_data["stats"][self.camera_config.id]
            stats["fps"] = self.camera_manager.get_stats(self.camera_config.id)["fps"]
            stats["processing_fps"] = self.frame_processor.get_stats()["processing_fps"]
            self.shared_data["stats"][self.camera_config.id] = stats

        # Check for brightness update commands
        self._check_brightness_updates()

    def _check_and_trigger_predictions(self):
        """Check if sequence is ready and trigger prediction via Celery."""
        try:
            # Check if sequence is ready
            if not self.frame_processor.is_sequence_ready():
                return

            logger.info(f"[SEQUENCE] SEQUENCE READY for {self.camera_config.id}")

            # Get the sequence and validate
            sequence = self.frame_processor.get_sequence()
            if sequence is None or len(sequence) == 0:
                logger.error(
                    f"[ERROR] Failed to get sequence for {self.camera_config.id}"
                )
                return

            arr = np.array(sequence)
            logger.info(
                f"[SEQUENCE] SEQUENCE STATS for {self.camera_config.id}: shape={arr.shape}, mean={arr.mean():.4f}, std={arr.std():.4f}"
            )

            if arr.std() < 0.001:
                logger.warning(
                    f"[WARNING] SEQUENCE APPEARS TO BE EMPTY/ZEROS for {self.camera_config.id}"
                )

            logger.info(
                f"[PREDICTION] TRIGGERING PREDICTION for {self.camera_config.id}"
            )

            # Create task data with camera_id embedded
            task_data = {
                "sequence": arr.tolist(),
                "camera_id": self.camera_config.id,
                "timestamp": time.time(),
            }

            # Send as single parameter to maintain backward compatibility
            task = celery_predict.delay(task_data)
            logger.info(
                f"[TASK] PREDICTION TASK SENT to Celery: {task.id} for camera {self.camera_config.id}"
            )

            if "prediction_tasks" not in self.shared_data:
                self.shared_data["prediction_tasks"] = {}
            self.shared_data["prediction_tasks"][self.camera_config.id] = task.id

        except Exception as e:
            logger.error(
                f"[ERROR] ERROR triggering prediction for {self.camera_config.id}: {e}"
            )

    def _check_brightness_updates(self):
        """Check for and apply brightness update commands."""
        try:
            # Check shared data for brightness update commands
            command_key = f"brightness_update_{self.camera_config.id}"
            if command_key in self.shared_data:
                new_brightness = self.shared_data.pop(
                    command_key
                )  # Remove after reading
                if self.frame_processor:
                    success = self.frame_processor.update_brightness(new_brightness)
                    if success:
                        logger.info(
                            f"Applied brightness update: {new_brightness} for {self.camera_config.id}"
                        )
                    else:
                        logger.error(
                            f"Failed to apply brightness update for {self.camera_config.id}"
                        )
        except Exception as e:
            logger.error(
                f"Error checking brightness updates for {self.camera_config.id}: {e}"
            )

    def stop(self):
        """Stop the camera pipeline process."""
        self._stop_event.set()

    def cleanup(self):
        """Clean up resources."""
        logger.info(f"Cleaning up camera pipeline for {self.camera_config.id}")
        if self.frame_processor:
            self.frame_processor.stop()
        if self.camera_manager:
            self.camera_manager.stop()
        logger.info(f"Camera pipeline cleanup complete for {self.camera_config.id}")
