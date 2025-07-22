# Camera Management System

## Overview

The Camera Management System handles multiple camera feeds, supports both USB and IP cameras, and provides centralized configuration, monitoring, and control capabilities.

## Architecture

### Components

1. **CameraManager** - Central camera orchestration
2. **CameraController** - Individual camera control
3. **CameraPipeline** - Per-camera processing pipeline
4. **Camera Database Models** - Camera configuration storage
5. **Video Stream Manager** - Real-time streaming coordination

### Data Flow

```
Database Config → CameraManager → CameraController → FrameCapture → FrameProcessor
                                        ↓
                              VideoStreamManager → API/WebSocket
```

## Camera Types

### USB Cameras

**Configuration:**
```python
{
    "id": "usb-cam-001",
    "name": "Front Door Camera",
    "source": 0,  # USB device index
    "camera_type": "usb",
    "resolution_width": 640,
    "resolution_height": 480,
    "fps": 30
}
```

### IP Cameras (RTSP)

**Configuration:**
```python
{
    "id": "ip-cam-001",
    "name": "Checkout Area Camera",
    "source": "rtsp://username:password@192.168.1.100:554/stream",
    "camera_type": "ip",
    "ip_address": "192.168.1.100",
    "port": 554,
    "credentials": {
        "username": "admin",
        "password": "password123"
    }
}
```

## Database Schema

### Camera Model

**Source:** `src/database/models/camera.py`

```python
class Camera(Base):
    __tablename__ = "cameras"

    # Primary identification
    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True)

    # Connection details
    source = Column(String(255), nullable=False)
    source_type = Column(String(50), default="webcam")

    # Video settings
    fps = Column(Integer, default=15)
    resolution_width = Column(Integer, default=640)
    resolution_height = Column(Integer, default=480)
    brightness = Column(Float, default=1.0)

    # Processing settings
    detection_enabled = Column(Boolean, default=True)
    detection_sensitivity = Column(Float, default=0.5)
    recording_enabled = Column(Boolean, default=False)

    # Location metadata
    location = Column(String(255))
    zone = Column(String(100))

    # Advanced settings (JSON)
    advanced_settings = Column(JSON, default={})

    # Status tracking
    status = Column(String(50), default="stopped")
    error_message = Column(Text)
    last_online = Column(DateTime(timezone=True))
```

## Camera Manager

### Initialization

**Source:** `src/camera_manager.py`

```python
class CameraManager(BaseComponent):
    def __init__(self):
        self.cameras = {}
        self.camera_processes = {}
        self.shared_data = {
            'frames': {},
            'stats': {},
            'commands': {}
        }

    def initialize_cameras(self, camera_configs):
        """Initialize cameras from database configuration."""
        for config in camera_configs:
            if config.enabled:
                self.add_camera(config)
        return True

    def add_camera(self, camera_config):
        """Add and start a new camera."""
        camera_id = camera_config.id

        # Create camera process
        process = CameraPipeline(
            camera_config=camera_config,
            shared_data=self.shared_data
        )

        self.camera_processes[camera_id] = process
        process.start()

        logger.info(f"Camera {camera_id} added and started")
```

### Camera Control

```python
def start_camera(self, camera_id: str):
    """Start specific camera."""
    if camera_id in self.camera_processes:
        self.camera_processes[camera_id].start()
        return True
    return False

def stop_camera(self, camera_id: str):
    """Stop specific camera."""
    if camera_id in self.camera_processes:
        self.camera_processes[camera_id].stop()
        return True
    return False

def update_camera_brightness(self, camera_id: str, brightness: float):
    """Update camera brightness setting."""
    if camera_id in self.shared_data['commands']:
        self.shared_data['commands'][camera_id] = {
            'type': 'brightness_update',
            'value': brightness
        }
        return True
    return False
```

## Camera Pipeline

### Pipeline Process

**Source:** `src/camera_pipeline.py`

```python
class CameraPipeline:
    def __init__(self, camera_config, shared_data):
        self.camera_config = camera_config
        self.shared_data = shared_data
        self._stop_event = threading.Event()
        self._process = None

    def run(self):
        """Main pipeline execution."""
        try:
            # Load configuration
            global_config = load_config("config/config.yaml")

            # Initialize components
            self.camera_manager = CameraManager()
            self.frame_processor = FrameProcessor(model_params)

            # Start processing loop
            while not self._stop_event.is_set():
                frame = self.camera_manager.get_frame(self.camera_config.id)

                if frame is not None:
                    self._handle_frame(frame)

                time.sleep(self._min_frame_interval)

        except Exception as e:
            logger.error(f"Pipeline error for {self.camera_config.id}: {e}")
        finally:
            self.cleanup()
```

### Frame Handling

```python
def _handle_frame(self, frame):
    """Process individual frame."""
    # Stream via video manager
    from src.api.video_stream import stream_manager
    if stream_manager:
        success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if success:
            stream_manager.process_frame(self.camera_config.id, buffer.tobytes())

    # Store for other uses
    self.shared_data['frames'][self.camera_config.id] = frame

    # Process for predictions
    if self.frame_processor:
        self.frame_processor.process_frame(frame)
        self._check_and_trigger_predictions()

    # Update statistics
    self._update_stats()
```

## API Integration

### Camera Endpoints

**Source:** `src/routers/cameras.py`

