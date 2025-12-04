"""
Square around bowler crop strategy.

Adapted from core/report/crop/policy.py::_square_around_bowler
Preserves the 0.25 margin and 1.5x height calculations.
"""

from typing import List, Tuple


def get_crop(landmarks: List[Tuple[float, float, float, float]], 
             frame_shape: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """Compute a square crop around the full bowler with 0.25 margin.
    
    Args:
        landmarks: List of (x, y, z, vis) in pixel coordinates
        frame_shape: (height, width) of frame
        
    Returns:
        (x, y, w, h) crop window in pixels
    """
    h, w = frame_shape
    
    # Filter visible landmarks (vis > 0.2)
    visible = [(x, y) for x, y, z, vis in landmarks if vis > 0.2 and 0 <= x < w and 0 <= y < h]
    
    if not visible:
        # Fallback: center crop
        size = min(h, w)
        x = (w - size) // 2
        y = (h - size) // 2
        return (x, y, size, size)
    
    # Compute bbox
    xs, ys = zip(*visible)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    bowler_height = max_y - min_y
    if bowler_height <= 0:
        bowler_height = h * 0.5
    
    # Final square size: 1.5 * bowler_height (0.25 margin above and below)
    final_size = int(1.5 * bowler_height)
    
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
