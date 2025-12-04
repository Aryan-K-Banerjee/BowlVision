#core/cv/vidgen/pause_at_events.py
'''--------------------------------------------------------------------------
This module contains functions to generate videos that pause at events for 2 seconds.
-------------------------------------------------------------------------'''

import os
import json
import cv2


def generate_pause_at_events(input_video_location: str, events_location: str, output_video_location: str):
    """
    Codes:
        "VIDEO_GENERATED"
        "NO_VIDEO"
        "INVALID_EVENTS"
        "ERROR"
    """

    PAUSE_SECONDS = 2.0

    try:
        if not os.path.exists(input_video_location):
            print("Input video not found")
            return "NO_VIDEO"

        # try to read events JSON; if missing, treat as no events (just copy video)
        events = {}
        if events_location and os.path.exists(events_location):
            try:
                with open(events_location, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                events = data.get('video', {}).get('events', {}) or {}
            except Exception as e:
                print(f"Failed to read events JSON: {e}")
                return "INVALID_EVENTS"

        cap = cv2.VideoCapture(input_video_location)
        if not cap.isOpened():
            print("Failed to open input video")
            return "NO_VIDEO"

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

        # determine event frames (prefer frame, fallback to time)
        event_frames = set()
        for k, ev in events.items():
            if not isinstance(ev, dict):
                continue
            if 'frame' in ev and ev.get('frame') is not None:
                try:
                    fidx = int(ev.get('frame'))
                    if 0 <= fidx < total_frames:
                        event_frames.add(fidx)
                except Exception:
                    continue
            elif 'time' in ev and ev.get('time') is not None:
                try:
                    t = float(ev.get('time'))
                    fidx = int(round(t * fps))
                    if 0 <= fidx < total_frames:
                        event_frames.add(fidx)
                except Exception:
                    continue

        # prepare writer
        out_dir = os.path.dirname(output_video_location)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_video_location, fourcc, float(fps), (width, height))
        if not writer.isOpened():
            print("Failed to open VideoWriter for output")
            cap.release()
            return "ERROR"

        pause_frames = max(1, int(round(PAUSE_SECONDS * fps)))

        frame_idx = 0
        while frame_idx < total_frames:
            ret, frame = cap.read()
            if not ret:
                break
            # ensure correct size
            if frame.shape[1] != width or frame.shape[0] != height:
                frame = cv2.resize(frame, (width, height))

            writer.write(frame)

            if frame_idx in event_frames:
                # write pause frames (repeat current frame)
                for _ in range(pause_frames):
                    writer.write(frame)

            frame_idx += 1

        writer.release()
        cap.release()

        print(f"Generated paused video saved to: {output_video_location}")
        return "VIDEO_GENERATED"

    except Exception as e:
        print(f"Error generating paused video: {e}")
        try:
            cap.release()
        except Exception:
            pass
        return "ERROR"
