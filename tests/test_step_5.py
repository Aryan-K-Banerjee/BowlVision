"""Test script for Step 5: Extract metrics from angles and events.

This script runs only the metrics extraction step for manual verification.
It assumes Steps 0-4 have already been completed for the test session.
"""

from pipeline.steps.video_existence import check_videos_exist
from pipeline.steps.extract_metrics import extract_metrics


def test_step_5_extract_metrics():
    """Test Step 5: Extract metrics from angles and events"""
    print("\n" + "="*60)
    print("TEST: Step 5 - Extract Metrics")
    print("="*60)
    print("This test will:")
    print("  1. Check which videos exist")
    print("  2. Consult metrics_directory for which metrics to extract")
    print("  3. Each metric loads its own data (angles, events)")
    print("  4. Calculate and aggregate all metrics")
    print("  5. Save to extracted_metrics.json in d_analysis/")
    print()
    print("Current metrics:")
    print("  - front_leg_brace (uses side view angles + events)")
    print("="*60)
    print()
    
    session_dir = "data/test_session"
    
    # First check which videos exist
    print("Checking video existence...")
    back_exists, side_exists = check_videos_exist(session_dir)
    print()
    
    # Run metrics extraction
    print("Running metrics extraction step...")
    extract_metrics(session_dir, back_exists, side_exists)
    
    print("\n" + "="*60)
    print("✓ Step 5 test completed!")
    print("="*60)
    print("\nCheck the following to verify results:")
    print("  - data/test_session/d_analysis/extracted_metrics.json")
    print()
    print("The JSON should contain:")
    print("  - extracted_metrics.front_leg_brace")
    print("    - front_knee_angle_at_ffc: {angle, frame}")
    print("    - front_knee_angle_at_release: {angle, frame}")
    print("    - difference_ffc_release: {angle, frame}")
    print("    - max_difference_ffc_release: {angle, knee_angle, frame}")
    print()


if __name__ == "__main__":
    test_step_5_extract_metrics()
