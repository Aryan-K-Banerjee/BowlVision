'''--------------------------------------------------------------
This file contains the business logic to extract skeleton keypoints
from videos using MediaPipe Pose.

This module processes videos frame-by-frame to extract 33 pose landmarks:
- Uses MediaPipe Pose with model_complexity=1
- Outputs to CSV file with columns: frame, time_s, and for each landmark:
  lm{i}_x, lm{i}_y, lm{i}_z, lm{i}_vis (visibility)
- Handles cases where no pose is detected (fills with 0.0)

Inputs:
- video_path: Path to the video file to process
- output_csv_path: Path where the keypoints CSV should be saved

Outputs:
- CSV file with keypoints for each frame
--------------------------------------------------------------'''

#Imports
import os
import csv
from typing import List
import cv2
import mediapipe as mp


def extract_skeleton_keypoints(video_path: str, output_csv_path: str) -> None:
    """Extract skeleton keypoints from a video using MediaPipe.
    
    Args:
        video_path: Path to the video file
        output_csv_path: Path where the keypoints CSV should be saved
    """
    #Check if the video exists
    if not os.path.exists(video_path):
        print(f"        EXTRACT_SKELETON: Video does not exist: {video_path}")
        return
    
    print(f"        EXTRACT_SKELETON: Processing video with MediaPipe...")
    
    try:
        success = _extract_keypoints_impl(video_path, output_csv_path)
        
        if success:
            print(f"        EXTRACT_SKELETON: Successfully extracted keypoints")
        else:
            print(f"        EXTRACT_SKELETON: Failed to extract keypoints")
    except Exception as e:
        print(f"        EXTRACT_SKELETON: Error extracting keypoints: {e}")


def _extract_keypoints_impl(video_location: str, output_csv_location: str) -> bool:
    """Performs the actual keypoint extraction. Returns True on success."""
    cap = None
    pose = None
    try:
        # Open video
        cap = cv2.VideoCapture(video_location)
        if not cap.isOpened():
            print("        EXTRACT_SKELETON: Could not open video")
            return False

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        
        print(f"        EXTRACT_SKELETON: Video has {total_frames} frames at {fps:.1f} fps")

        # Prepare MediaPipe pose with highest quality model
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,  # Use heavy model for maximum accuracy
            enable_segmentation=False
        )

        # Ensure output dir exists
        out_dir = os.path.dirname(output_csv_location)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        # Prepare CSV header
        # MediaPipe pose has 33 landmarks
        num_landmarks = 33
        header = ["frame", "time_s"]
        for i in range(num_landmarks):
            header += [f"lm{i}_x", f"lm{i}_y", f"lm{i}_z", f"lm{i}_vis"]

        # Process video and write to CSV
        with open(output_csv_location, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)

            frame_idx = 0
            frames_processed = 0
            frames_with_pose = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Convert BGR to RGB for MediaPipe
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(image)

                # Build row data
                row: List[float] = [frame_idx, float(frame_idx) / max(1.0, fps)]

                if results.pose_landmarks:
                    lm_list = results.pose_landmarks.landmark
                    frames_with_pose += 1
                    # Fill landmarks
                    for i in range(num_landmarks):
                        if i < len(lm_list):
                            lm = lm_list[i]
                            row += [
                                float(lm.x),
                                float(lm.y),
                                float(getattr(lm, 'z', 0.0)),
                                float(getattr(lm, 'visibility', 0.0))
                            ]
                        else:
                            row += [0.0, 0.0, 0.0, 0.0]
                else:
                    # No landmarks detected
                    row += [0.0] * (num_landmarks * 4)

                writer.writerow(row)
                frame_idx += 1
                frames_processed += 1
                
                # Progress update every 100 frames
                if frames_processed % 100 == 0:
                    print(f"        EXTRACT_SKELETON: Processed {frames_processed}/{total_frames} frames...")

        print(f"        EXTRACT_SKELETON: Processed {frames_processed} frames, detected pose in {frames_with_pose} frames")
        return True

    except Exception as e:
        print(f"        EXTRACT_SKELETON: Exception during processing: {e}")
        return False

    finally:
        # Cleanup resources
        if pose is not None:
            try:
                pose.close()
            except Exception:
                pass
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass
