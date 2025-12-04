#src/cv/calculate_angles.py
'''--------------------------------------------------------------------------
This module contains functions to calculate angles between joints.

Inputs:
- keypoints_location: str : The location of the CSV file containing the extracted keypoints.
- output_angles_location: str : The location to save the calculated angles CSV file.

Outputs:
- The calculated angles saved at output_angles_location.
-------------------------------------------------------------------------'''

# module imports
import os
import csv
from typing import Dict, List, Tuple


# angle imports
import core.angles.front_knee_angle as front_knee_angle


# The main orchestration function used by the pipeline
def calculate_angles(back_exists: bool, side_exists: bool,
                     back_keypoints_location: str, side_keypoints_location: str,
                     back_output_angles_location: str, side_output_angles_location: str) -> None:
    """Wrapper that calculates angles for back and side views.

    For each view, if the corresponding exists flag is False the wrapper
    prints a short message and skips that view. Otherwise it delegates
    to `_calculate_angles_impl(...)` which returns a boolean indicating
    success. The wrapper prints minimal status messages and does not
    return status codes.
    """
    # Back view
    if not back_exists:
        print("NO Back View")
    else:
        print("Calculating angles for Back View...")
        try:
            ok = _calculate_angles_impl(back_keypoints_location, back_output_angles_location, view='back')
            if ok:
                print("Angles calculated: Back View")
            else:
                print("Error calculating angles: Back View")
        except Exception:
            print("Error calculating angles: Back View")

    # Side view
    if not side_exists:
        print("NO Side View")
    else:
        print("Calculating angles for Side View...")
        try:
            ok = _calculate_angles_impl(side_keypoints_location, side_output_angles_location, view='side')
            if ok:
                print("Angles calculated: Side View")
            else:
                print("Error calculating angles: Side View")
        except Exception:
            print("Error calculating angles: Side View")


def _calculate_angles_impl(keypoints_location: str, output_angles_location: str, view: str) -> bool:
    """Perform angle calculation for a single view. Returns True on success."""
    try:
        if not os.path.exists(keypoints_location):
            return False

        # read keypoints CSV into a frame->landmarks mapping
        frames: Dict[int, List[Tuple[float, float, float, float]]] = {}
        with open(keypoints_location, 'r', encoding='utf-8', newline='') as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            if header is None:
                return False

            # infer number of landmarks
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
            return False

        # prepare output CSV header
        angle_columns = []
        mode_side = False
        if view and view.lower().startswith('side'):
            mode_side = True
            angle_columns.append('front_knee_angle')

        # ensure output directory exists
        outdir = os.path.dirname(output_angles_location)
        if outdir and not os.path.exists(outdir):
            os.makedirs(outdir, exist_ok=True)

        with open(output_angles_location, 'w', encoding='utf-8', newline='') as outfh:
            writer = csv.writer(outfh)
            header = ['frame'] + angle_columns
            writer.writerow(header)

            # iterate frames in order
            for fi in sorted(frames.keys()):
                row = [fi]
                if mode_side:
                    try:
                        # defensive visibility check: if hip/knee/ankle not visible,
                        # assign a sentinel value -1.0 to indicate not-available.
                        lm_list = frames.get(fi)
                        # mediapipe left-side indices
                        HIP_IDX = 23
                        KNEE_IDX = 25
                        ANKLE_IDX = 27

                        def _vis(idx: int) -> float:
                            try:
                                return float(lm_list[idx][3]) if lm_list and idx < len(lm_list) else 0.0
                            except Exception:
                                return 0.0

                        # consider visible if visibility score > 0.2
                        if (_vis(HIP_IDX) <= 0.2) or (_vis(KNEE_IDX) <= 0.2) or (_vis(ANKLE_IDX) <= 0.2):
                            row.append(-1.0)
                        else:
                            ang = front_knee_angle.calculate_angle(frames, fi)
                            # if calculation somehow returned a near-360 reflex value while
                            # the landmarks were present, keep it; only use -1 when not visible.
                            row.append(float(ang))
                    except Exception:
                        row.append(-1.0)
                writer.writerow(row)

        return True

    except Exception:
        return False