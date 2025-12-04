'''--------------------------------------------------------------
Calculate Angles Orchestrator

This module orchestrates the calculation of angles from keypoints for
both back and side views.

The three-tiered architecture:
1. Pipeline calls this orchestrator
2. Orchestrator delegates to calculate_angles_for_view logic
3. Logic consults angle_directory and calls business logic functions

This design allows new angles to be added without modifying this file:
- Add the calculation logic in pipeline/logic/angles/
- Register it in angle_directory.py
- It will automatically be calculated
--------------------------------------------------------------'''

from pipeline.logic.step_4_calculate_angles.calculate_angles_for_view import calculate_angles_for_view
from pipeline import location_constants as lc


def calculate_angles(session_dir: str, back_view_exists: bool, side_view_exists: bool):
    """Orchestrate angle calculation for both views.
    
    Args:
        session_dir: Path to the session directory
        back_view_exists: Whether the back view video exists
        side_view_exists: Whether the side view video exists
    """
    # Calculate angles for back view
    if not back_view_exists:
        print("    CALCULATE_ANGLES: Back View doesn't exist, skipping")
    else:
        print("    CALCULATE_ANGLES: Calculating angles for Back View...")
        keypoints_path = session_dir + lc.back_view_keypoints
        angles_path = session_dir + lc.back_view_angles
        
        calculate_angles_for_view(keypoints_path, angles_path, 'back')
    
    # Calculate angles for side view
    if not side_view_exists:
        print("    CALCULATE_ANGLES: Side View doesn't exist, skipping")
    else:
        print("    CALCULATE_ANGLES: Calculating angles for Side View...")
        keypoints_path = session_dir + lc.side_view_keypoints
        angles_path = session_dir + lc.side_view_angles
        
        calculate_angles_for_view(keypoints_path, angles_path, 'side')
    
    print("    CALCULATE_ANGLES: Angle calculation complete")
