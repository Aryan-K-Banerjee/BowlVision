'''--------------------------------------------------------------
Calculate Angles for a Single View

This module contains the implementation logic for calculating angles
from keypoints for a single view.

This is called by the orchestrator and:
- Loads keypoints from CSV
- Consults the angle directory
- Performs visibility checks
- Calls angle calculation functions
- Writes results to CSV
--------------------------------------------------------------'''

import os
import csv
from typing import Dict, List, Tuple
from pipeline.logic.step_4_calculate_angles.angle_directory import get_angles_for_view


def calculate_angles_for_view(keypoints_path: str, angles_path: str, view: str) -> None:
    """Calculate angles for a single view.
    
    Args:
        keypoints_path: Path to the keypoints CSV file
        angles_path: Path where angles CSV should be saved
        view: 'back' or 'side'
    """
    if not os.path.exists(keypoints_path):
        print(f"        ANGLES: Keypoints file not found: {keypoints_path}")
        return
    
    # Get angle calculations for this view from the directory
    angle_specs = get_angles_for_view(view)
    
    if not angle_specs:
        print(f"        ANGLES: No angles defined for {view} view")
        # Still create empty file for consistency
        _create_empty_angles_file(angles_path)
        return
    
    angle_names = [spec['name'] for spec in angle_specs]
    print(f"        ANGLES: Calculating {len(angle_specs)} angle(s): {', '.join(angle_names)}")
    
    try:
        # Read keypoints CSV into a frame→landmarks mapping
        frames: Dict[int, List[Tuple[float, float, float, float]]] = {}
        
        with open(keypoints_path, 'r', encoding='utf-8', newline='') as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            if header is None:
                print(f"        ANGLES: Empty keypoints file")
                return
            
            # Infer number of landmarks
            num_extra = max(0, len(header) - 2)
            num_landmarks = num_extra // 4 if num_extra >= 4 else 0
            
            for row in reader:
                if not row:
                    continue
                try:
                    frame_idx = int(float(row[0]))
                except Exception:
                    continue
                
                lm_vals: List[Tuple[float, float, float, float]] = []
                for i in range(num_landmarks):
                    base = 2 + i * 4
                    try:
                        x = float(row[base])
                        y = float(row[base + 1])
                        z = float(row[base + 2])
                        vis = float(row[base + 3])
                    except Exception:
                        x = y = z = vis = 0.0
                    lm_vals.append((x, y, z, vis))
                
                frames[frame_idx] = lm_vals
        
        if not frames:
            print(f"        ANGLES: No frames found in keypoints file")
            return
        
        print(f"        ANGLES: Loaded {len(frames)} frames")
        
        # Prepare output CSV
        outdir = os.path.dirname(angles_path)
        if outdir and not os.path.exists(outdir):
            os.makedirs(outdir, exist_ok=True)
        
        with open(angles_path, 'w', encoding='utf-8', newline='') as outfh:
            writer = csv.writer(outfh)
            header = ['frame'] + angle_names
            writer.writerow(header)
            
            # Iterate frames in order
            frames_calculated = 0
            for fi in sorted(frames.keys()):
                row = [fi]
                
                # Calculate each angle for this frame
                for spec in angle_specs:
                    angle_func = spec['function']
                    visibility_check = spec.get('visibility_check', [])
                    
                    # Check if required landmarks are visible
                    lm_list = frames.get(fi)
                    landmarks_visible = True
                    
                    if visibility_check and lm_list:
                        for lm_idx, threshold in visibility_check:
                            try:
                                vis = float(lm_list[lm_idx][3]) if lm_idx < len(lm_list) else 0.0
                                if vis <= threshold:
                                    landmarks_visible = False
                                    break
                            except Exception:
                                landmarks_visible = False
                                break
                    
                    # Calculate angle or use sentinel value
                    if not landmarks_visible:
                        angle = -1.0  # Sentinel value for not visible
                    else:
                        try:
                            angle = angle_func(frames, fi)
                        except Exception as e:
                            print(f"        ANGLES: Error calculating {spec['name']} at frame {fi}: {e}")
                            angle = -1.0
                    
                    row.append(float(angle))
                
                writer.writerow(row)
                frames_calculated += 1
        
        print(f"        ANGLES: Calculated angles for {frames_calculated} frames")
        
    except Exception as e:
        print(f"        ANGLES: Error processing {view} view: {e}")


def _create_empty_angles_file(angles_path: str) -> None:
    """Create an empty angles file with just frame column."""
    outdir = os.path.dirname(angles_path)
    if outdir and not os.path.exists(outdir):
        os.makedirs(outdir, exist_ok=True)
    
    with open(angles_path, 'w', encoding='utf-8', newline='') as outfh:
        writer = csv.writer(outfh)
        writer.writerow(['frame'])
