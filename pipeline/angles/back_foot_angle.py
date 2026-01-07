"""
Back Foot Angle Calculation

This module calculates the back foot angle with the ground.
The angle measures how much the heel is elevated relative to a 
horizontal line from the toe.

Geometry:
- Vertex: Toe (right foot index, landmark 32)
- Point 1: Heel (right heel, landmark 30)
- Point 2: Horizontal reference point at same Y as toe

The angle represents heel elevation:
- 0° = flat foot (heel at same height as toe)
- 90° = heel fully raised above toe
- Negative values possible if heel is below toe (camera tilt)

This works for both side view and back view.
"""

import math
from typing import Dict, List, Tuple, Optional


def calculate_back_foot_angle(
    keypoints: Dict[int, List[Tuple[float, float, float, float]]], 
    frame: int
) -> float:
    """Calculate the back foot angle with the ground for a given frame.
    
    Args:
        keypoints: Dict mapping frame index to list of landmarks (x, y, z, vis)
        frame: Frame index to calculate angle for
        
    Returns:
        Angle in degrees (-90 to 90). Returns 0.0 if landmarks are missing/invalid.
        Positive = heel above toe, Negative = heel below toe.
    """
    lm_list = _get_landmarks(keypoints, frame)
    if not lm_list:
        return 0.0

    # MediaPipe indices for right foot (back leg)
    HEEL_IDX = 30   # Right heel
    TOE_IDX = 32    # Right foot index (toe)

    if max(HEEL_IDX, TOE_IDX) >= len(lm_list):
        return 0.0

    try:
        heel_x, heel_y, _, heel_vis = lm_list[HEEL_IDX]
        toe_x, toe_y, _, toe_vis = lm_list[TOE_IDX]
    except Exception:
        return 0.0

    # Check visibility
    if heel_vis < 0.2 or toe_vis < 0.2:
        return 0.0

    # Calculate the angle of the heel relative to a horizontal line from the toe
    dx = heel_x - toe_x
    dy = heel_y - toe_y  # Note: In image coords, Y increases downward
    
    # Handle edge case where heel and toe have same X position
    if abs(dx) < 1e-6:
        if dy < 0:
            return 90.0   # Heel above toe
        elif dy > 0:
            return -90.0  # Heel below toe
        else:
            return 0.0    # Same position
    
    # Calculate angle from horizontal
    # In image coordinates, Y increases downward, so we negate dy
    angle_rad = math.atan2(-dy, abs(dx))
    angle_deg = math.degrees(angle_rad)
    
    # Clamp to [-90, 90] range
    angle_deg = max(-90.0, min(90.0, angle_deg))
    
    return float(angle_deg)


def _get_landmarks(keypoints, frame: int) -> Optional[List]:
    """Get landmarks for a frame from keypoints dict."""
    try:
        if isinstance(keypoints, dict):
            if frame in keypoints:
                return keypoints[frame]
            return keypoints.get(str(frame)) or keypoints.get(int(frame))
        return keypoints[frame]
    except Exception:
        return None
