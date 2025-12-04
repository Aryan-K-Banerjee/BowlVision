"""
Bowler alignment metric structure builder.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


def build(session_dir: Path, back_exists: bool, side_exists: bool) -> Optional[Dict[str, Any]]:
    """Build bowler_alignment metric entry."""
    analyzed_path = session_dir / 'd_analysis' / 'analyzed_metrics.json'
    if not analyzed_path.exists():
        return None
    
    with open(analyzed_path, 'r') as f:
        data = json.load(f)
    
    metric_data = data.get('analyzed_metrics', {}).get('bowler_alignment')
    if not metric_data:
        return None
    
    classification = metric_data.get('classification', {})
    angle_data = metric_data.get('back_foot_xy_angle', {})
    angle_value = angle_data.get('value', {}).get('angle', 0)
    
    return {
        'id': 'bowler_alignment',
        'name': 'Bowler Alignment',
        'group': 'Biomechanics',
        'value': angle_value,
        'unit': 'degrees',
        'score': 5.0,  # Classification doesn't have numeric score
        'rating': classification.get('value', 'unknown'),
        'tags': [],
        'description': 'Classifies bowler alignment as front-on, semi side-on, or side-on',
        'analysis': classification.get('description', 'No analysis available'),
        'screenshots': []  # Could add BFC screenshot
    }
