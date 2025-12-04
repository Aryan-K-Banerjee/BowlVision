"""
Stage 1 - JSON Creation Orchestrator

Generates report.json by combining pipeline artifacts (analyzed_metrics.json, scores.json, etc.)
Calls structure builders to create each section of the report.
"""

import json
from pathlib import Path
from typing import Dict, Any

from pipeline.logic.step_7_generate_report.stage_1_json_creation.json_structure_directory import (
    get_structure_builder
)


def generate_report_json(session_dir: str, back_view_exists: bool, side_view_exists: bool) -> str:
    """Generate report.json from pipeline artifacts.
    
    Args:
        session_dir: Path to session directory
        back_view_exists: Whether back view video exists
        side_view_exists: Whether side view video exists
        
    Returns:
        Path to generated report.json
    """
    session_dir = Path(session_dir)
    
    print("    JSON_CREATION: Starting report.json generation...")
    
    # Build each section using structure builders
    report = {
        'version': '1.0',
        'header': _build_section('header', session_dir, back_view_exists, side_view_exists),
        'video_events_classification': _build_section('video_events', session_dir, back_view_exists, side_view_exists),
        'scores': _build_section('scores', session_dir, back_view_exists, side_view_exists),
        'metrics': _build_metrics(session_dir, back_view_exists, side_view_exists)
    }
    
    # Write report.json
    output_path = session_dir / 'results' / 'report.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"    JSON_CREATION: Generated {output_path}")
    
    return str(output_path)


def _build_section(section_name: str, session_dir: Path, back_exists: bool, side_exists: bool) -> Dict[str, Any]:
    """Build a single section using registered structure builder."""
    builder = get_structure_builder(section_name)
    if builder:
        return builder(session_dir, back_exists, side_exists)
    else:
        print(f"      WARNING: No builder for section '{section_name}'")
        return {}


def _build_metrics(session_dir: Path, back_exists: bool, side_exists: bool) -> list:
    """Build metrics list using individual metric builders."""
    metrics = []
    
    # Only include actual performance metrics, not classifications
    metric_names = ['front_leg_brace']
    
    for metric_name in metric_names:
        builder = get_structure_builder(f'metric_{metric_name}')
        if builder:
            metric_data = builder(session_dir, back_exists, side_exists)
            if metric_data:  # Only add if builder returned data
                metrics.append(metric_data)
        else:
            print(f"      WARNING: No builder for metric '{metric_name}'")
    
    return metrics
