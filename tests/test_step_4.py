"""Test script for Step 4: Calculate angles from keypoints.

This script runs only the angle calculation step for manual verification.
It assumes Steps 0-3 have already been completed for the test session.
"""

from pipeline.steps.video_existence import check_videos_exist
from pipeline.steps.calculate_angles import calculate_angles


def test_step_4_calculate_angles():
    """Test Step 4: Calculate angles from extracted keypoints"""
    print("\n" + "="*60)
    print("TEST: Step 4 - Calculate Angles")
    print("="*60)
    print("This test will:")
    print("  1. Check which videos exist")
    print("  2. Load keypoints from c_keypoints/ CSVs")
    print("  3. Consult angle_directory for which angles to calculate")
    print("  4. Calculate angles using business logic functions")
    print("  5. Save angles to CSV files in c_keypoints/")
    print()
    print("Current angles:")
    print("  - Side view: front_knee_angle (left leg, back of knee)")
    print("  - Back view: (none yet)")
    print("="*60)
    print()
    
    session_dir = "data/test_session"
    
    # First check which videos exist
    print("Checking video existence...")
    back_exists, side_exists = check_videos_exist(session_dir)
    print()
    
    # Run angle calculation
    print("Running angle calculation step...")
    calculate_angles(session_dir, back_exists, side_exists)
    
    print("\n" + "="*60)
    print("✓ Step 4 test completed!")
    print("="*60)
    print("\nCheck the following to verify results:")
    print("  - data/test_session/c_keypoints/back_view_angles.csv")
    print("  - data/test_session/c_keypoints/side_view_angles.csv")
    print()
    print("Each CSV should have:")
    print("  - Header: frame, front_knee_angle (for side view)")
    print("  - One row per frame")
    print("  - Angle values in degrees (or -1.0 if landmarks not visible)")
    print()


if __name__ == "__main__":
    test_step_4_calculate_angles()
