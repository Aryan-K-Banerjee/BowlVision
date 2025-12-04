"""Test script for Step 7: Generate Report.

This script runs the full report generation pipeline (3 stages) for manual verification.
It assumes Steps 0-6 have already been completed for the test session.
"""

import os
from pathlib import Path
from pipeline.steps.video_existence import check_videos_exist
from pipeline.steps.generate_report import generate_report


def test_step_7_report():
    """Test Step 7: Generate Report"""
    print("\n" + "="*60)
    print("TEST: Step 7 - Generate Report (Refactored 3-Stage Pipeline)")
    print("="*60)
    print("This test will:")
    print("  1. Check which videos exist")
    print("  2. Stage 1: Generate report.json from pipeline artifacts")
    print("  3. Stage 2: Generate screenshots (original, skeleton, overlay)")
    print("  4. Stage 3: Render HTML report")
    print("="*60)
    print()
    
    session_dir = "data/test_session"
    
    # Check inputs
    print("Checking inputs...")
    back_exists, side_exists = check_videos_exist(session_dir)
    
    # Run report generation
    print("\nRunning report generation...")
    generate_report(session_dir, back_exists, side_exists)
    
    # Verify outputs
    results_dir = Path(session_dir) / "results"
    report_json = results_dir / "report.json"
    report_html = results_dir / "report.html"
    screenshots_dir = results_dir / "screenshots"
    
    print("\n" + "="*60)
    print("Verification Results:")
    print("="*60)
    
    if report_json.exists():
        print(f"✓ report.json created ({report_json.stat().st_size} bytes)")
    else:
        print("❌ report.json MISSING")
        
    if report_html.exists():
        print(f"✓ report.html created ({report_html.stat().st_size} bytes)")
    else:
        print("❌ report.html MISSING")
        
    if screenshots_dir.exists():
        count = len(list(screenshots_dir.glob("*.png")))
        print(f"✓ Screenshots directory created with {count} images")
        if count > 0:
            print("  Sample screenshots:")
            for p in list(screenshots_dir.glob("*.png"))[:3]:
                print(f"  - {p.name}")
    else:
        print("❌ Screenshots directory MISSING")
        
    print("\nTo view the report, open:")
    print(f"  {report_html.absolute()}")
    print()


if __name__ == "__main__":
    test_step_7_report()
