'''--------------------------------------------------------------
Front Leg Brace Metric

This metric measures the front knee angle at key events (FFC and release)
to evaluate the quality of the front leg brace in the bowling action.

The metric calculates:
- Front knee angle at FFC (Front Foot Contact)
- Front knee angle at release
- Difference between FFC and release angles
- Maximum flex from FFC (maximum difference point)
- Maximum difference between FFC and max flex

Data sources:
- Side view angles CSV (for front_knee_angle column)
- Side view events JSON (for FFC and release frame numbers)

Output structure:
{
    "front_leg_brace": {
        "front_knee_angle_at_ffc": {"angle": float, "frames": [int]},
        "front_knee_angle_at_release": {"angle": float, "frames": [int]},
        "difference_ffc_release": {"angle": float, "frames": [int, int]},
        "max_flex_from_ffc": {"angle": float, "frames": [int]},
        "max_difference_ffc_flex": {"angle": float, "frames": [int, int]}
    }
}

Sentinel values:
- angle = -1.0: Data not available (landmarks not visible)
- frames = [-1]: Event not found
--------------------------------------------------------------'''

import os
import json
import csv
from typing import Dict, Any, List
from pipeline import location_constants as lc


def extract_front_leg_brace(session_dir: str) -> Dict[str, Any]:
    """Extract front leg brace metrics from angles and events.
    
    Args:
        session_dir: Path to the session directory
        
    Returns:
        Dict with front_leg_brace metrics structure
    """
    # Build file paths
    angles_path = session_dir + lc.side_view_angles
    events_path = session_dir + lc.final_side_events
    
    # Check if files exist
    if not os.path.exists(angles_path):
        print(f"        FRONT_LEG_BRACE: Angles file not found: {angles_path}")
        return _create_unavailable_result("Angles file not found")
    
    if not os.path.exists(events_path):
        print(f"        FRONT_LEG_BRACE: Events file not found: {events_path}")
        return _create_unavailable_result("Events file not found")
    
    # Load data
    angles_by_frame = _read_angles_csv(angles_path)
    events = _read_events_json(events_path)
    
    if not angles_by_frame:
        print(f"        FRONT_LEG_BRACE: No angle data found")
        return _create_unavailable_result("No angle data")
    
    if not events:
        print(f"        FRONT_LEG_BRACE: No events data found")
        return _create_unavailable_result("No events data")
    
    # Calculate metrics
    print(f"        FRONT_LEG_BRACE: Calculating metrics...")
    result = _calculate_metrics(angles_by_frame, events)
    
    print(f"        FRONT_LEG_BRACE: Metrics calculated successfully")
    return result


def _read_angles_csv(path: str) -> Dict[int, float]:
    """Read angles CSV and return frame → front_knee_angle mapping."""
    angles = {}
    try:
        with open(path, 'r', encoding='utf-8', newline='') as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            if not header:
                return {}
            
            # Find front_knee_angle column
            try:
                angle_idx = header.index('front_knee_angle')
            except ValueError:
                # Fallback to second column if available
                angle_idx = 1 if len(header) > 1 else None
            
            if angle_idx is None:
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


