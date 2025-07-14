# AI Model Setup Guide

This guide covers the setup and configuration of the LRCN (Long-term Recurrent Convolutional Networks) model for shoplifting detection.

## Model Overview

The system uses an LRCN neural network architecture that combines:

- **Convolutional Neural Networks (CNN)** - Extract spatial features from video frames
- **Long Short-Term Memory (LSTM)** - Analyze temporal patterns across frame sequences
- **Fully Connected Layers** - Binary classification (normal/shoplifting behavior)

## Model Specifications

### Input Requirements
- **Sequence Length:** 160 consecutive frames
- **Frame Size:** 90x90 pixels (grayscale)
- **Input Shape:** `(batch_size, 160, 90, 90, 1)`
- **Preprocessing:** Normalized to [0, 1] range

### Architecture Details
```python
# Simplified model architecture
model = Sequential([
    # CNN layers for spatial feature extraction
    TimeDistributed(Conv2D(32, (3, 3), activation='relu')),
    TimeDistributed(MaxPooling2D((2, 2))),
    TimeDistributed(Conv2D(64, (3, 3), activation='relu')),
    TimeDistributed(MaxPooling2D((2, 2))),
    TimeDistributed(Conv2D(128, (3, 3), activation='relu')),
    TimeDistributed(MaxPooling2D((2, 2))),
    
    # Flatten for LSTM
    TimeDistributed(Flatten()),
    
    # LSTM layers for temporal analysis
    LSTM(256, return_sequences=True),
    LSTM(128),
    
    # Classification layers
    Dense(64, activation='relu'),
    Dropout(0.5),
    Dense(1, activation='sigmoid')  # Binary classification
])
```

### Output
- **Binary Classification:** 0 = Normal behavior, 1 = Shoplifting behavior
- **Confidence Score:** Float value between 0.0 and 1.0
- **Threshold:** Configurable detection threshold (default: 0.6)

## Model File Setup

### Required Model File
Place your trained LRCN model at:
```
models/lrcn_160S_90_90Q.h5
```

### Model File Format
- **Format:** HDF5 (.h5) file
- **Framework:** TensorFlow/Keras
- **Size:** Typically 50-200MB depending on architecture
- **Permissions:** Ensure the file is readable by the application

### Alternative Model Path
If your model is located elsewhere, update the configuration:

**In .env file:**
```bash
MODEL_PATH=path/to/your/model.h5
```

**In config/config.yaml:**
```yaml
model:
  path: "path/to/your/model.h5"
```

## Model Training Requirements

If you need to train your own model, consider these requirements:

### Dataset Requirements
- **Video Duration:** 3-5 second clips (160 frames at ~30 FPS)
- **Resolution:** Original videos can be any resolution (will be resized to 90x90)
- **Format:** Common video formats (MP4, AVI, MOV)
- **Labeling:** Binary labels (0=normal, 1=shoplifting)
- **Dataset Size:** Minimum 10,000 clips, recommended 50,000+ clips

### Training Data Structure
```
training_data/
├── normal/
│   ├── normal_001.mp4
│   ├── normal_002.mp4
│   └── ...
└── shoplifting/
    ├── shoplifting_001.mp4
    ├── shoplifting_002.mp4
    └── ...
```

### Training Environment
- **Python:** 3.8+
- **TensorFlow:** 2.16+
- **Hardware:** GPU with 8GB+ VRAM recommended
- **Memory:** 32GB+ RAM for large datasets
- **Storage:** 500GB+ for training data and model checkpoints

### Training Script Example
```python
import tensorflow as tf
from tensorflow.keras import layers, models

def create_lrcn_model(sequence_length=160, frame_height=90, frame_width=90):
    model = models.Sequential([
        layers.TimeDistributed(
            layers.Conv2D(32, (3, 3), activation='relu'),
            input_shape=(sequence_length, frame_height, frame_width, 1)
        ),
        layers.TimeDistributed(layers.MaxPooling2D((2, 2))),
        layers.TimeDistributed(layers.Conv2D(64, (3, 3), activation='relu')),
        layers.TimeDistributed(layers.MaxPooling2D((2, 2))),
        layers.TimeDistributed(layers.Conv2D(128, (3, 3), activation='relu')),
        layers.TimeDistributed(layers.MaxPooling2D((2, 2))),
        layers.TimeDistributed(layers.Flatten()),
        
        layers.LSTM(256, return_sequences=True, dropout=0.3),
        layers.LSTM(128, dropout=0.3),
        
        layers.Dense(64, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy', 'precision', 'recall']
    )
    
    return model

# Train the model
model = create_lrcn_model()
history = model.fit(
    train_generator,
    epochs=50,
    validation_data=val_generator,
    callbacks=[
        tf.keras.callbacks.EarlyStopping(patience=10),
        tf.keras.callbacks.ModelCheckpoint('best_model.h5', save_best_only=True)
    ]
)

# Save final model
model.save('models/lrcn_160S_90_90Q.h5')
```

## Model Configuration

