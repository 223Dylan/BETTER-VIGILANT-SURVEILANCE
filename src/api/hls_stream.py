from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
import cv2
import asyncio
import os
import tempfile
import subprocess
from typing import Dict, Optional
from loguru import logger
import time
import threading
import numpy as np
from pathlib import Path

router = APIRouter(tags=["hls"])

# Global references to shared data - will be injected from main server
shared_frames = {}
stream_manager = None
camera_controller = None

# HLS stream managers
hls_processes: Dict[str, subprocess.Popen] = {}
hls_output_dirs: Dict[str, str] = {}
hls_feed_threads: Dict[str, threading.Thread] = {}
hls_stop_events: Dict[str, threading.Event] = {}

def initialize_hls_data(frames_ref, stream_mgr, cam_ctrl):
    """Initialize access to shared camera data."""
    global shared_frames, stream_manager, camera_controller
    shared_frames = frames_ref
    stream_manager = stream_mgr
    camera_controller = cam_ctrl
    logger.info("HLS router initialized with shared camera data")

def create_hls_directory(camera_id: str) -> str:
    """Create a temporary directory for HLS files."""
    temp_dir = tempfile.mkdtemp(prefix=f"hls_{camera_id}_")
    hls_output_dirs[camera_id] = temp_dir
    logger.info(f"Created HLS directory for camera {camera_id}: {temp_dir}")
    return temp_dir

def start_hls_stream(camera_id: str, input_source: str) -> bool:
    """Start HLS streaming using FFmpeg."""
    try:
        if camera_id in hls_processes:
            # Stop existing process
            stop_hls_stream(camera_id)
        
        # Create output directory
        output_dir = create_hls_directory(camera_id)
        playlist_path = os.path.join(output_dir, "playlist.m3u8")
        segment_pattern = os.path.join(output_dir, "segment_%03d.ts")
        
        # FFmpeg command for HLS streaming with more robust settings
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",  # Overwrite output files
            "-f", "rawvideo",  # Input format (we'll pipe raw frames)
            "-pixel_format", "bgr24",
            "-video_size", "640x480",  # Adjust based on camera resolution
            "-framerate", "15",
            "-i", "pipe:0",  # Read from stdin
            "-c:v", "libx264",  # Video codec
            "-preset", "veryfast",  # Faster than ultrafast but more stable
            "-tune", "zerolatency",  # Low latency
            "-g", "15",  # GOP size (1 second at 15fps)
            "-keyint_min", "15",  # Minimum keyframe interval
            "-sc_threshold", "0",  # Disable scene detection
            "-f", "hls",  # Output format
            "-hls_time", "3",  # Segment duration (3 seconds for stability)
            "-hls_list_size", "3",  # Keep 3 segments in playlist
            "-hls_flags", "delete_segments+round_durations",  # Delete old segments and round durations
            "-hls_segment_filename", segment_pattern,
            "-hls_playlist_type", "event",  # Event playlist type
            "-hls_base_url", f"/api/video/hls/{camera_id}/",  # Base URL for segments
            playlist_path
        ]
        
        logger.info(f"Starting FFmpeg for HLS with command: {' '.join(ffmpeg_cmd)}")
        
        # Start FFmpeg process
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0
        )
        
        hls_processes[camera_id] = process
        logger.info(f"Started HLS stream for camera {camera_id} with FFmpeg PID {process.pid}")
        
        # Check if process started successfully
        import time
        time.sleep(0.1)  # Give it a moment
        if process.poll() is not None:
            # Process died immediately
            stdout, stderr = process.communicate()
            logger.error(f"FFmpeg process died immediately for camera {camera_id}")
            logger.error(f"FFmpeg stdout: {stdout.decode() if stdout else 'None'}")
            logger.error(f"FFmpeg stderr: {stderr.decode() if stderr else 'None'}")
            if camera_id in hls_processes:
                del hls_processes[camera_id]
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to start HLS stream for camera {camera_id}: {e}")
        return False

def stop_hls_stream(camera_id: str) -> bool:
    """Stop HLS streaming for a camera."""
    try:
        # Stop the frame feeding thread
        if camera_id in hls_stop_events:
            hls_stop_events[camera_id].set()
            del hls_stop_events[camera_id]
        
        if camera_id in hls_feed_threads:
            thread = hls_feed_threads[camera_id]
            thread.join(timeout=2)  # Wait max 2 seconds
            del hls_feed_threads[camera_id]
        
        # Stop the FFmpeg process
        if camera_id in hls_processes:
            process = hls_processes[camera_id]
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            del hls_processes[camera_id]
            logger.info(f"Stopped HLS stream for camera {camera_id}")
        
        # Clean up output directory
        if camera_id in hls_output_dirs:
            output_dir = hls_output_dirs[camera_id]
            try:
                import shutil
                shutil.rmtree(output_dir)
                logger.info(f"Cleaned up HLS directory for camera {camera_id}")
            except Exception as e:
                logger.warning(f"Failed to clean up HLS directory for camera {camera_id}: {e}")
            del hls_output_dirs[camera_id]
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to stop HLS stream for camera {camera_id}: {e}")
        return False

