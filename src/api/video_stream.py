import asyncio
import time
from typing import Dict

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from loguru import logger

from src.video_stream_manager import VideoStreamManager

router = APIRouter(tags=["video"])

# Create a singleton instance
stream_manager = VideoStreamManager()

# Initialize the stream manager
if not stream_manager.initialize():
    logger.error("Failed to initialize stream manager")
    raise RuntimeError("Failed to initialize stream manager")

logger.info(
    "VideoStreamManager initialized with WebSocket endpoint: /api/video/stream/{camera_id}"
)

# Background task to inject frames from shared memory
import asyncio
import signal
import sys
import threading

shared_data = None  # Will be set by api_server
_injection_running = True  # Global flag to control injection loop
_injection_thread = None  # Reference to the injection thread


def signal_handler(signum, frame):
    """Handle shutdown signals to gracefully stop the injection loop."""
    global _injection_running
    logger.info(f"Received signal {signum}, shutting down frame injection loop...")
    _injection_running = False


def start_frame_injection_task():
    """Start background task to inject frames from shared memory."""

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    def injection_loop():
        global _injection_running
        while _injection_running:
            try:
                if shared_data:
                    # Check for frame data in shared memory
                    for key in list(shared_data.keys()):
                        if key.startswith("frame_"):
                            camera_id = key.replace("frame_", "")
                            frame_bytes = shared_data.get(key)

                            # Only inject frames if camera is actually enabled and running
                            if frame_bytes and stream_manager._initialized:
                                try:
                                    # Check if camera is enabled in database
                                    from src.services.camera_db_service import (
                                        camera_db_service,
                                    )

                                    camera = camera_db_service.get_camera_by_id(
                                        camera_id
                                    )

                                    if (
                                        camera
                                        and camera.enabled
                                        and camera.status == "active"
                                    ):
                                        # Inject frame into stream manager
                                        stream_manager.inject_frame_for_streaming(
                                            camera_id, frame_bytes
                                        )
                                        logger.debug(
                                            f"Injected shared frame for {camera_id}"
                                        )
                                    else:
                                        # Camera is disabled or stopped - skip frame injection
                                        logger.debug(
                                            f"Skipping frame injection for disabled/stopped camera: {camera_id}"
                                        )
                                        # Remove the frame from shared memory to prevent accumulation
                                        if key in shared_data:
                                            del shared_data[key]
                                except Exception as db_error:
                                    logger.warning(
                                        f"Error checking camera status for {camera_id}: {db_error}"
                                    )
                                    # If we can't check status, skip injection to be safe
                                    continue
                time.sleep(0.033)  # ~30 FPS injection rate
            except Exception as e:
                logger.error(f"Error in frame injection loop: {e}")
                time.sleep(1)

        logger.info("Frame injection loop stopped")

    # Start background thread
    global _injection_thread
    _injection_thread = threading.Thread(target=injection_loop, daemon=True)
    _injection_thread.start()
    logger.info("Started frame injection background task")

    return _injection_thread


def stop_frame_injection():
    """Stop the frame injection loop."""
    global _injection_running, _injection_thread
    _injection_running = False
    logger.info("Frame injection loop stop requested")

    # Wait for thread to finish if it exists
    if _injection_thread and _injection_thread.is_alive():
        logger.info("Waiting for injection thread to finish...")
        _injection_thread.join(timeout=5)
        if _injection_thread.is_alive():
            logger.warning("Injection thread did not finish gracefully")


def cleanup_frame_injection():
    """Clean up frame injection resources."""
    global _injection_running, _injection_thread
    _injection_running = False

    if _injection_thread and _injection_thread.is_alive():
        _injection_thread.join(timeout=2)

    logger.info("Frame injection cleanup completed")


def is_injection_running():
    """Check if the frame injection loop is running."""
    return _injection_running and _injection_thread and _injection_thread.is_alive()


# Start the injection task
start_frame_injection_task()


