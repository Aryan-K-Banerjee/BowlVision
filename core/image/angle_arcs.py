#core/image/angle_arcs
'''--------------------------------------------------------------------------
This module contains functions to generate videos that have these characteristics:
-Black background
-Green skeleton
-Angle arcs displayed at key joints
-Pause at events for 2 seconds
-------------------------------------------------------------------------'''

#imports

import os
import csv
import json
import math
from statistics import median
from typing import Dict, List, Tuple, Optional

import cv2
import numpy as np

import core.angles.front_knee_angle as front_knee_angle

from core.image.image_utils import read_joints_csv, read_angles_csv, draw_angle_arc, get_pose_connections


#function that generates video with black skeleton and angle arcs that pauses at events
def generate_angle_arcs_with_pause(
        input_csv_location: str,
        angles_csv_location: str,
        events_location: str,
        view: str,
        output_video_location: str
):
    """
    So basically each angles file has a function called render_points that takes in
    the csv location, and a frame, and will return the necessary points to draw and arc.
    I suggest this approach.

    1: Use the input csv location to read in the keypoints for each frame.
    2: Draw the green skeleton on a black background for each frame.
    3: For each frame, call the appropriate angle function's render_points to get the arc points.
    4: use a function to draw the arc on the frame.
    5: Use the angles csv location to read in the angles for each frame and feed it in the function so calculations don't need to be redone.
    6: Check the events json to see if the current frame is an event frame, if so duplicate the frame
       enough times to create a 2 second pause based on the fps.

    Return codes:
        "VIDEO_GENERATED", "NO_JOINTS_CSV", "INVALID_EVENTS", "ERROR"
    
    For now theres only front_knee_angle implemented, so only side view is supported.
    For front view just return ERROR for now.
    """
    PAUSE_SECONDS = 2.0
    VISIBILITY_THRESHOLD = 0.2

    try:
        # read joints
        frames_map, inferred_fps = read_joints_csv(input_csv_location)
        if not frames_map:
            return "NO_JOINTS_CSV"

        max_frame = max(frames_map.keys())

        # read angles
        angles_map = read_angles_csv(angles_csv_location)

        # read events
        events = {}
        video_file = None
        if events_location and os.path.exists(events_location):
            try:
                with open(events_location, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                events = data.get('video', {}).get('events', {}) or {}
                video_file = data.get('video', {}).get('file_location')
            except Exception:
                return "INVALID_EVENTS"

        fps = inferred_fps or 25.0
        width, height = 640, 480
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

        # determine event frames
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

        # obtain connections from shared utils (mediapipe if available)
        connections = get_pose_connections()

        # iterate frames
        for fi in range(0, max_frame + 1):
            canvas = np.zeros((height, width, 3), dtype=np.uint8)

            lm_list = frames_map.get(fi)
            if lm_list:
                # draw connections
                for conn in connections:
                    try:
                        a, b = int(conn[0]), int(conn[1])
                    except Exception:
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

                # angle points from module
                if view and view.lower().startswith('side'):
                    pts = front_knee_angle.render_points(frames_map, fi)
                    if pts:
                        # pts are normalized coords (x,y) pairs
                        p1n, p2n, p3n = pts
                        p1 = (int(p1n[0] * width), int(p1n[1] * height))
                        p2 = (int(p2n[0] * width), int(p2n[1] * height))
                        p3 = (int(p3n[0] * width), int(p3n[1] * height))
                        angle_val = angles_map.get(fi)
                        draw_angle_arc(canvas, p1, p2, p3, angle_val)

            writer.write(canvas)

            if fi in event_frames:
                for _ in range(pause_frames):
                    writer.write(canvas)

        writer.release()
        print(f"Generated angle arcs paused video: {output_video_location}")
        return "VIDEO_GENERATED"

    except FileNotFoundError:
        return "NO_JOINTS_CSV"
    except json.JSONDecodeError:
        return "INVALID_EVENTS"
    except Exception as e:
        print(f"Error generating angle arcs video: {e}")
        try:
            writer.release()
        except Exception:
            pass
        return "ERROR"
