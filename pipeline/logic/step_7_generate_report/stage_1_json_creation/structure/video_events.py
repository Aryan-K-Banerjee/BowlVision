"""
Video events structure builder.

Builds the video_events_classification block with event screenshots.
"""

import json
from pathlib import Path
from typing import Dict, Any, List


def build(session_dir: Path, back_exists: bool, side_exists: bool) -> Dict[str, Any]:
    """Build video events classification block.
    
    Returns:
        Block with video summary, events, and screenshot specs
    """
    # Load events from b_clips (not b_preprocessed)
    back_events = _load_events(session_dir / 'b_clips' / 'back_view_events.json') if back_exists else {}
    side_events = _load_events(session_dir / 'b_clips' / 'side_view_events.json') if side_exists else {}
    
    # Extract classification from analyzed_metrics
    analyzed_metrics = _load_json(session_dir / 'd_analysis' / 'analyzed_metrics.json')
    classification_info = _extract_classifications(analyzed_metrics)
    
    # Build section
    section = {
        'video_summary': {
            'back_exists': back_exists,
            'side_exists': side_exists
        },
        'events_by_view': {
            'back': back_events if back_exists else {},
            'side': side_events if side_exists else {}
        },
        'classification': classification_info,
        'screenshots': _build_event_screenshots(back_events, side_events, back_exists, side_exists)
    }
    
    return section


def _load_json(path: Path) -> Dict[str, Any]:
    """Load JSON file, return empty dict if not found."""
    if not path.exists():
        return {}
    
    with open(path, 'r') as f:
        return json.load(f)


def _load_events(path: Path) -> Dict[str, Any]:
    """Load events JSON."""
    if not path.exists():
        return {}
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Extract events from nested structure
    if 'video' in data and 'events' in data['video']:
        return data['video']['events']
    elif 'events' in data:
        return data['events']
    return data


def _extract_classifications(analyzed_metrics: dict) -> Dict[str, Any]:
    """Extract classification data from analyzed metrics."""
    if not analyzed_metrics or 'analyzed_metrics' not in analyzed_metrics:
        return {}
    
    metrics = analyzed_metrics['analyzed_metrics']
    classifications = {}
    
    # Hip vs knee dominance
    if 'hip_vs_knee_dominance' in metrics:
        classification = metrics['hip_vs_knee_dominance'].get('classification', {})
        classifications['hip_vs_knee_dominance'] = classification.get('value', 'unknown')
    
    # Bowler alignment
    if 'bowler_alignment' in metrics:
        classification = metrics['bowler_alignment'].get('classification', {})
        classifications['bowler_alignment'] = classification.get('value', 'unknown')
    
    return classifications


def _build_event_screenshots(back_events: dict, side_events: dict, 
                             back_exists: bool, side_exists: bool) -> List[dict]:
    """Build screenshot specs for key events."""
    screenshots = []
    
    # Key events to capture
    event_names = ['jump', 'bfc', 'ffc', 'release']
    
    # Side view events
    if side_exists and side_events:
        for event_name in event_names:
            event = side_events.get(event_name)
            if event and 'frame' in event:
                screenshots.append({
                    'view': 'side',
                    'frames': [event['frame']],
                    'blended': False,
                    'types': ['original', 'skeleton', 'overlay'],
                    'angles': ['none'],
                    'crop_strategy': 'square_around_bowler',
                    'output_name': f'event_{event_name}_side'
                })
    
    # Back view events
    if back_exists and back_events:
        for event_name in event_names:
            event = back_events.get(event_name)
            if event and 'frame' in event:
                screenshots.append({
                    'view': 'back',
                    'frames': [event['frame']],
                    'blended': False,
                    'types': ['original', 'skeleton', 'overlay'],
                    'angles': ['none'],
                    'crop_strategy': 'square_around_bowler',
                    'output_name': f'event_{event_name}_back'
                })
    
    return screenshots
