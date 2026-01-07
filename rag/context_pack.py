"""
Context Pack Builder
Extracts a compact context pack from the report JSON for LLM grounding.
"""

import json
from pathlib import Path
from typing import Optional


def build_context_pack(report_data: dict) -> dict:
    """
    Build a compact context pack from report JSON.
    Only includes essential fields for LLM grounding.
    
    Args:
        report_data: The full report JSON data
        
    Returns:
        A compact context pack dictionary
    """
    header = report_data.get('header', {})
    
    # Bowler info
    bowler_raw = header.get('bowler', {})
    bowler = {
        'name': bowler_raw.get('name', 'Unknown'),
        'hand': bowler_raw.get('hand', 'Unknown'),
        'description': bowler_raw.get('description', '')
    }
    
    # Session info
    session_raw = header.get('session', {})
    session = {
        'name': session_raw.get('name', 'Unknown Session'),
        'date': session_raw.get('date', ''),
        'description': session_raw.get('description', '')
    }
    
    # Video summary (existence flags)
    video_summary_raw = header.get('video_summary', {})
    video_summary = {
        'back_exists': video_summary_raw.get('back_view', {}).get('exists', False),
        'side_exists': video_summary_raw.get('side_view', {}).get('exists', False)
    }
    if video_summary['back_exists']:
        video_summary['back_events'] = video_summary_raw.get('back_view', {}).get('events', {})
    if video_summary['side_exists']:
        video_summary['side_events'] = video_summary_raw.get('side_view', {}).get('events', {})
    
    # Overall score
    score_summary = header.get('score_summary', {})
    overall = {
        'overall_score': score_summary.get('overall_score', 0),
        'grade': score_summary.get('grade', 'N/A')
    }
    
    # Metrics
    metrics = []
    for m in report_data.get('metrics', []):
        metric = {
            'id': m.get('id', ''),
            'name': m.get('name', '')
        }
        # Add optional fields if present
        if m.get('score') is not None:
            metric['score'] = m['score']
        if m.get('rating'):
            metric['rating'] = m['rating']
        if m.get('value') is not None:
            metric['value'] = round(m['value'], 2) if isinstance(m['value'], float) else m['value']
        if m.get('unit'):
            metric['unit'] = m['unit']
        if m.get('description'):
            metric['description'] = m['description']
        if m.get('analysis'):
            metric['analysis'] = m['analysis']
        if m.get('extra_data'):
            metric['extra_data'] = m['extra_data']
        metrics.append(metric)
    
    # Classifications
    classifications = []
    for c in report_data.get('classifications', []):
        classification = {
            'id': c.get('id', ''),
            'name': c.get('name', '')
        }
        if c.get('rating'):
            classification['rating'] = c['rating']
        if c.get('value') is not None:
            classification['value'] = round(c['value'], 2) if isinstance(c['value'], float) else c['value']
        if c.get('unit'):
            classification['unit'] = c['unit']
        if c.get('description'):
            classification['description'] = c['description']
        if c.get('analysis'):
            classification['analysis'] = c['analysis']
        if c.get('extra_data'):
            classification['extra_data'] = c['extra_data']
        classifications.append(classification)
    
    return {
        'bowler': bowler,
        'session': session,
        'video_summary': video_summary,
        'overall': overall,
        'metrics': metrics,
        'classifications': classifications
    }


def load_report(session_dir: str = 'data/run') -> Optional[dict]:
    """
    Load report JSON from the current run directory.
    
    Args:
        session_dir: Path to the session directory
        
    Returns:
        Report data dict or None if not found
    """
    report_path = Path(session_dir) / 'results' / 'results.json'
    if not report_path.exists():
        return None
    
    with open(report_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_context_pack(session_dir: str = 'data/run') -> Optional[dict]:
    """
    Load report and build context pack in one call.
    
    Args:
        session_dir: Path to the session directory
        
    Returns:
        Context pack dict or None if report not found
    """
    report = load_report(session_dir)
    if report is None:
        return None
    return build_context_pack(report)
