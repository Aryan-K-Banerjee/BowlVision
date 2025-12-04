"""
Front knee angle function for screenshot overlays.

Computes the three points (p1, p2, p3) needed to draw the front knee angle arc.
Adapted from core behavior but uses pipeline's angle calculation logic.
"""

import math
from typing import List, Tuple, Optional


def get_angle_points(landmarks: List[Tuple[float, float, float, float]], 
                     frame_shape: Tuple[int, int]) -> Optional[Tuple]:
    """Compute front knee angle render points.
    
    Args:
        landmarks: List of (x, y, z, vis) in pixel coordinates
        frame_shape: (height, width) of frame
        
    Returns:
        Tuple of (p1_px, p2_px, p3_px) in pixel coords, or None if not visible
    """
    # MediaPipe indices for left side (front leg)
    HIP_IDX = 23
    KNEE_IDX = 25
    ANKLE_IDX = 27
    TOE_IDX = 31
    
    if max(HIP_IDX, KNEE_IDX, ANKLE_IDX, TOE_IDX) >= len(landmarks):
        return None
    
    hip = landmarks[HIP_IDX]
    knee = landmarks[KNEE_IDX]
    ankle = landmarks[ANKLE_IDX]
    toe = landmarks[TOE_IDX]
    
    # Check visibility
    if hip[3] <= 0.2 or knee[3] <= 0.2 or ankle[3] <= 0.2:
        return None
    
    # Compute midpoints (similar to pipeline angle calculation)
    p1 = ((hip[0] + knee[0]) / 2.0, (hip[1] + knee[1]) / 2.0)
    p2 = (knee[0], knee[1])
    p3 = ((ankle[0] + knee[0]) / 2.0, (ankle[1] + knee[1]) / 2.0)
    
    return (p1, p2, p3)
