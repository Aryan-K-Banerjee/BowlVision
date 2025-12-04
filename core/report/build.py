"""
BowlVision Report Builder Orchestrator

Main entry point for rendering session reports. Executes recipe JSON to generate
tiles (original/skeleton/overlay variants), builds manifest, and renders HTML report.
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Optional
import cv2
import numpy as np

from core.report.selectors.events_selector import select as select_event
from core.report.selectors.front_leg_brace_selector import select as select_metric
from core.report.crop.policy import get_crop
from core.report.render.original import render as render_original
from core.report.render.skeleton import render as render_skeleton
from core.report.render.overlay import render as render_overlay
from core.report.compose.blend import blend


def build_report(
    session_dir: Path,
    analysis_results_path: Path,
    back_video_path: Optional[Path],
    side_video_path: Optional[Path],
    back_joints_csv: Optional[Path],
    side_joints_csv: Optional[Path],
    back_angles_csv: Optional[Path],
    side_angles_csv: Optional[Path]
) -> Path:
    """
    Build complete HTML report with tiles.
    
    Args:
        session_dir: Session root directory
        analysis_results_path: Path to analysis_results.json
        back_video_path: Path to back view video (or None)
        side_video_path: Path to side view video (or None)
        back_joints_csv: Path to back view keypoints (or None)
        side_joints_csv: Path to side view keypoints (or None)
        back_angles_csv: Path to back view angles (or None)
        side_angles_csv: Path to side view angles (or None)
    
    Returns:
        Path to generated session_report.html
    """
    session_dir = Path(session_dir)
    
    # Load analysis results
    with open(analysis_results_path, 'r') as f:
        analysis_data = json.load(f)
    
    # Unwrap if it has analysis_results wrapper
    if 'analysis_results' in analysis_data:
        analysis_results = analysis_data['analysis_results']
    else:
        analysis_results = analysis_data
    
    # Load recipe
    recipe_path = Path(__file__).parent / 'recipes' / 'default.json'
    with open(recipe_path, 'r') as f:
        recipe_data = json.load(f)
    
    # Extract panels array from recipe
    panels = recipe_data.get('panels', []) if isinstance(recipe_data, dict) else recipe_data
    
    # Create report directories
    report_dir = session_dir / 'report'
    frames_dir = report_dir / 'frames'
    frames_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy CSS to report dir
    css_source = Path(__file__).parent / 'static' / 'report.css'
    css_dest = report_dir / 'static'
    css_dest.mkdir(exist_ok=True)
    import shutil
    shutil.copy(css_source, css_dest / 'report.css')
    
    # Load videos and landmarks
    videos = {}
    landmarks = {}
    angles = {}
    
    if back_video_path and back_video_path.exists():
        videos['back_view'] = cv2.VideoCapture(str(back_video_path))
        if back_joints_csv and back_joints_csv.exists():
            landmarks['back_view'] = _load_landmarks(back_joints_csv)
        if back_angles_csv and back_angles_csv.exists():
            angles['back_view'] = _load_angles(back_angles_csv)
    
    if side_video_path and side_video_path.exists():
        videos['side_view'] = cv2.VideoCapture(str(side_video_path))
        if side_joints_csv and side_joints_csv.exists():
            landmarks['side_view'] = _load_landmarks(side_joints_csv)
        if side_angles_csv and side_angles_csv.exists():
            angles['side_view'] = _load_angles(side_angles_csv)
    
    # Process each panel in recipe
    manifest_panels = []
    
    for panel in panels:
        panel_result = _process_panel(
            panel,
            analysis_results,
            videos,
            landmarks,
            angles,
            frames_dir
        )
        manifest_panels.append(panel_result)
    
    # Release videos
    for cap in videos.values():
        cap.release()
    
    # Build manifest
    manifest = {
        'session': analysis_results['session_metadata'],
        'bowler': analysis_results['bowler_metadata'],
        'panels': manifest_panels
    }
    
    manifest_path = report_dir / 'report_manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Render HTML
    html_path = _render_html(report_dir, manifest)
    
    return html_path


def _process_panel(
    panel: dict,
    analysis_results: dict,
    videos: Dict[str, cv2.VideoCapture],
    landmarks: Dict[str, dict],
    angles: Dict[str, dict],
    frames_dir: Path
) -> dict:
    """Process single panel: resolve target, render variants, save tiles."""
    
    # Parse frame_source string (format: "event:jump" or "metric:group:key")
    frame_source = panel['frame_source']
    if ':' not in frame_source:
        raise ValueError(f"Invalid frame_source format: {frame_source}")
    
    parts = frame_source.split(':')
    source_type = parts[0]
    
    # Resolve render target
    if source_type == 'event':
        # Format: "event:jump"
        event_key = parts[1]
        target = select_event(
            panel['view'],  # "back" or "side"
            event_key,      # event key like "jump", "ffc"
            analysis_results['videos_data']
        )
    elif source_type == 'metric':
        # Format: "metric:front_leg_brace:ffc" -> extract key "ffc"
        if len(parts) < 3:
            raise ValueError(f"Metric frame_source needs format 'metric:group:key': {frame_source}")
        metric_key = parts[2]  # "ffc", "release", "max_diff"
        target = select_metric(
            metric_key,
            analysis_results.get('analysis', {})  # Pass full analysis dict
        )
    else:
        raise ValueError(f"Unknown frame_source type: {source_type}")
    
    # Generate a label from panel_slug if not provided
    label = panel.get('label', panel.get('panel_slug', 'Unknown').replace('_', ' ').title())
    
    # Build result structure
    result = {
        'group': panel['group'],
        'label': label,
        'view': panel['view'],
        'exists': target.exists,
        'variants': {}
    }
    
    if not target.exists:
        # Generate placeholder paths but don't create files
        for variant in panel['variants']:
            result['variants'][variant] = 'frames/placeholder.png'
        return result
    
    # Get frame from video (convert "back"/"side" to "back_view"/"side_view")
    view_key = f"{target.view}_view"
    frame_num = target.frame
    
    if view_key not in videos or view_key not in landmarks:
        result['exists'] = False
        for variant in panel['variants']:
            result['variants'][variant] = 'frames/placeholder.png'
        return result
    
    cap = videos[view_key]
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    ret, frame = cap.read()
    
    if not ret:
        result['exists'] = False
        for variant in panel['variants']:
            result['variants'][variant] = 'frames/placeholder.png'
        return result
    
    # Get landmarks for this frame
    frame_landmarks = landmarks[view_key].get(frame_num)
    if frame_landmarks is None:
        result['exists'] = False
        for variant in panel['variants']:
            result['variants'][variant] = 'frames/placeholder.png'
        return result
    
    # Convert landmarks from normalized [0,1] to pixel coordinates
    h, w = frame.shape[:2]
    landmarks_px = []
    for lm in frame_landmarks:
        x_norm, y_norm, z, vis = lm
        x_px = x_norm * w
        y_px = y_norm * h
        landmarks_px.append((x_px, y_px, z, vis))
    
    # Compute crop window
    crop_window = get_crop(
        target.view,        # "back" or "side"
        frame_num,          # frame number
        landmarks_px,       # landmarks in PIXEL coordinates
        frame.shape[:2],    # (height, width)
        panel['crop_policy']  # policy name
    )
    
    # Extract angle value from analysis results if this is a metric panel
    angle_value = None
    if source_type == 'metric' and 'front_knee_angle' in panel.get('overlays', []):
        # Get the angle from analysis results for this metric
        metric_group = parts[1]  # "front_leg_brace"
        metric_key = parts[2]    # "ffc", "release", "max_diff"
        
        # Map metric keys to analysis field names
        metric_field_map = {
            "ffc": "front_knee_angle_at_ffc",
            "release": "front_knee_angle_at_release",
            "max_diff": "max_difference_ffc_release"
        }
        
        field_name = metric_field_map.get(metric_key)
        if field_name:
            analysis = analysis_results.get('analysis', {})
            metric_group_data = analysis.get(metric_group, {})
            metrics = metric_group_data.get('metrics', {})
            metric_data = metrics.get(field_name, {})
            value_data = metric_data.get('value', {})
            # For max_diff, use 'knee_angle' instead of 'angle' (angle is the difference value)
            if metric_key == "max_diff":
                angle_value = value_data.get('knee_angle')
            else:
                angle_value = value_data.get('angle')
    
    # Render variants
    overlays = panel.get('overlays', [])
    
    for variant in panel['variants']:
        if variant == 'original':
            tile = render_original(frame, landmarks_px, crop_window, overlays, angle_value)
        elif variant == 'skeleton':
            tile = render_skeleton(frame, landmarks_px, crop_window, overlays, angle_value)
        elif variant == 'overlay':
            tile = render_overlay(frame, landmarks_px, crop_window, overlays, angle_value)
        else:
            raise ValueError(f"Unknown variant: {variant}")
        
        # Handle composite
        if 'composite_with' in panel:
            composite_config = panel['composite_with']
            
            # Parse composite frame_source (same format as main frame_source)
            comp_frame_source = composite_config['frame_source']
            comp_parts = comp_frame_source.split(':')
            comp_type = comp_parts[0]
            
            # Resolve composite target
            if comp_type == 'event':
                comp_event_key = comp_parts[1]
                comp_target = select_event(
                    panel['view'],
                    comp_event_key,
                    analysis_results['videos_data']
                )
            elif comp_type == 'metric':
                if len(comp_parts) < 3:
                    raise ValueError(f"Metric frame_source needs format 'metric:group:key': {comp_frame_source}")
                comp_metric_key = comp_parts[2]
                comp_target = select_metric(
                    comp_metric_key,
                    analysis_results.get('analysis', {})
                )
            else:
                raise ValueError(f"Unknown composite frame_source type: {comp_type}")
            
            # If composite target exists, render it and blend
            if comp_target.exists:
                # Get composite frame
                comp_view_key = f"{comp_target.view}_view"
                comp_frame_num = comp_target.frame
                
                if comp_view_key in videos and comp_view_key in landmarks:
                    comp_cap = videos[comp_view_key]
                    comp_cap.set(cv2.CAP_PROP_POS_FRAMES, comp_frame_num)
                    ret, comp_frame = comp_cap.read()
                    
                    if ret:
                        comp_frame_landmarks = landmarks[comp_view_key].get(comp_frame_num)
                        if comp_frame_landmarks is not None:
                            # Convert to pixel coordinates
                            h, w = comp_frame.shape[:2]
                            comp_landmarks_px = []
                            for lm in comp_frame_landmarks:
                                x_norm, y_norm, z, vis = lm
                                x_px = x_norm * w
                                y_px = y_norm * h
                                comp_landmarks_px.append((x_px, y_px, z, vis))
                            
                            # Compute crop for composite frame (same policy)
                            comp_crop_window = get_crop(
                                comp_target.view,
                                comp_frame_num,
                                comp_landmarks_px,
                                comp_frame.shape[:2],
                                panel['crop_policy']
                            )
                            
                            # Extract angle value for composite frame if needed
                            comp_angle_value = None
                            if comp_type == 'metric' and 'front_knee_angle' in overlays:
                                comp_metric_group = comp_parts[1]
                                comp_metric_key = comp_parts[2]
                                
                                comp_metric_field_map = {
                                    "ffc": "front_knee_angle_at_ffc",
                                    "release": "front_knee_angle_at_release",
                                    "max_diff": "max_difference_ffc_release"
                                }
                                
                                comp_field_name = comp_metric_field_map.get(comp_metric_key)
                                if comp_field_name:
                                    analysis = analysis_results.get('analysis', {})
                                    comp_metric_group_data = analysis.get(comp_metric_group, {})
                                    comp_metrics = comp_metric_group_data.get('metrics', {})
                                    comp_metric_data = comp_metrics.get(comp_field_name, {})
                                    comp_value_data = comp_metric_data.get('value', {})
                                    # For max_diff, use 'knee_angle' instead of 'angle' (angle is the difference value)
                                    if comp_metric_key == "max_diff":
                                        comp_angle_value = comp_value_data.get('knee_angle')
                                    else:
                                        comp_angle_value = comp_value_data.get('angle')
                            
                            # Render composite tile (same variant as main tile)
                            if variant == 'original':
                                base_tile = render_original(comp_frame, comp_landmarks_px, comp_crop_window, overlays, comp_angle_value)
                            elif variant == 'skeleton':
                                base_tile = render_skeleton(comp_frame, comp_landmarks_px, comp_crop_window, overlays, comp_angle_value)
                            elif variant == 'overlay':
                                base_tile = render_overlay(comp_frame, comp_landmarks_px, comp_crop_window, overlays, comp_angle_value)
                            
                            # Blend using opacity values [alpha, beta]
                            opacity = composite_config.get('opacity', [0.5, 0.5])
                            tile = blend(base_tile, tile, opacity[0], opacity[1])
        
        # Save tile
        filename = f"{panel['group']}_{label.replace(' ', '_').lower()}_{variant}.png"
        filepath = frames_dir / filename
        cv2.imwrite(str(filepath), tile)
        
        result['variants'][variant] = f'frames/{filename}'
    
    return result


def _load_landmarks(csv_path: Path) -> Dict[int, np.ndarray]:
    """Load landmarks CSV into dict keyed by frame number."""
    landmarks = {}
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            frame = int(row['frame'])
            lms = []
            for i in range(33):
                x = float(row[f'lm{i}_x'])
                y = float(row[f'lm{i}_y'])
                z = float(row[f'lm{i}_z'])
                vis = float(row[f'lm{i}_vis'])
                lms.append([x, y, z, vis])
            landmarks[frame] = np.array(lms)
    
    return landmarks


def _load_angles(csv_path: Path) -> Dict[int, float]:
    """Load angles CSV into dict keyed by frame number."""
    angles_map = {}
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        # Check if this CSV has angle data (some views may only have 'frame' column)
        if 'front_knee_angle' not in reader.fieldnames:
            return angles_map  # Return empty dict if no angle column
        
        for row in reader:
            frame = int(row['frame'])
            angle = float(row['front_knee_angle'])
            angles_map[frame] = angle
    
    return angles_map


def _render_html(report_dir: Path, manifest: dict) -> Path:
    """Render HTML template with manifest data."""
    template_path = Path(__file__).parent / 'templates' / 'report.html'
    
    with open(template_path, 'r') as f:
        template = f.read()
    
    # Prepare metadata
    session_meta = manifest['session']
    bowler_meta = manifest['bowler']
    
    # Replace template variables
    replacements = {
        '{{session_name}}': session_meta['name'],
        '{{session_description}}': session_meta.get('description', 'No description'),
        '{{session_date}}': session_meta.get('date', 'N/A'),
        '{{bowler_name}}': bowler_meta['name'],
        '{{bowler_type}}': bowler_meta.get('type', 'Unknown'),
        '{{bowler_hand}}': bowler_meta.get('hand', 'Unknown'),
        '{{bowler_description}}': bowler_meta.get('description', 'No description'),
        '__MANIFEST_JSON__': json.dumps(manifest)
    }
    
    html = template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)
    
    # Write HTML
    html_path = report_dir / 'session_report.html'
    with open(html_path, 'w') as f:
        f.write(html)
    
    return html_path
