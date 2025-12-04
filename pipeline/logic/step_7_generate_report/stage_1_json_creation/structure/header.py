"""
Header structure builder.

Builds the header block from session_info.json, bowler_info.json, and scores.json.
"""

import json
from pathlib import Path
from typing import Dict, Any


def build(session_dir: Path, back_exists: bool, side_exists: bool) -> Dict[str, Any]:
    """Build header block.
    
    Returns:
        Header block with session info, bowler info, scores summary, etc.
    """
    # Load artifacts
    session_info = _load_json(session_dir / 'session_info.json')
    bowler_info = _load_json(session_dir / 'bowler_info.json')
    scores = _load_json(session_dir / 'd_analysis' / 'scores.json')
    analyzed_metrics = _load_json(session_dir / 'd_analysis' / 'analyzed_metrics.json')
    
    # Build header
    header = {
        'session_info': session_info,
        'bowler_info': bowler_info,
        'bowler_image': 'bowler_image.jpg' if (session_dir / 'bowler_image.jpg').exists() else None,
        'score_summary': _build_score_summary(scores),
        'classification_summary': _build_classification_summary(analyzed_metrics),
        'video_existence_summary': _build_video_summary(back_exists, side_exists)
    }
    
    return header


def _load_json(path: Path) -> Dict[str, Any]:
    """Load JSON file, return empty dict if not found."""
    if not path.exists():
        return {}
    
    with open(path, 'r') as f:
        return json.load(f)


def _build_score_summary(scores: dict) -> str:
    """Build summary text from scores."""
    if not scores:
        return "No scores available"
    
    # scores.json has overall_score directly
    total = scores.get('overall_score', 0)
    
    return f"Overall Score: {total:.2f}"


def _build_classification_summary(analyzed_metrics: dict) -> str:
    """Build classification summary from analyzed metrics."""
    if not analyzed_metrics or 'analyzed_metrics' not in analyzed_metrics:
        return "No classifications available"
    
    metrics = analyzed_metrics['analyzed_metrics']
    classifications = []
    
    # Hip vs knee dominance
    if 'hip_vs_knee_dominance' in metrics:
        classification = metrics['hip_vs_knee_dominance'].get('classification', {})
        value = classification.get('value', 'unknown')
        if value != 'unknown':
            classifications.append(value.replace('_', ' ').title())
    
    # Bowler alignment
    if 'bowler_alignment' in metrics:
        classification = metrics['bowler_alignment'].get('classification', {})
        value = classification.get('value', 'unknown')
        if value != 'unknown':
            classifications.append(value.replace('_', ' ').title())
    
    if classifications:
        return ", ".join(classifications)
    return "No classifications available"


def _build_video_summary(back_exists: bool, side_exists: bool) -> str:
    """Build summary of video availability."""
    if back_exists and side_exists:
        return "Both back and side view videos available"
    elif side_exists:
        return "Side view video available (back view missing)"
    elif back_exists:
        return "Back view video available (side view missing)"
    else:
        return "No videos available"
