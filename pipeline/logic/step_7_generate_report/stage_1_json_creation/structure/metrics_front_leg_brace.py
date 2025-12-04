"""
Front leg brace metric structure builder.

Builds metric entry with values, analysis, and screenshot specs.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


def build(session_dir: Path, back_exists: bool, side_exists: bool) -> Optional[Dict[str, Any]]:
    """Build front_leg_brace metric entry.
    
    Returns:
        Metric dict with all data and screenshot specs, or None if metric not available
    """
    # Load analyzed metrics
    analyzed_path = session_dir / 'd_analysis' / 'analyzed_metrics.json'
    if not analyzed_path.exists():
        return None
    
    with open(analyzed_path, 'r') as f:
        data = json.load(f)
    
    analyzed_metrics = data.get('analyzed_metrics', {})
    front_leg_brace = analyzed_metrics.get('front_leg_brace')
    
    if not front_leg_brace:
        return None
    
    # Load scores
    scores_path = session_dir / 'd_analysis' / 'scores.json'
    score = 0
    if scores_path.exists():
        with open(scores_path, 'r') as f:
            scores_data = json.load(f)
        score = scores_data.get('scores', {}).get('front_leg_brace', {}).get('score', 0)
    
    # Load events for frame numbers
    events_path = session_dir / 'b_clips' / 'side_view_events.json'
    events = _load_events(events_path) if side_exists else {}
    
    # Extract key values
    ffc_data = front_leg_brace.get('front_knee_angle_at_ffc', {})
    release_data = front_leg_brace.get('front_knee_angle_at_release', {})
    
    ffc_value = ffc_data.get('value', {}).get('angle', 0)
    release_value = release_data.get('value', {}).get('angle', 0)
    ffc_assessment = ffc_data.get('assessment', 'unknown')
    
    # Build metric entry
    return {
        'id': 'front_leg_brace',
        'name': 'Front Leg Brace',
        'group': 'Brace',
        'value': ffc_value,
        'unit': 'degrees',
        'score': score,  # Use actual score from scores.json
        'rating': ffc_assessment,
        'tags': [],
        'description': 'Front knee angle at FFC - measures leg brace quality',
        'analysis': f'Front knee at FFC: {ffc_value:.1f}°, at release: {release_value:.1f}°',
        'screenshots': _build_screenshots(front_leg_brace, events, side_exists)
    }


def _load_events(path: Path) -> dict:
    """Load events JSON."""
    if not path.exists():
        return {}
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if 'video' in data and 'events' in data['video']:
        return data['video']['events']
    elif 'events' in data:
        return data['events']
    return data


def _build_screenshots(metric_data: dict, events: dict, side_exists: bool) -> List[dict]:
    """Build screenshot specs for this metric."""
    screenshots = []
    
    if not side_exists:
        return screenshots
    
    # FFC screenshot
    ffc_data = metric_data.get('front_knee_angle_at_ffc', {})
    ffc_frames = ffc_data.get('value', {}).get('frames', [])
    ffc_angle = ffc_data.get('value', {}).get('angle')
    
    if ffc_frames and ffc_frames[0] != -1:
        screenshots.append({
            'view': 'side',
            'frames': [ffc_frames[0]],
            'blended': False,
            'types': ['original', 'skeleton', 'overlay'],
            'angles': ['front_knee'],
            'angle_value': ffc_angle,
            'crop_strategy': 'front_leg_focus',
            'output_name': 'metric_front_leg_brace_ffc'
        })
    
    # Release screenshot
    release_data = metric_data.get('front_knee_angle_at_release', {})
    release_frames = release_data.get('value', {}).get('frames', [])
    release_angle = release_data.get('value', {}).get('angle')
    
    if release_frames and release_frames[0] != -1:
        screenshots.append({
            'view': 'side',
            'frames': [release_frames[0]],
            'blended': False,
            'types': ['original', 'skeleton', 'overlay'],
            'angles': ['front_knee'],
            'angle_value': release_angle,
            'crop_strategy': 'front_leg_focus',
            'output_name': 'metric_front_leg_brace_release'
        })
    
    return screenshots
