'''--------------------------------------------------------------
Analyze Metrics Business Logic

This module analyzes extracted metrics by comparing them against
thresholds defined in rules.yaml.

For each metric, it evaluates the value and assigns:
- assessment: ideal/good/okay/poor/unavailable
- description: Human-readable threshold description

The analysis is simpler than the core version - it just compares
metrics to rules and writes the analyzed result.
--------------------------------------------------------------'''

import os
import json
import yaml
from typing import Dict, Any
from pipeline import location_constants as lc


def analyze_metrics(session_dir: str) -> None:
    """Analyze extracted metrics against rules.
    
    Args:
        session_dir: Path to the session directory
    """
    # Build file paths
    extracted_metrics_path = session_dir + lc.extracted_metrics
    rules_path = "pipeline/logic/step_6_analyze/rules.yaml"  # Local rules file
    analyzed_metrics_path = session_dir + lc.analyzed_metrics
    
    # Check if files exist
    if not os.path.exists(extracted_metrics_path):
        print(f"        ANALYZE_METRICS: Extracted metrics file not found: {extracted_metrics_path}")
        return
    
    if not os.path.exists(rules_path):
        print(f"        ANALYZE_METRICS: Rules file not found: {rules_path}")
        return
    
    # Load data
    extracted_metrics = _load_json(extracted_metrics_path)
    rules = _load_yaml(rules_path)
    
    if not extracted_metrics or not rules:
        print(f"        ANALYZE_METRICS: Failed to load data files")
        return
    
    print(f"        ANALYZE_METRICS: Analyzing metrics...")
    
    # Analyze all metrics
    analyzed = {"analyzed_metrics": {}}
    
    # Get extracted metrics
    extracted = extracted_metrics.get("extracted_metrics", {})
    
    # Analyze each metric category
    for metric_name, metric_data in extracted.items():
        # Special handling for hip_vs_knee_dominance (custom classification)
        if metric_name == "hip_vs_knee_dominance":
            print(f"        ANALYZE_METRICS: Analyzing {metric_name} (custom classification)...")
            analyzed["analyzed_metrics"][metric_name] = _analyze_hip_vs_knee_dominance(metric_data)
        # Special handling for bowler_alignment (custom classification)
        elif metric_name == "bowler_alignment":
            print(f"        ANALYZE_METRICS: Analyzing {metric_name} (custom classification)...")
            analyzed["analyzed_metrics"][metric_name] = _analyze_bowler_alignment(metric_data)
        elif metric_name in rules.get("metrics", {}):
            print(f"        ANALYZE_METRICS: Analyzing {metric_name}...")
            analyzed["analyzed_metrics"][metric_name] = _analyze_metric_category(
                metric_name, metric_data, rules["metrics"][metric_name]
            )
        else:
            print(f"        ANALYZE_METRICS: No rules found for {metric_name}, skipping")
    
    # Write analyzed metrics
    _write_json(analyzed_metrics_path, analyzed)
    
    print(f"        ANALYZE_METRICS: Analysis complete, wrote to {analyzed_metrics_path}")


