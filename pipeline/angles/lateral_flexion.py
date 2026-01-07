"""
Lateral Flexion Angle Calculation

Measures the angle of spine lateral flexion by comparing
the head position relative to a vertical line from the base of spine.

Key landmarks used:
- Mid-point of shoulders (11, 12) as reference
- Mid-point of hips (23, 24) as base of spine
- Head (0 - nose) or (9-10 average - ears)
"""

import math
from typing import Dict, List, Tuple, Optional
from pipeline.angles.angle_utils import calculate_angle_between_points


def calculate_lateral_flexion_angle(
    keypoints: Dict[int, List[Tuple[float, float, float, float]]], 
    frame: int
) -> float:
    """Calculate the lateral flexion angle for a given frame.
    
    Measures how much the head deviates from vertical relative to spine base.
    0° = perfectly upright, positive = leaning away (worse)
    
    Args:
        keypoints: Dict mapping frame index to list of landmarks (x, y, z, vis)
        frame: Frame index to calculate angle for
        
    Returns:
        Angle in degrees from vertical. Returns 0.0 if landmarks are missing/invalid.
    """
    lm_list = _get_landmarks(keypoints, frame)
    if not lm_list:
        return 0.0

    # Landmark indices
    NOSE_IDX = 0
    LEFT_SHOULDER_IDX = 11
    RIGHT_SHOULDER_IDX = 12
    LEFT_HIP_IDX = 23
    RIGHT_HIP_IDX = 24

    if max(NOSE_IDX, LEFT_SHOULDER_IDX, RIGHT_SHOULDER_IDX, LEFT_HIP_IDX, RIGHT_HIP_IDX) >= len(lm_list):
        return 0.0

    try:
        nose_x, nose_y, _, nose_vis = lm_list[NOSE_IDX]
        ls_x, ls_y, _, ls_vis = lm_list[LEFT_SHOULDER_IDX]
        rs_x, rs_y, _, rs_vis = lm_list[RIGHT_SHOULDER_IDX]
        lh_x, lh_y, _, lh_vis = lm_list[LEFT_HIP_IDX]
        rh_x, rh_y, _, rh_vis = lm_list[RIGHT_HIP_IDX]
    except Exception:
        return 0.0

    # Check visibility
    if nose_vis < 0.2 or ls_vis < 0.2 or rs_vis < 0.2 or lh_vis < 0.2 or rh_vis < 0.2:
        return 0.0

    # Compute midpoints
    mid_hip_x = (lh_x + rh_x) / 2
    mid_hip_y = (lh_y + rh_y) / 2
    
    # Create a virtual point straight up from mid_hip (vertical reference)
    # In image coords, "up" means smaller y
    vertical_point_x = mid_hip_x
    vertical_point_y = mid_hip_y - 100  # Point straight up
    
    # The angle: mid_hip is vertex, one arm to vertical point, one arm to nose
    p1 = (vertical_point_x, vertical_point_y)  # Vertical reference
    p2 = (mid_hip_x, mid_hip_y)                 # Vertex (base of spine)
    p3 = (nose_x, nose_y)                        # Head position

    try:
        angle = calculate_angle_between_points(p1, p2, p3)
        # Angle is from vertical, so 0 = upright
        return abs(angle)
    except Exception:
        return 0.0


def _get_landmarks(keypoints: Dict, frame: int) -> Optional[List]:
    """Get landmarks for a frame."""
    if frame not in keypoints:
        return None
    return keypoints[frame]
