"""
Image processing utilities.
"""

from typing import Optional, Tuple

import cv2
import numpy as np


def resize_frame(
    frame: np.ndarray,
    target_size: Tuple[int, int] = (224, 224),
    maintain_aspect: bool = True,
) -> np.ndarray:
    """
    Resize a frame to target size while optionally maintaining aspect ratio.

    Args:
        frame: Input frame as numpy array
        target_size: Target size as (width, height)
        maintain_aspect: Whether to maintain aspect ratio

    Returns:
        Resized frame
    """
    if frame is None:
        return None

    if maintain_aspect:
        h, w = frame.shape[:2]
        aspect = w / h
        target_w, target_h = target_size

        if aspect > target_w / target_h:
            new_w = target_w
            new_h = int(target_w / aspect)
        else:
            new_h = target_h
            new_w = int(target_h * aspect)

        resized = cv2.resize(frame, (new_w, new_h))

        # Create a black canvas of target size
        canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)

        # Calculate position to paste resized image
        x_offset = (target_w - new_w) // 2
        y_offset = (target_h - new_h) // 2

        # Paste resized image onto canvas
        canvas[y_offset : y_offset + new_h, x_offset : x_offset + new_w] = resized
        return canvas
    else:
        return cv2.resize(frame, target_size)
