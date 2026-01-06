# services/upload.py

from pathlib import Path
import shutil
import json
from datetime import datetime, timezone
from werkzeug.utils import secure_filename

RUN_DIR = Path("data/run")
A_INPUTS = RUN_DIR / "a_inputs"
B_CLIPS = RUN_DIR / "b_clips"
C_KEYPOINTS = RUN_DIR / "c_keypoints"
RESULTS = RUN_DIR / "results"


def _utc_now_z():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def setup_dir():
    """Ensure data/run folder structure exists without deleting (avoids Windows file locking)."""
    # Create directories if they don't exist
    A_INPUTS.mkdir(parents=True, exist_ok=True)
    B_CLIPS.mkdir(parents=True, exist_ok=True)
    C_KEYPOINTS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "screenshots").mkdir(parents=True, exist_ok=True)
    (RESULTS / "videos").mkdir(parents=True, exist_ok=True)
    
    # Clear old event files from previous tagging sessions
    for event_file in A_INPUTS.glob("input_*_events.json"):
        try:
            event_file.unlink()
        except (PermissionError, OSError):
            pass  # Ignore if file is locked


def save_metadata_and_videos(
    bowler_name,
    bowler_hand,
    bowler_description,
    bowler_image,
    session_name,
    session_date,
    session_description,
    input_back_view,
    input_side_view
):
    """Save metadata.json + any provided uploads into data/run/a_inputs/."""

    # -------- Save optional bowler image --------
    bowler_image_path = None
    if bowler_image and bowler_image.filename:
        img_name = secure_filename(bowler_image.filename)
        ext = Path(img_name).suffix.lower()

        if ext in {".png", ".jpg", ".jpeg", ".webp"}:
            img_dst = A_INPUTS / f"bowler_image{ext}"
            bowler_image.save(img_dst)
            bowler_image_path = img_dst.as_posix()

    # -------- Save optional videos --------
    back_path = None
    back_original = None
    if input_back_view and input_back_view.filename:
        back_original = secure_filename(input_back_view.filename)
        back_dst = A_INPUTS / "input_back_view.mp4"
        input_back_view.save(back_dst)
        back_path = back_dst.as_posix()

    side_path = None
    side_original = None
    if input_side_view and input_side_view.filename:
        side_original = secure_filename(input_side_view.filename)
        side_dst = A_INPUTS / "input_side_view.mp4"
        input_side_view.save(side_dst)
        side_path = side_dst.as_posix()

    # -------- Write metadata.json --------
    metadata = {
        "createdAt": _utc_now_z(),
        "bowler": {
            "name": bowler_name,
            "hand": bowler_hand,
            "description": bowler_description,
            "imagePath": bowler_image_path
        },
        "session": {
            "name": session_name,
            "date": session_date,
            "description": session_description
        },
        "inputs": {
            "backView": {
                "provided": bool(back_path),
                "path": back_path,
                "originalFilename": back_original
            },
            "sideView": {
                "provided": bool(side_path),
                "path": side_path,
                "originalFilename": side_original
            }
        }
    }

    (A_INPUTS / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