@router.websocket("/api/video/stream/{camera_id}")
async def video_stream(websocket: WebSocket, camera_id: str):
    """WebSocket endpoint for video streaming."""
    if not stream_manager._initialized:
        logger.error("Stream manager not initialized")
        await websocket.close()
        return

    try:
        # Log the full WebSocket URL
        ws_url = f"ws://{websocket.client.host}:{websocket.client.port}/api/video/stream/{camera_id}"
        logger.info(f"Attempting WebSocket connection to: {ws_url}")

        # Accept connection
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for camera {camera_id} at {ws_url}")

        # Start streaming
        await stream_manager.start_stream(camera_id, websocket)
        logger.info(f"Started streaming for camera {camera_id} via {ws_url}")

        try:
            last_frame_time = time.time()
            frames_sent = 0
            while True:
                # Get current stats
                stats = stream_manager.get_stats(camera_id)

                # Calculate time since last frame
                current_time = time.time()
                elapsed = current_time - last_frame_time

                # Only send frame if enough time has passed (respect target FPS)
                if elapsed >= stream_manager._min_frame_interval:
                    # Check if camera is actually running
                    camera_is_running = await check_camera_status(camera_id)

                    if not camera_is_running:
                        # Camera is stopped - clear buffer and send error
                        if camera_id in stream_manager.streams:
                            stream_manager.streams[camera_id].clear()
                        await websocket.send_json({"error": "Camera stopped"})
                        await asyncio.sleep(1)  # Wait before next check
                    else:
                        # Send next frame
                        await stream_manager.send_frame(camera_id)
                        frames_sent += 1

                        # Log every 30 frames
                        if frames_sent % 30 == 0:
                            logger.info(
                                f"Sent {frames_sent} frames for camera {camera_id} at {ws_url}"
                            )

                        # If buffer is getting low, log a warning
                        if stats["buffer_size"] < 5:
                            logger.warning(
                                f"Low buffer for camera {camera_id} at {ws_url}: {stats['buffer_size']} frames"
                            )

                    last_frame_time = current_time
                else:
                    # Sleep for a short time to prevent CPU spinning
                    await asyncio.sleep(0.001)

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for camera {camera_id} at {ws_url}")
        except Exception as e:
            logger.error(
                f"Error in video stream for camera {camera_id} at {ws_url}: {e}"
            )
        finally:
            # Stop streaming
            await stream_manager.stop_stream(camera_id)
            logger.info(
                f"Stopped streaming for camera {camera_id} at {ws_url} after sending {frames_sent} frames"
            )

    except Exception as e:
        logger.error(f"Error in video stream endpoint for camera {camera_id}: {e}")
        if not websocket.client_state.DISCONNECTED:
            await websocket.close()


@router.get("/status/{camera_id}")
async def get_stream_status(camera_id: str):
    """Get streaming status for a camera."""
    if not stream_manager._initialized:
        logger.error("Stream manager not initialized")
        return {"error": "Stream manager not initialized"}

    try:
        stats = stream_manager.get_stats(camera_id)
        logger.info(f"Stream status for camera {camera_id}: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error getting stream status for camera {camera_id}: {e}")
        return {"error": str(e)}


@router.get("/connection/{camera_id}")
async def get_connection_status(camera_id: str):
    """Get detailed connection status for a camera."""
    if not stream_manager._initialized:
        logger.error("Stream manager not initialized")
        return {"error": "Stream manager not initialized"}

    try:
        status = stream_manager.get_connection_status(camera_id)
        logger.info(f"Connection status for camera {camera_id}: {status}")
        return status
    except Exception as e:
        logger.error(f"Error getting connection status for camera {camera_id}: {e}")
        return {"error": str(e)}


@router.get("/debug/{camera_id}")
async def get_stream_debug(camera_id: str):
    """Get detailed debug information for a camera stream."""
    if not stream_manager._initialized:
        return {"error": "Stream manager not initialized"}

    try:
        buffer_status = stream_manager.get_buffer_status(camera_id)
        stats = stream_manager.get_stats(camera_id)
        connection_status = stream_manager.get_connection_status(camera_id)

        debug_info = {
            "camera_id": camera_id,
            "timestamp": time.time(),
            "buffer_status": buffer_status,
            "stream_stats": stats,
            "connection_status": connection_status,
            "stream_manager_running": stream_manager._running,
            "stream_manager_initialized": stream_manager._initialized,
        }

        logger.info(f"Debug info for camera {camera_id}: {debug_info}")
        return debug_info
    except Exception as e:
        logger.error(f"Error getting debug info for camera {camera_id}: {e}")
        return {"error": str(e)}


