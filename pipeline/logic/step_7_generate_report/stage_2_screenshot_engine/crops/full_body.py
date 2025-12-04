"""
Full body crop strategy - simple centered crop of the full frame.
"""

from typing import List, Tuple


def get_crop(landmarks: List[Tuple[float, float, float, float]], 
             frame_shape: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """Return full frame as crop (no cropping).
    
    Args:
        landmarks: List of (x, y, z, vis) in pixel coordinates (unused)
        frame_shape: (height, width) of frame
        
    Returns:
        (0, 0, width, height) - full frame
    """
    h, w = frame_shape
    return (0, 0, w, h)
