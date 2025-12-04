"""
Front leg focus crop strategy.

Adapted from core/report/crop/policy.py::_focus_front_leg
Preserves the 30% padding calculation.
"""

from typing import List, Tuple


def get_crop(landmarks: List[Tuple[float, float, float, float]], 
             frame_shape: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """Compute a square crop focused on the front leg.
    
    Args:
        landmarks: List of (x, y, z, vis) in pixel coordinates
        frame_shape: (height, width) of frame
        
    Returns:
        (x, y, w, h) crop window in pixels
    """
    h, w = frame_shape
    
    # MediaPipe left-side indices for front leg
    HIP_IDX = 23
    KNEE_IDX = 25
    ANKLE_IDX = 27
    TOE_IDX = 31
    
    # Extract front leg landmarks
    front_leg_indices = [HIP_IDX, KNEE_IDX, ANKLE_IDX, TOE_IDX]
    visible = []
    for idx in front_leg_indices:
        if idx < len(landmarks):
            x, y, z, vis = landmarks[idx]
            if vis > 0.2 and 0 <= x < w and 0 <= y < h:
                visible.append((x, y))
    
    if not visible:
        # Fallback: center crop
        size = min(h, w) // 2
        x = (w - size) // 2
        y = (h - size) // 2
        return (x, y, size, size)
    
    # Compute bbox
    xs, ys = zip(*visible)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    bbox_w = max_x - min_x
    bbox_h = max_y - min_y
    
    # Add 30% padding and make square
    padding = 0.3
    bbox_size = max(bbox_w, bbox_h)
    final_size = int(bbox_size * (1 + 2 * padding))
    
    # Center
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    # Compute crop window
    x = int(center_x - final_size / 2)
    y = int(center_y - final_size / 2)
    
    # Clamp to frame bounds
    x = max(0, min(x, w - final_size))
    y = max(0, min(y, h - final_size))
    
    # If window exceeds bounds, adjust size
    final_size = min(final_size, w - x, h - y)
    
    return (x, y, final_size, final_size)
