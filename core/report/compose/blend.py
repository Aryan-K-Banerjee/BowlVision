# core/report/compose/blend.py
"""Blend two tiles for composite shots."""

import numpy as np
import cv2
from typing import Tuple


def blend(tile_a: np.ndarray, tile_b: np.ndarray, 
          alpha_a: float, alpha_b: float) -> np.ndarray:
    """Blend two tiles with given opacities.
    
    Args:
        tile_a: first tile (BGR numpy array)
        tile_b: second tile (BGR numpy array, same size as tile_a)
        alpha_a: opacity for tile_a (0.0 - 1.0)
        alpha_b: opacity for tile_b (0.0 - 1.0)
    
    Returns:
        Blended tile (BGR numpy array)
    """
    # Ensure tiles are same size
    if tile_a.shape != tile_b.shape:
        # Resize tile_b to match tile_a
        tile_b = cv2.resize(tile_b, (tile_a.shape[1], tile_a.shape[0]))
    
    # Blend
    blended = cv2.addWeighted(tile_a, alpha_a, tile_b, alpha_b, 0)
    
    return blended
