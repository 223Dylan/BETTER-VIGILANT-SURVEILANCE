# Frame Processing Pipeline

## Overview

The frame processing pipeline is responsible for converting raw video frames into format suitable for the LRCN model. It handles frame capture, preprocessing, sequence building, and performance optimization.

## Architecture

### Components

1. **FrameCapture** - Captures frames from camera sources
2. **FrameProcessor** - Processes and buffers frames
3. **SequenceBuilder** - Assembles frame sequences for model input
4. **FrameStorageService** - Handles frame persistence

### Data Flow

```
Camera Source → FrameCapture → FrameProcessor → SequenceBuilder → Model Input
                                      ↓
                              FrameStorageService
```

## Frame Processing Steps

### 1. Frame Capture

**Source:** `src/frame_capture.py`

- Captures frames from USB or IP cameras
- Handles connection failures and reconnection
- Enforces target FPS rate
- Provides frame statistics

**Configuration:**
```python
{
    "fps": 30,
    "resolution_width": 640,
    "resolution_height": 480,
    "timeout": 5.0
}
```

### 2. Frame Preprocessing

**Source:** `src/frame_processor.py`

The preprocessing pipeline performs the following operations:

#### Basic Preprocessing
- **Grayscale Conversion**: RGB → Grayscale (enabled by default)
- **Resizing**: Frames resized to 90x90 pixels
- **Normalization**: Pixel values normalized to [0,1] range

#### Advanced Preprocessing (Optional)
- **Background Removal**: Frame differencing to remove static elements
- **Shadow Removal**: Removes pixels below configurable threshold
- **Gaussian Blur**: Noise reduction and smoothing
- **Brightness/Contrast Adjustment**: Per-camera adjustments

#### Configuration

**Global Settings:** `config/config.yaml`
```yaml
preprocessing:
  grayscale: true
  background_removal: false
  shadow_removal: false
  shadow_threshold: 10
  gaussian_blur: false
  blur_kernel_size: 5
  brightness: 1.0
  contrast: 1.0
  augmentation:
    enabled: false
    horizontal_flip: true
    rotation_probability: 0.5
    rotation_angle: 30
```

**Per-Camera Settings:** Database configuration
```python
camera.brightness = 1.2  # Individual camera brightness
```

### 3. Sequence Building

The system builds sequences of 160 consecutive frames for LRCN model input:

- **Sequence Length**: 160 frames (configurable)
- **Frame Size**: 90x90x1 (grayscale)
- **Buffer Management**: Circular buffer for memory efficiency
- **Sequence Completion**: Triggers model prediction

### 4. Performance Optimization

#### Threading
- **Processing Thread**: Separate thread for frame processing
- **Queue Management**: Asynchronous frame queuing
- **Frame Dropping**: Intelligent frame dropping when queue is full

#### Memory Management
- **Pre-allocated Buffers**: Reduces memory allocation overhead
- **Circular Buffers**: Efficient memory usage
- **Frame Compression**: JPEG compression for storage

#### GPU Acceleration
```python
# OpenCV optimizations
cv2.setUseOptimized(True)
cv2.ocl.setUseOpenCL(use_gpu)
```

## API Reference

### FrameProcessor Class

#### Initialization
```python
processor = FrameProcessor(config)
processor.initialize()
processor.start()
```

#### Methods
- `process_frame(frame)` - Add frame to processing queue
- `is_sequence_ready()` - Check if sequence is complete
- `get_sequence()` - Retrieve completed sequence
- `update_brightness(value)` - Dynamic brightness adjustment
- `get_stats()` - Get performance statistics

### FrameCapture Class

#### Initialization
```python
capture = FrameCapture(config)
capture.initialize()
capture.start()
```

#### Methods
- `get_frame()` - Capture single frame
- `get_stats()` - Get capture statistics
- `cleanup()` - Release camera resources

## Performance Monitoring

### Metrics Tracked

1. **Processing FPS** - Frames processed per second
2. **Capture FPS** - Frames captured per second
3. **Queue Depth** - Number of frames in processing queue
4. **Processing Time** - Average time per frame
5. **Memory Usage** - RAM consumption
6. **Frame Drops** - Number of dropped frames

### Logging
```python
logger.info(f"Performance stats - FPS: {fps:.1f}, Queue: {queue_size}/{max_size}")
```

## Configuration Examples

### High-Performance Setup
```yaml
preprocessing:
  grayscale: true
  background_removal: false
  gaussian_blur: false
  brightness: 1.0

processing:
  use_gpu: true
  skip_frames: 0
  max_queue_size: 50
```

### Quality-Focused Setup
```yaml
preprocessing:
  grayscale: true
  background_removal: true
  shadow_removal: true
  gaussian_blur: true
  brightness: 1.1

processing:
  use_gpu: false
  skip_frames: 1
  max_queue_size: 20
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   - Reduce `max_queue_size`
   - Enable frame dropping
   - Check for memory leaks

2. **Low Processing FPS**
   - Enable GPU acceleration
   - Reduce frame resolution
   - Disable advanced preprocessing

3. **Frame Drops**
   - Increase `max_queue_size`
   - Optimize processing pipeline
   - Check system resources

### Debug Commands
```python
# Check processor status
stats = processor.get_stats()
print(f"Processing FPS: {stats['processing_fps']}")

# Monitor queue size
print(f"Queue: {processor.frame_buffer.qsize()}")

# Check sequence status
ready = processor.is_sequence_ready()
print(f"Sequence ready: {ready}")
```

## Best Practices

1. **Camera Configuration**
   - Use appropriate resolution (640x480 recommended)
   - Set stable FPS (15-30 FPS)
   - Ensure good lighting conditions

2. **Performance Tuning**
   - Enable GPU if available
   - Adjust queue sizes based on system resources
   - Monitor processing metrics regularly

3. **Quality vs Performance**
   - Disable advanced preprocessing for real-time systems
   - Use background removal only when necessary
   - Balance brightness/contrast adjustments

4. **Memory Management**
   - Regularly monitor memory usage
   - Clean up resources properly
   - Use frame compression for storage
