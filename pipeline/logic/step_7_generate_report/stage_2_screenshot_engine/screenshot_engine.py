"""
Screenshot Engine - Stage 2 Orchestrator

Reads screenshot specs from report.json and generates all screenshot images.
Coordinates type renderers, angle functions, and crop strategies via registries.
"""

import json
import csv
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from pipeline.logic.step_7_generate_report.stage_2_screenshot_engine.type_registry import get_type_renderer
from pipeline.logic.step_7_generate_report.stage_2_screenshot_engine.angle_registry import get_angle_function
from pipeline.logic.step_7_generate_report.stage_2_screenshot_engine.crop_registry import get_crop_function


def generate_screenshots(session_dir: str, report_json_path: str):
    """Generate all screenshots from report.json specs.
    
    Args:
        session_dir: Path to session directory
        report_json_path: Path to report.json file
    """
    session_dir = Path(session_dir)
    
    # Load report.json
    with open(report_json_path, 'r') as f:
        report_data = json.load(f)
    
    # Create screenshots output directory
    screenshots_dir = session_dir / 'results' / 'screenshots'
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # Collect all screenshot specs from all sections
    all_specs = _collect_all_screenshot_specs(report_data)
    
    print(f"    SCREENSHOT_ENGINE: Found {len(all_specs)} screenshot specs to generate")
    
    # Load videos and keypoints (lazy loading, cached)
    video_cache = {}
    keypoints_cache = {}
    
    for i, spec in enumerate(all_specs, 1):
        print(f"    SCREENSHOT_ENGINE: Generating {i}/{len(all_specs)}: {spec.get('output_name', 'unknown')}")
        _generate_screenshot(spec, session_dir, screenshots_dir, video_cache, keypoints_cache)
    
    # Release videos
    for cap in video_cache.values():
        if cap is not None:
            cap.release()
    
    print(f"    SCREENSHOT_ENGINE: Generated {len(all_specs)} screenshots")


def _collect_all_screenshot_specs(report_data: dict) -> List[dict]:
    """Extract all screenshot specs from report.json structure."""
    specs = []
    
    # From video_events_classification section
    if 'video_events_classification' in report_data:
        section_specs = report_data['video_events_classification'].get('screenshots', [])
        specs.extend(section_specs)
    
    # From metrics section
    if 'metrics' in report_data:
        for metric in report_data['metrics']:
            metric_specs = metric.get('screenshots', [])
            specs.extend(metric_specs)
    
    return specs


def _generate_screenshot(spec: dict, session_dir: Path, screenshots_dir: Path,
                        video_cache: dict, keypoints_cache: dict):
    """Generate a single screenshot from spec."""
    view = spec.get('view', 'side')  # 'side' or 'back'
    frames = spec.get('frames', [])
    blended = spec.get('blended', False)
    types = spec.get('types', ['original'])
    angle_name = spec.get('angles', ['none'])[0] if spec.get('angles') else 'none'
    crop_strategy = spec.get('crop_strategy', 'full_body')
    output_name = spec.get('output_name', 'screenshot')
    
    if not frames:
        print(f"      WARNING: No frames specified for {output_name}")
        return
    
    # Load video and keypoints for this view
    video_cap = _get_video(view, session_dir, video_cache)
    keypoints = _get_keypoints(view, session_dir, keypoints_cache)
    
    if video_cap is None or keypoints is None:
        print(f"      WARNING: Missing video or keypoints for {view} view")
        return
    
    # Get frame(s)
    if blended and len(frames) > 1:
        # Blend multiple frames
        base_frame = _blend_frames(video_cap, frames)
    else:
        # Single frame
        base_frame = _get_frame(video_cap, frames[0])
    
    if base_frame is None:
        print(f"      WARNING: Could not load frame for {output_name}")
        return
    
    # Get landmarks for the frame (use first frame if blended)
    frame_num = frames[0]
    landmarks_px = _get_landmarks_px(keypoints, frame_num, base_frame.shape[:2])
    
    if landmarks_px is None:
        print(f"      WARNING: No landmarks for frame {frame_num}")
        return
    
    # Get angle points if angle overlay is requested
    angle_points = None
    if angle_name and angle_name != 'none':
        angle_func = get_angle_function(angle_name)
        if angle_func:
            points = angle_func(landmarks_px, base_frame.shape[:2])
            if points:
                # Get angle value from spec if provided, otherwise None (will be computed)
                angle_value = spec.get('angle_value')
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
