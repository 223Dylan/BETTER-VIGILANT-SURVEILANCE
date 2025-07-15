import time
from typing import Dict, List, Optional, Tuple

import numpy as np
import tensorflow as tf
from loguru import logger
from tensorflow.keras.layers import (
    LSTM,
    Conv2D,
    Dense,
    Dropout,
    Flatten,
    Input,
    MaxPooling2D,
    TimeDistributed,
)
from tensorflow.keras.models import Model, Sequential

from .base import BaseComponent
from .model import load_model  # Import load_model from model.py


class LegacyLSTM(LSTM):
    """Custom LSTM layer that handles legacy parameters."""

    def __init__(self, *args, **kwargs):
        # Remove legacy parameters
        legacy_params = ["time_major", "unroll"]
        for param in legacy_params:
            kwargs.pop(param, None)
        super().__init__(*args, **kwargs)

    @classmethod
    def from_config(cls, config):
        # Remove legacy parameters from config
        legacy_params = ["time_major", "unroll"]
        for param in legacy_params:
            config.pop(param, None)
        return super().from_config(config)


class ModelHandler(BaseComponent):
    """Handles model loading and prediction for shoplifting detection."""

    def __init__(self, config=None):
        super().__init__(config)
        self.model: Optional[tf.keras.Model] = None
        self.model_path: str = self.get_config(
            "model.path", "model we use/lrcn_160S_90_90Q.h5"
        )
        self.input_shape: Tuple[int, int, int, int] = tuple(
            self.get_config("model.input_shape", [160, 90, 90, 1])
        )
        self.probability_thresholds: Dict[str, int] = self.get_config(
            "processing.probability_thresholds", {"low": 75, "medium": 85, "high": 90}
        )
        self._prediction_times = []
        self._last_prediction_time = 0
        self._prediction_function = None
        self._batch_size = 4  # Process multiple sequences at once
        self._sequence_queue: List[np.ndarray] = []
        self._prediction_queue: List[Tuple[float, int, str]] = []
        self._warmup_done = False
        self._last_stats_time = 0
        self._stats_interval = 1.0  # Update stats every second
        self._total_prediction_time = 0
        self._prediction_count = 0
        self._last_prediction_start = 0

    def initialize(self) -> bool:
        """Load and initialize the model."""
        try:
            logger.info(f"Loading model from {self.model_path}")

            # Use the load_model function from model.py (now includes custom objects)
            self.model = load_model(self.model_path)

            # Configure TensorFlow settings
            tf.config.optimizer.set_jit(True)  # Enable XLA compilation
            tf.config.optimizer.set_experimental_options(
                {
                    "layout_optimizer": True,
                    "constant_folding": True,
                    "shape_optimization": True,
                    "remapping": True,
                    "arithmetic_optimization": True,
                    "dependency_optimization": True,
                    "loop_optimization": True,
                    "function_optimization": True,
                    "debug_stripper": True,
                    "disable_model_pruning": False,
                    "scoped_allocator_optimization": True,
                    "pin_to_host_optimization": True,
                    "implementation_selector": True,
                    "auto_mixed_precision": True,
                }
            )

            # Enable memory growth to prevent TF from allocating all GPU memory
            gpus = tf.config.list_physical_devices("GPU")
            if gpus:
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)

            # Create a prediction function using tf.function for better performance
            @tf.function(jit_compile=True)
            def predict_function(x):
                return self.model(x, training=False)

            self._prediction_function = predict_function

            # Quick warm-up with a single batch
            logger.info("Warming up model...")
            dummy_input = np.zeros(
                (self._batch_size, *self.input_shape), dtype=np.float32
            )
            _ = self._prediction_function(dummy_input)
            self._warmup_done = True
            logger.info("Model warm-up completed")

            logger.info("Model loaded and optimized successfully")
            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.cleanup()
            return False

    def start(self) -> bool:
        """Start the model handler."""
        if not self._initialized:
            logger.error("Model not initialized")
            return False

        self._running = True
        self._sequence_queue.clear()
        self._prediction_queue.clear()
        self._last_stats_time = time.perf_counter()
        self._total_prediction_time = 0
        self._prediction_count = 0
        self._last_prediction_start = 0
        logger.info("Model handler started")
        return True

    def stop(self) -> bool:
        """Stop the model handler."""
        self._running = False
        logger.info("Model handler stopped")
        return True

    def cleanup(self) -> None:
        """Clean up model resources."""
        self.model = None
        self._initialized = False
        self._running = False
        self._sequence_queue.clear()
        self._prediction_queue.clear()
        self._warmup_done = False
        self._total_prediction_time = 0
        self._prediction_count = 0
        self._last_prediction_start = 0
        logger.info("Model resources cleaned up")

    def predict(self, sequence: np.ndarray) -> Tuple[float, int, str]:
        """Make prediction on a sequence of frames with performance tracking."""
        if not self._running or self.model is None:
            raise RuntimeError("Model handler not ready")

        try:
            # Add sequence to queue
            self._sequence_queue.append(sequence)

            # Process batch if queue is full
            if len(self._sequence_queue) >= self._batch_size:
                return self._process_batch()

            # Process single sequence if queue is not full
            return self._process_single(sequence)

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise

    def _process_batch(self) -> Tuple[float, int, str]:
        """Process a batch of sequences."""
        try:
            start_time = time.perf_counter()
            self._last_prediction_start = start_time

            # Prepare batch input
            batch_input = np.stack(self._sequence_queue)

            # Make predictions
            predictions = self._prediction_function(batch_input)

            # Process predictions
            results = []
            for pred in predictions:
                predicted_label = np.argmax(pred)
                probability = float(max(pred[0], pred[1]) * 100)
                message = self._generate_message(probability, predicted_label)
                results.append((probability, predicted_label, message))

            # Update timing stats
            prediction_time = time.perf_counter() - start_time
            avg_time = prediction_time / len(results)

            # Update total prediction time and count
            self._total_prediction_time += prediction_time
            self._prediction_count += len(results)

            # Only update stats periodically
            current_time = time.perf_counter()
            if current_time - self._last_stats_time >= self._stats_interval:
                if avg_time < 10:  # Only record if less than 10 seconds
                    self._prediction_times.append(avg_time)
                    if len(self._prediction_times) > 100:
                        self._prediction_times.pop(0)
                self._last_stats_time = current_time

            # Clear queue and return first result
            self._sequence_queue.clear()
            return results[0]

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            self._sequence_queue.clear()
            raise

    def _process_single(self, sequence: np.ndarray) -> Tuple[float, int, str]:
        """Process a single sequence."""
        try:
            start_time = time.perf_counter()
            self._last_prediction_start = start_time

            # Ensure sequence has correct shape
            if sequence.shape != self.input_shape:
                raise ValueError(
                    f"Invalid sequence shape. Expected {self.input_shape}, got {sequence.shape}"
                )

            # Prepare input tensor
            input_data = np.expand_dims(sequence, axis=0).astype(np.float32)

            # Make prediction
            predictions = self._prediction_function(input_data)[0]

            # Calculate prediction time
            prediction_time = time.perf_counter() - start_time

            # Update total prediction time and count
            self._total_prediction_time += prediction_time
            self._prediction_count += 1

            # Only update stats periodically
            current_time = time.perf_counter()
            if current_time - self._last_stats_time >= self._stats_interval:
                if prediction_time < 10:  # Only record if less than 10 seconds
                    self._prediction_times.append(prediction_time)
                    if len(self._prediction_times) > 100:
                        self._prediction_times.pop(0)
                self._last_stats_time = current_time

            # Extract prediction results
            predicted_label = np.argmax(predictions)
            probability = float(max(predictions[0], predictions[1]) * 100)

            # Create message
            message = self._generate_message(probability, predicted_label)

            return probability, predicted_label, message

        except Exception as e:
            logger.error(f"Single prediction failed: {e}")
            raise

    def get_prediction_stats(self) -> Dict:
        """Get prediction statistics."""
        try:
            # Calculate average prediction time
            avg_time = (
                sum(self._prediction_times) / len(self._prediction_times)
                if self._prediction_times
                else 0
            )
            # Convert to milliseconds, cap at 10s
            avg_time_ms = min(avg_time * 1000, 10000)

            return {
                "avg_prediction_time": avg_time_ms
                / 1000,  # Convert back to seconds for consistency
                "predictions_per_second": 1.0 / avg_time if avg_time > 0 else 0,
                "total_predictions": len(self._prediction_times),
            }
        except Exception as e:
            logger.error(f"Error getting prediction stats: {e}")
            return {
                "avg_prediction_time": 0,
                "predictions_per_second": 0,
                "total_predictions": 0,
            }

    def _generate_message(self, probability: float, label: int) -> str:
        """Generate human-readable message based on prediction."""
        if label == 0:  # Potential theft
            if probability <= self.probability_thresholds["low"]:
                return "There is little chance of theft"
            elif probability <= self.probability_thresholds["medium"]:
                return "High probability of theft"
            else:
                return "Very high probability of theft"
        else:  # Normal movement
            if probability <= self.probability_thresholds["low"]:
                return "The movement is confusing, watch"
            elif probability <= self.probability_thresholds["medium"]:
                return "I think it's normal, but it's better to watch"
            else:
                return "Movement is normal"

    def get_model_info(self) -> Dict:
        """Get model information."""
        if self.model is None:
            return {"status": "not_loaded"}

        return {
            "status": "loaded",
            "input_shape": self.input_shape,
            "output_shape": self.model.output_shape,
            "model_path": self.model_path,
            "batch_size": self._batch_size,
            "warmup_done": self._warmup_done,
        }