@router.post("/inject-frame/{camera_id}")
async def inject_frame(camera_id: str, request: Request):
    """Inject a real frame for streaming."""
    try:
        # Read raw frame data from request body
        frame_data = await request.body()

        # Inject frame directly into stream
        result = stream_manager.inject_frame_for_streaming(camera_id, frame_data)

        # Get buffer status after injection
        buffer_status = stream_manager.get_buffer_status(camera_id)

        return {
            "success": result,
            "frame_size": len(frame_data),
            "buffer_status": buffer_status,
            "timestamp": time.time(),
        }

    except Exception as e:
        logger.error(f"Error injecting frame for camera {camera_id}: {e}")
        return {"error": str(e)}


@router.post("/inject-test-frame/{camera_id}")
async def inject_test_frame(camera_id: str):
    """Inject a REAL frame from camera for debugging streaming issues."""
    try:
        import cv2

        # Capture REAL frame from camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return {"error": "Failed to open camera"}

        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            return {"error": "Failed to capture frame"}

        # Encode as JPEG
        success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            return {"error": "Failed to encode frame"}

        frame_bytes = buffer.tobytes()

        # Inject directly into stream
        result = stream_manager.inject_frame_for_streaming(camera_id, frame_bytes)

        # Get buffer status after injection
        buffer_status = stream_manager.get_buffer_status(camera_id)

        return {
            "success": result,
            "frame_size": len(frame_bytes),
            "buffer_status": buffer_status,
            "timestamp": time.time(),
            "frame_type": "REAL_CAMERA",
        }

    except Exception as e:
        logger.error(f"Error injecting real frame for camera {camera_id}: {e}")
        return {"error": str(e)}


@router.post("/fix-connection/{camera_id}")
async def fix_connection_tracking(camera_id: str):
    """Force fix connection tracking issues for debugging."""
    if not stream_manager._initialized:
        return {"error": "Stream manager not initialized"}

    try:
        result = stream_manager.fix_connection_tracking(camera_id)
        return {
            "camera_id": camera_id,
            "timestamp": time.time(),
            "fix_result": result,
            "buffer_status": stream_manager.get_buffer_status(camera_id),
            "connection_status": stream_manager.get_connection_status(camera_id),
        }
    except Exception as e:
        logger.error(f"Error fixing connection for {camera_id}: {e}")
        return {"error": f"Failed to fix connection: {str(e)}"}