### Detection Thresholds
Configure detection sensitivity in `.env`:
```bash
DETECTION_THRESHOLD_LOW=0.3
DETECTION_THRESHOLD_MEDIUM=0.6
DETECTION_THRESHOLD_HIGH=0.8
```

Or in `config/config.yaml`:
```yaml
processing:
  probability_thresholds:
    low: 0.3
    medium: 0.6
    high: 0.8
```

### GPU Configuration
Enable GPU acceleration for faster inference:

**In .env:**
```bash
USE_GPU=true
```

**In config/config.yaml:**
```yaml
model:
  use_gpu: true
```

### Model Caching
Enable model caching to improve startup time:
```yaml
model:
  enable_model_caching: true
```

## Model Performance Optimization

### GPU Setup
1. **Install CUDA** (NVIDIA GPUs only):
   ```bash
   # Check CUDA installation
   nvidia-smi
   ```

2. **Install TensorFlow GPU**:
   ```bash
   pip install tensorflow-gpu
   ```

3. **Verify GPU Detection**:
   ```python
   import tensorflow as tf
   print("GPUs Available:", tf.config.list_physical_devices('GPU'))
   ```

### Memory Optimization
For systems with limited memory:

```yaml
model:
  batch_size: 1
  memory_limit_mb: 2048
```

### Inference Optimization
```yaml
processing:
  # Process every nth frame to reduce load
  skip_frames: 2
  
  # Reduce buffer size
  frame_buffer:
    max_size: 80  # Half the sequence length
```

## Model Validation

### Test Model Loading
```bash
python -c "
import tensorflow as tf
model = tf.keras.models.load_model('models/lrcn_160S_90_90Q.h5')
print('Model loaded successfully')
print('Input shape:', model.input_shape)
print('Output shape:', model.output_shape)
"
```

### Test Model Inference
```python
import numpy as np
import tensorflow as tf

# Load model
model = tf.keras.models.load_model('models/lrcn_160S_90_90Q.h5')

# Create dummy data (160 frames, 90x90 grayscale)
dummy_input = np.random.rand(1, 160, 90, 90, 1)

# Test inference
prediction = model.predict(dummy_input)
print(f"Test prediction: {prediction[0][0]:.4f}")
```

## Model Monitoring

### Performance Metrics
The system tracks:
- **Inference Time** - Time per prediction
- **Memory Usage** - GPU/CPU memory consumption
- **Accuracy Metrics** - True/False positives and negatives
- **Confidence Distribution** - Distribution of prediction scores

### Monitoring Dashboard
View model performance in Kibana:
- Navigate to http://localhost:5601
- Select "Detection Metrics" dashboard
- Monitor real-time model performance

## Troubleshooting

### Common Issues

**Model Loading Errors:**
```bash
# Check file exists and permissions
ls -la models/lrcn_160S_90_90Q.h5

# Verify TensorFlow version compatibility
python -c "import tensorflow as tf; print(tf.__version__)"
```

**GPU Issues:**
```bash
# Check CUDA installation
nvidia-smi

# Check TensorFlow GPU detection
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

**Memory Issues:**
- Reduce batch size to 1
- Enable memory growth for GPU
- Monitor system memory usage

**Performance Issues:**
- Enable GPU if available
- Increase skip_frames for lower accuracy/higher speed
- Reduce frame buffer size

### Error Messages

**"ValueError: Error when checking model input"**
- Check input shape matches model requirements (160, 90, 90, 1)
- Verify model architecture compatibility

**"ResourceExhaustedError: Out of memory"**
- Reduce batch size
- Enable GPU memory growth
- Free up system memory

**"InvalidArgumentError: GPU device not found"**
- Install CUDA and cuDNN
- Install tensorflow-gpu package
- Set USE_GPU=false to use CPU

## Model Updates

### Updating the Model
1. **Backup current model:**
   ```bash
   cp models/lrcn_160S_90_90Q.h5 models/lrcn_160S_90_90Q.h5.backup
   ```

2. **Replace model file:**
   ```bash
   cp /path/to/new/model.h5 models/lrcn_160S_90_90Q.h5
   ```

3. **Restart application:**
   ```bash
   python main.py
   ```

### Model Versioning
Consider implementing model versioning:
```
models/
├── lrcn_160S_90_90Q_v1.h5
├── lrcn_160S_90_90Q_v2.h5
└── lrcn_160S_90_90Q.h5  # Current model (symlink)
```

## Best Practices

1. **Model Backup** - Always backup working models before updates
2. **Testing** - Test new models thoroughly before production deployment
3. **Monitoring** - Continuously monitor model performance metrics
4. **Versioning** - Keep track of model versions and performance
5. **Documentation** - Document model training parameters and datasets used

## Related Documentation

- **[Frame Processing](02_FRAME_PROCESSING.md)** - Video preprocessing pipeline
- **[System Overview](01_SYSTEM_OVERVIEW.md)** - Overall system architecture
- **[Configuration Guide](11_CONFIGURATION_GUIDE.md)** - Complete configuration reference
- **[Troubleshooting](12_TROUBLESHOOTING_GUIDE.md)** - Common issues and solutions 