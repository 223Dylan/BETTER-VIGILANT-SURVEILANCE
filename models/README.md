# Models Directory

This directory contains the AI models used by the Shoplifting Detection System.

## Required Model File

The system requires an LRCN (Long-term Recurrent Convolutional Networks) model file:

**Expected File:** `lrcn_160S_90_90Q.h5`

### Model Specifications

- **Architecture**: LRCN (Convolutional + LSTM layers)
- **Input Shape**: (160, 90, 90, 1) - 160 grayscale frames of 90x90 pixels
- **Output Shape**: (2,) - Binary classification [normal_behavior, shoplifting]
- **Framework**: TensorFlow/Keras
- **File Format**: HDF5 (.h5)

### Model Training Information

The model should be trained on:
- **Sequence Length**: 160 frames per sequence
- **Frame Size**: 90x90 pixels
- **Color Space**: Grayscale
- **Classes**: 
  - Class 0: Normal behavior
  - Class 1: Shoplifting behavior

### Frame Preprocessing for Training

The model expects frames preprocessed with:
1. **Frame Differencing**: `cv2.absdiff(current_frame, previous_frame)`
2. **Gaussian Blur**: `cv2.GaussianBlur(diff, (3,3), 0)`
3. **Resize**: Resize to 90x90 pixels
4. **Grayscale**: Convert to single channel
5. **Normalization**: Pixel values in range [0,1]

### Getting a Model

You have several options to obtain a model:

#### Option 1: Use Pre-trained Model
If you have access to a pre-trained LRCN model for shoplifting detection:
1. Place the `.h5` file in this directory
2. Rename it to `lrcn_160S_90_90Q.h5`
3. Update the configuration if needed

#### Option 2: Train Your Own Model
To train your own model, you'll need:
1. **Dataset**: Video sequences of shoplifting and normal behavior
2. **Training Framework**: TensorFlow/Keras
3. **Reference Paper**: "Early Detection of Collective or Individual Theft Attempts Using Long-term Recurrent Convolutional Networks"

#### Option 3: Use Alternative Model
To use a different model:
1. Place your model file in this directory
2. Update the `MODEL_PATH` in your configuration:
   ```yaml
   # config/config.yaml
   model:
     path: "models/your_model_name.h5"
   ```
   
   OR
   
   ```bash
   # .env file
   MODEL_PATH=models/your_model_name.h5
   ```

### Model Performance Considerations

**For Development:**
- Use CPU inference for testing: `USE_GPU=false`
- Smaller batch sizes: `batch_size: 1`

**For Production:**
- Enable GPU if available: `USE_GPU=true`
- Optimize model loading: `enable_model_caching: true`
- Monitor prediction latency

### Model File Structure

Expected directory structure:
```
models/
├── README.md                 # This file
├── lrcn_160S_90_90Q.h5      # Main LRCN model (required)
└── checkpoints/             # Training checkpoints (optional)
```

### Troubleshooting

**Model Loading Issues:**
- Ensure the model file is not corrupted
- Check TensorFlow/Keras compatibility
- Verify the model was saved with compatible versions

**Prediction Errors:**
- Verify input shape matches model expectations
- Check data preprocessing pipeline
- Ensure frame sequences are properly formatted

**Performance Issues:**
- Enable model caching for faster loading
- Use GPU acceleration if available
- Monitor memory usage with large models

### Sample Model Code

If you're training your own model, here's a basic LRCN architecture:

```python
import tensorflow as tf
from tensorflow.keras.layers import *
from tensorflow.keras.models import Sequential

def create_lrcn_model(sequence_length=160, img_height=90, img_width=90, num_classes=2):
    """Create LRCN model for video classification."""
    
    model = Sequential([
        # TimeDistributed CNN layers
        TimeDistributed(Conv2D(16, (3, 3), activation='relu'), 
                       input_shape=(sequence_length, img_height, img_width, 1)),
        TimeDistributed(MaxPooling2D((2, 2))),
        TimeDistributed(Conv2D(32, (3, 3), activation='relu')),
        TimeDistributed(MaxPooling2D((2, 2))),
        TimeDistributed(Conv2D(64, (3, 3), activation='relu')),
        TimeDistributed(MaxPooling2D((2, 2))),
        TimeDistributed(Flatten()),
        
        # LSTM layers
        LSTM(64, return_sequences=True),
        Dropout(0.5),
        LSTM(32),
        Dropout(0.5),
        
        # Dense layers
        Dense(64, activation='relu'),
        Dropout(0.5),
        Dense(num_classes, activation='softmax')
    ])
    
    return model

# Compile model
model = create_lrcn_model()
model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# Save model
model.save('lrcn_160S_90_90Q.h5')
```

### Security Note

**Important**: Model files can be large and should not be committed to version control. Add them to `.gitignore` and use:
- Model hosting services
- External storage solutions
- Download scripts for model deployment

For questions about model training or implementation, refer to the main documentation in the `docs/` directory. 