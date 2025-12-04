'''--------------------------------------------------------------
Bowler Alignment Metric

This metric classifies bowlers as front-on, semi side-on, or side-on
based on back foot orientation at BFC (Back Foot Contact).

Method:
Uses cosine projection geometry to determine foot rotation angle.
At JUMP frame, the foot points at camera (max visible length).
At BFC frame, the horizontal projection reveals rotation.

Formula: θ = arccos(L_obs / L_full)
- L_full: Full foot length at JUMP (3D distance heel to toe)
- L_obs: Horizontal projection at BFC (x-axis distance only)

Classification (done in Step 6):
- 0-20°: front_on
- 20-60°: semi_side_on
- 60+°: side_on

Data sources:
- Side view keypoints CSV (for landmark positions)
- Side view events JSON (for JUMP and BFC frame numbers)

Output structure:
{
    "bowler_alignment": {
        "back_foot_xy_angle": {"angle": float, "frames": [int]}
    }
}

Sentinel values:
- angle = -1.0: Data not available (landmarks not visible or invalid)
- frames = [-1]: Event not found
--------------------------------------------------------------'''

import os
import json
import csv
import math
from typing import Dict, Any, List, Tuple
from pipeline import location_constants as lc


def extract_bowler_alignment(session_dir: str) -> Dict[str, Any]:
    """Extract bowler alignment metric from keypoints and events.
    
    Args:
        session_dir: Path to the session directory
        
    Returns:
        Dict with bowler_alignment metrics structure
    """
    # Build file paths
    side_keypoints_path = session_dir + lc.side_view_keypoints
    side_events_path = session_dir + lc.final_side_events
    
    # Check if files exist
    if not os.path.exists(side_keypoints_path):
        print(f"        BOWLER_ALIGNMENT: Keypoints file not found: {side_keypoints_path}")
        return _create_unavailable_result("Keypoints file not found")
    
    if not os.path.exists(side_events_path):
        print(f"        BOWLER_ALIGNMENT: Events file not found: {side_events_path}")
        return _create_unavailable_result("Events file not found")
    
    # Load data
    keypoints_by_frame = _read_keypoints_csv(side_keypoints_path)
    events = _read_events_json(side_events_path)
    
    if not keypoints_by_frame:
        print(f"        BOWLER_ALIGNMENT: No keypoints data found")
        return _create_unavailable_result("No keypoints data")
    
    if not events:
        print(f"        BOWLER_ALIGNMENT: No events data found")
        return _create_unavailable_result("No events data")
    
    # Get event frames
    jump_frame = _get_event_frame(events, 'jump')
    bfc_frame = _get_event_frame(events, 'bfc')
    
    if jump_frame is None or bfc_frame is None:
        print(f"        BOWLER_ALIGNMENT: Required events not found (jump={jump_frame}, bfc={bfc_frame})")
        return _create_unavailable_result("Required events not found")
    
    # Calculate alignment angle
    print(f"        BOWLER_ALIGNMENT: Calculating foot orientation angle...")
    angle, result_frame = _calculate_foot_orientation_angle(
        keypoints_by_frame, jump_frame, bfc_frame
    )
    
    if angle < 0:
        print(f"        BOWLER_ALIGNMENT: Failed to calculate angle")
        return _create_unavailable_result("Calculation failed")
    
    print(f"        BOWLER_ALIGNMENT: Back foot angle at BFC: {angle:.1f}°")
    
    return {
        "bowler_alignment": {
            "back_foot_xy_angle": {
                "angle": float(angle),
                "frames": [int(result_frame)]
            }
        }
    }


