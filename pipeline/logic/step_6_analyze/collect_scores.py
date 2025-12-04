'''--------------------------------------------------------------
Collect Scores Business Logic

This module calculates weighted scores from analyzed metrics.

Scoring system:
- ideal: 1.0 point
- good: 0.5 points
- okay: 0.25 points
- poor: 0.0 points
- unavailable/no_rule: excluded from calculation

Weighting:
1. Field-level weights within each metric category
2. Metric-level weights for overall bowling action score

If weights not found, equal weights (simple average) are used.
If metric weight is 0, it's excluded from overall score.

Output: scores.json with:
- Scores for each metric category
- Overall bowling action score
--------------------------------------------------------------'''

import os
import json
import yaml
from typing import Dict, Any, Tuple
from pipeline import location_constants as lc


# Assessment to points mapping
ASSESSMENT_POINTS = {
    "ideal": 1.0,
    "good": 0.5,
    "okay": 0.25,
    "poor": 0.0,
    "unavailable": None,  # Exclude from calculation
    "no_rule": None  # Exclude from calculation
}


def collect_scores(session_dir: str) -> None:
    """Calculate weighted scores from analyzed metrics.
    
    Args:
        session_dir: Path to the session directory
    """
    # Build file paths
    analyzed_metrics_path = session_dir + lc.analyzed_metrics
    weights_path = "pipeline/logic/step_6_analyze/weights.yaml"
    scores_path = session_dir + lc.scores
    
    # Check if files exist
    if not os.path.exists(analyzed_metrics_path):
        print(f"        COLLECT_SCORES: Analyzed metrics file not found: {analyzed_metrics_path}")
        return
    
    if not os.path.exists(weights_path):
        print(f"        COLLECT_SCORES: Weights file not found: {weights_path}")
        return
    
    # Load data
    analyzed_metrics = _load_json(analyzed_metrics_path)
    weights = _load_yaml(weights_path)
    
    if not analyzed_metrics:
        print(f"        COLLECT_SCORES: Failed to load analyzed metrics")
        return
    
    print(f"        COLLECT_SCORES: Calculating scores...")
    
    # Calculate scores
    scores = {"scores": {}}
    metric_scores = {}  # For calculating overall score
    
    # Get analyzed metrics
    analyzed = analyzed_metrics.get("analyzed_metrics", {})
    
    # Calculate score for each metric category
    for metric_name, metric_data in analyzed.items():
        if "error" in metric_data:
            scores["scores"][metric_name] = {
                "error": metric_data["error"],
                "score": None
            }
            continue
        
        # Get weights for this metric
        field_weights = weights.get("field_weights", {}).get(metric_name, {})
        
        # Calculate metric score
        metric_score, field_scores = _calculate_metric_score(metric_data, field_weights)
        
        scores["scores"][metric_name] = {
            "score": metric_score,
            "field_scores": field_scores
        }
        
        # Store for overall calculation (if metric has a weight)
        metric_weight = weights.get("metric_weights", {}).get(metric_name, 1.0)
        if metric_weight > 0 and metric_score is not None:
            metric_scores[metric_name] = {
                "score": metric_score,
                "weight": metric_weight
            }
    
    # Calculate overall score
    overall_score = _calculate_overall_score(metric_scores)
    scores["overall_score"] = overall_score
    
    # Write scores
    _write_json(scores_path, scores)
    
    print(f"        COLLECT_SCORES: Scores calculated, wrote to {scores_path}")


def _calculate_metric_score(metric_data: Dict[str, Any], field_weights: Dict[str, float]) -> Tuple[float, Dict[str, Any]]:
    """Calculate weighted score for a metric category.
    
    Returns:
        (metric_score, field_scores_dict)
    """
    field_scores = {}
    weighted_sum = 0.0
    total_weight = 0.0
    
    for field_name, field_data in metric_data.items():
        if field_name == "error":
            continue
        
        assessment = field_data.get("assessment", "unavailable")
        points = ASSESSMENT_POINTS.get(assessment)
        
        # Skip if unavailable or no rule
        if points is None:
            field_scores[field_name] = {
                "assessment": assessment,
                "points": None,
                "weight": None
            }
            continue
        
        # Get weight (default to 1.0 if not specified)
        weight = field_weights.get(field_name, 1.0)
        
        field_scores[field_name] = {
            "assessment": assessment,
            "points": points,
            "weight": weight
        }
        
        weighted_sum += points * weight
        total_weight += weight
    
    # Calculate average (or None if no valid fields)
    if total_weight > 0:
        metric_score = weighted_sum / total_weight
    else:
        metric_score = None
    
    return metric_score, field_scores


def _calculate_overall_score(metric_scores: Dict[str, Dict[str, float]]) -> float:
    """Calculate overall weighted score across all metrics.
    
    Args:
        metric_scores: Dict of {metric_name: {score, weight}}
    
    Returns:
        Overall score (0.0 to 1.0) or None if no metrics
    """
    if not metric_scores:
        return None
    
    weighted_sum = 0.0
    total_weight = 0.0
    
    for metric_name, data in metric_scores.items():
        score = data["score"]
        weight = data["weight"]
        
        if score is not None and weight > 0:
            weighted_sum += score * weight
            total_weight += weight
    
    if total_weight > 0:
        return weighted_sum / total_weight
    else:
        return None


def _load_json(path: str) -> Dict[str, Any]:
    """Load JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"        COLLECT_SCORES: Error loading JSON from {path}: {e}")
        return {}


def _load_yaml(path: str) -> Dict[str, Any]:
    """Load YAML file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"        COLLECT_SCORES: Error loading YAML from {path}: {e}")
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
        print(f"        COLLECT_SCORES: Error writing JSON to {path}: {e}")