'''--------------------------------------------------------------
This file contains the business logic to trim and optionally flip videos.

This module trims videos based on tagged events:
- Trims from 2 seconds before jump to 2 seconds after release
- Optionally flips the video horizontally for left-handed bowlers
- Updates the events JSON file with adjusted frame numbers and timestamps

Inputs:
- video_location: The location of the input video
- events_location: The location of the JSON file containing the tagged events
- output_video_location: The location to save the trimmed video
- output_events_location: The location to save the updated event JSON file
- flip_horizontal: Whether to flip the video horizontally

Outputs:
- The trimmed (and possibly flipped) video saved at output_video_location
- The updated event JSON file saved at output_events_location
--------------------------------------------------------------'''

#Imports
import os
import json
import cv2
import numpy as np
from typing import Optional


def trim_and_process_video(
    video_path: str,
    events_path: str,
    output_video_path: str,
    output_events_path: str,
    flip_horizontal: bool = False
) -> None:
    """Trim a video based on tagged events and optionally flip it.
    
    Args:
        video_path: Path to the input video file
        events_path: Path to the events JSON file
        output_video_path: Path where the trimmed video should be saved
        output_events_path: Path where the updated events JSON should be saved
        flip_horizontal: Whether to flip the video horizontally
    """
    #Check if the video exists
    if not os.path.exists(video_path):
        print(f"        TRIM_VIDEO: Video does not exist: {video_path}")
        return
    
    if not os.path.exists(events_path):
        print(f"        TRIM_VIDEO: Events file does not exist: {events_path}")
        return
    
    print(f"        TRIM_VIDEO: Processing video (flip={flip_horizontal})")
    
    try:
        success = _trim_video_impl(
            video_path,
            events_path,
            output_video_path,
            output_events_path,
            flip_horizontal
        )
        
        if success:
            print(f"        TRIM_VIDEO: Successfully processed video")
        else:
            print(f"        TRIM_VIDEO: Failed to process video")
    except Exception as e:
        print(f"        TRIM_VIDEO: Error processing video: {e}")


def _trim_video_impl(
    video_location: str,
    events_location: str,
    output_video_location: str,
    output_events_location: str,
    flip_horizontal: bool
) -> bool:
    """Performs the actual trim operation. Returns True on success, False otherwise."""
    cap = None
    writer = None
    try:
        # Load events
        with open(events_location, 'r', encoding='utf-8') as f:
            data = json.load(f)

        video_meta = data.get('video', {})
        events = video_meta.get('events', {})

        # Need at least jump and release
        jump = events.get('jump')
        release = events.get('release')
        if jump is None or release is None:
            print("        TRIM_VIDEO: Missing jump or release event")
            return False

        # Open video and read properties
        cap = cv2.VideoCapture(video_location)
        if not cap.isOpened():
            print("        TRIM_VIDEO: Could not open video")
            return False

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        duration = total_frames / fps if fps > 0 else 0.0

        # Event times (prefer 'time' field, fallback to frame/fps)
        def _event_time(ev: dict) -> Optional[float]:
            if ev is None:
                return None
            if 'time' in ev and ev['time'] is not None:
                return float(ev['time'])
            if 'frame' in ev and ev['frame'] is not None:
                try:
                    return float(ev['frame']) / max(1.0, fps)
                except Exception:
                    return None
            return None

        jump_time = _event_time(jump)
        release_time = _event_time(release)
        if jump_time is None or release_time is None:
            print("        TRIM_VIDEO: Could not determine event times")
            return False

        # Compute trim window: 2 seconds before jump, 2 seconds after release
        start_time = max(0.0, jump_time - 2.0)
        end_time = min(duration, release_time + 2.0)
        if end_time <= start_time:
            print("        TRIM_VIDEO: Invalid trim window")
            return False

        start_frame = max(0, int(round(start_time * fps)))
        end_frame = min(total_frames - 1, int(round(end_time * fps)))

        print(f"        TRIM_VIDEO: Trimming from {start_time:.2f}s to {end_time:.2f}s (frames {start_frame}-{end_frame})")

        # Prepare output writer
        out_dir = os.path.dirname(output_video_location)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_video_location, fourcc, float(fps), (width, height))
        if not writer.isOpened():
            print("        TRIM_VIDEO: Could not create output video writer")
            return False

        # Seek and copy frames
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

        print(f"        TRIM_VIDEO: Wrote {frames_written} frames")

        # Build updated events json relative to trimmed video
        new_events = {}
        for k in ('jump', 'bfc', 'ffc', 'release'):
            ev = events.get(k)
            if ev is None:
                continue
            # Compute original time/frame
            orig_time = _event_time(ev)
            orig_frame = int(ev.get('frame')) if ev.get('frame') is not None else int(round(orig_time * fps))
            # Adjusted
            adj_time = max(0.0, orig_time - start_time)
            adj_frame = max(0, orig_frame - start_frame)
            new_events[k] = {'frame': int(adj_frame), 'time': float(adj_time)}

        out = {
            'video': {
                'view': video_meta.get('view', 'unknown'),
                'file_location': output_video_location,
                'events': new_events,
            }
        }

        # Ensure dir exists and write updated events
        out_dir2 = os.path.dirname(output_events_location)
        if out_dir2 and not os.path.exists(out_dir2):
            os.makedirs(out_dir2, exist_ok=True)
        
        with open(output_events_location, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=4)

        return True

    except Exception as e:
        print(f"        TRIM_VIDEO: Exception during processing: {e}")
        return False

    finally:
        # Always attempt to release the capture and writer
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
