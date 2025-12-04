'''--------------------------------------------------------------
Hip vs Knee Dominance Metric

This metric analyzes whether a bowler is hip dominant or knee dominant
based on their back knee angle at BFC (Back Foot Contact).

The metric extracts:
- Back knee angle at BFC from back view
- Back knee angle at BFC from side view

Classification (done in Step 6 analysis):
- If either angle < 150°: knee dominant
- Otherwise: hip dominant

Data sources:
- Back view angles CSV (for back_knee_angle column)
- Side view angles CSV (for back_knee_angle column)
- Back view events JSON (for BFC frame number)
- Side view events JSON (for BFC frame number)

Output structure:
{
    "hip_vs_knee_dominance": {
        "back_knee_angle_back_view": {"angle": float, "frames": [int]},
        "back_knee_angle_side_view": {"angle": float, "frames": [int]}
    }
}

Sentinel values:
- angle = -1.0: Data not available (landmarks not visible)
- frames = [-1]: Event not found
--------------------------------------------------------------'''

import os
import json
import csv
from typing import Dict, Any
from pipeline import location_constants as lc


def extract_hip_vs_knee_dominance(session_dir: str) -> Dict[str, Any]:
    """Extract hip vs knee dominance metrics from angles and events.
    
    Args:
        session_dir: Path to the session directory
        
    Returns:
        Dict with hip_vs_knee_dominance metrics structure
    """
    # Build file paths
    back_angles_path = session_dir + lc.back_view_angles
    side_angles_path = session_dir + lc.side_view_angles
    back_events_path = session_dir + lc.final_back_events
    side_events_path = session_dir + lc.final_side_events
    
    # Load data
    back_angles = _read_angles_csv(back_angles_path)
    side_angles = _read_angles_csv(side_angles_path)
    back_events = _read_events_json(back_events_path)
    side_events = _read_events_json(side_events_path)
    
    # Get BFC frame from back view events
    back_bfc_frame = _get_event_frame(back_events, 'bfc')
    # Get BFC frame from side view events
    side_bfc_frame = _get_event_frame(side_events, 'bfc')
    
    SENTINEL = -1.0
    
    # Extract back knee angle at BFC from back view
    back_view_angle = SENTINEL
    back_view_frame = -1
    if back_bfc_frame is not None and back_bfc_frame in back_angles:
        angle_val = back_angles[back_bfc_frame]
        # Check if angle is valid (not sentinel)
        if angle_val > -1.0:
            back_view_angle = float(angle_val)
            back_view_frame = int(back_bfc_frame)
    
    # Extract back knee angle at BFC from side view
    side_view_angle = SENTINEL
    side_view_frame = -1
    if side_bfc_frame is not None and side_bfc_frame in side_angles:
        angle_val = side_angles[side_bfc_frame]
        # Check if angle is valid (not sentinel)
        if angle_val > -1.0:
            side_view_angle = float(angle_val)
            side_view_frame = int(side_bfc_frame)
    
    print(f"        HIP_VS_KNEE: Back view angle at BFC: {back_view_angle}°")
    print(f"        HIP_VS_KNEE: Side view angle at BFC: {side_view_angle}°")
    
    return {
        "hip_vs_knee_dominance": {
            "back_knee_angle_back_view": {
                "angle": back_view_angle,
                "frames": [back_view_frame]
            },
            "back_knee_angle_side_view": {
                "angle": side_view_angle, 
                "frames": [side_view_frame]
            }
        }
    }


def _read_angles_csv(path: str) -> Dict[int, float]:
    """Read angles CSV and return frame → back_knee_angle mapping."""
    angles = {}
    
    if not os.path.exists(path):
        return {}
    
    try:
        with open(path, 'r', encoding='utf-8', newline='') as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            if not header:
                return {}
            
            # Find back_knee_angle column
            try:
                angle_idx = header.index('back_knee_angle')
            except ValueError:
                # Column doesn't exist yet
                return {}
            
            for row in reader:
                if not row:
                    continue
                try:
                    frame = int(float(row[0]))
                    angle = float(row[angle_idx])
                    angles[frame] = angle
                except Exception:
                    continue
        
        return angles
    except Exception:
        return {}


def _read_events_json(path: str) -> Dict[str, Any]:
    """Read events JSON and return events mapping."""
    if not os.path.exists(path):
        return {}
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Extract events from nested structure
            if isinstance(data, dict) and 'video' in data:
                return data.get('video', {}).get('events', {})
            if isinstance(data, dict) and 'events' in data:
                return data.get('events', {})
            return data
    except Exception:
        return {}


def _get_event_frame(events: Dict[str, Any], event_name: str) -> int:
    """Get frame number for a specific event."""
    if not events:
        return None
        
    event = events.get(event_name)
    if not event:
        return None
        
    try:
        if isinstance(event, dict) and 'frame' in event:
            return int(event['frame'])
        elif isinstance(event, (int, float)):
            return int(event)
    except Exception:
        pass
        
    return None
