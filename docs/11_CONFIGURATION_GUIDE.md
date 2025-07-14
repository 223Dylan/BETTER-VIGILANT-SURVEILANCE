# Configuration Guide

This guide covers all configuration options for the Shoplifting Detection System.

## Configuration Files Overview

The system uses multiple configuration files:

- **`.env`** - Environment variables and secrets
- **`config/config.yaml`** - Main system configuration
- **`alembic.ini`** - Database migration settings
- **`docker-compose.dev.yml`** - Development infrastructure

## Environment Variables (.env)

### Database Configuration

```bash
# Main database connection
DATABASE_URL=postgresql://username:password@localhost:5432/shoplifting_detection

# Alternative format
DB_HOST=localhost
DB_PORT=5432
DB_NAME=shoplifting_detection
DB_USER=postgres
DB_PASSWORD=your_password

# Connection pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

### Security Settings

```bash
# JWT Authentication (CHANGE THESE!)
JWT_SECRET_KEY=your-super-secret-jwt-key-at-least-32-characters-long
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_ALGORITHM=HS256

# Data Encryption (CHANGE THESE!)
ENCRYPTION_PASSWORD=your-encryption-password-change-in-production
ENCRYPTION_SALT=your-encryption-salt-change-in-production

# API Keys (Legacy - use JWT instead)
API_KEY_ADMIN=admin123
API_KEY_USER=user123
API_KEY_VIEWER=viewer123
```

### Model Configuration

```bash
# AI Model Settings
MODEL_PATH=models/lrcn_160S_90_90Q.h5
USE_GPU=false
MODEL_SEQUENCE_LENGTH=160
MODEL_FRAME_SIZE=90

# Detection Thresholds
DETECTION_THRESHOLD_LOW=0.3
DETECTION_THRESHOLD_MEDIUM=0.6
DETECTION_THRESHOLD_HIGH=0.8
```

### API Server Settings

```bash
# Server Configuration
API_HOST=0.0.0.0
API_PORT=8001
API_WORKERS=4
API_DEBUG=true

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080

# Request Limits
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
MAX_CONTENT_LENGTH=10485760
MAX_HEADER_SIZE=8192
```

### External Services

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_CACHE_TTL=3600

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX_PREFIX=shoplifting-detection

# Logstash
LOGSTASH_HOST=localhost
LOGSTASH_PORT=5000

# Kibana
KIBANA_URL=http://localhost:5601
```

### Camera Settings

```bash
# Default Camera Settings
CAMERA_FPS=30
CAMERA_RESOLUTION_WIDTH=640
CAMERA_RESOLUTION_HEIGHT=480
CAMERA_TIMEOUT=5.0
DEFAULT_CAMERA_FPS=15
DEFAULT_CAMERA_RESOLUTION_WIDTH=640
DEFAULT_CAMERA_RESOLUTION_HEIGHT=480
```

### Processing Configuration

```bash
# Frame Processing
FRAME_QUEUE_SIZE=100
FRAME_PROCESSING_INTERVAL=0.033  # ~30 FPS
FRAME_RETENTION_DAYS=7
FRAME_BUFFER_SIZE=30
FRAME_WIDTH=320
FRAME_HEIGHT=240
JPEG_QUALITY=85
SKIP_FRAMES=0

# Performance
USE_GPU=false
FRAME_PROCESSING_THREADS=4
MAX_CONCURRENT_CAMERAS=10
MEMORY_LIMIT_MB=2048
```

### Logging Configuration

```bash
# Logging Settings
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_PATH=logs/main.log
LOG_MAX_SIZE=10
LOG_BACKUP_COUNT=5

# Log Categories
LOG_DETECTION_EVENTS=true
LOG_API_REQUESTS=true
LOG_CAMERA_EVENTS=true
LOG_SYSTEM_METRICS=true
```

### Notifications

```bash
# Email Notifications
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=admin@yourcompany.com
ALERT_EMAIL_RECIPIENTS=admin@localhost

# Webhook Notifications
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
WEBHOOK_TIMEOUT=10
SLACK_WEBHOOK=http://localhost:8000/api/slack
```

### File Storage

