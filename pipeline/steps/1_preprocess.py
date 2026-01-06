"""
Step 1: Preprocess Videos

This step preprocesses the input videos:
1. Trims videos to 2 seconds before jump and 2 seconds after release
2. Updates event frame numbers relative to the trimmed clips
3. Flips videos horizontally if bowler is left-handed
4. Saves preprocessed videos and updated events to b_clips/

The module follows the same structure as Step 0 with a top-level function
that calls helper functions.
"""

import json
import os
import cv2
from pathlib import Path
from typing import Callable, Optional


def preprocess(session_dir: str, log: Optional[Callable[[str, int, str], None]] = None) -> dict:
    """
    Main preprocessing function.
    
    Args:
        session_dir: Path to the session directory (e.g., 'data/run/')
        log: Optional logging callback with signature (message, level, type)
             level: 0 = major step, 1 = sub-step, 2 = detail
             type: 'info', 'success', 'warning', 'error'
    
    Returns:
        dict with keys:
            - success: boolean indicating if step completed successfully
            - processed_views: list of views that were processed
    """
    # Default no-op logger if none provided
    if log is None:
        log = lambda msg, level=1, type='info': None
    
    log("> Step 1: Preprocess videos", 0, 'info')
    
    inputs_dir = Path(session_dir) / 'a_inputs'
    outputs_dir = Path(session_dir) / 'b_clips'
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    result = {
        'success': False,
        'processed_views': []
    }
    
    # Load metadata to check which views exist and get bowler hand
    metadata_path = inputs_dir / 'metadata.json'
    if not metadata_path.exists():
        log("✖ metadata.json not found", 1, 'error')
        return result
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # Check bowler hand and determine if flipping is needed
    bowler_hand = metadata.get('bowler', {}).get('hand', 'Right')
    flip = bowler_hand.lower() == 'left'
    
    if flip:
        log(f"- Bowler is left-handed, will flip videos horizontally", 1, 'info')
    else:
        log(f"- Bowler is right-handed, no flipping needed", 1, 'info')
    
    # Process each view
    views_to_process = [
        ('back', 'backView'),
        ('side', 'sideView')
    ]
    
    for view_name, metadata_key in views_to_process:
        inputs_config = metadata.get('inputs', {})
        view_config = inputs_config.get(metadata_key, {})
        
        if not view_config.get('provided', False):
            log(f"- {view_name.capitalize()} view not provided, skipping", 1, 'info')
            continue
        
        # Paths
        video_input = inputs_dir / f'input_{view_name}_view.mp4'
        events_input = inputs_dir / f'input_{view_name}_events.json'
        video_output = outputs_dir / f'{view_name}_view.mp4'
        events_output = outputs_dir / f'{view_name}_view_events.json'
        
        log(f"- Processing {view_name} view...", 1, 'info')
        
        # Trim and process
        success = _trim_and_process_video(
            str(video_input),
            str(events_input),
            str(video_output),
            str(events_output),
            flip,
            log
        )
        
        if success:
            result['processed_views'].append(view_name)
            log(f"  ✓ {view_name.capitalize()} view preprocessed", 2, 'success')
        else:
            log(f"  ✖ Failed to preprocess {view_name} view", 2, 'error')
    
    result['success'] = len(result['processed_views']) > 0
    
    if result['success']:
        log("✓ Preprocessing complete", 1, 'success')
        log(f"- Processed {len(result['processed_views'])} view(s)", 1, 'info')
    else:
        log("✖ Preprocessing failed", 1, 'error')
    
    return result


def _trim_and_process_video(
    video_path: str,
    events_path: str,
    output_video_path: str,
    output_events_path: str,
    flip_horizontal: bool,
    log: Callable
) -> bool:
    """Trim a video based on tagged events and optionally flip it."""
    cap = None
    writer = None
    try:
        # Check files exist
        if not os.path.exists(video_path):
            log(f"    Video not found: {video_path}", 3, 'error')
            return False
        
        if not os.path.exists(events_path):
            log(f"    Events file not found: {events_path}", 3, 'error')
            return False
        
        # Load events (support multiple event JSON formats)
        with open(events_path, 'r', encoding='utf-8') as f:
            events_json = json.load(f)

        # Normalize events dict: support {"events": {...}}, {"video": {"events": {...}}},
        # or top-level mapping of event names.
        events_map = {}
        if isinstance(events_json, dict):
            if 'events' in events_json and isinstance(events_json['events'], dict):
                events_map = {k: v for k, v in events_json['events'].items()}
            elif 'video' in events_json and isinstance(events_json['video'], dict) and 'events' in events_json['video']:
                events_map = {k: v for k, v in events_json['video']['events'].items()}
            else:
                # assume top-level mapping of events
                events_map = {k: v for k, v in events_json.items()}

        def _get_frame_for(name: str):
            # Try exact key, lowercase, title-case
            if name in events_map:
                return events_map[name]
            if name.lower() in events_map:
                return events_map[name.lower()]
            if name.title() in events_map:
                return events_map[name.title()]
            return None

        # Get event frames (coerce to ints when possible)
        jump_frame = _get_frame_for('Jump')
        release_frame = _get_frame_for('Release')
        try:
            jump_frame = int(jump_frame) if jump_frame is not None else None
        except Exception:
            jump_frame = None
        try:
            release_frame = int(release_frame) if release_frame is not None else None
        except Exception:
            release_frame = None

        if jump_frame is None or release_frame is None:
            log("    Missing Jump or Release event", 3, 'error')
            return False
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            log("    Could not open video", 3, 'error')
            return False
        
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Calculate trim window: 2 seconds before jump, 2 seconds after release
        frames_before = int(2.0 * fps)
        frames_after = int(2.0 * fps)
        
        start_frame = max(0, jump_frame - frames_before)
        end_frame = min(total_frames - 1, release_frame + frames_after)
        
        log(f"    Trimming frames {start_frame}-{end_frame} (2s before jump to 2s after release)", 3, 'info')
        
        # Create output writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_video_path, fourcc, float(fps), (width, height))
        if not writer.isOpened():
            log("    Could not create output writer", 3, 'error')
            return False
        
        # Process frames
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        frames_written = 0
        
        for fidx in range(start_frame, end_frame + 1):
            ret, frame = cap.read()
            if not ret:
                break
            
            # Ensure frame size matches
            if frame.shape[1] != width or frame.shape[0] != height:
                frame = cv2.resize(frame, (width, height))
            
            # Flip horizontally if needed
            if flip_horizontal:
                frame = cv2.flip(frame, 1)
            
            writer.write(frame)
            frames_written += 1
        
        log(f"    Wrote {frames_written} frames", 3, 'info')
        
        # Update events JSON with adjusted frame numbers
        adjusted_events = {}
        for event_name in ['Jump', 'BFC', 'FFC', 'Release']:
            val = _get_frame_for(event_name)
            if val is not None:
                try:
                    original_frame = int(val)
                except Exception:
                    continue
                adjusted_frame = max(0, original_frame - start_frame)
                adjusted_events[event_name] = adjusted_frame
        
        # Write updated events
        with open(output_events_path, 'w', encoding='utf-8') as f:
            json.dump(adjusted_events, f, indent=2)
        
        return True
        
    except Exception as e:
        log(f"    Exception: {e}", 3, 'error')
        return False
        
    finally:
        if writer is not None:
            try:
                writer.release()
            except Exception:
                pass
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass


# Below would be other helper functions as needed for the preprocessing step