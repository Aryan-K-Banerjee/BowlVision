"""
Original type renderer - renders the original frame without modifications.

Adapted from core/report/render/original.py
"""

import numpy as np
import cv2
from typing import List, Tuple, Optional


def render(frame: np.ndarray, landmarks: List[Tuple[float, float, float, float]], 
           angle_points: Optional[Tuple] = None) -> np.ndarray:
    """Render original frame without any overlays.
    
    Args:
        frame: Full video frame (BGR)
        landmarks: List of (x, y, z, vis) in pixel coordinates (unused for original)
        angle_points: Optional tuple of (p1, p2, p3, angle_value) (unused for original)
        
    Returns:
        Copy of the original frame
    """
    return frame.copy()
