"""
Calculates the angle on the back side of the front knee using keypoint data.
It should always be the angle on the left side as videos of left handers 
will be flipped during preprocessing so all videos should be consistent.

Key landmarks used:
- Left Hip (index 23)
- Left Knee (index 25)
- Left Ankle (index 27)
- Left Foot Index (index 31) - for determining which side is "back"
"""

import math
from typing import Dict, List, Tuple, Optional
from pipeline.angles.angle_utils import calculate_angle_between_points


def calculate_front_knee_angle(keypoints: Dict[int, List[Tuple[float, float, float, float]]], frame: int) -> float:
    """Calculate the front knee angle for a given frame.
    
    Args:
        keypoints: Dict mapping frame index to list of landmarks (x, y, z, vis)
        frame: Frame index to calculate angle for
        
    Returns:
        Angle in degrees. Returns 0.0 if landmarks are missing/invalid.
    """
    # Get landmarks for this frame
    lm_list = _get_landmarks(keypoints, frame)
    if not lm_list:
        return 0.0

    # MediaPipe pose indices for left side (front leg after preprocessing)
    HIP_IDX = 23
    KNEE_IDX = 25
    ANKLE_IDX = 27

    if max(HIP_IDX, KNEE_IDX, ANKLE_IDX) >= len(lm_list):
        return 0.0

    try:
        hx, hy, _, _ = lm_list[HIP_IDX]
        kx, ky, _, _ = lm_list[KNEE_IDX]
        ax, ay, _, _ = lm_list[ANKLE_IDX]
    except Exception:
        return 0.0

    # Compute render points (midpoints as requested)
    p1 = ((hx + kx) / 2.0, (hy + ky) / 2.0)
    p2 = (kx, ky)
    p3 = ((ax + kx) / 2.0, (ay + ky) / 2.0)

    try:
        angle = calculate_angle_between_points(p1, p2, p3)
        
        # Ensure we pick the angle that corresponds to the back of the knee
        v1 = (p1[0] - p2[0], p1[1] - p2[1])
        v2 = (p3[0] - p2[0], p3[1] - p2[1])

        def ang(a):
            return math.atan2(a[1], a[0])

        t1 = ang(v1)
        t2 = ang(v2)

        def ang_diff(a, b):
            d = b - a
            while d <= -math.pi:
                d += 2 * math.pi
            while d > math.pi:
                d -= 2 * math.pi
            return d

        diff = ang_diff(t1, t2)
        small_rad = abs(diff)
        large_rad = 2 * math.pi - small_rad

        # Attempt to get toe/foot index (left foot index is 31)
        toe_idx = 31
        try:
            if toe_idx < len(lm_list):
                tx, ty, _, _ = lm_list[toe_idx]
                v_toe = (tx - kx, ty - ky)
                toe_ang = ang(v_toe)
                toe_rel = ang_diff(t1, toe_ang)

                inside_small = False
                if diff >= 0:
                    inside_small = (0 <= toe_rel <= diff)
                else:
                    inside_small = (diff <= toe_rel <= 0)

                if inside_small:
                    chosen_deg = math.degrees(large_rad)
                else:
                    chosen_deg = math.degrees(small_rad)
                return float(chosen_deg)
        except Exception:
            return float(angle)

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
