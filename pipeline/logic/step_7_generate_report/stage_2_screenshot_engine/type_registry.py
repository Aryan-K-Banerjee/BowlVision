"""
Type registry - maps type names to renderer functions.

Registry pattern allows easy extension of new visualization types.
"""

from pipeline.logic.step_7_generate_report.stage_2_screenshot_engine.types import (
    original,
    skeleton,
    overlay
)


TYPE_REGISTRY = {
    'original': original.render,
    'skeleton': skeleton.render,
    'overlay': overlay.render,
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