def _calculate_foot_orientation_angle(
    keypoints_by_frame: Dict[int, List[Tuple[float, float, float, float]]],
    jump_frame: int,
    bfc_frame: int
) -> Tuple[float, int]:
    """Calculate foot orientation angle using cosine projection.
    
    Returns:
        (angle_degrees, bfc_frame) or (-1.0, -1) if calculation fails
    """
    SENTINEL = -1.0
    
    # Right foot landmarks: Heel (30), Foot Index (32)
    HEEL_IDX = 30
    TOE_IDX = 32
    
    # Get landmarks at JUMP frame
    jump_landmarks = keypoints_by_frame.get(jump_frame)
    if not jump_landmarks or len(jump_landmarks) <= max(HEEL_IDX, TOE_IDX):
        return (SENTINEL, -1)
    
    # Get landmarks at BFC frame
    bfc_landmarks = keypoints_by_frame.get(bfc_frame)
    if not bfc_landmarks or len(bfc_landmarks) <= max(HEEL_IDX, TOE_IDX):
        return (SENTINEL, -1)
    
    try:
        # Extract JUMP frame landmarks (full 3D length)
        jump_heel = jump_landmarks[HEEL_IDX]
        jump_toe = jump_landmarks[TOE_IDX]
        
        # Check visibility at JUMP
        if jump_heel[3] <= 0.2 or jump_toe[3] <= 0.2:  # visibility threshold
            return (SENTINEL, -1)
        
        # Calculate L_full (3D distance at JUMP)
        dx_full = jump_toe[0] - jump_heel[0]
        dy_full = jump_toe[1] - jump_heel[1]
        dz_full = jump_toe[2] - jump_heel[2]
        L_full = math.sqrt(dx_full**2 + dy_full**2 + dz_full**2)
        
        if L_full < 1e-6:  # Too small
            return (SENTINEL, -1)
        
        # Extract BFC frame landmarks (horizontal projection only)
        bfc_heel = bfc_landmarks[HEEL_IDX]
        bfc_toe = bfc_landmarks[TOE_IDX]
        
        # Check visibility at BFC
        if bfc_heel[3] <= 0.2 or bfc_toe[3] <= 0.2:
            return (SENTINEL, -1)
        
        # Calculate L_obs (horizontal distance only at BFC)
        L_obs = abs(bfc_toe[0] - bfc_heel[0])
        
        # Handle edge case: L_obs > L_full (measurement error)
        ratio = L_obs / L_full
        if ratio > 1.0:
            ratio = 1.0
        
        # Calculate angle: θ = arccos(L_obs / L_full)
        angle_rad = math.acos(ratio)
        angle_deg = abs(math.degrees(angle_rad))
        
        return (angle_deg, bfc_frame)
        
    except Exception as e:
        print(f"        BOWLER_ALIGNMENT: Error calculating angle: {e}")
        return (SENTINEL, -1)


def _read_keypoints_csv(path: str) -> Dict[int, List[Tuple[float, float, float, float]]]:
    """Read keypoints CSV into frame -> landmarks mapping."""
    keypoints = {}
    
    try:
        with open(path, 'r', encoding='utf-8', newline='') as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            if not header:
                return {}
            
            # Infer number of landmarks
            num_extra = max(0, len(header) - 2)
            num_landmarks = num_extra // 4 if num_extra >= 4 else 0
            
            for row in reader:
                if not row:
                    continue
                try:
                    frame = int(float(row[0]))
                except Exception:
                    continue
                
                landmarks = []
                for i in range(num_landmarks):
                    base = 2 + i * 4
                    try:
                        x = float(row[base])
                        y = float(row[base + 1])
                        z = float(row[base + 2])
                        vis = float(row[base + 3])
                    except Exception:
                        x = y = z = vis = 0.0
                    landmarks.append((x, y, z, vis))
                
                keypoints[frame] = landmarks
        
        return keypoints
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


def _create_unavailable_result(reason: str) -> Dict[str, Any]:
    """Create a result structure when data is unavailable."""
    return {
        "bowler_alignment": {
            "error": reason,
            "back_foot_xy_angle": {"angle": -1.0, "frames": [-1]}
        }
    }