```bash
# File Paths
UPLOAD_DIRECTORY=uploads
TEMP_FRAMES_DIRECTORY=temp_frames
OUTPUT_DIRECTORY=output
MAX_UPLOAD_SIZE=100

# Video Settings
ALLOWED_VIDEO_EXTENSIONS=mp4,avi,mov,mkv
VIDEO_PROCESSING_TIMEOUT=300
```

### Development Settings

```bash
# Environment
ENVIRONMENT=development

# Feature Flags
REACT_APP_FEATURE_CAMERA=true
REACT_APP_FEATURE_ALERTS=true

# React Development
REACT_APP_API_URL=http://localhost:8001
DANGEROUSLY_DISABLE_HOST_CHECK=true
FAST_REFRESH=true
WDS_SOCKET_HOST=localhost
WDS_SOCKET_PORT=3000
WDS_SOCKET_PATH=/ws
```

## Main Configuration (config/config.yaml)

### Model Configuration

```yaml
model:
  # Path to the LRCN model file
  path: "models/lrcn_160S_90_90Q.h5"
  
  # Model parameters
  sequence_length: 160
  frame_size: 90
  input_shape: [160, 90, 90, 1]
  
  # Performance settings
  use_gpu: false
  batch_size: 1
  enable_model_caching: true
```

### Frame Processing

```yaml
preprocessing:
  # Basic preprocessing (required for LRCN)
  grayscale: true
  resize_width: 90
  resize_height: 90
  normalize: true
  
  # Advanced preprocessing (optional)
  background_removal: false
  shadow_removal: false
  shadow_threshold: 10
  gaussian_blur: false
  blur_kernel_size: 5
  
  # Color adjustments
  brightness: 1.0
  contrast: 1.0
  
  # Data augmentation
  augmentation:
    enabled: false
    horizontal_flip: true
    rotation_probability: 0.5
    rotation_angle: 30
```

### Processing Pipeline

```yaml
processing:
  # Performance settings
  use_gpu: false
  skip_frames: 0
  max_queue_size: 50
  processing_threads: 4
  
  # Detection thresholds
  probability_thresholds:
    low: 0.3
    medium: 0.6
    high: 0.8
  
  # Alert settings
  alert_settings:
    cooldown_period: 60
    max_alerts_per_minute: 5
    auto_dismiss_threshold: 0.2
  
  # Frame buffer
  frame_buffer:
    max_size: 160
    timeout: 10
```

### Camera Configuration

```yaml
cameras:
  # Default settings for all cameras
  defaults:
    fps: 15
    resolution_width: 640
    resolution_height: 480
    timeout: 5.0
    retry_attempts: 3
    retry_delay: 5
  
  # Individual camera configurations
  usb_camera_1:
    name: "Front Door Camera"
    source: 0  # USB camera index
    source_type: "usb"
    location: "Front Entrance"
    zone: "entrance"
    enabled: true
    detection_enabled: true
    detection_sensitivity: 0.6
    
  ip_camera_1:
    name: "Checkout Camera 1"
    source: "rtsp://username:password@192.168.1.100:554/stream"
    source_type: "rtsp"
    location: "Checkout Area"
    zone: "checkout"
    enabled: true
    detection_enabled: true
    detection_sensitivity: 0.7
    
  video_file_1:
    name: "Test Video"
    source: "uploads/videos/test_video.mp4"
    source_type: "file"
    location: "Test Environment"
    zone: "testing"
    enabled: false
    detection_enabled: true
    detection_sensitivity: 0.5
```

### Video Streaming

```yaml
streaming:
  # Protocol settings
  enable_hls: true
  enable_mjpeg: true
  
  # HLS configuration
  hls:
    segment_duration: 2
    playlist_size: 5
    
  # MJPEG configuration
  mjpeg:
    quality: 85
    fps: 15
    
  # Buffer settings
  buffer_size: 50
  max_clients: 10
```

### Database Settings

```yaml
database:
  # Connection (can be overridden by environment variables)
  host: "localhost"
  port: 5432
  name: "shoplifting_detection"
  user: "postgres"
  password: "password"
  
  # Pool settings
  pool_size: 20
  max_overflow: 30
  pool_timeout: 30
  pool_recycle: 3600
  
  # Migration settings
  auto_migrate: true
  backup_before_migration: true
```

### Logging Configuration

