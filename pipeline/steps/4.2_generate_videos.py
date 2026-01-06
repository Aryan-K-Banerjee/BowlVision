"""
Step 4.2: Generate Videos

This step generates visualization videos from the processed clips and keypoints:
- Green Skeleton: Skeleton rendered on black background

For now, only implementing green skeleton videos to validate Steps 1 and 2.

Videos are saved to data/run/results/videos/
"""

import os
import csv
import numpy as np
import cv2
from pathlib import Path
from typing import Callable, Optional, List, Tuple
import mediapipe as mp


def generate_videos(session_dir: str, log: Optional[Callable[[str, int, str], None]] = None) -> dict:
    """
    Main video generation function.
    
    Args:
        session_dir: Path to the session directory (e.g., 'data/run/')
        log: Optional logging callback with signature (message, level, type)
             level: 0 = major step, 1 = sub-step, 2 = detail
             type: 'info', 'success', 'warning', 'error'
    
    Returns:
        dict with keys:
            - success: boolean indicating if step completed successfully
            - generated_videos: list of generated video paths
    """
    # Default no-op logger if none provided
    if log is None:
        log = lambda msg, level=1, type='info': None
    
    log("> Step 4.2: Generate videos", 0, 'info')
    
    clips_dir = Path(session_dir) / 'b_clips'
    keypoints_dir = Path(session_dir) / 'c_keypoints'
    videos_dir = Path(session_dir) / 'results' / 'videos'
    videos_dir.mkdir(parents=True, exist_ok=True)
    
    result = {
        'success': False,
        'generated_videos': []
    }
    
    # Process each view
    views_to_process = ['back', 'side']
    
    for view_name in views_to_process:
        video_path = clips_dir / f'{view_name}_view.mp4'
        keypoints_path = keypoints_dir / f'{view_name}_view_keypoints.csv'
        
        if not video_path.exists() or not keypoints_path.exists():
            log(f"- {view_name.capitalize()} view files not found, skipping", 1, 'info')
            continue
        
        log(f"- Generating green skeleton video for {view_name} view...", 1, 'info')
        
        # Generate green skeleton video
        output_path = videos_dir / f'{view_name}_view_skeleton.mp4'
        success = _generate_skeleton_video(
            str(video_path),
            str(keypoints_path),
            str(output_path),
            log
        )
        
        if success:
            result['generated_videos'].append(str(output_path))
            log(f"  ✓ {view_name.capitalize()} skeleton video generated", 2, 'success')
        else:
            log(f"  ✖ Failed to generate skeleton video for {view_name} view", 2, 'error')
    
    result['success'] = len(result['generated_videos']) > 0
    
    if result['success']:
        log("✓ Video generation complete", 1, 'success')
        log(f"- Generated {len(result['generated_videos'])} video(s)", 1, 'info')
    else:
        log("✖ Video generation failed", 1, 'error')
    
    return result


def _generate_skeleton_video(
    video_path: str,
    keypoints_path: str,
    output_path: str,
    log: Callable
) -> bool:
    """Generate a green skeleton video on black background."""
    cap = None
    writer = None
    try:
        # Open video to get dimensions
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            log("    Could not open video", 3, 'error')
            return False
        
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        log(f"    Video dimensions: {width}x{height}, {total_frames} frames at {fps:.1f} fps", 3, 'info')
        
        # Load keypoints from CSV
        keypoints_data = _load_keypoints_from_csv(keypoints_path)
        if not keypoints_data:
            log("    Failed to load keypoints", 3, 'error')
            return False
        
        log(f"    Loaded {len(keypoints_data)} frames of keypoints", 3, 'info')
        
        # Get MediaPipe connections
        connections = _get_pose_connections()
        
        # Create output writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, float(fps), (width, height))
        if not writer.isOpened():
            log("    Could not create output writer", 3, 'error')
            return False
        
        # Generate frames
        for frame_idx in range(len(keypoints_data)):
            # Create black canvas
            canvas = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Get landmarks for this frame
            landmarks = keypoints_data[frame_idx]
            
            # Convert normalized coordinates to pixel coordinates
            pixel_landmarks = []
            for i in range(0, len(landmarks), 4):
                if i + 3 < len(landmarks):
                    x_norm, y_norm, z, vis = landmarks[i:i+4]
                    x_pixel = int(x_norm * width)
                    y_pixel = int(y_norm * height)
                    pixel_landmarks.append((x_pixel, y_pixel, z, vis))
            
            # Draw skeleton
            _draw_skeleton(canvas, pixel_landmarks, connections, color=(0, 255, 0), thickness=2)
            
            writer.write(canvas)
            
            if (frame_idx + 1) % 50 == 0:
                log(f"    Generated {frame_idx + 1}/{len(keypoints_data)} frames...", 3, 'info')
        
        log(f"    Generated {len(keypoints_data)} frames", 3, 'success')
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


def _load_keypoints_from_csv(csv_path: str) -> List[List[float]]:
    """Load keypoints from CSV file."""
    try:
        keypoints_data = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            
            for row in reader:
                # Skip frame and time_s columns
                landmarks = [float(x) for x in row[2:]]
                keypoints_data.append(landmarks)
        
        return keypoints_data
    except Exception as e:
        print(f"Error loading keypoints: {e}")
        return []


def _get_pose_connections() -> List[Tuple[int, int]]:
    """Return MediaPipe pose skeleton connections."""
    try:
        return list(mp.solutions.pose.POSE_CONNECTIONS)
    except Exception:
        # Fallback connections if MediaPipe not available
        return [
            (11, 13), (13, 15),  # Left arm
            (12, 14), (14, 16),  # Right arm
            (11, 12),             # Shoulders
            (23, 25), (25, 27), (27, 31),  # Left leg
            (24, 26), (26, 28), (28, 32),  # Right leg
            (23, 24),             # Hips
            (11, 23), (12, 24),   # Torso
        ]


def _draw_skeleton(
    canvas: np.ndarray,
    landmarks: List[Tuple[float, float, float, float]],
    connections: List[Tuple[int, int]],
    color=(0, 255, 0),
    thickness=2,
    visibility_threshold=0.2
):
    """Draw pose skeleton on canvas."""
    # Draw connections (lines)
    for start_idx, end_idx in connections:
        if start_idx < len(landmarks) and end_idx < len(landmarks):
            x1, y1, z1, vis1 = landmarks[start_idx]
            x2, y2, z2, vis2 = landmarks[end_idx]
            
            if vis1 > visibility_threshold and vis2 > visibility_threshold:
                pt1 = (int(x1), int(y1))
                pt2 = (int(x2), int(y2))
                cv2.line(canvas, pt1, pt2, color, thickness, lineType=cv2.LINE_AA)
    
    # Draw landmarks (circles)
    for i, (x, y, z, vis) in enumerate(landmarks):
        if vis > visibility_threshold:
            cv2.circle(canvas, (int(x), int(y)), 3, color, -1, lineType=cv2.LINE_AA)
