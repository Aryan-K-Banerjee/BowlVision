# core/cv/extract_joints.py
'''--------------------------------------------------------------------------
This module contains functions to extract joints from videos using mediapipe.
-------------------------------------------------------------------------'''
# module imports
import os
import csv
import time
from typing import List
import cv2
import numpy as np
import mediapipe as mp



# function to extract joints from video
def extract_joints(video_name: str, video_exists: bool, video_location: str, output_csv_location: str) -> None:
    """Wrapper to extract pose joints from a video.

    If `video_exists` is False, prints `NO {video_name}` and returns.
    Otherwise delegates to `_extract_joints_impl(...)` and prints a
    short success/error message. The wrapper does not return status codes.
    """
    if not video_exists:
        print(f"NO {video_name}")
        return

    print(f"Extracting keypoints for video: {video_name}")
    try:
        ok = _extract_joints_impl(video_location, output_csv_location)
        if ok:
            print(f"Keypoints extracted: {video_name}")
        else:
            print("Error extracting keypoints")
    except Exception:
        print("Error extracting keypoints")


def _extract_joints_impl(video_location: str, output_csv_location: str) -> bool:
    """Performs the actual extraction and writes CSV. Returns True on success."""
    cap = None
    pose = None
    try:
        if not os.path.exists(video_location):
            return False

        cap = cv2.VideoCapture(video_location)
        if not cap.isOpened():
            return False

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        # total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

        # prepare mediapipe pose
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(static_image_mode=False, model_complexity=1, enable_segmentation=False)

        # ensure output dir exists
        out_dir = os.path.dirname(output_csv_location)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        # prepare CSV header
        # mediapipe pose has 33 landmarks
        num_landmarks = 33
        header = ["frame", "time_s"]
        for i in range(num_landmarks):
            header += [f"lm{i}_x", f"lm{i}_y", f"lm{i}_z", f"lm{i}_vis"]

        with open(output_csv_location, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)

            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # convert color
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(image)

                row: List[float] = [frame_idx, float(frame_idx) / max(1.0, fps)]

                if results.pose_landmarks:
                    lm_list = results.pose_landmarks.landmark
                    # fill landmarks
                    for i in range(num_landmarks):
                        if i < len(lm_list):
                            lm = lm_list[i]
                            row += [float(lm.x), float(lm.y), float(getattr(lm, 'z', 0.0)), float(getattr(lm, 'visibility', 0.0))]
                        else:
                            row += [0.0, 0.0, 0.0, 0.0]
                else:
                    # no landmarks detected
                    row += [0.0] * (num_landmarks * 4)

                writer.writerow(row)
                frame_idx += 1

        # success
        return True

    except Exception:
        return False

    finally:
        # cleanup resources
        try:
            if pose is not None:
                try:
                    pose.close()
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
