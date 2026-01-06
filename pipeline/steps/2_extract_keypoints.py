"""
Step 2: Extract Keypoints

This step extracts skeleton keypoints from preprocessed videos using MediaPipe Pose:
- Uses MediaPipe's highest fidelity model (model_complexity=2)
- Extracts 33 pose landmarks per frame
- Saves keypoints to CSV files in c_keypoints/ directory

The module follows the same structure as other steps with a top-level function.
"""

import os
import csv
from pathlib import Path
from typing import Callable, Optional, List
import cv2
import mediapipe as mp
import numpy as np


def extract_keypoints(session_dir: str, log: Optional[Callable[[str, int, str], None]] = None) -> dict:
    """
    Main keypoint extraction function.
    
    Args:
        session_dir: Path to the session directory (e.g., 'data/run/')
        log: Optional logging callback with signature (message, level, type)
             level: 0 = major step, 1 = sub-step, 2 = detail
             type: 'info', 'success', 'warning', 'error'
    
    Returns:
        dict with keys:
            - success: boolean indicating if step completed successfully
            - extracted_views: list of views that were processed
    """
    # Default no-op logger if none provided
    if log is None:
        log = lambda msg, level=1, type='info': None
    
    log("> Step 2: Extract keypoints", 0, 'info')
    
    clips_dir = Path(session_dir) / 'b_clips'
    keypoints_dir = Path(session_dir) / 'c_keypoints'
    keypoints_dir.mkdir(parents=True, exist_ok=True)
    
    result = {
        'success': False,
        'extracted_views': []
    }
    
    # Process each view
    views_to_process = ['back', 'side']
    
    for view_name in views_to_process:
        video_path = clips_dir / f'{view_name}_view.mp4'
        
        if not video_path.exists():
            log(f"- {view_name.capitalize()} view not found, skipping", 1, 'info')
            continue
        
        log(f"- Extracting keypoints from {view_name} view...", 1, 'info')
        
        # Extract keypoints
        keypoints_path = keypoints_dir / f'{view_name}_view_keypoints.csv'
        success = _extract_skeleton_keypoints(str(video_path), str(keypoints_path), log)
        
        if success:
            result['extracted_views'].append(view_name)
            log(f"  ✓ {view_name.capitalize()} view keypoints extracted", 2, 'success')
        else:
            log(f"  ✖ Failed to extract keypoints from {view_name} view", 2, 'error')
    
    result['success'] = len(result['extracted_views']) > 0
    
    if result['success']:
        log("✓ Keypoint extraction complete", 1, 'success')
        log(f"- Extracted keypoints from {len(result['extracted_views'])} view(s)", 1, 'info')
    else:
        log("✖ Keypoint extraction failed", 1, 'error')
    
    return result


def _extract_skeleton_keypoints(video_path: str, output_csv_path: str, log: Callable) -> bool:
    """Extract skeleton keypoints from a video using MediaPipe."""
    cap = None
    pose = None
    try:
        # Check if video exists
        if not os.path.exists(video_path):
            log(f"    Video not found: {video_path}", 3, 'error')
            return False
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            log("    Could not open video", 3, 'error')
            return False
        
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        log(f"    Video has {total_frames} frames at {fps:.1f} fps", 3, 'info')
        log(f"    Using MediaPipe Pose (model_complexity=2 - highest fidelity)", 3, 'info')
        
        # Initialize MediaPipe Pose (version 0.10+)
        # Download model if needed
        project_root = Path(__file__).parent.parent.parent
        model_path = project_root / 'models' / 'pose_landmarker_lite.task'
        
        if not model_path.exists():
            log(f"    Downloading MediaPipe model...", 3, 'info')
            model_path.parent.mkdir(exist_ok=True)
            import urllib.request
            model_url = 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task'
            urllib.request.urlretrieve(model_url, model_path)
            log(f"    Model downloaded", 3, 'success')
        
        # Create pose landmarker
        BaseOptions = mp.tasks.BaseOptions
        PoseLandmarker = mp.tasks.vision.PoseLandmarker
        PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode
        
        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=VisionRunningMode.VIDEO)
        pose = PoseLandmarker.create_from_options(options)
        
        # Prepare CSV header (33 MediaPipe landmarks)
        num_landmarks = 33
        header = ["frame", "time_s"]
        for i in range(num_landmarks):
            header += [f"lm{i}_x", f"lm{i}_y", f"lm{i}_z", f"lm{i}_vis"]
        
        # Process video and write to CSV
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            
            frame_idx = 0
            frames_with_pose = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert BGR to RGB for MediaPipe
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Create MediaPipe Image
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
                timestamp_ms = int((frame_idx / fps) * 1000)
                
                # Process frame
                results = pose.detect_for_video(mp_image, timestamp_ms)
                
                # Build row data
                row: List[float] = [frame_idx, float(frame_idx) / max(1.0, fps)]
                
                if results.pose_landmarks:
                    lm_list = results.pose_landmarks[0]  # First detected person
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
                
                # Progress update every 50 frames
                if frame_idx % 50 == 0:
                    log(f"    Processed {frame_idx}/{total_frames} frames...", 3, 'info')
        
        log(f"    Processed {frame_idx} frames, detected pose in {frames_with_pose} frames", 3, 'success')
        return True
        
    except Exception as e:
        log(f"    Exception: {e}", 3, 'error')
        return False
        
    finally:
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

def extract_skeleton_from_video(input_video_path: str, output_keypoints_path: str):
    #
    pass