def feed_frame_to_hls(camera_id: str, frame_bytes: bytes) -> bool:
    """Feed a frame to the HLS stream."""
    try:
        if camera_id not in hls_processes:
            return False
            
        process = hls_processes[camera_id]
        if process.poll() is not None:
            # Process has died
            logger.warning(f"HLS process for camera {camera_id} has died")
            del hls_processes[camera_id]
            return False
        
        # Write frame to FFmpeg stdin
        process.stdin.write(frame_bytes)
        process.stdin.flush()
        return True
        
    except BrokenPipeError:
        logger.warning(f"Broken pipe for HLS stream {camera_id}")
        stop_hls_stream(camera_id)
        return False
    except Exception as e:
        logger.error(f"Failed to feed frame to HLS stream {camera_id}: {e}")
        return False

def frame_feeder_thread(camera_id: str):
    """Thread that continuously feeds frames to HLS stream."""
    logger.info(f"Starting frame feeder thread for HLS camera {camera_id}")
    stop_event = hls_stop_events[camera_id]
    frames_fed = 0
    last_log_time = time.time()
    
    while not stop_event.is_set():
        try:
            # Check if camera is running
            if camera_controller:
                statuses = camera_controller.get_all_camera_status()
                if statuses.get(camera_id) != "active":
                    logger.debug(f"Camera {camera_id} is not active, stopping HLS feed")
                    break
            
            # Check if FFmpeg process is still alive
            if camera_id not in hls_processes:
                logger.warning(f"No HLS process found for camera {camera_id}, stopping feeder")
                break
                
            process = hls_processes[camera_id]
            if process.poll() is not None:
                # Process died
                stdout, stderr = process.communicate()
                logger.error(f"FFmpeg process died for camera {camera_id}")
                logger.error(f"FFmpeg stdout: {stdout.decode() if stdout else 'None'}")
                logger.error(f"FFmpeg stderr: {stderr.decode() if stderr else 'None'}")
                del hls_processes[camera_id]
                break
            
            # Get frame data (similar to MJPEG implementation)
            frame_data = None
            
            # Try to get frame from stream_manager buffer first
            if stream_manager and hasattr(stream_manager, 'get_latest_frame'):
                frame_bytes = stream_manager.get_latest_frame(camera_id)
                if frame_bytes:
                    # Convert JPEG bytes back to frame for FFmpeg
                    nparr = np.frombuffer(frame_bytes, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        frame_data = frame
            
            # Fallback to shared_frames
            if frame_data is None and shared_frames and camera_id in shared_frames:
                frame = shared_frames[camera_id]
                if frame is not None:
                    frame_data = np.array(frame)
            
            # If still no frame data, create a test frame for FFmpeg
            if frame_data is None:
                # Create a simple test frame to keep FFmpeg alive
                frame_data = np.zeros((480, 640, 3), dtype=np.uint8)
                # Add some pattern so it's not completely black
                frame_data[::20, :] = [100, 100, 100]  # Horizontal lines
                frame_data[:, ::20] = [150, 150, 150]  # Vertical lines
                # Add timestamp
                import time
                timestamp = time.strftime("%H:%M:%S")
                cv2.putText(frame_data, f"Test Frame {timestamp}", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # If we have frame data, feed it to FFmpeg
            if frame_data is not None:
                # Ensure frame is the right size
                if frame_data.shape != (480, 640, 3):
                    frame_data = cv2.resize(frame_data, (640, 480))
                
                # Convert to bytes for FFmpeg (raw BGR24)
                raw_bytes = frame_data.astype(np.uint8).tobytes()
                success = feed_frame_to_hls(camera_id, raw_bytes)
                
                if success:
                    frames_fed += 1
                    # Log progress periodically
                    current_time = time.time()
                    if current_time - last_log_time >= 10:  # Every 10 seconds
                        logger.info(f"HLS feeder for {camera_id}: fed {frames_fed} frames")
                        last_log_time = current_time
                else:
                    logger.warning(f"Failed to feed frame to HLS for camera {camera_id}")
                    break
            else:
                logger.debug(f"No frame data available for HLS camera {camera_id}")
            
            # Wait for next frame (15 FPS)
            stop_event.wait(1/15)
            
        except Exception as e:
            logger.error(f"Error in HLS frame feeder for camera {camera_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            break
    
    logger.info(f"Frame feeder thread stopped for HLS camera {camera_id} after feeding {frames_fed} frames")

def auto_start_hls_stream(camera_id: str) -> bool:
    """Auto-start HLS stream for a camera if not already running."""
    try:
        if camera_id in hls_processes:
            # Already running
            process = hls_processes[camera_id]
            if process.poll() is None:
                return True
            else:
                # Process died, clean up
                stop_hls_stream(camera_id)
        
        # Start the HLS stream
        success = start_hls_stream(camera_id, "auto")
        if not success:
            return False
        
        # Start frame feeding thread
        stop_event = threading.Event()
        hls_stop_events[camera_id] = stop_event
        
        feed_thread = threading.Thread(
            target=frame_feeder_thread,
            args=(camera_id,),
            daemon=True
        )
        hls_feed_threads[camera_id] = feed_thread
        feed_thread.start()
        
        logger.info(f"Auto-started HLS stream for camera {camera_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to auto-start HLS stream for camera {camera_id}: {e}")
        return False

@router.get("/api/video/hls/{camera_id}/playlist.m3u8")
async def get_hls_playlist(camera_id: str):
    """Get HLS playlist for a camera, auto-starting stream if needed."""
    try:
        # Auto-start HLS stream if not already running
        if camera_id not in hls_output_dirs:
            logger.info(f"Auto-starting HLS stream for camera {camera_id}")
            success = auto_start_hls_stream(camera_id)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to start HLS stream")
            
            # Wait longer for FFmpeg to create initial segments and process some frames
            logger.info(f"Waiting for HLS stream to initialize for camera {camera_id}")
            await asyncio.sleep(5)
        
        if camera_id not in hls_output_dirs:
            raise HTTPException(status_code=404, detail="HLS stream not found")
        
        playlist_path = os.path.join(hls_output_dirs[camera_id], "playlist.m3u8")
        
        # Wait for playlist to be ready (up to 10 seconds)
        for i in range(20):  # 20 * 0.5 = 10 seconds
            if os.path.exists(playlist_path):
                break
            await asyncio.sleep(0.5)
        
        if not os.path.exists(playlist_path):
            raise HTTPException(status_code=404, detail="Playlist not ready yet, please try again")
        
        with open(playlist_path, 'r') as f:
            content = f.read()
        
        # Log for debugging
        logger.debug(f"Serving HLS playlist for camera {camera_id}, content length: {len(content)}")
        
        return Response(
            content=content,
            media_type="application/vnd.apple.mpegurl",
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Origin, X-Requested-With",
            }
        )
        
    except Exception as e:
        logger.error(f"Error serving HLS playlist for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/video/hls/{camera_id}/{segment_name}")
async def get_hls_segment(camera_id: str, segment_name: str):
    """Get HLS segment for a camera."""
    try:
        if camera_id not in hls_output_dirs:
            raise HTTPException(status_code=404, detail="HLS stream not found")
        
        # Validate segment name to prevent directory traversal
        if not segment_name.endswith('.ts') or '/' in segment_name or '..' in segment_name:
            raise HTTPException(status_code=400, detail="Invalid segment name")
        
        segment_path = os.path.join(hls_output_dirs[camera_id], segment_name)
        
        if not os.path.exists(segment_path):
            raise HTTPException(status_code=404, detail="Segment not found")
        
        def generate_segment():
            with open(segment_path, 'rb') as f:
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
            }
        )
        
    except Exception as e:
        logger.error(f"Error serving HLS segment {segment_name} for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/video/hls/{camera_id}/start")
