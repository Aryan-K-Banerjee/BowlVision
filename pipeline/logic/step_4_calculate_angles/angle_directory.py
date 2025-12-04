'''--------------------------------------------------------------
Angle Calculation Directory

This module keeps track of which angle calculation functions should
be run for which views. This allows the orchestrator to remain unchanged
when new angle calculations are added.

To add a new angle:
1. Create the business logic file in pipeline/logic/angles/
2. Add the function to the appropriate view list below
3. The orchestrator will automatically call it

Format:
{
    'view_name': [
        {
            'name': 'angle_column_name',
            'function': calculation_function,
            'visibility_check': [(landmark_idx, threshold), ...]
        },
        ...
    ]
}
--------------------------------------------------------------'''

from pipeline.logic.step_4_calculate_angles.angles.front_knee_angle import calculate_front_knee_angle
from pipeline.logic.step_4_calculate_angles.angles.back_knee_angle import calculate_back_knee_angle


# Define visibility checks for front knee angle
# Requires left hip (23), knee (25), and ankle (27) to be visible
FRONT_KNEE_VISIBILITY = [(23, 0.2), (25, 0.2), (27, 0.2)]

# Define visibility checks for back knee angle
# Requires right hip (24), knee (26), and ankle (28) to be visible
BACK_KNEE_VISIBILITY = [(24, 0.2), (26, 0.2), (28, 0.2)]


# Back view angles
BACK_VIEW_ANGLES = [
    {
        'name': 'back_knee_angle',
        'function': calculate_back_knee_angle,
        'visibility_check': BACK_KNEE_VISIBILITY
    }
]


# Side view angles
SIDE_VIEW_ANGLES = [
    {
        'name': 'front_knee_angle',
        'function': calculate_front_knee_angle,
        'visibility_check': FRONT_KNEE_VISIBILITY
    },
    {
        'name': 'back_knee_angle',
        'function': calculate_back_knee_angle,
        'visibility_check': BACK_KNEE_VISIBILITY
    }
]


def get_angles_for_view(view: str) -> list:
    """Get the list of angle calculations for a specific view.
    
    Args:
        view: 'back' or 'side'
        
    Returns:
        List of angle calculation dictionaries
    """
    view_lower = view.lower()
    
    if 'back' in view_lower:
        return BACK_VIEW_ANGLES
    elif 'side' in view_lower:
        return SIDE_VIEW_ANGLES
    else:
        return []
