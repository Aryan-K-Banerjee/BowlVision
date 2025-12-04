# core/report/render/skeleton.py
"""Render skeleton-only tiles on black background."""

import numpy as np
import cv2
from typing import List, Tuple


def render(frame_image: np.ndarray, landmarks: List[Tuple[float, float, float, float]], 
           crop_window: Tuple[int, int, int, int], overlays: List[str], angle_value: float = None) -> np.ndarray:
    """Render a skeleton tile on black background.
    
    Args:
        frame_image: the full video frame (BGR) - used only for shape
        landmarks: list of (x, y, z, vis) in pixel coordinates
        crop_window: (x, y, w, h) crop region
        overlays: list of overlay names (e.g., ["front_knee_angle"])
        angle_value: optional pre-calculated angle (degrees) from analysis results
    
    Returns:
        Cropped tile with skeleton on black (BGR)
    """
    x, y, w, h = crop_window
    fh, fw = frame_image.shape[:2]
    
    # Create black canvas matching frame size
    canvas = np.zeros((fh, fw, 3), dtype=np.uint8)
    
    # Draw skeleton connections
    _draw_skeleton(canvas, landmarks)
    
    # Crop the canvas FIRST
    tile = np.zeros((h, w, 3), dtype=np.uint8)
    
    src_x1 = max(0, x)
    src_y1 = max(0, y)
    src_x2 = min(fw, x + w)
    src_y2 = min(fh, y + h)
    
    dst_x1 = src_x1 - x
    dst_y1 = src_y1 - y
    dst_x2 = dst_x1 + (src_x2 - src_x1)
    dst_y2 = dst_y1 + (src_y2 - src_y1)
    
    if src_x2 > src_x1 and src_y2 > src_y1:
        tile[dst_y1:dst_y2, dst_x1:dst_x2] = canvas[src_y1:src_y2, src_x1:src_x2]
    
    # Draw angle arcs AFTER cropping (on the cropped tile)
    if "front_knee_angle" in overlays:
        # Adjust landmarks to be relative to crop window
        crop_landmarks = [(lx - x, ly - y, z, vis) for lx, ly, z, vis in landmarks]
        _draw_front_knee_arc(tile, crop_landmarks, angle_value)
    
    return tile


def _draw_skeleton(canvas: np.ndarray, landmarks: List[Tuple[float, float, float, float]]):
    """Draw pose skeleton connections."""
    from core.image.image_utils import get_pose_connections
    
    connections = get_pose_connections()
    h, w = canvas.shape[:2]
    
    # Draw lines
    for start_idx, end_idx in connections:
        if start_idx < len(landmarks) and end_idx < len(landmarks):
            x1, y1, z1, vis1 = landmarks[start_idx]
            x2, y2, z2, vis2 = landmarks[end_idx]
            
            if vis1 > 0.2 and vis2 > 0.2:
                pt1 = (int(x1), int(y1))
                pt2 = (int(x2), int(y2))
                cv2.line(canvas, pt1, pt2, (0, 255, 0), 2)
    
    # Draw points
    for x, y, z, vis in landmarks:
        if vis > 0.2:
            cv2.circle(canvas, (int(x), int(y)), 3, (0, 255, 0), -1)


def _draw_front_knee_arc(canvas: np.ndarray, landmarks: List[Tuple[float, float, float, float]], angle_value: float = None):
    """Draw front knee angle arc if points are available.
    
    Args:
        canvas: the image to draw on
        landmarks: list of (x, y, z, vis) in pixel coords relative to canvas
        angle_value: optional pre-calculated angle (degrees) from analysis results
    """
    try:
        from core.angles import front_knee_angle
        from core.image.image_utils import draw_angle_arc
        
        # Convert landmarks to normalized format expected by render_points
        # (MediaPipe format: x,y in [0,1], but we have pixels)
        h, w = canvas.shape[:2]
        norm_landmarks = [(x/w, y/h, z, vis) for x, y, z, vis in landmarks]
        
        # Get render points (these will be in normalized coords)
        points = front_knee_angle.render_points({"frame": norm_landmarks}, "frame")
        
        if points:
            p1, p2, p3 = points
            # Convert back to pixels
            p1_px = (int(p1[0] * w), int(p1[1] * h))
            p2_px = (int(p2[0] * w), int(p2[1] * h))
            p3_px = (int(p3[0] * w), int(p3[1] * h))
            
            # Use provided angle if available, otherwise compute it
            if angle_value is None:
                from core.angles.angle_utils import calculate_angle_between_points
                angle = calculate_angle_between_points(p1, p2, p3)
            else:
                angle = angle_value
            
            # Draw arc - using bright cyan color for visibility
            # The draw_angle_arc function will handle >180 degree angles correctly
            draw_angle_arc(canvas, p1_px, p2_px, p3_px, angle, (0, 255, 255))
    except Exception as e:
        # Skip arc if computation fails
        print(f"[DEBUG] Failed to draw front knee arc: {e}")
        pass
