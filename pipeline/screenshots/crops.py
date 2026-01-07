"""
Crop strategies for screenshot generation.

Each crop function takes landmarks and frame shape, returning a crop window.
"""

from typing import List, Tuple, Optional


def crop_square_around_bowler(landmarks: List[Tuple], frame_shape: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """Create a square crop centered on the bowler.
    
    Args:
        landmarks: List of (x, y, z, vis) tuples in pixel coordinates
        frame_shape: (height, width) of frame
        
    Returns:
        (x, y, width, height) crop window
    """
    h, w = frame_shape
    
    if not landmarks:
        # Fallback to center square
        size = min(h, w)
        x = (w - size) // 2
        y = (h - size) // 2
        return (x, y, size, size)
    
    # Find visible landmarks bounding box
    visible_x = []
    visible_y = []
    for x_px, y_px, z, vis in landmarks:
        if vis > 0.2:
            visible_x.append(x_px)
            visible_y.append(y_px)
    
    if not visible_x:
        size = min(h, w)
        return ((w - size) // 2, (h - size) // 2, size, size)
    
    # Compute bounding box
    min_x, max_x = min(visible_x), max(visible_x)
    min_y, max_y = min(visible_y), max(visible_y)
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    
    # Add padding
    box_w = max_x - min_x
    box_h = max_y - min_y
    size = int(max(box_w, box_h) * 1.3)
    size = max(size, 200)
    
    # Center crop
    x = int(cx - size / 2)
    y = int(cy - size / 2)
    
    # Clamp to frame bounds
    x = max(0, min(x, w - size))
    y = max(0, min(y, h - size))
    
    return (x, y, size, size)


def crop_front_leg_focus(landmarks: List[Tuple], frame_shape: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """Create a crop focused on the front leg area.
    
    Uses landmarks 23 (left hip), 25 (left knee), 27 (left ankle), 31 (left toe).
    
    Args:
        landmarks: List of (x, y, z, vis) tuples in pixel coordinates
        frame_shape: (height, width) of frame
        
    Returns:
        (x, y, width, height) crop window
    """
    h, w = frame_shape
    
    # Front leg landmarks
    leg_indices = [23, 25, 27, 31]
    
    leg_x = []
    leg_y = []
    
    if landmarks and len(landmarks) > max(leg_indices):
        for idx in leg_indices:
            x_px, y_px, z, vis = landmarks[idx]
            if vis > 0.2:
                leg_x.append(x_px)
                leg_y.append(y_px)
    
    if not leg_x:
        # Fallback to lower right quadrant
        return (w // 4, h // 3, w // 2, int(h * 0.6))
    
    # Compute bounding box with padding
    min_x, max_x = min(leg_x), max(leg_x)
    min_y, max_y = min(leg_y), max(leg_y)
    
    # Add significant padding
    pad_x = (max_x - min_x) * 0.5
    pad_y = (max_y - min_y) * 0.3
    
    x = int(min_x - pad_x)
    y = int(min_y - pad_y)
    crop_w = int(max_x - min_x + 2 * pad_x)
    crop_h = int(max_y - min_y + 2 * pad_y)
    
    # Ensure minimum size
    crop_w = max(crop_w, 200)
    crop_h = max(crop_h, 250)
    
    # Clamp to frame bounds
    x = max(0, min(x, w - crop_w))
    y = max(0, min(y, h - crop_h))
    
    return (x, y, crop_w, crop_h)


def crop_back_foot_focus(landmarks: List[Tuple], frame_shape: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """Create a crop focused on the back foot area.
    
    Uses landmarks 24 (right hip), 26 (right knee), 28 (right ankle), 30 (right heel), 32 (right toe).
    
    Args:
        landmarks: List of (x, y, z, vis) tuples in pixel coordinates
        frame_shape: (height, width) of frame
        
    Returns:
        (x, y, width, height) crop window
    """
    h, w = frame_shape
    
    # Back foot landmarks
    foot_indices = [28, 30, 32]  # Ankle, heel, toe
    
    foot_x = []
    foot_y = []
    
    if landmarks and len(landmarks) > max(foot_indices):
        for idx in foot_indices:
            x_px, y_px, z, vis = landmarks[idx]
            if vis > 0.2:
                foot_x.append(x_px)
                foot_y.append(y_px)
    
    if not foot_x:
        # Fallback to lower portion
        return (0, int(h * 0.5), w, int(h * 0.5))
    
    # Compute bounding box with padding
    min_x, max_x = min(foot_x), max(foot_x)
    min_y, max_y = min(foot_y), max(foot_y)
    
    # Add padding
    pad = max(max_x - min_x, max_y - min_y) * 1.5
    pad = max(pad, 100)
    
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    
    x = int(cx - pad)
    y = int(cy - pad)
    size = int(pad * 2)
    
    # Clamp to frame bounds
    x = max(0, min(x, w - size))
    y = max(0, min(y, h - size))
    
    return (x, y, size, size)


def crop_full_body(landmarks: List[Tuple], frame_shape: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """Return full frame (no crop).
    
    Args:
        landmarks: List of (x, y, z, vis) tuples (unused)
        frame_shape: (height, width) of frame
        
    Returns:
        (0, 0, width, height) - full frame
    """
    h, w = frame_shape
    return (0, 0, w, h)


def crop_upper_body(landmarks: List[Tuple], frame_shape: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """Create a crop focused on the upper body (shoulders, head, arms).
    
    Uses shoulders and head landmarks.
    
    Args:
        landmarks: List of (x, y, z, vis) tuples in pixel coordinates
        frame_shape: (height, width) of frame
        
    Returns:
        (x, y, width, height) crop window
    """
    h, w = frame_shape
    
    # Upper body landmarks: head, shoulders, elbows, wrists
    upper_indices = [0, 11, 12, 13, 14, 15, 16]
    
    upper_x = []
    upper_y = []
    
    if landmarks and len(landmarks) > max(upper_indices):
        for idx in upper_indices:
            x_px, y_px, z, vis = landmarks[idx]
            if vis > 0.2:
                upper_x.append(x_px)
                upper_y.append(y_px)
    
    if not upper_x:
        # Fallback to upper half
        return (0, 0, w, h // 2)
    
    # Compute bounding box with padding
    min_x, max_x = min(upper_x), max(upper_x)
    min_y, max_y = min(upper_y), max(upper_y)
    
    pad = max(max_x - min_x, max_y - min_y) * 0.3
    
    x = int(min_x - pad)
    y = int(min_y - pad)
    crop_w = int(max_x - min_x + 2 * pad)
    crop_h = int(max_y - min_y + 2 * pad)
    
    # Clamp to frame bounds
    x = max(0, min(x, w - crop_w))
    y = max(0, min(y, h - crop_h))
    
    return (x, y, crop_w, crop_h)


def crop_bowling_arm_focus(landmarks: List[Tuple], frame_shape: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """Create a crop focused on the bowling arm (right arm).
    
    Uses right shoulder, elbow, wrist landmarks.
    
    Args:
        landmarks: List of (x, y, z, vis) tuples in pixel coordinates
        frame_shape: (height, width) of frame
        
    Returns:
        (x, y, width, height) crop window
    """
    h, w = frame_shape
    
    # Bowling arm landmarks (right side)
    arm_indices = [12, 14, 16]  # Shoulder, elbow, wrist
    
    arm_x = []
    arm_y = []
    
    if landmarks and len(landmarks) > max(arm_indices):
        for idx in arm_indices:
            x_px, y_px, z, vis = landmarks[idx]
            if vis > 0.2:
                arm_x.append(x_px)
                arm_y.append(y_px)
    
    if not arm_x:
        return crop_upper_body(landmarks, frame_shape)
    
    # Compute bounding box with padding
    min_x, max_x = min(arm_x), max(arm_x)
    min_y, max_y = min(arm_y), max(arm_y)
    
    pad = max(max_x - min_x, max_y - min_y) * 0.5
    pad = max(pad, 80)
    
    x = int(min_x - pad)
    y = int(min_y - pad)
    size = int(max(max_x - min_x, max_y - min_y) + 2 * pad)
    
    # Clamp to frame bounds
    x = max(0, min(x, w - size))
    y = max(0, min(y, h - size))
    
    return (x, y, size, size)


def crop_non_bowling_arm_focus(landmarks: List[Tuple], frame_shape: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """Create a crop focused on the non-bowling arm (left arm).
    
    Uses left shoulder, elbow, wrist landmarks.
    
    Args:
        landmarks: List of (x, y, z, vis) tuples in pixel coordinates
        frame_shape: (height, width) of frame
        
    Returns:
        (x, y, width, height) crop window
    """
    h, w = frame_shape
    
    # Non-bowling arm landmarks (left side)
    arm_indices = [11, 13, 15]  # Shoulder, elbow, wrist
    
    arm_x = []
    arm_y = []
    
    if landmarks and len(landmarks) > max(arm_indices):
        for idx in arm_indices:
            x_px, y_px, z, vis = landmarks[idx]
            if vis > 0.2:
                arm_x.append(x_px)
                arm_y.append(y_px)
    
    if not arm_x:
        return crop_upper_body(landmarks, frame_shape)
    
    # Compute bounding box with padding
    min_x, max_x = min(arm_x), max(arm_x)
    min_y, max_y = min(arm_y), max(arm_y)
    
    pad = max(max_x - min_x, max_y - min_y) * 0.5
    pad = max(pad, 80)
    
    x = int(min_x - pad)
    y = int(min_y - pad)
    size = int(max(max_x - min_x, max_y - min_y) + 2 * pad)
    
    # Clamp to frame bounds
    x = max(0, min(x, w - size))
    y = max(0, min(y, h - size))
    
    return (x, y, size, size)


# Crop registry
CROP_REGISTRY = {
    'square_around_bowler': crop_square_around_bowler,
    'front_leg_focus': crop_front_leg_focus,
    'back_foot_focus': crop_back_foot_focus,
    'full_body': crop_full_body,
    'upper_body': crop_upper_body,
    'bowling_arm_focus': crop_bowling_arm_focus,
    'non_bowling_arm_focus': crop_non_bowling_arm_focus,
}


def get_crop_function(crop_name: str):
    """Get crop function by name.
    
    Args:
        crop_name: Name of crop strategy
        
    Returns:
        Crop function, or None if not found
    """
    return CROP_REGISTRY.get(crop_name)


def get_all_crops():
    """Get list of all registered crop strategy names."""
    return list(CROP_REGISTRY.keys())
