"""
Screenshot Engine - Generates all screenshot images from results.json specs.

Coordinates type renderers, angle functions, and crop strategies via registries.
"""

import json
import csv
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from pipeline.screenshots.types import get_type_renderer
from pipeline.screenshots.angles import get_angle_function
from pipeline.screenshots.crops import get_crop_function


def generate_screenshots(session_dir: str, results_json_path: str) -> List[str]:
    """Generate all screenshots from results.json specs.
    
    Args:
        session_dir: Path to session directory
        results_json_path: Path to results.json file
        
    Returns:
        List of generated screenshot paths
    """
    session_dir = Path(session_dir)
    
    # Load results.json
    with open(results_json_path, 'r') as f:
        results_data = json.load(f)
    
    # Create screenshots output directory
    screenshots_dir = session_dir / 'results' / 'screenshots'
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # Collect all screenshot specs from all sections
    all_specs = _collect_all_screenshot_specs(results_data)
    
    print(f"    SCREENSHOT_ENGINE: Found {len(all_specs)} screenshot specs to generate")
    
    # Load videos and keypoints (lazy loading, cached)
    video_cache = {}
    keypoints_cache = {}
    generated_paths = []
    
    for i, spec in enumerate(all_specs, 1):
        output_name = spec.get('output_name', 'unknown')
        print(f"    SCREENSHOT_ENGINE: Generating {i}/{len(all_specs)}: {output_name}")
        paths = _generate_screenshot(spec, session_dir, screenshots_dir, video_cache, keypoints_cache)
        generated_paths.extend(paths)
    
    # Release videos
    for cap in video_cache.values():
        if cap is not None:
            cap.release()
    
    print(f"    SCREENSHOT_ENGINE: Generated {len(generated_paths)} screenshots")
    return generated_paths


def _collect_all_screenshot_specs(results_data: dict) -> List[dict]:
    """Extract all screenshot specs from results.json structure."""
    specs = []
    
    # From header video_summary section
    if 'header' in results_data:
        header = results_data['header']
        if 'video_summary' in header:
            video_summary = header['video_summary']
            summary_specs = video_summary.get('screenshots', [])
            specs.extend(summary_specs)
    
    # From classifications section
    if 'classifications' in results_data:
        for classification in results_data['classifications']:
            class_specs = classification.get('screenshots', [])
            specs.extend(class_specs)
    
    # From metrics section
    if 'metrics' in results_data:
        for metric in results_data['metrics']:
            metric_specs = metric.get('screenshots', [])
            specs.extend(metric_specs)
    
    return specs


def _generate_screenshot(spec: dict, session_dir: Path, screenshots_dir: Path,
                        video_cache: dict, keypoints_cache: dict) -> List[str]:
    """Generate a single screenshot from spec.
    
    Returns:
        List of generated file paths
    """
    view = spec.get('view', 'side')  # 'side' or 'back'
    frames = spec.get('frames', [])
    blended = spec.get('blended', False)
    types = spec.get('types', ['original'])
    angles = spec.get('angles', [])
    angle_name = angles[0] if angles else 'none'
    crop_strategy = spec.get('crop_strategy', 'full_body')
    output_name = spec.get('output_name', 'screenshot')
    angle_value = spec.get('angle_value')
    
    generated_paths = []
    
    if not frames:
        print(f"      WARNING: No frames specified for {output_name}")
        return generated_paths
    
    # Load video and keypoints for this view
    video_cap = _get_video(view, session_dir, video_cache)
    keypoints = _get_keypoints(view, session_dir, keypoints_cache)
    
    if video_cap is None:
        print(f"      WARNING: Missing video for {view} view")
        return generated_paths
    
    if keypoints is None:
        print(f"      WARNING: Missing keypoints for {view} view")
        return generated_paths
    
    # Get frame(s)
    if blended and len(frames) > 1:
        # Blend multiple frames
        base_frame = _blend_frames(video_cap, frames)
    else:
        # Single frame
        base_frame = _get_frame(video_cap, frames[0])
    
    if base_frame is None:
        print(f"      WARNING: Could not load frame for {output_name}")
        return generated_paths
    
    # Get landmarks for the frame (use first frame if blended)
    frame_num = frames[0]
    landmarks_px = _get_landmarks_px(keypoints, frame_num, base_frame.shape[:2])
    
    if landmarks_px is None:
        print(f"      WARNING: No landmarks for frame {frame_num}")
        # Still generate original screenshot without landmarks
        landmarks_px = []
    
    # Get angle points if angle overlay is requested
    angle_points = None
    if angle_name and angle_name != 'none' and landmarks_px:
        angle_func = get_angle_function(angle_name)
        if angle_func:
            points = angle_func(landmarks_px, base_frame.shape[:2])
            if points:
                # Include angle value if provided
                angle_points = (*points, angle_value)
    
    # Get crop function
    crop_func = get_crop_function(crop_strategy)
    if not crop_func:
        print(f"      WARNING: Unknown crop strategy: {crop_strategy}")
        crop_func = get_crop_function('full_body')
    
    # Compute crop window
    crop_window = crop_func(landmarks_px, base_frame.shape[:2])
    
    # Generate each type variant
    for type_name in types:
        type_renderer = get_type_renderer(type_name)
        if not type_renderer:
            print(f"      WARNING: Unknown type: {type_name}")
            continue
        
        # Render full frame
        rendered_frame = type_renderer(base_frame, landmarks_px, angle_points)
        
        # Crop the rendered frame
        cropped = _apply_crop(rendered_frame, crop_window)
        
        # Save
        filename = f"{output_name}_{type_name}.png"
        output_path = screenshots_dir / filename
        cv2.imwrite(str(output_path), cropped)
        generated_paths.append(str(output_path))
    
    return generated_paths


