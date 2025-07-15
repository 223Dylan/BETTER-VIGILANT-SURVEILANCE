from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
import cv2
import asyncio
import os
import tempfile
import subprocess
import time
import threading
import numpy as np
from typing import Dict
from loguru import logger

router = APIRouter(tags=["simple-hls"])

# Global references to shared data
shared_frames = {}
stream_manager = None
camera_controller = None

# Simple HLS management
hls_output_dirs: Dict[str, str] = {}
hls_processes: Dict[str, subprocess.Popen] = {}
hls_threads: Dict[str, threading.Thread] = {}
hls_stop_events: Dict[str, threading.Event] = {}


def initialize_simple_hls_data(frames_ref, stream_mgr, cam_ctrl):
    """Initialize access to shared camera data."""
    global shared_frames, stream_manager, camera_controller
    shared_frames = frames_ref
    stream_manager = stream_mgr
    camera_controller = cam_ctrl
    logger.info("Simple HLS router initialized with shared camera data")


def create_hls_directory(camera_id: str) -> str:
    """Create a temporary directory for HLS files."""
    temp_dir = tempfile.mkdtemp(prefix=f"simple_hls_{camera_id}_")
    hls_output_dirs[camera_id] = temp_dir
    logger.info(f"Created simple HLS directory for camera {camera_id}: {temp_dir}")
    return temp_dir


def hls_generator_thread(camera_id: str):
    """Thread that generates HLS segments from JPEG frames."""
    logger.info(f"Starting simple HLS generator thread for camera {camera_id}")
    stop_event = hls_stop_events[camera_id]
    output_dir = hls_output_dirs[camera_id]

    segment_duration = 2  # 2 seconds per segment (shorter for less lag)
    frames_per_segment = (
        10 * segment_duration
    )  # 10 FPS * 2 seconds = 20 frames (lighter)
    segment_index = 0
    frame_count = 0
    frames_for_segment = []

    while not stop_event.is_set():
        try:
            # Check if camera is still active
            camera_is_active = False
            if camera_controller:
                statuses = camera_controller.get_all_camera_status()
                camera_is_active = statuses.get(camera_id) == "active"

            # If camera is not active for too long, stop the HLS stream
            if not camera_is_active:
                # Generate a few more test segments then stop
                if (
                    frame_count > 30
                ):  # After ~3 seconds of inactivity (reduced from 10s)
                    logger.info(
                        f"Camera {camera_id} inactive, stopping simple HLS stream"
                    )
                    break

            # Get frame data
            frame_data = None

            # Try to get frame from stream_manager buffer first
            if stream_manager and hasattr(stream_manager, "get_latest_frame"):
                frame_bytes = stream_manager.get_latest_frame(camera_id)
                if frame_bytes:
                    # Convert JPEG bytes to frame
                    nparr = np.frombuffer(frame_bytes, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        frame_data = frame

            # Fallback to shared_frames
            if frame_data is None and shared_frames and camera_id in shared_frames:
                frame = shared_frames[camera_id]
                if frame is not None:
                    frame_data = np.array(frame)

            # Generate test frame if no data
            if frame_data is None:
                frame_data = np.zeros((480, 640, 3), dtype=np.uint8)
                frame_data[::40, :] = [100, 100, 200]  # Blue lines
                timestamp = time.strftime("%H:%M:%S")
                cv2.putText(
                    frame_data,
                    f"HLS Test {timestamp}",
                    (50, 240),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 255),
                    2,
                )

            # Add frame to current segment
            if frame_data is not None:
                frames_for_segment.append(frame_data)
                frame_count += 1

                # When we have enough frames, create a segment
                if len(frames_for_segment) >= frames_per_segment:
                    create_hls_segment(
                        camera_id, segment_index, frames_for_segment, output_dir
                    )
                    segment_index += 1
                    frames_for_segment = []

                    # Update playlist
                    create_hls_playlist(camera_id, segment_index, output_dir)

            # Sleep to maintain 10 FPS (less intensive)
            stop_event.wait(1 / 10)

        except Exception as e:
            logger.error(f"Error in simple HLS generator for camera {camera_id}: {e}")
            break

    logger.info(f"Simple HLS generator thread stopped for camera {camera_id}")

    # Clean up when thread stops
    if camera_id in hls_output_dirs:
        stop_simple_hls_stream(camera_id)


def create_hls_segment(
    camera_id: str, segment_index: int, frames: list, output_dir: str
):
    """Create an HLS segment from a list of frames."""
    try:
        segment_path = os.path.join(output_dir, f"segment_{segment_index:03d}.ts")
        temp_video = os.path.join(output_dir, f"temp_{segment_index:03d}.mp4")

        # Create temporary video from frames using OpenCV
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(temp_video, fourcc, 10.0, (640, 480))

        for frame in frames:
            if frame.shape != (480, 640, 3):
                frame = cv2.resize(frame, (640, 480))
            out.write(frame)

        out.release()

        # Convert to TS segment using FFmpeg (optimized for speed)
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            temp_video,
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-tune",
            "zerolatency",
            "-crf",
            "28",
            "-g",
            "10",  # Lower quality for speed, smaller GOP
            "-f",
            "mpegts",
            segment_path,
        ]

        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

        # Clean up temp file
        if os.path.exists(temp_video):
            os.remove(temp_video)

        if result.returncode == 0:
            # Only log every 10th segment to reduce noise
            if segment_index % 10 == 0:
                logger.debug(
                    f"Created HLS segment {segment_index} for camera {camera_id}"
                )
        else:
            logger.error(f"FFmpeg error creating segment: {result.stderr}")

    except Exception as e:
        logger.error(f"Error creating HLS segment for camera {camera_id}: {e}")


