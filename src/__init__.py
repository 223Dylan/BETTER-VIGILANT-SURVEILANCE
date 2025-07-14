"""
Shoplifting Detection System
"""

from .camera_manager import CameraManager
from .frame_capture import FrameCapture
from .frame_processor import FrameProcessor
from .model_handler import ModelHandler
from .tasks import predict_sequence

__all__ = [
    'CameraManager',
    'FrameCapture',
    'FrameProcessor',
    'ModelHandler',
    'predict_sequence'
] 