# core/cv/preprocess_videos.py
'''--------------------------------------------------------------------------
This module contains functions to preprocess videos, for now which will only 
trim the videos based on event tagging.
Basically, it will trim 2 seconds before and jump, and 2 seconds after the release.

Inputs:
- video_location: str : The location of the input video.
- events_location: str : The location of the JSON file containing the tagged events.
- output_video_location: str : The location to save the trimmed video.
- output_events_location: str : The location to save the updated event JSON file.

Outputs:
- The trimmed video saved at output_video_location.
- The updated event JSON file saved at output_events_location.

-------------------------------------------------------------------------'''
import os
import json
import cv2
from typing import Optional


# the main function to trim videos
def trim_video(video_name: str, video_exists: bool, video_location: str, events_location: str, output_video_location: str, output_events_location: str) -> None:
    """Wrapper for trimming a video around tagged events.

    This function prints minimal status messages and delegates the
    actual trimming work to `_trim_video_impl` which returns a bool
    indicating success. The wrapper intentionally does not return
    status codes; it prints short human-readable messages instead.
    """
    if not video_exists:
        print(f"NO {video_name}")
        return

    print(f"Trimming video: {video_name} based on events from: {events_location}")
    try:
        ok = _trim_video_impl(video_location, events_location, output_video_location, output_events_location)
        if ok:
            print(f"Trimmed successfully: {video_name}")
        else:
            print("Error trimming video")
    except Exception:
        print("Error trimming video")


def _trim_video_impl(video_location: str, events_location: str, output_video_location: str, output_events_location: str) -> bool:
    """Performs the actual trim operation. Returns True on success, False otherwise.

    This helper centralizes resource management and returns a boolean to the
    caller so the public wrapper can remain simple.
    """
    cap = None
    writer = None
    try:
        if not os.path.exists(video_location):
            return False
        if not os.path.exists(events_location):
            return False

        # load events
        with open(events_location, 'r', encoding='utf-8') as f:
            data = json.load(f)

        video_meta = data.get('video', {})
        events = video_meta.get('events', {})

        # need at least jump and release
        jump = events.get('jump')
        release = events.get('release')
        if jump is None or release is None:
            return False

        # open video and read properties
        cap = cv2.VideoCapture(video_location)
        if not cap.isOpened():
            return False

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        duration = total_frames / fps if fps > 0 else 0.0

        # event times (prefer 'time' field, fallback to frame/fps)
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
            return False

        # compute trim window
        start_time = max(0.0, jump_time - 2.0)
        end_time = min(duration, release_time + 2.0)
        if end_time <= start_time:
            return False

        start_frame = max(0, int(round(start_time * fps)))
        end_frame = min(total_frames - 1, int(round(end_time * fps)))

        # prepare output writer
        out_dir = os.path.dirname(output_video_location)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_video_location, fourcc, float(fps), (width, height))
        if not writer.isOpened():
            return False

        # seek and copy frames
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        for fidx in range(start_frame, end_frame + 1):
            ret, frame = cap.read()
            if not ret:
                break
            # frame could be different size; ensure writer frame size matches
            if frame.shape[1] != width or frame.shape[0] != height:
                frame = cv2.resize(frame, (width, height))
            writer.write(frame)

        # build updated events json relative to trimmed video
        new_events = {}
        for k in ('jump', 'bfc', 'ffc', 'release'):
            ev = events.get(k)
            if ev is None:
                continue
            # compute original time/frame
            orig_time = _event_time(ev)
            orig_frame = int(ev.get('frame')) if ev.get('frame') is not None else int(round(orig_time * fps))
            # adjusted
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

        # ensure dir exists and write updated events
        out_dir2 = os.path.dirname(output_events_location)
        if out_dir2 and not os.path.exists(out_dir2):
            os.makedirs(out_dir2, exist_ok=True)
        with open(output_events_location, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=4)

        return True

    except Exception:
        return False

    finally:
        # always attempt to release the capture and writer
        try:
            if writer is not None:
                try:
                    writer.release()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass
        except Exception:
            pass


# any helper functions can go here