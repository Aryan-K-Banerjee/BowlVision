"""
Screenshots Package

Screenshot generation engine with modular type renderers, 
crop strategies, and angle overlay functions.
"""

from pipeline.screenshots.screenshot_engine import generate_screenshots
from pipeline.screenshots.types import get_type_renderer, get_all_types
from pipeline.screenshots.crops import get_crop_function, get_all_crops
from pipeline.screenshots.angles import get_angle_function, get_all_angles
from pipeline.screenshots.drawing import draw_skeleton, draw_angle_arc

__all__ = [
    'generate_screenshots',
    'get_type_renderer',
    'get_all_types',
    'get_crop_function',
    'get_all_crops',
    'get_angle_function',
    'get_all_angles',
    'draw_skeleton',
    'draw_angle_arc',
]
