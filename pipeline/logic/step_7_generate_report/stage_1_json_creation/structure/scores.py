"""
Scores structure builder.

Builds the scores block from scores.json.
"""

import json
from pathlib import Path
from typing import Dict, Any


def build(session_dir: Path, back_exists: bool, side_exists: bool) -> Dict[str, Any]:
    """Build scores block.
    
    Returns:
        Scores block with overall score and breakdowns
    """
    # Load scores
    scores_path = session_dir / 'd_analysis' / 'scores.json'
    if not scores_path.exists():
        return {
            'overall_score': 0,
            'subscores': []
        }
    
    with open(scores_path, 'r') as f:
        scores_data = json.load(f)
    
    overall = scores_data.get('overall_score', 0)
    scores_dict = scores_data.get('scores', {})
    
    # Build subscores list (only metrics with actual scores, not null)
    subscores = []
    for metric_name, metric_data in scores_dict.items():
        score = metric_data.get('score')
        if score is not None:  # Only include metrics that have scores
            subscores.append({
                'name': metric_name.replace('_', ' ').title(),
                'score': score
            })
    
    return {
        'overall_score': overall,
        'subscores': subscores
    }
