import copy
import json
import logging
import multiprocessing
import os
import sys
import threading
import time
import traceback
from collections import deque
from multiprocessing import Manager, Process
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import api_server
import cv2
import numpy as np
import psutil
import requests
import uvicorn
import yaml
from celery import Celery
from celery.result import AsyncResult
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.alert_system import AlertSystem
from src.api.routers.frames import router as frames_router
from src.api.video_stream import router as video_router
from src.camera_controller import CameraController
from src.camera_manager import CameraManager
from src.frame_capture import FrameCapture
from src.frame_processor import FrameProcessor
from src.middleware.audit_logger import AuditLogMiddleware
from src.middleware.encryption import EncryptionMiddleware, RequestSigningMiddleware
from src.middleware.request_limits import RequestLimitsMiddleware
from src.middleware.security import SecurityMiddleware
from src.middleware.security_headers import SecurityHeadersMiddleware
from src.model import load_model
from src.routers import auth, ws
from src.tasks import celery_predict
from src.utils import CameraConfig, Config, ensure_directory, setup_environment
from src.utils.config import load_config
from src.utils.secrets import secrets_manager
from src.utils.system_monitor import SystemMonitor
from src.video_stream_manager import VideoStreamManager
from utils.alerting import AlertConfig, get_alert_manager, init_alerting
from utils.log_aggregator import get_log_aggregator, init_log_aggregation
from utils.logging_config import setup_logging
from utils.monitoring import get_monitor, init_monitoring

# Initialize logging with rotation policies and aggregation
logger = setup_logging(
    name="main",
    level="INFO",
    log_file="logs/main.log",
    max_bytes=10 * 1024 * 1024,  # 10MB
    backup_count=5,
    rotation="midnight",
)

# Initialize log aggregation only if Elasticsearch is available
elasticsearch_handler = None
try:
    elasticsearch_host = os.getenv("ELASTICSEARCH_HOST", "localhost")
    elasticsearch_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))

    # Try to connect to Elasticsearch
    response = requests.get(f"http://{elasticsearch_host}:{elasticsearch_port}")
    if response.status_code == 200:
        elasticsearch_handler = init_log_aggregation(
            host=elasticsearch_host,
            port=elasticsearch_port,
            index_prefix="camera-system",
        )
        logger.addHandler(elasticsearch_handler)
        logger.info("Log aggregation initialized with Elasticsearch")
    else:
        logger.info("Elasticsearch is not available - running without log aggregation")
except Exception as e:
    logger.warning(f"Failed to initialize log aggregation: {e}")
    logger.info("Continuing without log aggregation")

# Initialize monitoring (using different port to avoid conflict with FastAPI)
monitor = init_monitoring(port=8002)

# Initialize alerting only if credentials are provided
alert_manager = None
try:
    # Check if we have valid alert configuration
    smtp_config = None
    if all(
        os.getenv(key)
        for key in [
            "SMTP_SERVER",
            "SMTP_PORT",
            "SMTP_USERNAME",
            "SMTP_PASSWORD",
            "ALERT_EMAIL_RECIPIENTS",
        ]
    ):
        smtp_config = {
            "smtp_server": os.getenv("SMTP_SERVER"),
            "port": int(os.getenv("SMTP_PORT")),
            "username": os.getenv("SMTP_USERNAME"),
            "password": os.getenv("SMTP_PASSWORD"),
            "recipients": os.getenv("ALERT_EMAIL_RECIPIENTS").split(","),
        }

    webhook_url = os.getenv("WEBHOOK_URL")
    slack_url = os.getenv("SLACK_WEBHOOK")

    if smtp_config or webhook_url or slack_url:
        alert_config = AlertConfig(
            email=smtp_config, webhook=webhook_url, slack=slack_url
        )
        alert_manager = init_alerting(alert_config)
        logger.info("Alert system initialized with available channels")
    else:
        logger.info("No alert configuration provided - running without alerts")