def _get_video(view: str, session_dir: Path, cache: dict) -> Optional[cv2.VideoCapture]:
    """Get video capture for view (cached)."""
    if view in cache:
        return cache[view]
    
    # Determine video path - videos are in b_clips directory
    if view == 'back':
        video_path = session_dir / 'b_clips' / 'back_view.mp4'
    else:  # 'side'
        video_path = session_dir / 'b_clips' / 'side_view.mp4'
    
    if not video_path.exists():
        cache[view] = None
        return None
    
    cap = cv2.VideoCapture(str(video_path))
    cache[view] = cap
    return cap


def _get_keypoints(view: str, session_dir: Path, cache: dict) -> Optional[dict]:
    """Get keypoints for view (cached)."""
    if view in cache:
        return cache[view]
    
    # Determine keypoints path
    if view == 'back':
        kp_path = session_dir / 'c_keypoints' / 'back_view_keypoints.csv'
    else:  # 'side'
        kp_path = session_dir / 'c_keypoints' / 'side_view_keypoints.csv'
    
    if not kp_path.exists():
        cache[view] = None
        return None
    
    keypoints = _load_keypoints_csv(kp_path)
    cache[view] = keypoints
    return keypoints


def _load_keypoints_csv(csv_path: Path) -> Dict[int, np.ndarray]:
    """Load keypoints CSV into frame -> landmarks mapping."""
    keypoints = {}
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            frame = int(row['frame'])
            lms = []
            for i in range(33):  # MediaPipe has 33 landmarks
                x = float(row[f'lm{i}_x'])
                y = float(row[f'lm{i}_y'])
                z = float(row[f'lm{i}_z'])
                vis = float(row[f'lm{i}_vis'])
                lms.append([x, y, z, vis])
            keypoints[frame] = np.array(lms)
    
    return keypoints


def _get_frame(cap: cv2.VideoCapture, frame_num: int) -> Optional[np.ndarray]:
    """Extract single frame from video."""
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    ret, frame = cap.read()
    return frame if ret else None


def _blend_frames(cap: cv2.VideoCapture, frame_nums: List[int]) -> Optional[np.ndarray]:
    """Blend multiple frames together (simple average)."""
    frames = []
    for frame_num in frame_nums:
        frame = _get_frame(cap, frame_num)
        if frame is not None:
            frames.append(frame.astype(np.float32))
    
    if not frames:
        return None
    
    # Average blend
    blended = np.mean(frames, axis=0).astype(np.uint8)
    return blended


def _get_landmarks_px(keypoints: dict, frame_num: int, frame_shape: Tuple[int, int]) -> Optional[List]:
    """Get landmarks in pixel coordinates for a frame."""
    if frame_num not in keypoints:
        return None
    
    landmarks_norm = keypoints[frame_num]
    h, w = frame_shape
    
    # Convert from normalized [0,1] to pixels
    landmarks_px = []
    for lm in landmarks_norm:
        x_norm, y_norm, z, vis = lm
        x_px = x_norm * w
        y_px = y_norm * h
        landmarks_px.append((x_px, y_px, z, vis))
    
    return landmarks_px


def _apply_crop(frame: np.ndarray, crop_window: Tuple[int, int, int, int]) -> np.ndarray:
    """Apply crop window to frame."""
    x, y, w, h = crop_window
    fh, fw = frame.shape[:2]
    
    # If full frame, just return it
    if x == 0 and y == 0 and w == fw and h == fh:
        return frame
    
    # Create output tile
    tile = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Compute safe source and destination regions
    src_x1 = max(0, x)
    src_y1 = max(0, y)
    src_x2 = min(fw, x + w)
    src_y2 = min(fh, y + h)
    
    dst_x1 = src_x1 - x
    dst_y1 = src_y1 - y
    dst_x2 = dst_x1 + (src_x2 - src_x1)
    dst_y2 = dst_y1 + (src_y2 - src_y1)
    
    if src_x2 > src_x1 and src_y2 > src_y1:
        tile[dst_y1:dst_y2, dst_x1:dst_x2] = frame[src_y1:src_y2, src_x1:src_x2]
    
    return tile
