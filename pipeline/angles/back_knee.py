"""
Back Knee Angle Calculation

This module calculates the back knee angle using keypoint data.
Uses the right leg (back leg after preprocessing flipping).

Key landmarks used:
- Right Hip (index 24)
- Right Knee (index 26)
- Right Ankle (index 28)
"""

import math
from typing import Dict, List, Tuple, Optional
from pipeline.angles.angle_utils import calculate_angle_between_points


def calculate_back_knee_angle(
    keypoints: Dict[int, List[Tuple[float, float, float, float]]], 
    frame: int
) -> float:
    """Calculate the back knee angle for a given frame.
    
    Args:
        keypoints: Dict mapping frame index to list of landmarks (x, y, z, vis)
        frame: Frame index to calculate angle for
        
    Returns:
        Angle in degrees. Returns 0.0 if landmarks are missing/invalid.
    """
    lm_list = _get_landmarks(keypoints, frame)
    if not lm_list:
        return 0.0

    # MediaPipe pose indices for right side (back leg)
    HIP_IDX = 24
    KNEE_IDX = 26
    ANKLE_IDX = 28

    if max(HIP_IDX, KNEE_IDX, ANKLE_IDX) >= len(lm_list):
        return 0.0

    try:
        hx, hy, _, h_vis = lm_list[HIP_IDX]
        kx, ky, _, k_vis = lm_list[KNEE_IDX]
        ax, ay, _, a_vis = lm_list[ANKLE_IDX]
    except Exception:
        return 0.0

    # Check visibility
    if h_vis < 0.2 or k_vis < 0.2 or a_vis < 0.2:
        return 0.0

    # Compute angle at knee
    p1 = (hx, hy)
    p2 = (kx, ky)
    p3 = (ax, ay)

    try:
        angle = calculate_angle_between_points(p1, p2, p3)
        return float(angle)
    except Exception:
        return 0.0


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
