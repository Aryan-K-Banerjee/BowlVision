"""Test script for Step 2: Preprocess videos.

This script runs only the preprocessing step for manual verification.
It assumes Step 0 and Step 1 have already been completed for the test session.
"""

from pipeline.steps.video_existence import check_videos_exist
from pipeline.steps.preprocess import preprocess_videos


def test_step_2_preprocess():
    """Test Step 2: Preprocess videos (trim and optionally flip)"""
    print("\n" + "="*60)
    print("TEST: Step 2 - Preprocess Videos")
    print("="*60)
    print("This test will:")
    print("  1. Check which videos exist")
    print("  2. Read bowler hand from bowler_info.json")
    print("  3. Trim videos (2s before jump to 2s after release)")
    print("  4. Flip horizontally if bowler is left-handed")
    print("  5. Save trimmed videos to b_clips/")
    print("  6. Update events JSON files with adjusted frame numbers")
    print("="*60)
    print()
    
    session_dir = "data/test_session"
    
    # First check which videos exist
    print("Checking video existence...")
    back_exists, side_exists = check_videos_exist(session_dir)
    print()
    
    # Run preprocessing
    print("Running preprocessing step...")
    preprocess_videos(session_dir, back_exists, side_exists)
    
    print("\n" + "="*60)
    print("✓ Step 2 test completed!")
    print("="*60)
    print("\nCheck the following to verify results:")
    print("  - data/test_session/b_clips/back_view.mp4")
    print("  - data/test_session/b_clips/side_view.mp4")
    print("  - data/test_session/b_clips/back_view_events.json")
    print("  - data/test_session/b_clips/side_view_events.json")
    print()


if __name__ == "__main__":
    test_step_2_preprocess()
