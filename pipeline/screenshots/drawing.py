"""
Shared drawing utilities for rendering screenshots.

Includes draw_angle_arc for angle overlays and draw_skeleton for pose visualization.
"""

import math
import cv2
import numpy as np
from typing import Optional, List, Tuple


def draw_angle_arc(canvas, p1, p2, p3, angle_deg: Optional[float] = None, color=(0, 200, 0)):
    """Draw a shaded angle arc (sector) on `canvas` with vertex at p2 between p1 and p3.
    
    This handles >180 degree angles correctly by drawing the reflex arc on the opposite side.
    
    Args:
        canvas: Image to draw on (modified in-place)
        p1: First point (x, y) in pixels
        p2: Vertex point (x, y) in pixels  
        p3: Third point (x, y) in pixels
        angle_deg: Optional angle value in degrees; if >180 draws reflex arc
        color: RGB tuple for arc fill color (default: green)
    """
    try:
        x1, y1 = float(p1[0]), float(p1[1])
        x2, y2 = float(p2[0]), float(p2[1])
        x3, y3 = float(p3[0]), float(p3[1])
    except Exception:
        return
    
    # Compute vectors from vertex
    v1 = (x1 - x2, y1 - y2)
    v2 = (x3 - x2, y3 - y2)
    mag1 = math.hypot(*v1)
    mag2 = math.hypot(*v2)
    if mag1 < 1e-3 or mag2 < 1e-3:
        return
    
    # Convert to angles
    a1 = math.degrees(math.atan2(v1[1], v1[0]))
    a2 = math.degrees(math.atan2(v2[1], v2[0]))
    
    def normalize_deg(a):
        while a < 0:
            a += 360
        while a >= 360:
            a -= 360
        return a
    
    a1n = normalize_deg(a1)
    a2n = normalize_deg(a2)
    
    # Compute difference
    diff = a2n - a1n
    if diff <= -180:
        diff += 360
    elif diff > 180:
        diff -= 360
    
    # If angle is >180, flip to draw reflex arc
    draw_diff = diff
    if angle_deg is not None and angle_deg > 180:
        if diff > 0:
            draw_diff = diff - 360
        else:
            draw_diff = diff + 360
    
    # Create arc points
    steps = max(6, int(abs(draw_diff) / 5) + 2)
    radius = int(max(12, min(80, (mag1 + mag2) / 4)))
    arc_pts = []
    for i in range(steps + 1):
        t = i / steps
        ang = math.radians(a1n + draw_diff * t)
        px = int(round(x2 + math.cos(ang) * radius))
        py = int(round(y2 + math.sin(ang) * radius))
        arc_pts.append((px, py))
    
    # Draw filled sector
    poly = [(int(round(x2)), int(round(y2)))] + arc_pts
    cv2.fillPoly(canvas, [np.array(poly, dtype=np.int32)], color)
    cv2.polylines(canvas, [np.array(arc_pts, dtype=np.int32)], False, (0, 255, 0), 1, lineType=cv2.LINE_AA)
    
    # Compute angle if not provided
    if angle_deg is None:
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        angle_deg = math.degrees(math.acos(max(-1.0, min(1.0, dot / (mag1 * mag2)))))
    
    # Draw text label
    bisector = math.radians(normalize_deg(a1n + draw_diff / 2.0))
    text_radius = radius + 18
    tx = int(round(x2 + math.cos(bisector) * text_radius))
    ty = int(round(y2 + math.sin(bisector) * text_radius))
    
    text = f"{angle_deg:.1f}°"
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    tx0 = tx - tw // 2
    ty0 = ty + th // 2
    cv2.rectangle(canvas, (tx0 - 4, ty0 - th - 4), (tx0 + tw + 4, ty0 + 4), (0, 0, 0), -1)
    cv2.putText(canvas, text, (tx0, ty0), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, lineType=cv2.LINE_AA)


def get_pose_connections() -> List[Tuple[int, int]]:
    """Return MediaPipe pose skeleton connections.
    
    Returns:
        List of (start_idx, end_idx) tuples for drawing skeleton lines
    """
    # Full body connections
    return [
        # Face
        (0, 1), (1, 2), (2, 3), (3, 7),
        (0, 4), (4, 5), (5, 6), (6, 8),
        (9, 10),
        # Torso
        (11, 12), (11, 23), (12, 24), (23, 24),
        # Left arm
        (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
        # Right arm
        (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
        # Left leg
        (23, 25), (25, 27), (27, 29), (27, 31), (29, 31),
        # Right leg
        (24, 26), (26, 28), (28, 30), (28, 32), (30, 32),
    ]


def draw_skeleton(canvas: np.ndarray, landmarks: List[Tuple[float, float, float, float]], 
                  color=(0, 255, 0), thickness=2, visibility_threshold=0.2):
    """Draw pose skeleton on canvas.
    
    Args:
        canvas: Image to draw on (modified in-place)
        landmarks: List of (x, y, z, vis) tuples in pixel coordinates
        color: RGB tuple for skeleton color (default: green)
        thickness: Line thickness
        visibility_threshold: Minimum visibility score to draw
    """
    connections = get_pose_connections()
    
    # Draw lines
    for start_idx, end_idx in connections:
        if start_idx < len(landmarks) and end_idx < len(landmarks):
            x1, y1, z1, vis1 = landmarks[start_idx]
            x2, y2, z2, vis2 = landmarks[end_idx]
            
            if vis1 > visibility_threshold and vis2 > visibility_threshold:
                pt1 = (int(x1), int(y1))
                pt2 = (int(x2), int(y2))
                cv2.line(canvas, pt1, pt2, color, thickness)
    
    # Draw points
    for x, y, z, vis in landmarks:
        if vis > visibility_threshold:
            cv2.circle(canvas, (int(x), int(y)), 3, color, -1)
