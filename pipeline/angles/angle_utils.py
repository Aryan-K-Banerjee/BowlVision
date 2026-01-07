"""
Utility functions for angle calculations.

These are shared helper functions used across different angle calculation modules.
"""

import math


def calculate_angle_between_points(p1: tuple, p2: tuple, p3: tuple) -> float:
    """Calculate the angle formed at point p2 by the line segments p1p2 and p2p3.

    Args:
        p1 (tuple): Coordinates of the first point (x, y)
        p2 (tuple): Coordinates of the vertex point (x, y)
        p3 (tuple): Coordinates of the third point (x, y)

    Returns:
        float: The angle in degrees
    """
    # Calculate the vectors
    v1 = (p1[0] - p2[0], p1[1] - p2[1])
    v2 = (p3[0] - p2[0], p3[1] - p2[1])

    # Calculate the dot product and magnitudes
    dot_prod = v1[0] * v2[0] + v1[1] * v2[1]
    mag_v1 = math.sqrt(v1[0]**2 + v1[1]**2)
    mag_v2 = math.sqrt(v2[0]**2 + v2[1]**2)

    # Calculate the angle in radians and then convert to degrees
    if mag_v1 == 0 or mag_v2 == 0:
        return 0.0  # Avoid division by zero; angle is undefined

    cos_angle = dot_prod / (mag_v1 * mag_v2)
    cos_angle = max(-1.0, min(1.0, cos_angle))  # Clamp value to avoid numerical issues
    angle_rad = math.acos(cos_angle)
    angle_deg = math.degrees(angle_rad)

    return angle_deg
