#core/angles/front_knee_angle.py
'''--------------------------------------------------------------------------
This module contains functions to calculate the front knee angle, and render it
-------------------------------------------------------------------------'''

from core.angles.angle_utils import calculate_angle_between_points

def calculate_angle(keypoints: dict, frame: int) -> float:
    """
    This function calculates the front knee angle for a given frame based on
    `keypoints` which is expected to be a mapping from frame index to a list
    of landmarks. Each landmark is a tuple (x, y, z, vis) with x,y normalized
    in [0,1].

    The points used are (all left-side):
      - p1: midpoint between left hip and left knee
      - p2: left knee
      - p3: midpoint between left ankle and left knee

    If landmarks are missing or invalid this returns 0.0.
    """
    # defensively handle a few possible keypoints representations
    lm_list = None
    try:
        if isinstance(keypoints, dict):
            # prefer integer key lookup
            if frame in keypoints:
                lm_list = keypoints[frame]
            else:
                # try string key or int cast
                lm_list = keypoints.get(str(frame)) or keypoints.get(int(frame))
        else:
            # not a dict, maybe a list-like where index==frame
            lm_list = keypoints[frame]
    except Exception:
        lm_list = None

    if not lm_list or len(lm_list) == 0:
        return 0.0

    # mediapipe pose indices for left side
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

    # compute render points (midpoints as requested)
    p1 = ((hx + kx) / 2.0, (hy + ky) / 2.0)
    p2 = (kx, ky)
    p3 = ((ax + kx) / 2.0, (ay + ky) / 2.0)

    try:
        angle = calculate_angle_between_points(p1, p2, p3)
        # ensure we pick the angle that corresponds to the back of the knee
        # (the side away from the toe). If toe/foot index is available use it
        # to decide whether the small angle or the reflex (360-small) angle is
        # the one on the back of the knee. If toe is not available, return the
        # computed (smaller) angle.
        #
        # We'll compute angular positions of the vectors to decide which side
        # the toe lies on relative to the small sector between the two bone
        # vectors; if the toe is inside the small sector, pick the reflex
        # angle (which will be > 180 when straight/hyperextended).
        import math

        # vector from knee to p1 and knee to p3 in normalized coords
        v1 = (p1[0] - p2[0], p1[1] - p2[1])
        v2 = (p3[0] - p2[0], p3[1] - p2[1])

        def ang(a):
            return math.atan2(a[1], a[0])

        t1 = ang(v1)
        t2 = ang(v2)

        def ang_diff(a, b):
            # difference b - a normalized to (-pi, pi]
            d = b - a
            while d <= -math.pi:
                d += 2 * math.pi
            while d > math.pi:
                d -= 2 * math.pi
            return d

        diff = ang_diff(t1, t2)
        small_rad = abs(diff)
        large_rad = 2 * math.pi - small_rad

        # attempt to get toe/foot index (left foot index is 31, right is 32)
        toe_idx = None
        try:
            # if knee index 25 is left (we used left indices), use left foot index 31
            # If data contains a right-side foot we could adapt, but for now assume left side
            toe_idx = 31
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
            # fallback to the small angle
            return float(angle)

        return float(angle)
    except Exception:
        return 0.0

def render_points(keypoints: dict, frame: int):
    """
    Return the three normalized (x,y) points used to render the front knee
    angle for the given frame, or None if they cannot be produced.

    Returns:
        tuple: (p1, p2, p3) where each p is (x, y) in normalized coords, or
               None if points are missing.
    """
    # reuse calculate_angle's landmark extraction logic
    lm_list = None
    try:
        if isinstance(keypoints, dict):
            lm_list = keypoints.get(frame) or keypoints.get(str(frame)) or keypoints.get(int(frame))
        else:
            lm_list = keypoints[frame]
    except Exception:
        lm_list = None

    if not lm_list or len(lm_list) == 0:
        return None

    HIP_IDX = 23
    KNEE_IDX = 25
    ANKLE_IDX = 27
    if max(HIP_IDX, KNEE_IDX, ANKLE_IDX) >= len(lm_list):
        return None

    try:
        hx, hy, _, _ = lm_list[HIP_IDX]
        kx, ky, _, _ = lm_list[KNEE_IDX]
        ax, ay, _, _ = lm_list[ANKLE_IDX]
    except Exception:
        return None

    p1 = ((hx + kx) / 2.0, (hy + ky) / 2.0)
    p2 = (kx, ky)
    p3 = ((ax + kx) / 2.0, (ay + ky) / 2.0)

    return (p1, p2, p3)