except Exception as e:
    logger.warning(f"Failed to initialize alert system: {e}")
    logger.info("Continuing without alert system")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Camera Monitoring API")

# IMPORTANT: CORS must be the FIRST middleware to handle preflight requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
    expose_headers=["Content-Type", "Authorization"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Add security middleware stack (order matters!)
app.add_middleware(RequestLimitsMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuditLogMiddleware)
app.add_middleware(EncryptionMiddleware)
app.add_middleware(RequestSigningMiddleware)
app.add_middleware(SecurityMiddleware)

# Include authentication router
app.include_router(auth.router)

# Include WebSocket router
app.include_router(ws.router)

# Add video streaming router
app.include_router(video_router)

# Add frames router
# app.include_router(frames_router)  # Temporarily disabled to test predictions


# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


# Initialize secrets
if not secrets_manager.validate_secrets():
    logger.error("Missing required secrets. Please check your .env file.")
    raise RuntimeError("Missing required secrets")


def create_display_grid(
    frames: dict, status: dict, predictions: dict = None, max_width: int = 1920
) -> np.ndarray:
    """Create a grid display of camera feeds with status and prediction information."""
    if not frames and not status:
        return np.zeros((480, 640, 3), dtype=np.uint8)
    n_cameras = len(status)
    grid_size = int(np.ceil(np.sqrt(n_cameras)))
    if frames:
        first_frame = next(f for f in frames.values() if f is not None)
        h, w = first_frame.shape[:2]
    else:
        h, w = 480, 640
    scale = min(1.0, max_width / (w * grid_size))
    new_w, new_h = int(w * scale), int(h * scale)
    grid = np.zeros((new_h * grid_size, new_w * grid_size, 3), dtype=np.uint8)
    for idx, (camera_id, cam_status) in enumerate(status.items()):
        i, j = idx // grid_size, idx % grid_size
        frame = frames.get(camera_id)
        if frame is not None:
            resized = cv2.resize(frame, (new_w, new_h))
            # Draw prediction overlay at the top
            pred_y_offset = 30
            if predictions and camera_id in predictions:
                pred = predictions[camera_id]
                prob = pred.get("probability", 0)
                label = pred.get("label", 0)
                message = pred.get("message", "")
                cv2.putText(
                    resized,
                    f"Probability: {prob:.1f}%",
                    (10, pred_y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                )
                pred_y_offset += 30
                cv2.putText(
                    resized,
                    message,
                    (10, pred_y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                )
                pred_y_offset += 30
            else:
                pred_y_offset += 60  # Reserve space if no prediction
            # Draw camera info overlay below prediction overlay
            info_lines = [
                f"Camera: {cam_status.get('name', camera_id)}",
                f"Location: {cam_status.get('location', 'N/A')}",
                f"Zone: {cam_status.get('zone', 'N/A')}",
            ]
            if cam_status.get("status") == "active":
                info_lines.extend(
                    [
                        f"FPS: {cam_status.get('fps', 0):.1f}",
                        f"Resolution: {cam_status.get('resolution', 'N/A')}",
                    ]
                )
            else:
                info_lines.append("Status: Failed")
            info_y_offset = pred_y_offset + 10  # Add spacing after prediction overlay
            for line in info_lines:
                cv2.putText(
                    resized,
                    line,
                    (10, info_y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2,
                )
                info_y_offset += 25
            grid[i * new_h : (i + 1) * new_h, j * new_w : (j + 1) * new_w] = resized
        else:
            placeholder = np.zeros((new_h, new_w, 3), dtype=np.uint8)
            if cam_status.get("status") == "failed":
                error_msg = cam_status.get("error", "Camera failed")
                words = error_msg.split()
                lines = []
                current_line = []
                for word in words:
                    if len(" ".join(current_line + [word])) < 40:
                        current_line.append(word)
                    else:
                        lines.append(" ".join(current_line))
                        current_line = [word]
                if current_line:
                    lines.append(" ".join(current_line))
                y_offset = new_h // 2 - (len(lines) * 30) // 2
                for line in lines:
                    cv2.putText(
                        placeholder,
                        line,
                        (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 0, 255),
                        1,
                    )
                    y_offset += 30
            grid[i * new_h : (i + 1) * new_h, j * new_w : (j + 1) * new_w] = placeholder
    return grid


def send_webhook_alert(webhook_url, camera_id, prediction):
    """Send webhook alert, but continue processing even if it fails."""
    try:
        payload = {
            "camera_id": camera_id,
            "probability": prediction.get("probability"),
            "label": prediction.get("label"),
            "message": prediction.get("message"),
        }
        requests.post(webhook_url, json=payload, timeout=5)
        logger.info(f"Webhook alert sent successfully for camera {camera_id}")
    except Exception as e:
        logger.warning(f"Webhook alert failed for camera {camera_id}: {e}")
        # Continue processing - don't raise the exception


def send_email_alert(recipients, camera_id, prediction):
    """Send email alert, but continue processing even if it fails."""
    try:
        # TODO: Implement email sending
        # This is a placeholder for email functionality
        logger.info(f"Would send email to {recipients} for camera {camera_id}")
    except Exception as e:
        logger.warning(f"Email alert failed for camera {camera_id}: {e}")
        # Continue processing - don't raise the exception


def handle_alerts(camera_id, prediction, alert_config):
    """Handle all alert types for a camera, continuing even if alerts fail."""
    if alert_config is None or alert_manager is None:
        return

    try:
        # Get cooldown period (default 60 seconds)
        cooldown = alert_config.get("cooldown", 60)

        # Check if we're in cooldown
        current_time = time.time()
        last_alert_time = getattr(handle_alerts, "_last_alert_time", {}).get(
            camera_id, 0
        )
        if current_time - last_alert_time < cooldown:
            logger.debug(f"Alert for {camera_id} in cooldown")
            return

        # Update last alert time
        if not hasattr(handle_alerts, "_last_alert_time"):
            handle_alerts._last_alert_time = {}
        handle_alerts._last_alert_time[camera_id] = current_time

        # Send webhook alerts
        if "webhooks" in alert_config:
            for webhook in alert_config["webhooks"]:
                send_webhook_alert(webhook["url"], camera_id, prediction)

        # Send email alerts
        if "email" in alert_config and "recipients" in alert_config["email"]:
            send_email_alert(alert_config["email"]["recipients"], camera_id, prediction)

    except Exception as e:
        logger.warning(f"Alert handling failed for camera {camera_id}: {e}")
        # Continue processing - don't raise the exception


def merge_camera_config(global_config, camera_dict):
    """Merge global config with camera-specific config."""
    # Get the config dictionary from the Config object
    merged = copy.deepcopy(
        global_config.config if hasattr(global_config, "config") else global_config
    )

    if "model_path" in camera_dict:
        merged["model"] = merged.get("model", {})
        merged["model"]["path"] = camera_dict["model_path"]
    if "thresholds" in camera_dict:
        merged["processing"] = merged.get("processing", {})
        merged["processing"]["probability_thresholds"] = camera_dict["thresholds"]
    if "frame_size" in camera_dict:
        merged["model"] = merged.get("model", {})
        merged["model"]["frame_size"] = camera_dict["frame_size"]
    if "sequence_length" in camera_dict:
        merged["model"] = merged.get("model", {})
        merged["model"]["sequence_length"] = camera_dict["sequence_length"]
    if "alert_webhook" in camera_dict:
        merged["alert_webhook"] = camera_dict["alert_webhook"]
    if "alert_threshold" in camera_dict:
        merged["alert_threshold"] = camera_dict["alert_threshold"]
    if "preprocessing" in camera_dict:
        merged["preprocessing"] = camera_dict["preprocessing"]
    return merged


def draw_rois_on_frame(frame, rois):
    if frame is None or not rois:
        return frame
    for roi in rois:
        points = np.array(roi["points"], np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [points], True, (0, 255, 0), 2)
        roi_name = roi.get("name")
        if roi_name:
            # Find the top-left point of the ROI polygon
            x, y = np.min(points[:, 0, 0]), np.min(points[:, 0, 1])
            # Draw a filled rectangle for label background
            (text_w, text_h), _ = cv2.getTextSize(
                str(roi_name), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
            )
            cv2.rectangle(
                frame, (x, y), (x + text_w + 6, y + text_h + 10), (0, 255, 0), -1
            )
            # Draw the label text inside the rectangle
            cv2.putText(
                frame,
                str(roi_name),
                (x + 3, y + text_h + 3),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 0),
                2,
            )
    return frame


def start_server(host: str, port: int, shared_data: Dict, controller: CameraController):
    """Start the FastAPI server."""
    try:
        logger.info(f"Starting FastAPI server on {host}:{port}")

        # Import here to avoid circular imports
        import api_server

        # Inject shared data and controller
        logger.info("Initializing API server with shared data...")
        api_server.initialize_shared_data(
            shared_data["frames"],
            shared_data.get("predictions", {}),
            shared_data.get("stats", {}),
            [],  # camera configs - can be fetched from controller if needed
        )
        logger.info("Shared data injected into API server")

        logger.info("Initializing camera controller in API server...")
        api_server.initialize_controller(controller)
        logger.info("Camera controller initialized in API server")

        # Log available routes
        logger.info("Available API routes:")
        for route in api_server.app.routes:
            if hasattr(route, "path"):
                methods = [
                    method
                    for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]
                    if hasattr(route, method.lower())
                ]
                if methods:
                    logger.info(f"  {', '.join(methods)} {route.path}")

        logger.info("Starting uvicorn server...")

        # Start server
        import uvicorn

        uvicorn.run(
            api_server.app,  # Use the FastAPI instance directly
            host=host,
            port=port,
            log_level="info",  # Changed from warning to info for more visibility
        )
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise


def process_frame(camera_id: str, frame: np.ndarray) -> dict:
    """Process a single frame and update metrics."""
    start_time = time.time()

    try:
        # ... existing frame processing code ...

        # Record metrics
        latency = time.time() - start_time
        monitor.record_camera_metrics(
            camera_id=camera_id,
            fps=1.0 / latency if latency > 0 else 0,
            latency=latency,
        )

        # Record model metrics if available
        if "confidence" in result:
            monitor.record_model_metrics(
                camera_id=camera_id,
                inference_time=result.get("inference_time", 0),
                confidence=result["confidence"],
            )

        return result

    except Exception as e:
        logger.error(
            f"Error processing frame for camera {camera_id}: {str(e)}",
            extra={"camera_id": camera_id, "error": str(e)},
        )
        monitor.record_error(camera_id, "frame_processing_error")
        raise


def initialize_alert_system(config: Config) -> AlertSystem:
    """Initialize the alert system."""
    alert_system = AlertSystem()
    logger.info("Alert system initialized with available channels")
    return alert_system


def main():
    """Main entry point."""
    try:
        logger.info("=" * 80)
        logger.info("STARTING BETTER VIGILANT SURVEILLANCE SYSTEM")
        logger.info("=" * 80)

        # Load configuration
        logger.info("Loading system configuration...")
        config = load_config()
        logger.info(f"Configuration loaded successfully from {config.config_path}")
        logger.info(
            f"Server will run on {config.config['server']['host']}:{config.config['server']['port']}"
        )

        # Log system information
        logger.info(f"Python version: {sys.version}")
        logger.info(f"System platform: {sys.platform}")
        logger.info(f"CPU cores: {multiprocessing.cpu_count()}")
        logger.info(f"Working directory: {os.getcwd()}")

        # Initialize shared data structures
        logger.info("Initializing shared data structures...")
        with Manager() as manager:
            shared_data = {
                "stats": manager.dict(),
                "frames": manager.dict(),
                "alerts": manager.dict(),
                "prediction_tasks": manager.dict(),
            }
            logger.info("Shared data structures initialized successfully")

            # Initialize Camera Controller (database-backed)
            logger.info("Initializing camera controller...")
            camera_controller = CameraController(shared_data)
            logger.info("Camera controller initialized successfully")

            # Initialize other components (Alerts)
            logger.info("Initializing alert system...")
            alert_system = initialize_alert_system(config)
            logger.info("Alert system initialized successfully")

            # Log available endpoints
            logger.info("Available API endpoints:")
            logger.info(
                f"  - Main API: http://{config.config['server']['host']}:{config.config['server']['port']}"
            )
            logger.info(
                f"  - Health check: http://{config.config['server']['host']}:{config.config['server']['port']}/api/health"
            )
            logger.info(f"  - WebSocket endpoints:")
            logger.info(f"    * /ws/audit - Real-time system activity stream (NEW)")
            logger.info(f"    * /ws/metrics - Real-time system metrics")
            logger.info(f"    * /ws/alerts - Real-time alert notifications")
            logger.info(f"    * /ws/camera/{{camera_id}} - Camera status updates")
            logger.info(f"  - Metrics: http://{config.config['server']['host']}:8002")

            # Log system features
            logger.info("System features:")
            logger.info(f"  - Real-time monitoring: {'✓' if monitor else '✗'}")
            logger.info(f"  - Alert system: {'✓' if alert_manager else '✗'}")
            logger.info(f"  - Log aggregation: {'✓' if elasticsearch_handler else '✗'}")
            logger.info(
                f"  - Redis WebSocket bridge: {'✓' if 'redis' in str(shared_data) else '✗'}"
            )
            logger.info(
                f"  - Audit logging: {'✓' if 'audit' in str(shared_data) else '✗'}"
            )

            # Start server process with controller
            logger.info("Starting FastAPI server process...")
            server_process = Process(
                target=start_server,
                args=(
                    config.config["server"]["host"],
                    config.config["server"]["port"],
                    shared_data,
                    camera_controller,
                ),
            )
            server_process.start()
            logger.info(f"Server process started with PID: {server_process.pid}")
            logger.info("System is ready - cameras are available but not started")
            logger.info(
                "Use the web interface or API to start cameras and begin monitoring"
            )
            logger.info("=" * 80)

            try:
                # Keep main process running, waiting for shutdown signal
                start_time = time.time()
                last_status_log = start_time
                while True:
                    time.sleep(1)

                    # Log system status every 5 minutes
                    current_time = time.time()
                    if current_time - last_status_log > 300:  # 5 minutes
                        uptime = int(current_time - start_time)
                        logger.info("=" * 60)
                        logger.info("SYSTEM STATUS CHECK")
                        logger.info("=" * 60)
                        logger.info(
                            f"Server process alive: {server_process.is_alive()}"
                        )
                        logger.info(f"Server process PID: {server_process.pid}")
                        logger.info(f"Shared data keys: {list(shared_data.keys())}")
                        logger.info(f"Uptime: {uptime} seconds ({uptime//60} minutes)")
                        logger.info("=" * 60)
                        last_status_log = current_time

            except KeyboardInterrupt:
                logger.info("Received shutdown signal...")
            finally:
                # Cleanup
                logger.info("=" * 80)
                logger.info("SHUTTING DOWN SYSTEM")
                logger.info("=" * 80)

                logger.info("Stopping camera controller...")
                camera_controller.stop_all_cameras()
                logger.info("Camera controller stopped")

                logger.info("Terminating server process...")
                server_process.terminate()
                server_process.join(timeout=10)
                if server_process.is_alive():
                    logger.warning(
                        "Server process did not terminate gracefully, forcing..."
                    )
                    server_process.kill()
                logger.info("Server process terminated")

                logger.info("System shutdown complete")
                logger.info("=" * 80)

    except Exception as e:
        logger.error("=" * 80)
        logger.error("FATAL ERROR DURING SYSTEM STARTUP")
        logger.error("=" * 80)
        logger.error(f"Error: {e}")
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
