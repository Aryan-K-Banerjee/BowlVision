"""
Hip vs knee dominance metric structure builder.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


def build(session_dir: Path, back_exists: bool, side_exists: bool) -> Optional[Dict[str, Any]]:
    """Build hip_vs_knee_dominance metric entry."""
    analyzed_path = session_dir / 'd_analysis' / 'analyzed_metrics.json'
    if not analyzed_path.exists():
        return None
    
    with open(analyzed_path, 'r') as f:
        data = json.load(f)
    
    metric_data = data.get('analyzed_metrics', {}).get('hip_vs_knee_dominance')
    if not metric_data:
        return None
    
    classification = metric_data.get('classification', {})
    
    return {
        'id': 'hip_vs_knee_dominance',
        'name': 'Hip vs Knee Dominance',
        'group': 'Biomechanics',
        'value': classification.get('value', 'unknown'),
        'unit': 'classification',
        'score': 5.0,  # Classification doesn't have numeric score
        'rating': classification.get('value', 'unknown'),
        'tags': [],
        'description': 'Classifies bowler as hip dominant or knee dominant based on back knee angle at BFC',
        'analysis': classification.get('description', 'No analysis available'),
        'screenshots': []  # Could add BFC screenshots with back knee angle
    }
