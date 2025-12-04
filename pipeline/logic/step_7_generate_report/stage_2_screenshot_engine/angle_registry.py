"""
Angle registry - maps angle names to geometry functions.

Registry pattern allows easy extension of new angle overlays.
"""

from pipeline.logic.step_7_generate_report.stage_2_screenshot_engine.angles import (
    front_knee,
    back_knee,
    none as none_angle
)


ANGLE_REGISTRY = {
    'front_knee': front_knee.get_angle_points,
    'back_knee': back_knee.get_angle_points,
    'none': none_angle.get_angle_points,
}


def get_angle_function(angle_name: str):
    """Get angle geometry function by name.
    
    Args:
        angle_name: Name of angle (e.g., 'front_knee', 'back_knee', 'none')
        
    Returns:
        Angle function, or None if not found
    """
    return ANGLE_REGISTRY.get(angle_name)


def get_all_angles():
    """Get list of all registered angle names."""
    return list(ANGLE_REGISTRY.keys())
