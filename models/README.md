# Models Directory

This directory contains the machine learning models used for shoplifting detection.

## Required Model

The system requires an LRCN (Long-term Recurrent Convolutional Network) model for video sequence analysis:

**File:** `lrcn_160S_90_90Q.h5`  
**Type:** Keras/TensorFlow H5 model  
**Input:** 160 frames of 90x90 grayscale images  
**Output:** Binary classification (shoplifting vs normal behavior)

## Getting the Model

### Option 1: Download Pre-trained Model (Recommended)

**Important**: The pre-trained model is not included in this repository due to size constraints.

**To obtain the model:**

1. **Contact the development team** for the pre-trained model file
2. **Download from cloud storage** (if available):
   ```bash
   # Example download command (update with actual URL)
   wget https://your-storage-url/lrcn_160S_90_90Q.h5 -O models/lrcn_160S_90_90Q.h5
   ```
3. **Build from training checkpoint** (if you have access to training data)

### Option 2: Train Your Own Model

If you have a dataset of shoplifting videos, you can train your own model:

1. **Prepare your dataset:**
   ```
   dataset/
   ├── shoplifting/     # Videos showing shoplifting behavior
   └── normal/          # Videos showing normal behavior
   ```

2. **Use the training notebook:**
   ```bash
   jupyter notebook models/run.ipynb
   ```

3. **Training requirements:**
   - Minimum 1000+ video clips (500 per class)
   - Videos should be 5-10 seconds long
   - Diverse scenarios and camera angles
   - GPU recommended for training

### Option 3: Use a Different Model

You can adapt the system to use a different model by:

1. **Updating the model path** in `config/config.yaml`:
   ```yaml
   model:
     path: "models/your_model.h5"
     sequence_length: 160  # Adjust if needed
     frame_size: 90        # Adjust if needed
   ```

2. **Ensuring compatibility:**
   - Model should accept input shape: `(batch_size, 160, 90, 90, 1)`
   - Model should output binary classification probabilities
   - Model should be in Keras/TensorFlow H5 format

## Model Architecture

The expected LRCN model architecture:

```
Input: (None, 160, 90, 90, 1)
├── TimeDistributed(CNN Layers)
├── LSTM Layers
├── Dense Layers
└── Output: (None, 2) - [normal_prob, shoplifting_prob]
```

## Preprocessing Pipeline

The model expects frames processed with this exact pipeline:

1. **Frame Differencing**: `cv2.absdiff(current_frame, previous_frame)`
2. **Gaussian Blur**: `cv2.GaussianBlur(diff, (3, 3), 0)`
3. **Resize**: `cv2.resize(diff, (90, 90))`
4. **Grayscale**: `cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)`
5. **Normalize**: `gray_frame / 255.0`

## Verification

To verify your model is working:

1. **Check model can be loaded:**
   ```python
   import tensorflow as tf
   model = tf.keras.models.load_model('models/lrcn_160S_90_90Q.h5')
   print(model.summary())
   ```

2. **Test with sample input:**
   ```python
   import numpy as np
   # Create dummy input
   dummy_input = np.random.random((1, 160, 90, 90, 1))
   prediction = model.predict(dummy_input)
   print(f"Prediction shape: {prediction.shape}")  # Should be (1, 2)
   ```

3. **Run the notebook:**
   ```bash
   jupyter notebook models/run.ipynb
   ```

## Troubleshooting

### Model Not Found Error
```
FileNotFoundError: Unable to open file models/lrcn_160S_90_90Q.h5
```
**Solution:** Ensure the model file exists and has the correct name.

### Model Loading Error
```
ValueError: Unable to load model
```
**Solution:** Check TensorFlow version compatibility. The model was trained with TensorFlow 2.x.

### Wrong Input Shape Error
```
ValueError: Input shape mismatch
```
**Solution:** Verify the model expects input shape `(batch_size, 160, 90, 90, 1)`.

## Model Performance

Expected performance metrics for the reference model:
- **Accuracy**: ~85-90% on test set
- **Precision**: ~88% for shoplifting detection
- **Recall**: ~82% for shoplifting detection
- **Inference Time**: ~200ms per 160-frame sequence

## Contributing

If you train a better model or improve the architecture:

1. Document the changes in this README
2. Update the configuration files accordingly
3. Provide performance benchmarks
4. Consider sharing with the community

## License

Model weights and training data usage should comply with your organization's data policies and applicable laws regarding surveillance footage. 