"""
Crop registry - maps crop strategy names to crop functions.

Registry pattern allows easy extension of new crop strategies.
"""

from pipeline.logic.step_7_generate_report.stage_2_screenshot_engine.crops import (
    square_around_bowler,
    front_leg_focus,
    full_body
)


CROP_REGISTRY = {
    'square_around_bowler': square_around_bowler.get_crop,
    'front_leg_focus': front_leg_focus.get_crop,
    'full_body': full_body.get_crop,
}


def get_crop_function(crop_name: str):
    """Get crop function by name.
    
    Args:
        crop_name: Name of crop strategy
        
    Returns:
        Crop function, or None if not found
    """
    return CROP_REGISTRY.get(crop_name)


def get_all_crops():
    """Get list of all registered crop strategy names."""
    return list(CROP_REGISTRY.keys())