def _analyze_metric_category(metric_name: str, metric_data: Dict[str, Any], metric_rules: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a single metric category (e.g., front_leg_brace)."""
    
    result = {}
    
    # If there's an error in the extracted metrics, preserve it
    if "error" in metric_data:
        result["error"] = metric_data["error"]
        return result
    
    # Get the rules for each sub-metric
    rules = metric_rules.get("rules", {})
    
    # Analyze each sub-metric
    for sub_metric_name, sub_metric_value in metric_data.items():
        if sub_metric_name == "error":
            continue
            
        if sub_metric_name in rules:
            rule = rules[sub_metric_name]
            
            # Extract the angle value (handle both old and new structures)
            if isinstance(sub_metric_value, dict):
                angle = sub_metric_value.get("angle", -1.0)
            else:
                angle = sub_metric_value
            
            # Evaluate against thresholds
            evaluation = _evaluate_threshold(angle, rule)
            
            # Build result with original value + assessment
            result[sub_metric_name] = {
                "value": sub_metric_value,  # Include original structure (angle + frames)
                "assessment": evaluation["assessment"],
                "description": evaluation["description"]
            }
        else:
            # No rule for this sub-metric, just pass through
            result[sub_metric_name] = {
                "value": sub_metric_value,
                "assessment": "no_rule",
                "description": "No rule defined for this metric"
            }
    
    return result


def _analyze_hip_vs_knee_dominance(metric_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze hip vs knee dominance using custom classification logic.
    
    Classification rule:
    - If either back knee angle (back view or side view) at BFC is < 150°: knee dominant
    - Otherwise: hip dominant
    """
    result = {}
    
    # Extract angle values
    back_view_data = metric_data.get("back_knee_angle_back_view", {})
    side_view_data = metric_data.get("back_knee_angle_side_view", {})
    
    back_view_angle = back_view_data.get("angle", -1.0)
    side_view_angle = side_view_data.get("angle", -1.0)
    
    # Check if data is available
    back_view_available = back_view_angle > -1.0
    side_view_available = side_view_angle > -1.0
    
    # Apply classification rule
    if not back_view_available and not side_view_available:
        # No data available
        classification = "unavailable"
        description = "Insufficient data to determine dominance classification"
    elif back_view_available and back_view_angle < 150.0:
        classification = "knee_dominant"
        description = f"Knee dominant (back view angle {back_view_angle:.1f}° < 150°)"
    elif side_view_available and side_view_angle < 150.0:
        classification = "knee_dominant"
        description = f"Knee dominant (side view angle {side_view_angle:.1f}° < 150°)"
    else:
        classification = "hip_dominant"
        description = f"Hip dominant (both angles >= 150°)"
    
    # Build result structure
    result["back_knee_angle_back_view"] = {
        "value": back_view_data,
        "assessment": classification if back_view_available else "unavailable",
        "description": f"Back view: {back_view_angle:.1f}°" if back_view_available else "Data not available"
    }
    
    result["back_knee_angle_side_view"] = {
        "value": side_view_data,
        "assessment": classification if side_view_available else "unavailable",
        "description": f"Side view: {side_view_angle:.1f}°" if side_view_available else "Data not available"
    }
    
    result["classification"] = {
        "value": classification,
        "assessment": classification,
        "description": description
    }
    
    return result


def _analyze_bowler_alignment(metric_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze bowler alignment using custom classification logic.
    
    Classification:
    - 0-20°: front_on
    - 20-60°: semi_side_on
    - 60+°: side_on
    """
    result = {}
    
    # Extract angle value
    angle_data = metric_data.get("back_foot_xy_angle", {})
    angle = angle_data.get("angle", -1.0)
    
    # Check if data is available
    angle_available = angle > -1.0
    
    # Apply classification rule
    if not angle_available:
        classification = "unavailable"
        description = "Insufficient data to determine alignment classification"
    elif angle < 20.0:
        classification = "front_on"
        description = f"Front-on alignment (angle: {angle:.1f}°, 0-20° range)"
    elif angle < 60.0:
        classification = "semi_side_on"
        description = f"Semi side-on alignment (angle: {angle:.1f}°, 20-60° range)"
    else:
        classification = "side_on"
        description = f"Side-on alignment (angle: {angle:.1f}°, 60+° range)"
    
    # Build result structure
    result["back_foot_xy_angle"] = {
        "value": angle_data,
        "assessment": classification if angle_available else "unavailable",
        "description": f"Back foot orientation: {angle:.1f}°" if angle_available else "Data not available"
    }
    
    result["classification"] = {
        "value": classification,
        "assessment": classification,
        "description": description
    }
    
    return result


def _evaluate_threshold(value: float, rule: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a single value against threshold rules."""
    
    # Handle sentinel/unavailable values (exactly -1.0)
    # Use a small epsilon for floating point comparison
    if abs(value - (-1.0)) < 0.001:
        return {
            "assessment": "unavailable",
            "description": "Data not available"
        }
    
    compare = rule.get("compare", "greater_equal")
    thresholds = rule.get("thresholds", {})
    
    # Extract threshold values
    ideal_thresh = thresholds.get("ideal", {})
    good_thresh = thresholds.get("good", {})
    okay_thresh = thresholds.get("okay", {})
    poor_thresh = thresholds.get("poor", {})
    
    ideal_val = ideal_thresh.get("value", 0)
    good_val = good_thresh.get("value", 0)
    okay_val = okay_thresh.get("value", 0)
    
    if compare == "greater_equal":
        # Higher is better
        if value >= ideal_val:
            return {
                "assessment": "ideal",
                "description": ideal_thresh.get("description", "Ideal")
            }
        elif value >= good_val:
            return {
                "assessment": "good",
                "description": good_thresh.get("description", "Good")
            }
        elif value >= okay_val:
            return {
                "assessment": "okay",
                "description": okay_thresh.get("description", "Okay")
            }
        else:
            return {
                "assessment": "poor",
                "description": poor_thresh.get("description", "Poor")
            }
    else:  # less_equal
        # Lower is better
        if value <= ideal_val:
            return {
                "assessment": "ideal",
                "description": ideal_thresh.get("description", "Ideal")
            }
        elif value <= good_val:
            return {
                "assessment": "good",
                "description": good_thresh.get("description", "Good")
            }
        elif value <= okay_val:
            return {
                "assessment": "okay",
                "description": okay_thresh.get("description", "Okay")
            }
        else:
            return {
                "assessment": "poor",
                "description": poor_thresh.get("description", "Poor")
            }


def _load_json(path: str) -> Dict[str, Any]:
    """Load JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"        ANALYZE_METRICS: Error loading JSON from {path}: {e}")
        return {}


def _load_yaml(path: str) -> Dict[str, Any]:
    """Load YAML file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"        ANALYZE_METRICS: Error loading YAML from {path}: {e}")
        return {}


def _write_json(path: str, data: Dict[str, Any]) -> None:
    """Write JSON file."""
    try:
        # Ensure output directory exists
        out_dir = os.path.dirname(path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"        ANALYZE_METRICS: Error writing JSON to {path}: {e}")
