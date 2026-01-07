"""
Bowling Arm Delay Angle Calculation

Measures the angle of the bowling arm relative to horizontal at FFC.
The shoulder is the vertex, with the hand position compared to a horizontal line.

Key landmarks used:
- Right Shoulder (12) - bowling arm shoulder (right-handed bowler)
- Right Wrist (16) - bowling hand
"""

import math
from typing import Dict, List, Tuple, Optional
from pipeline.angles.angle_utils import calculate_angle_between_points


def calculate_bowling_arm_delay_angle(
    keypoints: Dict[int, List[Tuple[float, float, float, float]]], 
    frame: int
) -> float:
    """Calculate the bowling arm delay angle for a given frame.
    
    Measures angle from horizontal at shoulder to hand.
    Negative = hand below horizontal (good), Positive = hand above (bad)
    
    Args:
        keypoints: Dict mapping frame index to list of landmarks (x, y, z, vis)
        frame: Frame index to calculate angle for
        
    Returns:
        Angle in degrees from horizontal. Returns 0.0 if landmarks are missing/invalid.
    """
    lm_list = _get_landmarks(keypoints, frame)
    if not lm_list:
        return 0.0

    # Landmark indices for right arm (bowling arm for right-hander)
    RIGHT_SHOULDER_IDX = 12
    RIGHT_WRIST_IDX = 16

    if max(RIGHT_SHOULDER_IDX, RIGHT_WRIST_IDX) >= len(lm_list):
        return 0.0

    try:
        rs_x, rs_y, _, rs_vis = lm_list[RIGHT_SHOULDER_IDX]
        rw_x, rw_y, _, rw_vis = lm_list[RIGHT_WRIST_IDX]
    except Exception:
        return 0.0

    # Check visibility
    if rs_vis < 0.2 or rw_vis < 0.2:
        return 0.0

    # Create horizontal reference point (to the right of shoulder)
    horizontal_point_x = rs_x + 100
    horizontal_point_y = rs_y
    
    # The angle: shoulder is vertex, one arm to horizontal, one arm to wrist
    p1 = (horizontal_point_x, horizontal_point_y)  # Horizontal reference
    p2 = (rs_x, rs_y)                               # Vertex (shoulder)
    p3 = (rw_x, rw_y)                               # Hand position

    try:
        angle = calculate_angle_between_points(p1, p2, p3)
        
        # Determine sign: below horizontal is negative (good), above is positive (bad)
        # In image coords, y increases downward, so wrist.y > shoulder.y means below
        if rw_y > rs_y:
            return -angle  # Below horizontal (good delay)
        else:
            return angle   # Above horizontal (bad - arm already up)
    except Exception:
        return 0.0


def _get_landmarks(keypoints: Dict, frame: int) -> Optional[List]:
    """Get landmarks for a frame."""
    if frame not in keypoints:
        return None
    return keypoints[frame]
