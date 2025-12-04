"""
Step 7: Generate Final Report

Main orchestrator that coordinates all 3 stages:
1. JSON Creation - combine artifacts into report.json
2. Screenshot Engine - generate all screenshots from specs
3. HTML Creation - render final HTML report

Refactored from core/report with preserved visual quality.
"""

from pipeline.logic.step_7_generate_report.stage_1_json_creation.generate_final_json import generate_report_json
from pipeline.logic.step_7_generate_report.stage_2_screenshot_engine.screenshot_engine import generate_screenshots
from pipeline.logic.step_7_generate_report.stage_3_html_creation.html_engine import generate_html_report


def generate_report(session_dir: str, back_view_exists: bool, side_view_exists: bool):
    """Generate complete HTML report with screenshots.
    
    Args:
        session_dir: Path to session directory
        back_view_exists: Whether back view video exists
        side_view_exists: Whether side view video exists
    """
    print("    REPORT: Starting report generation (3-stage architecture)...")
    
    # Stage 1: Generate report.json from pipeline artifacts
    print("    REPORT: Stage 1 - Generating report.json...")
    report_json_path = generate_report_json(session_dir, back_view_exists, side_view_exists)
    
    # Stage 2: Generate all screenshots from report.json specs
    print("    REPORT: Stage 2 - Generating screenshots...")
    generate_screenshots(session_dir, report_json_path)
    
    # Stage 3: Render HTML from report.json and screenshots
    print("    REPORT: Stage 3 - Generating HTML...")
    html_path = generate_html_report(session_dir, report_json_path)
    
    print(f"    REPORT: Report generation complete - {html_path}")