@router.websocket("/simple-stream/{camera_id}")
async def simple_video_stream(websocket: WebSocket, camera_id: str):
    """LEGACY: Simple WebSocket endpoint that directly streams from buffer - NOT USED BY FRONTEND."""
    try:
        # Accept connection immediately
        await websocket.accept()
        logger.info(f"[LEGACY] Simple stream connected for {camera_id}")

        frames_sent = 0
        last_frame_time = time.time()
        consecutive_empty_count = 0

        while True:
            try:
                current_time = time.time()
                elapsed = current_time - last_frame_time

                # Maintain ~15 FPS (66ms between frames)
                if elapsed >= 0.066:
                    # Check if camera is actually running first
                    camera_is_running = await check_camera_status(camera_id)

                    if not camera_is_running:
                        # Camera is stopped - send error and stop sending old frames
                        await websocket.send_json({"error": "Camera stopped"})
                        consecutive_empty_count += 1
                        # Clear buffer to prevent sending stale frames
                        if camera_id in stream_manager.streams:
                            stream_manager.streams[camera_id].clear()
                    elif (
                        camera_id in stream_manager.streams
                        and stream_manager.streams[camera_id]
                        and len(stream_manager.streams[camera_id]) > 0
                    ):

                        # Reset empty count when frames are available
                        consecutive_empty_count = 0

                        # Get frame directly from buffer
                        frame = stream_manager.streams[camera_id].popleft()

                        # Send frame directly
                        await websocket.send_bytes(frame)
                        frames_sent += 1
                        last_frame_time = current_time

                        # Log success occasionally
                        if frames_sent % 100 == 0:  # Reduced logging frequency
                            buffer_size = len(stream_manager.streams[camera_id])
                            logger.info(
                                f"[SUCCESS] Simple stream sent {frames_sent} frames for {camera_id}, Buffer: {buffer_size}"
                            )

                    else:
                        # Only send error if buffer has been empty for a while
                        consecutive_empty_count += 1
                        if (
                            consecutive_empty_count > 5
                        ):  # Send error only after 5 consecutive empty checks
                            await websocket.send_json({"error": "No frame available"})
                            consecutive_empty_count = 0  # Reset counter

                    last_frame_time = current_time
                else:
                    # Short sleep to prevent CPU spinning
                    await asyncio.sleep(0.001)

            except WebSocketDisconnect:
                logger.info(
                    f"[DISCONNECT] Simple stream disconnected for {camera_id} after {frames_sent} frames"
                )
                break
            except Exception as e:
                logger.error(f"[ERROR] Error in simple stream for {camera_id}: {e}")
                break

    except Exception as e:
        logger.error(f"[ERROR] Error starting simple stream for {camera_id}: {e}")
        if not websocket.client_state.DISCONNECTED:
            await websocket.close()


async def check_camera_status(camera_id: str) -> bool:
    """Check if a camera is currently running by querying the controller."""
    try:
        # Import here to avoid circular imports
        from api_server import camera_controller

        if camera_controller:
            statuses = camera_controller.get_all_camera_statuses()
            return statuses.get(camera_id) == "active"
        return False
    except Exception as e:
        logger.debug(f"Could not check camera status for {camera_id}: {e}")
        return True  # Default to allowing streaming if we can't check


@router.get("/simple-debug/{camera_id}")
async def get_simple_debug(camera_id: str):
    """Get simple debug info without complex connection tracking."""
    try:
        # Direct buffer check
        buffer_exists = camera_id in stream_manager.streams
        buffer_size = len(stream_manager.streams[camera_id]) if buffer_exists else 0

        debug_info = {
            "camera_id": camera_id,
            "timestamp": time.time(),
            "buffer_exists": buffer_exists,
            "buffer_size": buffer_size,
            "buffer_max_size": stream_manager.buffer_size,
            "stream_manager_running": stream_manager._running,
            "stream_manager_initialized": stream_manager._initialized,
            "simple_stream_ready": buffer_exists and buffer_size > 0,
        }

        logger.info(f"Simple debug for {camera_id}: {debug_info}")
        return debug_info

    except Exception as e:
        logger.error(f"Error getting simple debug for {camera_id}: {e}")
        return {"error": str(e)}


@router.post("/control/injection/stop")
async def stop_frame_injection_endpoint():
    """Stop the frame injection loop."""
    try:
        stop_frame_injection()
        return {"status": "success", "message": "Frame injection loop stop requested"}
    except Exception as e:
        logger.error(f"Error stopping frame injection: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/control/injection/start")
async def start_frame_injection_endpoint():
    """Start the frame injection loop."""
    try:
        global _injection_running
        _injection_running = True
        start_frame_injection_task()
        return {"status": "success", "message": "Frame injection loop started"}
    except Exception as e:
        logger.error(f"Error starting frame injection: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/control/injection/status")
async def get_injection_status():
    """Get the status of the frame injection loop."""
    try:
        return {
            "status": "success",
            "injection_running": is_injection_running(),
            "injection_flag": _injection_running,
            "thread_alive": (
                _injection_thread.is_alive() if _injection_thread else False
            ),
        }
    except Exception as e:
        logger.error(f"Error getting injection status: {e}")
        return {"status": "error", "message": str(e)}
