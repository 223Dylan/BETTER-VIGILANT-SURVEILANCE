from fastapi import APIRouter, Response, HTTPException
from fastapi.responses import StreamingResponse
import cv2
import asyncio
import time
import numpy as np
from typing import Generator
from loguru import logger

router = APIRouter(tags=["mjpeg"])

# Global references to shared data - will be injected from main server
shared_frames = {}
stream_manager = None
camera_controller = None


def initialize_mjpeg_data(frames_ref, stream_mgr, cam_ctrl):
    """Initialize access to shared camera data."""
    global shared_frames, stream_manager, camera_controller
    shared_frames = frames_ref
    stream_manager = stream_mgr
    camera_controller = cam_ctrl
    logger.info("MJPEG router initialized with shared camera data")


def generate_mjpeg_stream(camera_id: str) -> Generator[bytes, None, None]:
    """Generate MJPEG stream with proper boundaries using real camera data."""
    boundary = "frame"
    frame_count = 0

    while True:
        try:
            frame_count += 1

            # Check if camera is running - if not, end the stream
            if camera_controller:
                statuses = camera_controller.get_all_camera_status()
                if statuses.get(camera_id) != "active":
                    # Reduced logging - only log every 50th frame to reduce noise
                    if frame_count % 50 == 0:
                        logger.debug(
                            f"Camera {camera_id} is not active, ending stream (frame {frame_count})"
                        )
                    break  # End the stream instead of showing test pattern

            # Try to get frame from stream_manager buffer first
            if stream_manager and hasattr(stream_manager, "get_latest_frame"):
                frame_bytes = stream_manager.get_latest_frame(camera_id)
                if frame_bytes:
                    yield format_mjpeg_frame(frame_bytes, boundary)
                    time.sleep(1 / 15)  # 15 FPS for live frames
                    continue

            # Fallback to shared_frames
            if shared_frames and camera_id in shared_frames:
                frame = shared_frames[camera_id]
                if frame is not None:
                    jpeg_bytes = encode_frame_to_jpeg(frame)
                    if jpeg_bytes:
                        yield format_mjpeg_frame(jpeg_bytes, boundary)
                        time.sleep(1 / 15)  # 15 FPS
                        continue

            # No frame available - generate test pattern
            frame = create_test_frame(camera_id, "No Frame Available")
            jpeg_bytes = encode_frame_to_jpeg(frame)
            if jpeg_bytes:
                yield format_mjpeg_frame(jpeg_bytes, boundary)

            time.sleep(1 / 5)  # Slower rate when no data

        except Exception as e:
            logger.error(f"Error generating MJPEG frame for {camera_id}: {e}")
            break


def encode_frame_to_jpeg(frame) -> bytes:
    """Encode frame to JPEG bytes."""
    try:
        ret, jpeg = cv2.imencode(
            ".jpg", np.array(frame), [cv2.IMWRITE_JPEG_QUALITY, 85]
        )
        return jpeg.tobytes() if ret else None
    except Exception as e:
        logger.error(f"Failed to encode frame to JPEG: {e}")
        return None


def format_mjpeg_frame(jpeg_bytes: bytes, boundary: str) -> bytes:
    """Format JPEG bytes as MJPEG multipart frame."""
    return (
        b"--" + boundary.encode() + b"\r\n"
        b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n"
    )


def create_test_frame(camera_id: str, message: str = "MJPEG Test Stream"):
    """Create a test frame with timestamp and custom message."""
    # Create a 640x480 test image
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Add some color based on camera_id
    if "local" in camera_id:
        frame[:, :] = [100, 150, 200]  # Blue-ish
    elif "entrance" in camera_id:
        frame[:, :] = [100, 200, 100]  # Green-ish
    else:
        frame[:, :] = [200, 100, 100]  # Red-ish

    # Add timestamp
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(
        frame,
        f"Camera: {camera_id}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )
    cv2.putText(
        frame, timestamp, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
    )
    cv2.putText(
        frame, message, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
    )

    return frame


@router.get("/api/video/mjpeg/{camera_id}")
async def mjpeg_stream(camera_id: str):
    """MJPEG stream endpoint that can be used directly in HTML video tag."""
    return StreamingResponse(
        generate_mjpeg_stream(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Origin, X-Requested-With",
        },
    )


@router.get("/api/video/mjpeg/{camera_id}/info")
async def mjpeg_info(camera_id: str):
    """Get information about the MJPEG stream."""
    return {
        "camera_id": camera_id,
        "stream_url": f"/api/video/mjpeg/{camera_id}",
        "format": "Motion JPEG",
        "resolution": "640x480",
        "fps": 15,
        "description": "MJPEG stream compatible with HTML5 video element",
    }
