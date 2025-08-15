# Frame Injection Loop Fix Summary

## Problem Description

The system was continuously processing video frames and running shoplifting detection even when cameras were switched off through the UI. This happened because:

1. **Frame injection loop runs continuously** - A daemon thread was injecting frames at 30 FPS regardless of camera status
2. **No camera status checking** - The injection loop didn't verify if cameras were actually enabled/running
3. **No shutdown mechanism** - The injection loop couldn't be stopped gracefully
4. **Background processes continue** - Celery tasks and video processing continued even with stopped cameras

## Root Cause

The frame injection loop in `src/api/video_stream.py` was designed to run continuously without checking:
- Whether cameras are enabled in the database
- Whether cameras have "active" status
- Whether the system is shutting down

## Fixes Implemented

### 1. Camera Status Validation in Frame Injection

**File**: `src/api/video_stream.py`
**Change**: Modified the injection loop to check camera status before injecting frames

```python
# Only inject frames if camera is actually enabled and running
if frame_bytes and stream_manager._initialized:
    try:
        # Check if camera is enabled in database
        from src.services.camera_db_service import camera_db_service
        camera = camera_db_service.get_camera_by_id(camera_id)

        if camera and camera.enabled and camera.status == "active":
            # Inject frame into stream manager
            stream_manager.inject_frame_for_streaming(camera_id, frame_bytes)
            logger.debug(f"Injected shared frame for {camera_id}")
        else:
            # Camera is disabled or stopped - skip frame injection
            logger.debug(f"Skipping frame injection for disabled/stopped camera: {camera_id}")
            # Remove the frame from shared memory to prevent accumulation
            if key in shared_data:
                del shared_data[key]
    except Exception as db_error:
        logger.warning(f"Error checking camera status for {camera_id}: {db_error}")
        # If we can't check status, skip injection to be safe
        continue
```

### 2. Graceful Shutdown Mechanism

**File**: `src/api/video_stream.py`
**Change**: Added signal handlers and shutdown control

```python
def signal_handler(signum, frame):
    """Handle shutdown signals to gracefully stop the injection loop."""
    global _injection_running
    logger.info(f"Received signal {signum}, shutting down frame injection loop...")
    _injection_running = False

def start_frame_injection_task():
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    def injection_loop():
        global _injection_running
        while _injection_running:  # Check shutdown flag
            # ... injection logic ...
```

### 3. API Control Endpoints

**File**: `src/api/video_stream.py`
**Change**: Added REST endpoints to control frame injection

```python
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
    # ... implementation ...

@router.get("/control/injection/status")
async def get_injection_status():
    """Get the status of the frame injection loop."""
    # ... implementation ...
```

### 4. Camera Controller Integration

**File**: `src/camera_controller.py`
**Change**: Integrated frame injection management with camera lifecycle

```python
def stop_all_cameras(self):
    """Stops all camera processes and updates database."""
    logger.info("Stopping all camera processes...")
    for camera_id in list(self.processes.keys()):
        self.stop_camera(camera_id)
    logger.info("All camera processes stopped.")

    # Close database session
    camera_db_service.close_session()

    # Optionally stop frame injection if no cameras are running
    self._check_and_manage_frame_injection()

def _check_and_manage_frame_injection(self):
    """Check if any cameras are running and manage frame injection accordingly."""
    try:
        # Check if any cameras are enabled and active
        cameras = camera_db_service.get_all_cameras()
        active_cameras = [c for c in cameras if c.enabled and c.status == "active"]

        if not active_cameras:
            logger.info("No active cameras detected, considering stopping frame injection")
            try:
                from src.api.video_stream import stop_frame_injection
                stop_frame_injection()
                logger.info("Frame injection loop stopped due to no active cameras")
            except ImportError:
                logger.debug("Could not import frame injection control functions")
        else:
            logger.info(f"Found {len(active_cameras)} active cameras, keeping frame injection running")
    except Exception as e:
        logger.warning(f"Error checking camera status for frame injection management: {e}")
```

## How It Works Now

### When Cameras Are Started:
1. Camera controller starts camera processes
2. Calls `_ensure_frame_injection_running()` to start frame injection
3. Frame injection loop begins processing frames for active cameras

### When Cameras Are Stopped:
1. Camera controller stops camera processes
2. Updates database status to "stopped" and sets `enabled=False`
3. Frame injection loop checks camera status before injecting frames
4. Skips frames for disabled/stopped cameras
5. Optionally stops frame injection if no cameras are active

### When System Shuts Down:
1. Main process receives shutdown signal
2. Calls `camera_controller.stop_all_cameras()`
3. Camera controller stops all cameras and frame injection
4. Frame injection loop receives shutdown signal and stops gracefully

## Benefits

1. **No more continuous processing** - Frames are only processed for active cameras
2. **Proper resource management** - Frame injection stops when not needed
3. **Graceful shutdown** - System can be stopped cleanly
4. **API control** - Frame injection can be controlled via REST endpoints
5. **Automatic management** - Frame injection starts/stops with cameras automatically

## Testing

Use the provided test script to verify the control endpoints:

```bash
python test_frame_injection_control.py
```

## API Endpoints

- `POST /api/video/control/injection/stop` - Stop frame injection
- `POST /api/video/control/injection/start` - Start frame injection
- `GET /api/video/control/injection/status` - Get injection status

## Next Steps

1. **Test the fixes** - Start the system and verify cameras can be stopped properly
2. **Monitor performance** - Ensure no unnecessary frame processing occurs
3. **Consider additional optimizations** - Such as dynamic frame rate adjustment based on camera count
