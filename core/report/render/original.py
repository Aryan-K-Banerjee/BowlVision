# core/report/render/original.py
"""Render original frame tiles with cropping."""

import numpy as np
import cv2
from typing import List, Tuple


def render(frame_image: np.ndarray, landmarks: List[Tuple[float, float, float, float]], 
           crop_window: Tuple[int, int, int, int], overlays: List[str], angle_value: float = None) -> np.ndarray:
    """Render an original frame tile.
    
    Args:
        frame_image: the full video frame (BGR)
        landmarks: list of (x, y, z, vis) in pixel coordinates
        crop_window: (x, y, w, h) crop region
        overlays: list of overlay names (ignored for original)
    
    Returns:
        Cropped tile (square numpy array, BGR)
    """
    x, y, w, h = crop_window
    fh, fw = frame_image.shape[:2]
    
    # Create output tile
    tile = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Compute valid source region
    src_x1 = max(0, x)
    src_y1 = max(0, y)
    src_x2 = min(fw, x + w)
    src_y2 = min(fh, y + h)
    
    # Compute destination region
    dst_x1 = src_x1 - x
    dst_y1 = src_y1 - y
    dst_x2 = dst_x1 + (src_x2 - src_x1)
    dst_y2 = dst_y1 + (src_y2 - src_y1)
    
    # Copy region
    if src_x2 > src_x1 and src_y2 > src_y1:
        tile[dst_y1:dst_y2, dst_x1:dst_x2] = frame_image[src_y1:src_y2, src_x1:src_x2]
    
    return tile