```python
@router.get("/")
async def get_cameras(db: Session = Depends(get_db)):
    """Get all cameras."""
    cameras = db.query(Camera).all()
    return cameras

@router.get("/{camera_id}")
async def get_camera(camera_id: str, db: Session = Depends(get_db)):
    """Get specific camera."""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera

@router.post("/")
async def create_camera(camera: CameraCreate, db: Session = Depends(get_db)):
    """Create new camera."""
    db_camera = Camera(**camera.dict())
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    return db_camera

@router.put("/{camera_id}")
async def update_camera(
    camera_id: str,
    camera_update: CameraUpdate,
    db: Session = Depends(get_db)
):
    """Update camera configuration."""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    for field, value in camera_update.dict(exclude_unset=True).items():
        setattr(camera, field, value)

    db.commit()
    return camera

@router.post("/{camera_id}/control")
async def control_camera(camera_id: str, action: CameraAction):
    """Control camera (start/stop/restart)."""
    from src.camera_manager import camera_manager

    if action.action == "start":
        result = camera_manager.start_camera(camera_id)
    elif action.action == "stop":
        result = camera_manager.stop_camera(camera_id)
    elif action.action == "restart":
        camera_manager.stop_camera(camera_id)
        result = camera_manager.start_camera(camera_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    return {"success": result, "action": action.action}
```

## Video Streaming

### Stream Manager

**Source:** `src/video_stream_manager.py`

```python
class VideoStreamManager:
    def __init__(self, buffer_size=50):
        self.streams = {}
        self.buffer_size = buffer_size
        self._running = False

    def process_frame(self, camera_id: str, frame: bytes) -> bool:
        """Add frame to camera stream buffer."""
        if camera_id not in self.streams:
            self.streams[camera_id] = deque(maxlen=self.buffer_size)

        self.streams[camera_id].append(frame)
        return True

    def get_latest_frame(self, camera_id: str) -> Optional[bytes]:
        """Get latest frame for camera."""
        if camera_id in self.streams and self.streams[camera_id]:
            return self.streams[camera_id][-1]
        return None
```

### HLS Streaming

**Source:** `src/api/hls_stream.py`

```python
@router.get("/{camera_id}/stream.m3u8")
async def get_hls_playlist(camera_id: str):
    """Get HLS playlist for camera."""
    playlist = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:2
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:2.0,
{camera_id}_segment_0.ts
#EXT-X-ENDLIST
"""
    return Response(content=playlist, media_type="application/vnd.apple.mpegurl")

@router.get("/{camera_id}/stream.ts")
async def get_hls_segment(camera_id: str):
    """Get HLS video segment."""
    frame = stream_manager.get_latest_frame(camera_id)
    if frame:
        return Response(content=frame, media_type="video/mp2t")
    raise HTTPException(status_code=404, detail="No frame available")
```

## Configuration Management

### Database Configuration

```python
# Create camera via API
camera_data = {
    "id": "checkout-cam-01",
    "name": "Checkout Camera 1",
    "source": "rtsp://admin:pass@192.168.1.100:554/stream",
    "source_type": "rtsp",
    "fps": 30,
    "resolution_width": 1920,
    "resolution_height": 1080,
    "detection_enabled": True,
    "detection_sensitivity": 0.6,
    "location": "Checkout Area",
    "zone": "checkout-1"
}

# Save to database
camera = Camera(**camera_data)
db.add(camera)
db.commit()
```

### Runtime Configuration

```python
# Update camera settings
await update_camera(camera_id, {
    "brightness": 1.2,
    "detection_sensitivity": 0.7,
    "fps": 25
})

# Control camera
await control_camera(camera_id, {"action": "restart"})
```

## Monitoring and Health Checks

### Health Metrics

```python
def get_camera_health_metrics(camera_id: str):
    """Get health metrics for camera."""
    return {
        "status": camera.status,
        "last_frame_time": camera.last_online,
        "fps_actual": get_actual_fps(camera_id),
        "fps_target": camera.fps,
        "error_count": get_error_count(camera_id),
        "uptime": calculate_uptime(camera_id)
    }
```

### Status Monitoring

```python
def monitor_camera_status():
    """Monitor all camera statuses."""
    for camera_id, process in camera_processes.items():
        if process.is_alive():
            status = "active"
        else:
            status = "stopped"

        # Update database
        update_camera_status(camera_id, status)

        # Log metrics
        log_camera_health_metrics(camera_id, {
            "status": status,
            "fps": get_fps(camera_id),
            "timestamp": datetime.utcnow()
        })
```

## Troubleshooting

### Common Issues

1. **Camera Connection Failures**
   ```python
   # Check camera accessibility
   cap = cv2.VideoCapture(camera_source)
   if not cap.isOpened():
       logger.error(f"Cannot open camera: {camera_source}")

   # Test RTSP connection
   import requests
   try:
       response = requests.get(f"http://{ip_address}/", timeout=5)
   except requests.RequestException as e:
       logger.error(f"Camera unreachable: {e}")
   ```

2. **Performance Issues**
   - Reduce FPS for multiple cameras
   - Lower resolution if needed
   - Check network bandwidth for IP cameras

3. **Frame Drops**
   - Increase buffer sizes
   - Optimize processing pipeline
   - Check system resources

### Debug Commands

```python
# Check camera status
status = camera_manager.get_camera_status(camera_id)
print(f"Camera status: {status}")

# Get frame statistics
stats = camera_manager.get_stats(camera_id)
print(f"FPS: {stats['fps']}, Frames: {stats['total_frames']}")

# Test camera connection
result = test_camera_connection(camera_config)
print(f"Connection test: {result}")
```

## Best Practices

1. **Camera Setup**
   - Use stable network connections for IP cameras
   - Configure appropriate resolution and FPS
   - Test cameras before deployment

2. **Resource Management**
   - Monitor system resources with multiple cameras
   - Use appropriate buffer sizes
   - Implement proper cleanup procedures

3. **Error Handling**
   - Implement automatic reconnection for failed cameras
   - Log all camera events and errors
   - Provide fallback mechanisms

4. **Security**
   - Use secure credentials for IP cameras
   - Implement camera access controls
   - Monitor for unauthorized access attempts
