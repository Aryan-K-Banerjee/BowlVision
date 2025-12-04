"""
None angle function - no angle overlay.

Used when screenshot doesn't need angle arc.
"""

from typing import List, Tuple, Optional


def get_angle_points(landmarks: List[Tuple[float, float, float, float]], 
                     frame_shape: Tuple[int, int]) -> Optional[Tuple]:
    """No angle points - returns None.
    
    Args:
        landmarks: List of (x, y, z, vis) in pixel coordinates (unused)
        frame_shape: (height, width) of frame (unused)
        
    Returns:
        None (no angle overlay)
    """
    return None
