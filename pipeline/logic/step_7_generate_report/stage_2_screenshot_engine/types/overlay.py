"""
Overlay type renderer - renders green skeleton overlaid on original frame.

Adapted from core/report/render/overlay.py
Preserves visual quality: green skeleton (0, 255, 0), cyan angle arcs (0, 255, 255).
"""

import numpy as np
import cv2
from typing import List, Tuple, Optional
from pipeline.logic.step_7_generate_report.stage_2_screenshot_engine.shared.drawing import (
    draw_skeleton,
    draw_angle_arc
)


def render(frame: np.ndarray, landmarks: List[Tuple[float, float, float, float]], 
           angle_points: Optional[Tuple] = None) -> np.ndarray:
    """Render skeleton overlay on original frame.
    
    Args:
        frame: Full video frame (BGR)
        landmarks: List of (x, y, z, vis) in pixel coordinates
        angle_points: Optional tuple of (p1, p2, p3, angle_value) for angle overlay
        
    Returns:
        Frame with green skeleton overlaid
    """
    # Create copy of frame
    canvas = frame.copy()
    
    # Draw skeleton in green
    draw_skeleton(canvas, landmarks, color=(0, 255, 0), thickness=2)
    
    # Draw angle arc if provided (cyan color for visibility)
    if angle_points is not None:
        p1, p2, p3, angle_value = angle_points
        draw_angle_arc(canvas, p1, p2, p3, angle_value, color=(0, 255, 255))
    
    return canvas
