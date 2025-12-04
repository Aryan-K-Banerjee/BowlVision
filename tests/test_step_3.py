"""Test script for Step 3: Extract skeleton keypoints.

This script runs only the skeleton extraction step for manual verification.
It assumes Steps 0-2 have already been completed for the test session.
"""

from pipeline.steps.video_existence import check_videos_exist
from pipeline.steps.get_skeleton import get_skeletons


def test_step_3_get_skeletons():
    """Test Step 3: Extract skeleton keypoints using MediaPipe"""
    print("\n" + "="*60)
    print("TEST: Step 3 - Extract Skeleton Keypoints")
    print("="*60)
    print("This test will:")
    print("  1. Check which videos exist")
    print("  2. Load preprocessed videos from b_clips/")
    print("  3. Use MediaPipe Pose to extract 33 landmarks per frame")
    print("  4. Save keypoints to CSV files in c_keypoints/")
    print()
    print("NOTE: This can take several minutes depending on video length!")
    print("="*60)
    print()
    
    session_dir = "data/test_session"
    
    # First check which videos exist
    print("Checking video existence...")
    back_exists, side_exists = check_videos_exist(session_dir)
    print()
    
    # Run skeleton extraction
    print("Running skeleton extraction step...")
    print("(MediaPipe will process each frame - this may take a while)")
    print()
    get_skeletons(session_dir, back_exists, side_exists)
    
    print("\n" + "="*60)
    print("✓ Step 3 test completed!")
    print("="*60)
    print("\nCheck the following to verify results:")
    print("  - data/test_session/c_keypoints/back_view_keypoints.csv")
    print("  - data/test_session/c_keypoints/side_view_keypoints.csv")
    print()
    print("Each CSV should have:")
    print("  - Header: frame, time_s, lm0_x, lm0_y, lm0_z, lm0_vis, ...")
    print("  - 33 landmarks (lm0 - lm32) with x, y, z, visibility")
    print("  - One row per frame")
    print()


if __name__ == "__main__":
    test_step_3_get_skeletons()
