'''--------------------------------------------------------------
This file contains the logic for calculating the back knee angle
from both back and side views.

The back knee angle is calculated using the right leg (right side of body
from MediaPipe's perspective). It measures the angle at the back of the knee.

Key landmarks used:
- Right Hip (index 24)
- Right Knee (index 26)
- Right Ankle (index 28)
- Right Foot Index (index 32) - for determining which side is "back"

The calculation uses midpoints between:
- p1: midpoint of hip and knee
- p2: knee (vertex)
- p3: midpoint of ankle and knee

This handles edge cases like determining whether to use the small angle
or reflex angle based on where the toe is positioned.
--------------------------------------------------------------'''

import math
from typing import Dict, List, Tuple
from pipeline.logic.step_4_calculate_angles.angle_utils import calculate_angle_between_points


def calculate_back_knee_angle(keypoints: Dict[int, List[Tuple[float, float, float, float]]], frame: int) -> float:
    """Calculate the back knee angle for a given frame.
    
    Args:
        keypoints: Dict mapping frame index to list of landmarks (x, y, z, vis)
        frame: Frame index to calculate angle for
        
    Returns:
        Angle in degrees. Returns 0.0 if landmarks are missing/invalid.
    """
    # Get landmarks for this frame
    lm_list = None
    try:
        if isinstance(keypoints, dict):
            # Try integer key lookup first
            if frame in keypoints:
                lm_list = keypoints[frame]
            else:
                # Try string key or int cast
                lm_list = keypoints.get(str(frame)) or keypoints.get(int(frame))
        else:
            # Not a dict, maybe a list-like where index==frame
            lm_list = keypoints[frame]
    except Exception:
        lm_list = None

    if not lm_list or len(lm_list) == 0:
        return 0.0

    # MediaPipe pose indices for right side (back leg for right-handed bowlers)
    HIP_IDX = 24
    KNEE_IDX = 26
    ANKLE_IDX = 28

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
        # (the side away from the toe). Use toe position to decide whether
        # the small angle or the reflex (360-small) angle is the back angle.
        
        # Vector from knee to p1 and knee to p3 in normalized coords
        v1 = (p1[0] - p2[0], p1[1] - p2[1])
        v2 = (p3[0] - p2[0], p3[1] - p2[1])

        def ang(a):
            return math.atan2(a[1], a[0])

        t1 = ang(v1)
        t2 = ang(v2)

        def ang_diff(a, b):
            # Difference b - a normalized to (-pi, pi]
            d = b - a
            while d <= -math.pi:
                d += 2 * math.pi
            while d > math.pi:
                d -= 2 * math.pi
            return d

        diff = ang_diff(t1, t2)
        small_rad = abs(diff)
        large_rad = 2 * math.pi - small_rad

        # Attempt to get toe/foot index (right foot index is 32)
        toe_idx = 32
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
            # Fallback to the small angle
            return float(angle)

        return float(angle)
    except Exception:
        return 0.0
