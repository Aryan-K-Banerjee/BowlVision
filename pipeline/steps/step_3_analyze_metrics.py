"""
Step 3: Analyze Metrics

Runs all metrics and classifications on the extracted keypoints,
then generates results.json with:
- Header (bowler info, session info, video summary)
- Classifications
- Metrics with scores
- Score summary
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

from pipeline.metrics import ALL_METRICS


# Metric weights for overall scoring
METRIC_WEIGHTS = {
    'front_leg_brace': 1.5,       # High importance
    'back_foot_stiffness': 1.0,
    'lateral_flexion': 1.2,
    'bowling_arm_delay': 1.3,
    'non_bowling_arm_extension': 1.0,
}


def run_step_3_analyze_metrics(session_dir: str, generator=None):
    """Run all metrics and generate results.json.
    
    Args:
        session_dir: Path to session directory
        generator: Optional SSE generator for progress updates
        
    Returns:
        Path to generated results.json
    """
    session_dir = Path(session_dir)
    results_dir = session_dir / 'results'
    results_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"  Step 3: Analyzing metrics...")
    
    # Load metadata
    metadata = _load_metadata(session_dir)
    
    # Load events for video summary
    side_events = _load_events(session_dir, 'side')
    back_events = _load_events(session_dir, 'back')
    
    # Run all metrics
    classifications = []
    metrics = []
    all_screenshots = []
    
    for i, metric_class in enumerate(ALL_METRICS, 1):
        metric_name = metric_class.name
        print(f"    Running {metric_name} ({i}/{len(ALL_METRICS)})...")
        
        try:
            # Create metric instance
            metric = metric_class(str(session_dir))
            
            # Run extraction -> analysis -> screenshots
            success = metric.run()
            
            if success:
                # Get metric result
                result = metric.to_dict()
                
                # Categorize by group
                if metric.group == "Classification":
                    classifications.append(result)
                else:
                    metrics.append(result)
                
                # Collect screenshots
                all_screenshots.extend(result.get('screenshots', []))
                
                print(f"      ✓ {metric_name}: {metric.rating}")
            else:
                print(f"      ✗ {metric_name}: Failed to extract/analyze")
                
        except Exception as e:
            print(f"      ✗ {metric_name}: Error - {e}")
    
    # Score all metrics
    print(f"    Scoring metrics...")
    metrics, score_summary = _score_metrics(metrics)
    
    # Build video summary with screenshots
    video_summary = _build_video_summary(session_dir, side_events, back_events)
    all_screenshots.extend(video_summary.get('screenshots', []))
    
    # Build header
    header = _build_header(metadata, video_summary, score_summary)
    
    # Build results structure
    results = {
        "header": header,
        "classifications": classifications,
        "metrics": metrics,
        "summary": _build_summary(classifications, metrics, score_summary)
    }
    
    # Save results.json
    results_path = results_dir / 'results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"  Step 3: Generated results.json with {len(classifications)} classifications and {len(metrics)} metrics")
    print(f"  Step 3: Overall score: {score_summary.get('overall_score', 'N/A')}")
    print(f"  Step 3: Total screenshots to generate: {len(all_screenshots)}")
    
    return str(results_path)


def _load_metadata(session_dir: Path) -> Dict:
    """Load metadata from a_inputs."""
    metadata_path = session_dir / 'a_inputs' / 'metadata.json'
    
    if not metadata_path.exists():
        return {}
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _load_events(session_dir: Path, view: str) -> Dict:
    """Load events JSON for a view."""
    events_path = session_dir / 'b_clips' / f'{view}_view_events.json'
    
    if not events_path.exists():
        return {}
    
    try:
        with open(events_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _build_header(metadata: Dict, video_summary: Dict, score_summary: Dict) -> Dict:
    """Build header section from metadata."""
    # Extract bowler info
    bowler = metadata.get('bowler', {})
    session = metadata.get('session', {})
    inputs = metadata.get('inputs', {})
    
    header = {
        "title": "Bowling Analysis Report",
        "created_at": metadata.get('createdAt', ''),
        
        # Bowler info
        "bowler": {
            "name": bowler.get('name', 'Unknown Bowler'),
            "hand": bowler.get('hand', 'Right'),
            "description": bowler.get('description', ''),
            "image_path": bowler.get('imagePath', '')
        },
        
        # Session info
        "session": {
            "name": session.get('name', 'Analysis Session'),
            "date": session.get('date', ''),
            "description": session.get('description', '')
        },
        
        # Video summary
        "video_summary": video_summary,
        
        # Score summary
        "score_summary": score_summary
    }
    
    return header


def _build_video_summary(session_dir: Path, side_events: Dict, back_events: Dict) -> Dict:
    """Build video summary section with event frames and screenshots."""
    clips_dir = session_dir / 'b_clips'
    
    # Check video existence
    side_exists = (clips_dir / 'side_view.mp4').exists()
    back_exists = (clips_dir / 'back_view.mp4').exists()
    
    # Standard event names
    event_names = ['Jump', 'BFC', 'FFC', 'Release']
    
    # Build video summary
    video_summary = {
        "side_view": {
            "exists": side_exists,
            "events": {}
        },
        "back_view": {
            "exists": back_exists,
            "events": {}
        },
        "screenshots": []
    }
    
    # Add side view events
    if side_exists and side_events:
        for event in event_names:
            frame = side_events.get(event)
            if frame is not None:
                video_summary["side_view"]["events"][event] = frame
                # Add screenshot spec for this event
                video_summary["screenshots"].append({
                    "view": "side",
                    "frames": [frame],
                    "blended": False,
                    "types": ["original", "skeleton", "overlay"],
                    "angles": [],
                    "crop_strategy": "square_around_bowler",
                    "output_name": f"video_summary_side_{event.lower()}"
                })
    
    # Add back view events
    if back_exists and back_events:
        for event in event_names:
            frame = back_events.get(event)
            if frame is not None:
                video_summary["back_view"]["events"][event] = frame
                # Add screenshot spec for this event
                video_summary["screenshots"].append({
                    "view": "back",
                    "frames": [frame],
                    "blended": False,
                    "types": ["original", "skeleton", "overlay"],
                    "angles": [],
                    "crop_strategy": "square_around_bowler",
                    "output_name": f"video_summary_back_{event.lower()}"
                })
    
    return video_summary


def _score_metrics(metrics: List[Dict]) -> Tuple[List[Dict], Dict]:
    """Score all metrics and calculate weighted overall score.
    
    Args:
        metrics: List of metric dicts
        
    Returns:
        Tuple of (updated metrics list, score summary dict)
    """
    scores = []
    weighted_scores = []
    total_weight = 0
    
    for metric in metrics:
        metric_id = metric.get('id', '')
        extra_data = metric.get('extra_data', {})
        
        # Get raw score from metric (already calculated by individual metrics)
        raw_score = extra_data.get('score')
        
        if raw_score is not None:
            # Get weight for this metric
            weight = METRIC_WEIGHTS.get(metric_id, 1.0)
            
            # Store score in the metric
            metric['score'] = raw_score
            
            # Track for overall calculation
            scores.append(raw_score)
            weighted_scores.append(raw_score * weight)
            total_weight += weight
    
    # Calculate overall score
    if weighted_scores and total_weight > 0:
        overall_score = sum(weighted_scores) / total_weight
    else:
        overall_score = None
    
    # Build score summary
    score_summary = {
        "overall_score": round(overall_score, 1) if overall_score is not None else None,
        "metric_scores": {},
        "metric_weights": METRIC_WEIGHTS.copy()
    }
    
    # Add individual metric scores to summary
    for metric in metrics:
        if metric.get('score') is not None:
            score_summary["metric_scores"][metric['id']] = {
                "score": metric['score'],
                "weight": METRIC_WEIGHTS.get(metric['id'], 1.0),
                "rating": metric.get('rating', 'unknown')
            }
    
    # Calculate score grade
    if overall_score is not None:
        if overall_score >= 80:
            score_summary["grade"] = "A"
        elif overall_score >= 65:
            score_summary["grade"] = "B"
        elif overall_score >= 50:
            score_summary["grade"] = "C"
        elif overall_score >= 35:
            score_summary["grade"] = "D"
        else:
            score_summary["grade"] = "F"
    
    return metrics, score_summary


def _build_summary(classifications: List[Dict], metrics: List[Dict], score_summary: Dict) -> Dict:
    """Build summary section from all results."""
    summary = {
        "total_classifications": len(classifications),
        "total_metrics": len(metrics),
        "classifications_summary": {},
        "metrics_summary": {},
        "overall_score": score_summary.get("overall_score"),
        "grade": score_summary.get("grade")
    }
    
    # Summarize classifications
    for c in classifications:
        summary["classifications_summary"][c["id"]] = c.get("rating", "unknown")
    
    # Summarize metrics
    for m in metrics:
        summary["metrics_summary"][m["id"]] = {
            "rating": m.get("rating", "unknown"),
            "score": m.get("score")
        }
    
    return summary


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        session_dir = sys.argv[1]
    else:
        session_dir = "data/run"
    
    run_step_3_analyze_metrics(session_dir)