def _calculate_metrics(angles_by_frame: Dict[int, float], events: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate front leg brace metrics from angles and events."""
    
    SENTINEL = -1.0
    
    # Helper to get angle at a frame
    def _angle_at(frame: int) -> float:
        if frame is None:
            return None
        try:
            val = angles_by_frame.get(int(frame))
            if val is None:
                return None
            # Treat sentinel (-1.0) as not available
            if isinstance(val, (int, float)) and float(val) <= -1.0:
                return None
            return float(val)
        except Exception:
            return None
    
    # Get event frames
    ffc_ev = events.get('ffc')
    release_ev = events.get('release')
    
    try:
        ffc_frame = int(ffc_ev.get('frame')) if ffc_ev and 'frame' in ffc_ev else None
    except Exception:
        ffc_frame = None
    
    try:
        release_frame = int(release_ev.get('frame')) if release_ev and 'frame' in release_ev else None
    except Exception:
        release_frame = None
    
    # Get angles at key events
    ffc_angle = _angle_at(ffc_frame) if ffc_frame is not None else None
    release_angle = _angle_at(release_frame) if release_frame is not None else None
    
    # Calculate simple metrics
    ffc_val = float(ffc_angle) if ffc_angle is not None else SENTINEL
    release_val = float(release_angle) if release_angle is not None else SENTINEL
    
    if ffc_angle is not None and release_angle is not None:
        diff_val = float(release_angle - ffc_angle)
    else:
        diff_val = SENTINEL
    
    # Calculate max difference from FFC within interval [FFC, release]
    max_diff = -1.0
    max_diff_frame = -1
    max_diff_knee_angle = SENTINEL
    
    if ffc_frame is not None and release_frame is not None and ffc_angle is not None:
        start = min(ffc_frame, release_frame)
        end = max(ffc_frame, release_frame)
        
        for fr in range(start, end + 1):
            a = _angle_at(fr)
            if a is None:
                continue
            d = abs(a - ffc_angle)
            if d > max_diff:
                max_diff = d
                max_diff_frame = fr
                max_diff_knee_angle = a
    
    if max_diff_frame == -1:
        max_diff_val = SENTINEL
        max_diff_frame_val = -1
        max_diff_knee_val = SENTINEL
    else:
        max_diff_val = float(max_diff)
        max_diff_frame_val = int(max_diff_frame)
        max_diff_knee_val = float(max_diff_knee_angle)
    
    # Build result structure with frames as lists
    def _wrap(angle_val, frame_vals):
        """Wrap angle and frames into standard structure.
        
        Args:
            angle_val: The angle value
            frame_vals: Single frame int or list of frame ints
        """
        # Ensure frames is always a list
        if isinstance(frame_vals, list):
            frames = frame_vals
        else:
            frames = [frame_vals] if frame_vals is not None else [-1]
        
        return {
            "angle": (angle_val if angle_val is not None else SENTINEL),
            "frames": frames
        }
    
    ffc_frame_out = ffc_frame if ffc_frame is not None else -1
    release_frame_out = release_frame if release_frame is not None else -1
    max_flex_frame_out = max_diff_frame_val if max_diff_frame_val != -1 else -1
    
    # Build frames lists for difference_ffc_release (both FFC and release)
    diff_frames = [ffc_frame_out, release_frame_out] if ffc_frame_out != -1 and release_frame_out != -1 else [-1]
    
    # Build frames lists for max_difference_ffc_flex (FFC and max flex)
    max_diff_frames = [ffc_frame_out, max_flex_frame_out] if ffc_frame_out != -1 and max_flex_frame_out != -1 else [-1]
    
    return {
        "front_leg_brace": {
            "front_knee_angle_at_ffc": _wrap(ffc_val, ffc_frame_out),
            "front_knee_angle_at_release": _wrap(release_val, release_frame_out),
            "difference_ffc_release": _wrap(diff_val, diff_frames),
            "max_flex_from_ffc": _wrap(max_diff_knee_val, max_flex_frame_out),
            "max_difference_ffc_flex": _wrap(max_diff_val, max_diff_frames)
        }
    }


def _create_unavailable_result(reason: str) -> Dict[str, Any]:
    """Create a result structure when data is unavailable."""
    return {
        "front_leg_brace": {
            "error": reason,
            "front_knee_angle_at_ffc": {"angle": -1.0, "frames": [-1]},
            "front_knee_angle_at_release": {"angle": -1.0, "frames": [-1]},
            "difference_ffc_release": {"angle": -1.0, "frames": [-1]},
            "max_flex_from_ffc": {"angle": -1.0, "frames": [-1]},
            "max_difference_ffc_flex": {"angle": -1.0, "frames": [-1]}
        }
    }