from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
import os
import tempfile
import subprocess
import asyncio
from loguru import logger
from pathlib import Path

router = APIRouter(tags=["hls-test"])

# Simple test HLS directory
test_hls_dir = None
test_process = None


def create_test_hls_stream():
    """Create a simple test HLS stream using FFmpeg test source."""
    global test_hls_dir, test_process

    try:
        # Create temporary directory
        test_hls_dir = tempfile.mkdtemp(prefix="hls_test_")
        playlist_path = os.path.join(test_hls_dir, "test.m3u8")
        segment_pattern = os.path.join(test_hls_dir, "test_%03d.ts")

        # Simple FFmpeg command with test source
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",  # Use lavfi (libavfilter) input
            "-i",
            "testsrc=duration=3600:size=640x480:rate=15",  # Test pattern source
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-tune",
            "zerolatency",
            "-g",
            "15",
            "-f",
            "hls",
            "-hls_time",
            "3",
            "-hls_list_size",
            "3",
            "-hls_flags",
            "delete_segments",
            "-hls_segment_filename",
            segment_pattern,
            playlist_path,
        ]

        logger.info(f"Starting test HLS with command: {' '.join(ffmpeg_cmd)}")

        # Start FFmpeg process
        test_process = subprocess.Popen(
            ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        logger.info(f"Started test HLS with PID {test_process.pid}")
        return True

    except Exception as e:
        logger.error(f"Failed to start test HLS: {e}")
        return False


@router.post("/api/test/hls/start")
async def start_test_hls():
    """Start a simple test HLS stream."""
    success = create_test_hls_stream()
    if success:
        return {"message": "Test HLS started", "directory": test_hls_dir}
    else:
        raise HTTPException(status_code=500, detail="Failed to start test HLS")


@router.get("/api/test/hls/playlist.m3u8")
async def get_test_playlist():
    """Get test HLS playlist."""
    if not test_hls_dir:
        raise HTTPException(status_code=404, detail="Test HLS not started")

    playlist_path = os.path.join(test_hls_dir, "test.m3u8")

    # Wait for playlist to be ready
    for i in range(20):
        if os.path.exists(playlist_path):
            break
        await asyncio.sleep(0.5)

    if not os.path.exists(playlist_path):
        raise HTTPException(status_code=404, detail="Test playlist not ready")

    with open(playlist_path, "r") as f:
        content = f.read()

    return Response(
        content=content,
        media_type="application/vnd.apple.mpegurl",
        headers={
            "Cache-Control": "no-cache",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/api/test/hls/{segment_name}")
async def get_test_segment(segment_name: str):
    """Get test HLS segment."""
    if not test_hls_dir:
        raise HTTPException(status_code=404, detail="Test HLS not started")

    if not segment_name.endswith(".ts"):
        raise HTTPException(status_code=400, detail="Invalid segment")

    segment_path = os.path.join(test_hls_dir, segment_name)

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
        },
    )