```yaml
logging:
  # Global log level
  level: "INFO"
  
  # File logging
  file:
    enabled: true
    path: "logs/main.log"
    max_size_mb: 10
    backup_count: 5
    
  # Console logging
  console:
    enabled: true
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
  # Component-specific loggers
  loggers:
    detection: "INFO"
    camera: "INFO"
    api: "INFO"
    database: "WARNING"
    performance: "INFO"
```

### Monitoring

```yaml
monitoring:
  # System monitoring
  enabled: true
  interval: 60
  
  # Metrics collection
  collect_system_metrics: true
  collect_detection_metrics: true
  collect_camera_metrics: true
  collect_api_metrics: true
  
  # ELK integration
  elk:
    enabled: true
    elasticsearch_url: "http://localhost:9200"
    logstash_host: "localhost"
    logstash_port: 5000
    index_prefix: "shoplifting-detection"
```

### Security

```yaml
security:
  # JWT settings
  jwt:
    secret_key: "change-this-secret-key-in-production"
    access_token_expire_minutes: 30
    refresh_token_expire_days: 7
    algorithm: "HS256"
    
  # Encryption
  encryption:
    enabled: true
    password: "change-this-encryption-password"
    salt: "change-this-encryption-salt"
    
  # Rate limiting
  rate_limiting:
    enabled: true
    requests_per_minute: 60
    requests_per_second: 10
    
  # CORS
  cors:
    enabled: true
    allowed_origins:
      - "http://localhost:3000"
      - "http://localhost:5173"
      - "http://localhost:8080"
    allow_credentials: true
```

### API Settings

```yaml
api:
  # Server configuration
  host: "0.0.0.0"
  port: 8001
  workers: 4
  debug: true
  reload: true
  
  # Documentation
  docs_url: "/docs"
  redoc_url: "/redoc"
  openapi_url: "/openapi.json"
  
  # Request settings
  max_request_size: 100  # MB
  request_timeout: 300   # seconds
  
  # WebSocket settings
  websocket:
    enabled: true
    max_connections: 100
    heartbeat_interval: 30
```

### Notifications

```yaml
notifications:
  # Email notifications
  email:
    enabled: false
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    username: "your-email@gmail.com"
    password: "your-app-password"
    from_address: "your-email@gmail.com"
    to_addresses:
      - "admin@yourcompany.com"
      
  # Webhook notifications
  webhook:
    enabled: false
    url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    timeout: 10
    retry_attempts: 3
    
  # Push notifications
  push:
    enabled: false
```

## Configuration Best Practices

### Security

1. **Change default secrets** - Never use default values in production
2. **Use environment variables** for sensitive data
3. **Generate strong JWT secrets**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
4. **Use HTTPS** in production
5. **Regularly rotate secrets**

### Performance

1. **Tune database connection pools** based on load
2. **Adjust processing threads** based on CPU cores
3. **Enable GPU** if available for model inference
4. **Configure frame processing** based on accuracy vs speed needs
5. **Monitor memory usage** and adjust limits

### Reliability

1. **Enable monitoring** and logging
2. **Set up health checks**
3. **Configure proper timeouts**
4. **Use retry mechanisms** for external services
5. **Set up backup procedures**

### Development vs Production

**Development Settings:**
```yaml
api:
  debug: true
  reload: true
  
logging:
  level: "DEBUG"
  
security:
  rate_limiting:
    enabled: false
```

**Production Settings:**
```yaml
api:
  debug: false
  reload: false
  workers: 8
  
logging:
  level: "INFO"
  
security:
  rate_limiting:
    enabled: true
    requests_per_minute: 100
```

## Configuration Validation

Test your configuration:

```bash
# Validate environment variables
python -c "from src.utils.config import load_config; print('Config OK')"

# Test database connection
python -c "from src.database.base import engine; engine.connect(); print('DB OK')"

# Validate camera configuration
python -c "from src.camera_manager import CameraManager; cm = CameraManager(); print('Cameras OK')"
```

## Common Configuration Issues

1. **Database connection failures** - Check DATABASE_URL format
2. **Model loading errors** - Verify MODEL_PATH and file existence
3. **Camera connection issues** - Check camera sources and permissions
4. **Port conflicts** - Ensure ports are available and not in use
5. **Memory issues** - Adjust memory limits and processing threads

For troubleshooting specific issues, see the [Troubleshooting Guide](12_TROUBLESHOOTING_GUIDE.md). 