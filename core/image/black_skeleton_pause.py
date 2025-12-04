# core/image/black_skeleton_pause.py
'''--------------------------------------------------------------------------
Generate a black-background video with a green skeleton rendered from a joints
CSV. The output will pause for a short duration at tagged event frames (from
an events JSON), similar to the other generators in `core.cv.vidgen`.
-------------------------------------------------------------------------'''
import os
import json
from typing import Dict, List, Tuple

import cv2

from core.image.image_utils import read_joints_csv, get_pose_connections


def generate_black_skeleton_pause(joints_csv_location: str, events_location: str, output_video_location: str):
    """Generate a black-background video showing a green skeleton from joints CSV.

    The function will pause at event frames specified in the events JSON for 2
    seconds (duplicate the frame). The CSV format is expected to match the
    output of `extract_joints`: header `frame,time_s,lm0_x,lm0_y,lm0_z,lm0_vis,...`.

    Return codes:
        "VIDEO_GENERATED", "NO_JOINTS_CSV", "INVALID_EVENTS", "ERROR"
    """

    PAUSE_SECONDS = 2.0
    VISIBILITY_THRESHOLD = 0.2

    try:
        if not os.path.exists(joints_csv_location):
            return "NO_JOINTS_CSV"

        # read joints CSV
        frames_map, inferred_fps = read_joints_csv(joints_csv_location)
        if not frames_map:
            return "NO_JOINTS_CSV"

        max_frame = max(frames_map.keys())

        # try to read events JSON
        events = {}
        if events_location and os.path.exists(events_location):
            try:
                with open(events_location, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                events = data.get('video', {}).get('events', {}) or {}
            except Exception as e:
                print(f"Failed to read events JSON: {e}")
                return "INVALID_EVENTS"

        # Determine fps and canvas size. If the events JSON references a video
        # file, prefer its fps and size. Otherwise use inferred fps and a
        # reasonable default size.
        fps = inferred_fps or 25.0
        width, height = 640, 480

        video_file = None
        if events_location and os.path.exists(events_location):
            try:
                # re-open JSON to look for file_location
                with open(events_location, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                video_file = data.get('video', {}).get('file_location')
            except Exception:
                video_file = None

        if video_file and os.path.exists(video_file):
            try:
                cap = cv2.VideoCapture(video_file)
                if cap.isOpened():
                    v_fps = cap.get(cv2.CAP_PROP_FPS) or fps
                    if v_fps:
                        fps = float(v_fps)
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
                    if w > 0 and h > 0:
                        width, height = w, h
                cap.release()
            except Exception:
                pass

        # resolve event frames (prefer frame index, fallback to time)
        event_frames = set()
        for k, ev in events.items():
            if not isinstance(ev, dict):
                continue
            if 'frame' in ev and ev.get('frame') is not None:
                try:
                    fidx = int(ev.get('frame'))
                    if 0 <= fidx <= max_frame:
                        event_frames.add(fidx)
                except Exception:
                    continue
            elif 'time' in ev and ev.get('time') is not None:
                try:
                    t = float(ev.get('time'))
                    fidx = int(round(t * fps))
                    if 0 <= fidx <= max_frame:
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
            return "ERROR"

        pause_frames = max(1, int(round(PAUSE_SECONDS * fps)))

        # obtain pose connections (mediapipe if available, otherwise fallback)
        connections = get_pose_connections()

        # render frames from 0..max_frame
        for fi in range(0, max_frame + 1):
            # create black canvas
            import numpy as _np
            canvas = _np.zeros((height, width, 3), dtype=_np.uint8)

            lm_list = frames_map.get(fi)
            if lm_list:
                # draw connections
                for conn in connections:
                    try:
                        a, b = int(conn[0]), int(conn[1])
                    except Exception:
                        # some POSE_CONNECTIONS entries may be frozensets/tuples
                        try:
                            a, b = list(conn)
                        except Exception:
                            continue

                    if a < len(lm_list) and b < len(lm_list):
                        ax, ay, az, av = lm_list[a]
                        bx, by, bz, bv = lm_list[b]
                        if ax > 0 and ay > 0 and bx > 0 and by > 0 and av > VISIBILITY_THRESHOLD and bv > VISIBILITY_THRESHOLD:
                            pa = (int(ax * width), int(ay * height))
                            pb = (int(bx * width), int(by * height))
                            cv2.line(canvas, pa, pb, (0, 255, 0), 2, lineType=cv2.LINE_AA)

                # draw landmarks
                for idx, (x, y, z, vis) in enumerate(lm_list):
                    if vis > VISIBILITY_THRESHOLD and x > 0 and y > 0:
                        p = (int(x * width), int(y * height))
                        cv2.circle(canvas, p, 3, (0, 255, 0), -1, lineType=cv2.LINE_AA)

            writer.write(canvas)

            if fi in event_frames:
                for _ in range(pause_frames):
                    writer.write(canvas)

        writer.release()
        print(f"Generated black skeleton paused video: {output_video_location}")
        return "VIDEO_GENERATED"

    except FileNotFoundError:
        return "NO_JOINTS_CSV"
    except json.JSONDecodeError:
        return "INVALID_EVENTS"
    except Exception as e:
        print(f"Error generating black skeleton pause video: {e}")
        try:
            writer.release()
        except Exception:
            pass
        return "ERROR"