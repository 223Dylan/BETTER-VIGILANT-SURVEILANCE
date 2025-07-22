# LRCN Model System

## Overview

The Long-term Recurrent Convolutional Networks (LRCN) model is the core deep learning component responsible for analyzing video sequences to detect shoplifting behavior. It combines spatial feature extraction via CNNs with temporal analysis through LSTMs.

## Model Architecture

### LRCN Structure

The model follows the architecture described in the research paper "Early Detection of Collective or Individual Theft Attempts Using Long-term Recurrent Convolutional Networks":

```
Input (160, 90, 90, 1) → CNN Layers → LSTM → Dense → Output (2)
```

### Components

1. **Convolutional Layers** - Extract spatial features from individual frames
2. **LSTM Layer** - Process temporal sequences and capture behavior patterns
3. **Dense Layers** - Final classification with dropout for regularization
4. **Output Layer** - Binary classification (shoplifting vs normal behavior)

### Model Specifications

- **Input Shape**: (160, 90, 90, 1) - 160 grayscale frames of 90x90 pixels
- **Output Shape**: (2,) - Binary classification probabilities
- **Model File**: `models/lrcn_160S_90_90Q.h5`
- **Framework**: TensorFlow/Keras 2.15.0

## Implementation

### Model Loading

**Source:** `src/model.py`

```python
def load_model(model_path: str) -> tf.keras.Model:
    """Load TensorFlow model with caching and optimization."""

    # Custom objects for legacy compatibility
    custom_objects = {
        'Conv2D': Conv2D,
        'MaxPooling2D': MaxPooling2D,
        'Dense': Dense,
        'Flatten': Flatten,
        'LSTM': LegacyLSTM,
        'TimeDistributed': TimeDistributed,
        'Dropout': Dropout
    }

    model = tf.keras.models.load_model(
        model_path,
        custom_objects=custom_objects,
        compile=False
    )

    return model
```

### Model Handler

**Source:** `src/model_handler.py`

```python
class ModelHandler(BaseComponent):
    """Handles model loading and prediction for shoplifting detection."""

    def __init__(self, config=None):
        self.model_path = config.get('model.path', 'models/lrcn_160S_90_90Q.h5')
        self.input_shape = tuple(config.get('model.input_shape', [160, 90, 90, 1]))
        self.probability_thresholds = config.get('processing.probability_thresholds', {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8
        })
```

### Prediction Pipeline

**Source:** `src/tasks.py`

```python
@app.task(name='shoplifting_detection.predict_sequence', bind=True, max_retries=3)
def predict_sequence(self, sequence_data):
    """Predict shoplifting probability for a sequence of frames."""

    # Make prediction
    prediction = model.predict(np.expand_dims(sequence, axis=0), verbose=0)[0]

    # Process output
    if prediction.shape == (2,):
        probability = float(prediction[1])  # Shoplifting probability
        label = int(prediction[1] > 0.5)

    return {
        'probability': probability,
        'label': label,
        'is_shoplifting': probability > 0.5,
        'confidence_level': get_confidence_level(probability)
    }
```

## Configuration

### Model Configuration

**File:** `config/config.yaml`

```yaml
model:
  path: "models/lrcn_160S_90_90Q.h5"
  sequence_length: 160
  frame_size: 90
  input_shape: [160, 90, 90, 1]

processing:
  use_gpu: false
  probability_thresholds:
    low: 0.3
    medium: 0.6
    high: 0.8
```

### TensorFlow Optimizations

```python
# Enable XLA compilation
tf.config.optimizer.set_jit(True)

# Optimization flags
tf.config.optimizer.set_experimental_options({
    'layout_optimizer': True,
    'constant_folding': True,
    'shape_optimization': True,
    'remapping': True,
    'arithmetic_optimization': True,
    'dependency_optimization': True,
    'loop_optimization': True,
    'function_optimization': True,
    'debug_stripper': True,
    'disable_model_pruning': False,
    'scoped_allocator_optimization': True,
    'pin_to_host_optimization': True,
    'implementation_selector': True,
    'auto_mixed_precision': True
})
```

## Prediction Process

### 1. Sequence Preparation

```python
# Input requirements
sequence_shape = (160, 90, 90, 1)  # 160 frames, 90x90 grayscale
input_data = np.expand_dims(sequence, axis=0)  # Add batch dimension
```

### 2. Model Inference

```python
# Prediction
prediction = model.predict(input_data, verbose=0)[0]

# Output processing
probability = float(prediction[1])  # Shoplifting probability
confidence = max(prediction[0], prediction[1])  # Overall confidence
```

