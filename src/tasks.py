import logging
import os
import time

import numpy as np
from celery import Celery

from src.detection_metrics import log_prediction_metrics
from src.model import load_model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery app
app = Celery("shoplifting_detection")

# Load configuration
app.config_from_object("celeryconfig")

# Get the model path from environment or use default
MODEL_PATH = os.getenv("MODEL_PATH", "models/lrcn_160S_90_90Q.h5")

# Load model globally
model = None


@app.task(name="shoplifting_detection.predict_sequence", bind=True, max_retries=3)
def predict_sequence(self, sequence_data):
    """Predict shoplifting probability for a sequence of frames."""
    global model

    try:
        # Support both old and new task formats
        if isinstance(sequence_data, dict) and "sequence" in sequence_data:
            # New format with embedded camera_id
            sequence = np.array(sequence_data["sequence"])
            camera_id = sequence_data.get("camera_id", "unknown")
            task_timestamp = sequence_data.get("timestamp", time.time())
            logger.info(f"Processing NEW FORMAT task for camera {camera_id}")
        else:
            sequence = np.array(sequence_data)
            camera_id = None
            task_timestamp = time.time()
            logger.info(f"Processing OLD FORMAT task (no camera_id)")

        # Log sequence processing details
        logger.info(
            f"Processing sequence of shape {sequence.shape} for camera {camera_id}"
        )

        # Analyze sequence data quality
        seq_mean = sequence.mean()
        seq_std = sequence.std()
        seq_min = sequence.min()
        seq_max = sequence.max()
        logger.info(
            f"[STATS] WORKER RECEIVED SEQUENCE: mean={seq_mean:.4f}, std={seq_std:.4f}, min={seq_min:.4f}, max={seq_max:.4f}"
        )

        # Compare first and last frames
        if sequence.shape[0] >= 2:
            first_frame_mean = sequence[0].mean()
            last_frame_mean = sequence[-1].mean()
            logger.info(
                f"[ANALYSIS] FRAME VARIATION: first_frame_mean={first_frame_mean:.4f}, last_frame_mean={last_frame_mean:.4f}"
            )

        # Data quality checks
        if seq_std < 0.001:
            logger.warning(
                "[WARNING] WORKER WARNING: Sequence appears to have no variation (std < 0.001)"
            )
        elif np.allclose(sequence[0], sequence[-1]):
            logger.warning(
                "[WARNING] WORKER WARNING: First and last frames are identical - possible repeated data"
            )

        # Load model if needed
        if model is None:
            logger.info(f"Loading model from {MODEL_PATH}")
            if not os.path.exists(MODEL_PATH):
                raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
            model = load_model(model_path=MODEL_PATH)

        # Make prediction (verbose=0 to suppress progress bar warnings)
        prediction = model.predict(np.expand_dims(sequence, axis=0), verbose=0)[0]
        logger.info(f"Raw prediction shape: {prediction.shape}")

        # For binary classification with two outputs
        if prediction.shape == (2,):
            # Get probability of shoplifting (second class)
            probability = float(prediction[1])
            label = int(prediction[1] > 0.5)
        else:
            # Fallback for other output formats
            probability = float(np.max(prediction))
            label = int(np.argmax(prediction))

        # Record processing time
        processing_time = time.time() - task_timestamp

        # Format prediction result
        result = {
            "is_shoplifting": bool(label == 1),
            "confidence": probability,
            "label": label,
            "camera_id": camera_id,
            "timestamp": time.time(),
            "task_timestamp": task_timestamp,
            "sequence_stats": {
                "mean": float(seq_mean),
                "std": float(seq_std),
                "frames": sequence.shape[0],
            },
            "sequence_length": sequence.shape[0],
        }

        logger.info(f"[PREDICTION] Prediction result for {camera_id}: {result}")

        # Log detection metrics for ELK stack
        if camera_id and camera_id != "unknown":
            try:
                log_prediction_metrics(
                    camera_id=camera_id,
                    prediction_result=result,
                    processing_time=processing_time,
                    performance_data={
                        "sequence_stats": result["sequence_stats"],
                        "prediction_shape": list(prediction.shape),
                        "model_loaded": model is not None,
                    },
                )
                logger.info(
                    f"[SUCCESS] Logged detection metrics for camera {camera_id}"
                )
            except Exception as e:
                logger.error(
                    f"[ERROR] Failed to log detection metrics for {camera_id}: {e}"
                )

        # Route prediction to WebSocket if camera_id is available
        if camera_id and camera_id != "unknown":
            try:
                # Import here to avoid circular imports
                from src.prediction_router import route_prediction_to_websocket

                route_prediction_to_websocket(camera_id, result)
                logger.info(
                    f"[SUCCESS] Successfully routed prediction to WebSocket for camera {camera_id}"
                )
            except Exception as e:
                logger.error(
                    f"[ERROR] Failed to route prediction to WebSocket for {camera_id}: {e}"
                )
        else:
            logger.warning(
                f"[WARNING] No camera_id provided, skipping WebSocket routing"
            )

        return result

    except Exception as e:
        logger.error(f"[ERROR] Error processing sequence: {str(e)}")
        # Retry the task with exponential backoff
        retry_delay = 2**self.request.retries
        self.retry(exc=e, countdown=retry_delay)


@app.task(name="shoplifting_detection.auto_clear_alerts", bind=True)
def auto_clear_alerts(self):
    """Periodic task to auto-clear old alerts."""
    try:
        from src.services.alert_manager import get_alert_manager

        alert_manager = get_alert_manager()
        cleared_count = alert_manager.auto_clear_old_alerts()

        logger.info(
            f"[AUTO-CLEAR] Periodic auto-clearance completed: {cleared_count} alerts cleared"
        )

        return {
            "status": "success",
            "cleared_count": cleared_count,
            "timestamp": time.time(),
        }

    except Exception as e:
        logger.error(f"[ERROR] Auto-clearance task failed: {str(e)}")
        return {"status": "error", "error": str(e), "timestamp": time.time()}


# Export the celery app
celery_predict = predict_sequence