async def start_camera_hls(camera_id: str):
    """Start HLS streaming for a camera."""
    try:
        # Use auto-start function with proper frame feeding
        success = auto_start_hls_stream(camera_id)
        
        if success:
            return {"message": f"HLS stream started for camera {camera_id}", "output_dir": hls_output_dirs.get(camera_id)}
        else:
            raise HTTPException(status_code=500, detail="Failed to start HLS stream")
            
    except Exception as e:
        logger.error(f"Error starting HLS stream for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/video/hls/{camera_id}/stop")
async def stop_camera_hls(camera_id: str):
    """Stop HLS streaming for a camera."""
    try:
        success = stop_hls_stream(camera_id)
        
        if success:
            return {"message": f"HLS stream stopped for camera {camera_id}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to stop HLS stream")
            
    except Exception as e:
        logger.error(f"Error stopping HLS stream for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/video/hls/{camera_id}/debug/status")
async def get_hls_status(camera_id: str):
    """Get HLS streaming status for a camera."""
    try:
        is_running = camera_id in hls_processes and hls_processes[camera_id].poll() is None
        
        # Check data availability
        shared_frames_available = shared_frames and camera_id in shared_frames and shared_frames[camera_id] is not None
        stream_manager_available = stream_manager and hasattr(stream_manager, 'get_latest_frame')
        stream_manager_frame = None
        if stream_manager_available:
            stream_manager_frame = stream_manager.get_latest_frame(camera_id) is not None
        
        camera_status = "unknown"
        if camera_controller:
            statuses = camera_controller.get_all_camera_status()
            camera_status = statuses.get(camera_id, "unknown")
        
        status = {
            "camera_id": camera_id,
            "hls_active": is_running,
            "output_directory": hls_output_dirs.get(camera_id),
            "process_id": hls_processes[camera_id].pid if is_running else None,
            "camera_status": camera_status,
            "shared_frames_available": shared_frames_available,
            "stream_manager_available": stream_manager_available,
            "stream_manager_frame_available": stream_manager_frame,
            "shared_frames_keys": list(shared_frames.keys()) if shared_frames else [],
            "hls_processes_count": len(hls_processes),
            "hls_feed_threads_count": len(hls_feed_threads)
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting HLS status for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 