### 3. Result Interpretation

```python
def get_confidence_level(probability):
    """Determine confidence level based on probability."""
    if probability >= 0.8:
        return "high"
    elif probability >= 0.6:
        return "medium"
    elif probability >= 0.3:
        return "low"
    else:
        return "very_low"

def get_threat_level(probability):
    """Determine threat level."""
    if probability >= 0.8:
        return "critical"
    elif probability >= 0.6:
        return "high"
    elif probability >= 0.4:
        return "medium"
    else:
        return "low"
```

## Performance Optimization

### Model Caching

```python
# Global model cache to avoid reloading
_model_cache = {}

def load_model(model_path: str) -> tf.keras.Model:
    if model_path in _model_cache:
        return _model_cache[model_path]

    model = tf.keras.models.load_model(model_path, ...)
    _model_cache[model_path] = model
    return model
```

### Batch Processing

```python
def predict_batch(sequences):
    """Process multiple sequences in batch for efficiency."""
    batch_input = np.array(sequences)
    predictions = model.predict(batch_input, verbose=0)

    results = []
    for pred in predictions:
        results.append({
            'probability': float(pred[1]),
            'is_shoplifting': pred[1] > 0.5
        })

    return results
```

### GPU Acceleration

```python
# Enable GPU memory growth
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)

# Use tf.function for better performance
@tf.function(jit_compile=True)
def predict_function(x):
    return model(x, training=False)
```

## Monitoring and Metrics

### Performance Metrics

```python
@dataclass
class PredictionMetrics:
    confidence: float
    label: str
    is_shoplifting: bool
    prediction_time_ms: float
    sequence_frames: int
    model_version: str = "lrcn_160S_90_90Q"
```

### Logging

```python
# Detailed sequence analysis
logger.info(f"[STATS] Sequence: mean={seq_mean:.4f}, std={seq_std:.4f}")
logger.info(f"[PREDICTION] Result: {probability:.2f} ({label})")

# Performance tracking
processing_time = time.time() - start_time
logger.info(f"Prediction time: {processing_time*1000:.1f}ms")
```

## Model Training Information

### Training Dataset

Based on the research paper, the model was trained on:
- Video sequences of shoplifting scenarios
- Normal customer behavior sequences
- Data augmentation techniques (horizontal flip, rotation)

### Preprocessing for Training

```python
def Pre_Process_Video(current_frame, previous_frame):
    # Frame differencing for motion detection
    diff = cv2.absdiff(current_frame, previous_frame)

    # Gaussian blur to reduce noise
    diff = cv2.GaussianBlur(diff, (3,3), 0)

    # Resize to model input size
    resized_frame = cv2.resize(diff, (90, 90))

    # Convert to grayscale
    gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)

    # Normalize
    normalized_frame = gray_frame / 255

    return normalized_frame
```

## Troubleshooting

### Common Issues

1. **Model Loading Errors**
   ```python
   # Legacy LSTM compatibility
   class LegacyLSTM(LSTM):
       def __init__(self, *args, **kwargs):
           legacy_params = ['time_major', 'unroll']
           for param in legacy_params:
               kwargs.pop(param, None)
           super().__init__(*args, **kwargs)
   ```

2. **Memory Issues**
   - Enable GPU memory growth
   - Use batch processing efficiently
   - Clear model cache when needed

3. **Performance Issues**
   - Enable XLA compilation
   - Use tf.function decorators
   - Optimize input pipeline

### Debug Commands

```python
# Check model status
print(f"Model loaded: {model is not None}")
print(f"Input shape: {model.input_shape}")
print(f"Output shape: {model.output_shape}")

# Test prediction
dummy_input = np.zeros((1, 160, 90, 90, 1))
test_output = model.predict(dummy_input)
print(f"Test prediction: {test_output}")

# Check TensorFlow configuration
print(f"GPU available: {len(tf.config.list_physical_devices('GPU')) > 0}")
print(f"XLA enabled: {tf.config.optimizer.get_jit()}")
```

## Best Practices

1. **Model Management**
   - Use model caching to avoid reloading
   - Implement proper error handling
   - Monitor prediction performance

2. **Input Validation**
   - Verify sequence shape before prediction
   - Check for empty or invalid sequences
   - Handle edge cases gracefully

3. **Performance Tuning**
   - Enable GPU acceleration when available
   - Use batch processing for multiple sequences
   - Implement proper memory management

4. **Result Interpretation**
   - Use appropriate probability thresholds
   - Consider confidence levels in decision making
   - Log predictions for analysis and debugging
