import tensorflow as tf
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dense, Flatten, LSTM, TimeDistributed, Dropout, Input
from loguru import logger
import os

# Global model cache
_model_cache = {}

class LegacyLSTM(LSTM):
    """Custom LSTM layer that handles legacy parameters."""
    def __init__(self, *args, **kwargs):
        # Remove legacy parameters
        legacy_params = ['time_major', 'unroll']
        for param in legacy_params:
            kwargs.pop(param, None)
        super().__init__(*args, **kwargs)

    @classmethod
    def from_config(cls, config):
        # Remove legacy parameters from config
        legacy_params = ['time_major', 'unroll']
        for param in legacy_params:
            config.pop(param, None)
        return super().from_config(config)

# Centralized custom objects for model loading
CUSTOM_OBJECTS = {
    'Conv2D': Conv2D,
    'MaxPooling2D': MaxPooling2D,
    'Dense': Dense,
    'Flatten': Flatten,
    'LSTM': LegacyLSTM,
    'TimeDistributed': TimeDistributed,
    'Dropout': Dropout
}

def load_model(model_path: str) -> tf.keras.Model:
    """
    Load a TensorFlow model from the given path.
    Uses caching to avoid reloading the same model multiple times.
    
    Args:
        model_path: Path to the model file (.h5)
        
    Returns:
        Loaded TensorFlow model
    """
    global _model_cache
    if '_model_cache' not in globals():
        _model_cache = {}
    
    # Check if model is already loaded
    if model_path in _model_cache:
        logger.info(f"Using cached model from {model_path}")
        return _model_cache[model_path]
    
    try:
        # Load the model with custom objects
        logger.info(f"Loading model from {model_path}")
        model = tf.keras.models.load_model(
            model_path,
            custom_objects=CUSTOM_OBJECTS,
            compile=False
        )
        
        # Cache the model
        _model_cache[model_path] = model
        
        # Warm up the model with a dummy input
        dummy_input = tf.zeros((1, 160, 90, 90, 1))  # Adjust shape based on your model
        _ = model.predict(dummy_input, verbose=0)
        
        logger.info("Model loaded and optimized successfully")
        return model
        
    except Exception as e:
        logger.error(f"Failed to load model from {model_path}: {e}")
        raise 