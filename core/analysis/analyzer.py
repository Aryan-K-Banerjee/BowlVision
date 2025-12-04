#core/analysis/analyzer.py
"""Analyze extracted metrics against rules and generate analysis results.

This module orchestrates the analysis process by:
1. Loading session and bowler metadata
2. Loading video events data
3. Loading extracted metrics
4. Loading rules from rules.yaml
5. Calling metric-specific analyzers (e.g., analyze_front_leg_brace)
6. Aggregating results into analysis_results.json

The output JSON structure includes session/bowler metadata, video status,
events, and detailed metric analysis with qualitative assessments.
"""

import os
import json
from typing import Dict, Any

try:
    import yaml
except ImportError:
    yaml = None

from core.analysis.metrics import front_leg_brace


def _load_json_safe(path: str) -> Dict[str, Any]:
    """Load JSON file safely, return empty dict on error."""
    try:
        if not os.path.exists(path):
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _load_yaml_safe(path: str) -> Dict[str, Any]:
    """Load YAML file safely, return empty dict on error."""
    if yaml is None:
        return {}
    try:
        if not os.path.exists(path):
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def analyze_metrics(
    session_metadata_location: str,
    bowler_metadata_location: str,
    back_view_exists: bool,
    side_view_exists: bool,
    back_view_events_location: str,
    side_view_events_location: str,
    extracted_metrics_location: str,
    analysis_results_location: str
) -> None:
    """Top-level analyzer orchestrator called by the pipeline.

    Loads all necessary data, calls metric-specific analyzers, and writes
    the final analysis_results.json with session metadata, video data, and
    detailed analysis results.
    """
    # Load metadata
    session_metadata = _load_json_safe(session_metadata_location)
    bowler_metadata = _load_json_safe(bowler_metadata_location)

    # Load events
    back_events = _load_json_safe(back_view_events_location) if back_view_exists else {}
    side_events = _load_json_safe(side_view_events_location) if side_view_exists else {}

    # Load extracted metrics
    extracted_metrics = _load_json_safe(extracted_metrics_location)

    # Load rules (rules.yaml is in core/analysis/)
    rules_path = os.path.join(os.path.dirname(__file__), 'rules.yaml')
    rules = _load_yaml_safe(rules_path)

    # Prepare videos_data section
    videos_data = {
        "back_view": {
            "exists": back_view_exists,
            "events": back_events.get('video', {}).get('events', {}) if back_view_exists else {},
        },
        "side_view": {
            "exists": side_view_exists,
            "events": side_events.get('video', {}).get('events', {}) if side_view_exists else {},
        }
    }

    # Call metric-specific analyzers
    analysis = {}

    # Front leg brace analysis (side view only)
    if side_view_exists:
        try:
            flb_analysis = front_leg_brace.analyze_front_leg_brace(extracted_metrics, rules)
            analysis.update(flb_analysis)
        except Exception:
            analysis["front_leg_brace"] = {"error": "Analysis failed"}
    else:
        analysis["front_leg_brace"] = {"note": "Side view not available"}

    # Future metrics can be added here (e.g., back view metrics)

    # Build final output structure
    output = {
        "analysis_results": {
            "session_metadata": session_metadata,
            "bowler_metadata": bowler_metadata,
            "videos_data": videos_data,
            "analysis": analysis,
        }
    }

    # Write to file
    try:
        out_dir = os.path.dirname(analysis_results_location)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        with open(analysis_results_location, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=4)
        print(f"Analysis results written to: {analysis_results_location}")
    except Exception as e:
        print(f"Error writing analysis results: {e}")
