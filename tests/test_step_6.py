"""Test script for Step 6: Analyze metrics against rules.

This script runs only the analysis step for manual verification.
It assumes Steps 0-5 have already been completed for the test session.
"""

from pipeline.steps.video_existence import check_videos_exist
from pipeline.steps.analyze import run_analysis


def test_step_6_analyze():
    """Test Step 6: Analyze metrics against rules"""
    print("\n" + "="*60)
    print("TEST: Step 6 - Analyze Metrics")
    print("="*60)
    print("This test will:")
    print("  1. Check which videos exist")
    print("  2. Load extracted_metrics.json")
    print("  3. Load rules.yaml")
    print("  4. Compare each metric against thresholds")
    print("  5. Assign assessments (ideal/good/okay/poor)")
    print("  6. Save to analyzed_metrics.json in d_analysis/")
    print()
    print("Current metrics being analyzed:")
    print("  - front_leg_brace (4 sub-metrics)")
    print("="*60)
    print()
    
    session_dir = "data/test_session"
    
    # First check which videos exist
    print("Checking video existence...")
    back_exists, side_exists = check_videos_exist(session_dir)
    print()
    
    # Run analysis
    print("Running analysis step...")
    run_analysis(session_dir, back_exists, side_exists)
    
    print("\n" + "="*60)
    print("✓ Step 6 test completed!")
    print("="*60)
    print("\nCheck the following to verify results:")
    print("  - data/test_session/d_analysis/analyzed_metrics.json")
    print()
    print("The JSON should contain:")
    print("  - analyzed_metrics.front_leg_brace")
    print("    - For each sub-metric:")
    print("      - value: {original metric structure}")
    print("      - assessment: ideal/good/okay/poor/unavailable")
    print("      - description: Human-readable threshold description")
    print()


if __name__ == "__main__":
    test_step_6_analyze()