def create_hls_playlist(camera_id: str, latest_segment: int, output_dir: str):
    """Create or update the HLS playlist."""
    try:
        playlist_path = os.path.join(output_dir, "playlist.m3u8")

        # Keep last 5 segments for better buffering
        segments_to_keep = 5
        start_segment = max(0, latest_segment - segments_to_keep)

        playlist_content = [
            "#EXTM3U",
            "#EXT-X-VERSION:3",
            "#EXT-X-TARGETDURATION:3",
            "#EXT-X-MEDIA-SEQUENCE:{}".format(start_segment),
        ]

        for i in range(start_segment, latest_segment):
            segment_file = f"segment_{i:03d}.ts"
            segment_path = os.path.join(output_dir, segment_file)

            if os.path.exists(segment_path):
                playlist_content.append("#EXTINF:2.0,")
                playlist_content.append(f"/api/simple/hls/{camera_id}/{segment_file}")

        with open(playlist_path, "w") as f:
            f.write("\n".join(playlist_content))

        # Only log every 10th playlist update to reduce noise
        if latest_segment % 10 == 0:
            logger.debug(
                f"Updated HLS playlist for camera {camera_id} with {latest_segment} segments"
            )

    except Exception as e:
        logger.error(f"Error creating HLS playlist for camera {camera_id}: {e}")


def start_simple_hls_stream(camera_id: str) -> bool:
    """Start simple HLS streaming for a camera."""
    try:
        if camera_id in hls_threads:
            stop_simple_hls_stream(camera_id)

        # Create output directory
        create_hls_directory(camera_id)

        # Start generator thread
        stop_event = threading.Event()
        hls_stop_events[camera_id] = stop_event

        thread = threading.Thread(
            target=hls_generator_thread, args=(camera_id,), daemon=True
        )
        hls_threads[camera_id] = thread
        thread.start()

        logger.info(f"Started simple HLS stream for camera {camera_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to start simple HLS stream for camera {camera_id}: {e}")
        return False


def stop_simple_hls_stream(camera_id: str) -> bool:
    """Stop simple HLS streaming for a camera."""
    try:
        # Stop thread
        if camera_id in hls_stop_events:
            hls_stop_events[camera_id].set()
            del hls_stop_events[camera_id]

        if camera_id in hls_threads:
            thread = hls_threads[camera_id]
            thread.join(timeout=2)
            del hls_threads[camera_id]

        # Clean up directory
        if camera_id in hls_output_dirs:
            output_dir = hls_output_dirs[camera_id]
            try:
                import shutil

                shutil.rmtree(output_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up HLS directory: {e}")
            del hls_output_dirs[camera_id]

        logger.info(f"Stopped simple HLS stream for camera {camera_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to stop simple HLS stream for camera {camera_id}: {e}")
        return False


@router.post("/api/simple/hls/{camera_id}/start")
async def start_simple_hls(camera_id: str):
    """Start simple HLS streaming for a camera."""
    success = start_simple_hls_stream(camera_id)
    if success:
        return {"message": f"Simple HLS started for camera {camera_id}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to start simple HLS")


@router.get("/api/simple/hls/{camera_id}/playlist.m3u8")
async def get_simple_hls_playlist(camera_id: str):
    """Get simple HLS playlist for a camera."""
    try:
        # Auto-start if not running
        if camera_id not in hls_output_dirs:
            logger.info(f"Auto-starting simple HLS for camera {camera_id}")
            success = start_simple_hls_stream(camera_id)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to start HLS")

            # Wait for initial segments (shorter wait)
            await asyncio.sleep(3)

        if camera_id not in hls_output_dirs:
            raise HTTPException(status_code=404, detail="HLS stream not found")

        playlist_path = os.path.join(hls_output_dirs[camera_id], "playlist.m3u8")

        # Wait for playlist
        for i in range(10):
            if os.path.exists(playlist_path):
                break
            await asyncio.sleep(0.5)

        if not os.path.exists(playlist_path):
            raise HTTPException(status_code=404, detail="Playlist not ready")

        with open(playlist_path, "r") as f:
            content = f.read()

        return Response(
            content=content,
            media_type="application/vnd.apple.mpegurl",
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Origin, X-Requested-With",
            },
        )

    except Exception as e:
        logger.error(f"Error serving simple HLS playlist for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/simple/hls/{camera_id}/{segment_name}")
async def get_simple_hls_segment(camera_id: str, segment_name: str):
    """Get simple HLS segment for a camera."""
    try:
        if camera_id not in hls_output_dirs:
            raise HTTPException(status_code=404, detail="HLS stream not found")

        if not segment_name.endswith(".ts"):
            raise HTTPException(status_code=400, detail="Invalid segment name")

        segment_path = os.path.join(hls_output_dirs[camera_id], segment_name)

        if not os.path.exists(segment_path):
            raise HTTPException(status_code=404, detail="Segment not found")

        def generate_segment():
            with open(segment_path, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    yield chunk

        return StreamingResponse(
            generate_segment(),
            media_type="video/mp2t",
            headers={
                "Cache-Control": "public, max-age=3600",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Origin, X-Requested-With",
            },
        )

    except Exception as e:
        logger.error(
            f"Error serving simple HLS segment {segment_name} for camera {camera_id}: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))
