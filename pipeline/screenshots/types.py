"""
Type renderers for screenshot generation.

Each renderer takes a frame and landmarks, returning a rendered version.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from pipeline.screenshots.drawing import draw_skeleton, draw_angle_arc


def render_original(frame: np.ndarray, landmarks: List[Tuple], 
                    angle_points: Optional[Tuple] = None) -> np.ndarray:
    """Return original frame unchanged.
    
    Args:
        frame: Original video frame
        landmarks: Pose landmarks (unused)
        angle_points: Angle overlay points (unused)
        
    Returns:
        Copy of original frame
    """
    return frame.copy()


def render_skeleton(frame: np.ndarray, landmarks: List[Tuple], 
                    angle_points: Optional[Tuple] = None) -> np.ndarray:
    """Render skeleton overlay on frame.
    
    Args:
        frame: Original video frame
        landmarks: List of (x, y, z, vis) tuples in pixel coordinates
        angle_points: Angle overlay points (unused for skeleton)
        
    Returns:
        Frame with skeleton overlay
    """
    canvas = frame.copy()
    
    if landmarks:
        draw_skeleton(canvas, landmarks, color=(0, 255, 0), thickness=2)
    
    return canvas


def render_overlay(frame: np.ndarray, landmarks: List[Tuple], 
                   angle_points: Optional[Tuple] = None) -> np.ndarray:
    """Render skeleton with angle arc overlay.
    
    Args:
        frame: Original video frame
        landmarks: List of (x, y, z, vis) tuples in pixel coordinates
        angle_points: Tuple of (p1, p2, p3, angle_value) for angle arc
        
    Returns:
        Frame with skeleton and angle overlay
    """
    canvas = frame.copy()
    
    # Draw skeleton first
    if landmarks:
        draw_skeleton(canvas, landmarks, color=(0, 255, 0), thickness=2)
    
    # Draw angle arc if provided
    if angle_points and len(angle_points) >= 3:
        p1, p2, p3 = angle_points[0], angle_points[1], angle_points[2]
        angle_value = angle_points[3] if len(angle_points) > 3 else None
        draw_angle_arc(canvas, p1, p2, p3, angle_value)
    
    return canvas


# Type registry
TYPE_REGISTRY = {
    'original': render_original,
    'skeleton': render_skeleton,
    'overlay': render_overlay,
}


def get_type_renderer(type_name: str):
    """Get type renderer function by name.
    
    Args:
        type_name: Name of type (e.g., 'original', 'skeleton', 'overlay')
        
    Returns:
        Render function, or None if not found
    """
    return TYPE_REGISTRY.get(type_name)


def get_all_types():
    """Get list of all registered type names."""
    return list(TYPE_REGISTRY.keys())
