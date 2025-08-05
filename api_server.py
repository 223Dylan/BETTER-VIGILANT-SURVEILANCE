import asyncio
import os
from typing import Dict, List

import cv2
import numpy as np
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Security,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security.api_key import APIKey, APIKeyHeader
from loguru import logger
from starlette.status import HTTP_403_FORBIDDEN

from src.api.hls_stream import initialize_hls_data
from src.api.hls_stream import router as hls_router
from src.api.mjpeg_stream import initialize_mjpeg_data
from src.api.mjpeg_stream import router as mjpeg_router
from src.api.routers.frames import router as frames_router
from src.api.simple_hls import initialize_simple_hls_data
from src.api.simple_hls import router as simple_hls_router
from src.api.simple_hls_test import router as test_hls_router
from src.api.video_stream import router as video_router
from src.api.video_stream import stream_manager
from src.middleware.audit_logger import AuditLogMiddleware
from src.middleware.encryption import EncryptionMiddleware, RequestSigningMiddleware
from src.middleware.request_limits import RequestLimitsMiddleware
from src.middleware.security import SecurityMiddleware
from src.middleware.security_headers import SecurityHeadersMiddleware
from src.routers import alerts, audit, auth, cameras, metrics, permissions, users, ws
from src.services.redis_websocket_bridge import redis_websocket_bridge
from src.utils.logging import setup_logging
from src.utils.secrets import secrets_manager
from src.websocket_manager import websocket_manager

# Setup logging
logger = setup_logging()

# Create FastAPI instance
app = FastAPI(title="Video Streaming API")


