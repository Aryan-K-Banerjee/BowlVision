"""
Non-Bowling Arm Extension Angle Calculation

Measures the extension of the non-bowling (left) arm.
A fully extended arm has an angle close to 180°.

Key landmarks used:
- Left Shoulder (11)
- Left Elbow (13)
- Left Wrist (15)
"""

import math
from typing import Dict, List, Tuple, Optional
from pipeline.angles.angle_utils import calculate_angle_between_points


def calculate_non_bowling_arm_angle(
    keypoints: Dict[int, List[Tuple[float, float, float, float]]], 
    frame: int
) -> float:
    """Calculate the non-bowling arm extension angle for a given frame.
    
    Measures the elbow angle - 180° = fully extended, <180° = bent
    
    Args:
        keypoints: Dict mapping frame index to list of landmarks (x, y, z, vis)
        frame: Frame index to calculate angle for
        
    Returns:
        Angle in degrees (elbow angle). Returns 0.0 if landmarks are missing/invalid.
    """
    lm_list = _get_landmarks(keypoints, frame)
    if not lm_list:
        return 0.0

    # Landmark indices for left arm (non-bowling arm for right-hander)
    LEFT_SHOULDER_IDX = 11
    LEFT_ELBOW_IDX = 13
    LEFT_WRIST_IDX = 15

    if max(LEFT_SHOULDER_IDX, LEFT_ELBOW_IDX, LEFT_WRIST_IDX) >= len(lm_list):
        return 0.0

    try:
        ls_x, ls_y, _, ls_vis = lm_list[LEFT_SHOULDER_IDX]
        le_x, le_y, _, le_vis = lm_list[LEFT_ELBOW_IDX]
        lw_x, lw_y, _, lw_vis = lm_list[LEFT_WRIST_IDX]
    except Exception:
        return 0.0

    # Check visibility
    if ls_vis < 0.2 or le_vis < 0.2 or lw_vis < 0.2:
        return 0.0

    # The angle at elbow: shoulder -> elbow -> wrist
    p1 = (ls_x, ls_y)   # Shoulder
    p2 = (le_x, le_y)   # Elbow (vertex)
    p3 = (lw_x, lw_y)   # Wrist

    try:
        angle = calculate_angle_between_points(p1, p2, p3)
        return angle
    except Exception:
        return 0.0


def calculate_max_non_bowling_arm_angle(
    keypoints: Dict[int, List[Tuple[float, float, float, float]]], 
    start_frame: int,
    end_frame: int
) -> Tuple[float, int]:
    """Find the maximum arm extension between two frames.
    
    Args:
        keypoints: Dict mapping frame index to list of landmarks
        start_frame: Starting frame (inclusive)
        end_frame: Ending frame (inclusive)
        
    Returns:
        Tuple of (max_angle, frame_of_max)
    """
    max_angle = 0.0
    max_frame = start_frame
    
    for frame in range(start_frame, end_frame + 1):
        angle = calculate_non_bowling_arm_angle(keypoints, frame)
        if angle > max_angle:
            max_angle = angle
            max_frame = frame
    
    return max_angle, max_frame


def _get_landmarks(keypoints: Dict, frame: int) -> Optional[List]:
    """Get landmarks for a frame."""
    if frame not in keypoints:
        return None
    return keypoints[frame]