@app.on_event("startup")
async def startup_event():
    """Initialize Redis WebSocket bridge on startup."""
    try:
        await redis_websocket_bridge.start_subscriber(websocket_manager)
        logger.info("[STARTUP] Redis WebSocket bridge initialized")
    except Exception as e:
        logger.error(f"[STARTUP] Failed to initialize Redis WebSocket bridge: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup Redis WebSocket bridge on shutdown."""
    try:
        await redis_websocket_bridge.stop_subscriber()
        redis_websocket_bridge.close()
        logger.info("[SHUTDOWN] Redis WebSocket bridge stopped")
    except Exception as e:
        logger.error(f"[SHUTDOWN] Error stopping Redis WebSocket bridge: {e}")


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

# Initialize secrets validation
if not secrets_manager.validate_secrets():
    logger.error("Missing required secrets. Please check your .env file.")
    raise RuntimeError("Missing required secrets")

# Initialize stream manager
if not stream_manager.initialize():
    logger.error("Failed to initialize stream manager")
    raise RuntimeError("Failed to initialize stream manager")
logger.info("Stream manager initialized")

# Include authentication router
app.include_router(auth.router)

# Include WebSocket router
app.include_router(ws.router)

# Include cameras router
app.include_router(cameras.router)

# Include alerts router
app.include_router(alerts.router, prefix="/api")

# Include video stream router
app.include_router(video_router, prefix="/api/video")

# Include HLS stream router
app.include_router(hls_router)

# Include MJPEG stream router
app.include_router(mjpeg_router)

# Include test HLS router
app.include_router(test_hls_router)

# Include simple HLS router
app.include_router(simple_hls_router)

# Include frames router
app.include_router(frames_router, prefix="/api")

# Include users router
app.include_router(users.router, prefix="/api")

# Include metrics router
app.include_router(metrics.router)

# Include audit router (already has /api/audit prefix)
app.include_router(audit.router)

# Include permissions router
app.include_router(permissions.router, prefix="/api/permissions")

# Include user notifications router
from src.routers import user_notifications

app.include_router(user_notifications.router, prefix="/api")

# These will be injected from main.py
shared_frames = {}
shared_predictions = {}
shared_stats = {}
camera_configs = None  # Inject from main.py for details/control
camera_controller = None  # Will be injected


def initialize_shared_data(frames: Dict, predictions: Dict, stats: Dict, configs: List):
    """Initialize shared data from main process."""
    global shared_frames, shared_predictions, shared_stats, camera_configs
    shared_frames = frames
    shared_predictions = predictions
    shared_stats = stats
    camera_configs = configs
    # Initialize WebSocket router with shared data
    ws.initialize_shared_data(stats)
    # Initialize MJPEG router with shared data
    initialize_mjpeg_data(shared_frames, stream_manager, camera_controller)
    # Initialize HLS router with shared data
    initialize_hls_data(shared_frames, stream_manager, camera_controller)
    # Initialize simple HLS router with shared data
    initialize_simple_hls_data(shared_frames, stream_manager, camera_controller)
    logger.info(
        f"Shared data initialized in API server - frames: {type(frames)}, keys: {list(frames.keys()) if frames else 'None'}"
    )


def initialize_controller(controller):
    """Injects the camera controller instance."""
    global camera_controller
    camera_controller = controller
    # Initialize the cameras router with the controller
    cameras.initialize_controller(controller)
    # Update MJPEG router with camera controller
    initialize_mjpeg_data(shared_frames, stream_manager, camera_controller)
    # Update HLS router with camera controller
    initialize_hls_data(shared_frames, stream_manager, camera_controller)
    # Update simple HLS router with camera controller
    initialize_simple_hls_data(shared_frames, stream_manager, camera_controller)
    logger.info("Camera controller initialized in API server.")


# Camera endpoints are now handled by the cameras router


@app.get("/cameras/{camera_id}/prediction")
def camera_prediction(camera_id: str):
    if not shared_predictions:
        raise HTTPException(status_code=503, detail="Predictions not available")
    prediction = shared_predictions.get(camera_id)
    if prediction is None:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/cameras/{camera_id}/frame")
def camera_frame(camera_id: str):
    if shared_frames is None:
        raise HTTPException(status_code=503, detail="Frames not available")
    frame = shared_frames.get(camera_id)
    if frame is None:
        raise HTTPException(status_code=404, detail="Frame not found")
    # Convert numpy array to JPEG
    ret, jpeg = cv2.imencode(".jpg", np.array(frame))
    if not ret:
        raise HTTPException(status_code=500, detail="Failed to encode frame")
    return Response(content=jpeg.tobytes(), media_type="image/jpeg")


@app.get("/cameras/details")
def camera_details():
    if camera_configs is None:
        return []
    return [cam.__dict__ for cam in camera_configs]


@app.get("/cameras/{camera_id}/logs")
def camera_logs(camera_id: str, lines: int = 50):
    log_file = f"logs/camera_{camera_id}.log"
    try:
        with open(log_file, "r") as f:
            log_lines = f.readlines()[-lines:]
        return {"logs": log_lines}
    except Exception:
        raise HTTPException(status_code=404, detail="Log file not found")


@app.websocket("/api/video/stream/{camera_id}")
async def video_stream(websocket: WebSocket, camera_id: str):
    await websocket.accept()
    logger.info(f"WebSocket streaming started for {camera_id}")
    frames_sent = 0
    last_camera_check = 0
    try:
        while True:
            # Check camera status every few frames to avoid constant DB queries
            current_time = asyncio.get_event_loop().time()
            if current_time - last_camera_check > 2.0:  # Check every 2 seconds
                camera_is_running = False
                if camera_controller:
                    statuses = camera_controller.get_all_camera_status()
                    camera_is_running = statuses.get(camera_id) == "active"

                if not camera_is_running:
                    # Camera is stopped - clear any buffered frames, send error, and close connection
                    if stream_manager and hasattr(
                        stream_manager, "clear_camera_buffer"
                    ):
                        stream_manager.clear_camera_buffer(camera_id)
                    await websocket.send_json({"error": "Camera stopped"})
                    logger.info(
                        f"Camera {camera_id} is stopped, closing WebSocket connection"
                    )
                    break  # Exit the loop to close the connection

                last_camera_check = current_time

            # Try to get frame from stream_manager buffer first
            if stream_manager and hasattr(stream_manager, "get_latest_frame"):
                frame_bytes = stream_manager.get_latest_frame(camera_id)
                if frame_bytes:
                    await websocket.send_bytes(frame_bytes)
                    frames_sent += 1
                    if frames_sent % 30 == 0:
                        logger.debug(
                            f"Sent {frames_sent} frames via stream manager for {camera_id}"
                        )
                    await asyncio.sleep(0.066)  # ~15 FPS
                    continue

            # Fallback to shared_frames
            if shared_frames is None:
                logger.debug(f"shared_frames is None for {camera_id}")
                await websocket.send_json({"error": "No frame available"})
                await asyncio.sleep(1)
                continue
            elif camera_id not in shared_frames:
                logger.debug(
                    f"Camera {camera_id} not in shared_frames. Available: {list(shared_frames.keys())}"
                )
                await websocket.send_json({"error": "No frame available"})
                await asyncio.sleep(1)
                continue

            frame = shared_frames[camera_id]
            if frame is None:
                await websocket.send_json({"error": "No frame available"})
                await asyncio.sleep(1)
                continue

            ret, jpeg = cv2.imencode(".jpg", np.array(frame))
            if not ret:
                await websocket.send_json({"error": "Failed to encode frame"})
                await asyncio.sleep(1)
                continue

            await websocket.send_bytes(jpeg.tobytes())
            await asyncio.sleep(0.1)  # Limit to ~10 FPS
    except WebSocketDisconnect:
        logger.info(
            f"WebSocket disconnected for {camera_id} after {frames_sent} frames"
        )
    except Exception as e:
        logger.error(f"Video stream error for camera {camera_id}: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    logger.info("[STARTUP] Starting FastAPI server with user management system...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
