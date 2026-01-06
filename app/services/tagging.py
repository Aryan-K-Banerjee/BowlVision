# services/tagging.py

from pathlib import Path
import json
import cv2

# Directory constants - resolve from project root (parent of app directory)
PROJECT_ROOT = Path(__file__).parent.parent.parent
RUN_DIR = PROJECT_ROOT / "data" / "run"
A_INPUTS = RUN_DIR / "a_inputs"
CACHE_DIR = A_INPUTS / "cache"

# Event order (strict sequence)
EVENT_ORDER = ["Jump", "BFC", "FFC", "Release"]


def get_available_views():
    """
    Check which views are available based on metadata.json.
    Returns dict with 'back' and 'side' booleans.
    """
    metadata_path = A_INPUTS / "metadata.json"
    if not metadata_path.exists():
        return {"back": False, "side": False}
    
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    inputs = metadata.get("inputs", {})
    return {
        "back": inputs.get("backView", {}).get("provided", False),
        "side": inputs.get("sideView", {}).get("provided", False)
    }


def get_video_path(view):
    """Get the video file path for a given view."""
    if view == "back":
        return A_INPUTS / "input_back_view.mp4"
    elif view == "side":
        return A_INPUTS / "input_side_view.mp4"
    return None


def get_cache_dir(view):
    """Get the frame cache directory for a given view."""
    return CACHE_DIR / view


def ensure_frame_cache(view):
    """
    Extract frames from video if cache doesn't exist.
    Uses OpenCV (cv2) for frame extraction.
    Returns the frame count.
    """
    video_path = get_video_path(view)
    cache_dir = get_cache_dir(view)
    
    if not video_path or not video_path.exists():
        return 0
    
    # Check if cache already exists and has frames
    if cache_dir.exists():
        existing_frames = list(cache_dir.glob("frame_*.jpg"))
        if existing_frames:
            return len(existing_frames)
    
    # Create cache directory
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Open video and extract frames
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return 0
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_filename = cache_dir / f"frame_{frame_count:05d}.jpg"
        cv2.imwrite(str(frame_filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_count += 1
    
    cap.release()
    return frame_count


def get_frame_count(view):
    """Get the total number of frames for a view."""
    cache_dir = get_cache_dir(view)
    if not cache_dir.exists():
        return 0
    return len(list(cache_dir.glob("frame_*.jpg")))


def get_frame_path(view, frame_num):
    """Get the path to a specific frame image."""
    cache_dir = get_cache_dir(view)
    frame_path = cache_dir / f"frame_{frame_num:05d}.jpg"
    if frame_path.exists():
        return frame_path
    return None


def get_existing_events(view):
    """
    Load existing events for a view if they exist.
    Returns dict with event names as keys and frame numbers as values.
    """
    if view == "back":
        events_path = A_INPUTS / "input_back_events.json"
    elif view == "side":
        events_path = A_INPUTS / "input_side_events.json"
    else:
        return None
    
    if not events_path.exists():
        return None
    
    with open(events_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data.get("events", None)


def save_events(view, events):
    """
    Save tagged events for a view.
    events: dict with keys Jump, BFC, FFC, Release and frame number values
    """
    if view == "back":
        events_path = A_INPUTS / "input_back_events.json"
    elif view == "side":
        events_path = A_INPUTS / "input_side_events.json"
    else:
        return False
    
    data = {
        "view": view,
        "events": events
    }
    
    with open(events_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    return True


def is_tagging_complete():
    """
    Check if all required tagging is complete.
    Returns True if all existing views have their events tagged.
    """
    views = get_available_views()
    
    for view_name, is_available in views.items():
        if is_available:
            events = get_existing_events(view_name)
            if not events:
                return False
            # Check all 4 events are present
            for event in EVENT_ORDER:
                if event not in events or events[event] is None:
                    return False
    
    return True


def get_tagging_state():
    """
    Get the complete tagging state for the frontend.
    Returns dict with view availability, frame counts, and existing tags.
    """
    views = get_available_views()
    state = {
        "views": {},
        "eventOrder": EVENT_ORDER
    }
    
    for view_name, is_available in views.items():
        if is_available:
            # Ensure frames are cached
            frame_count = ensure_frame_cache(view_name)
            existing_events = get_existing_events(view_name)
            
            state["views"][view_name] = {
                "available": True,
                "frameCount": frame_count,
                "events": existing_events or {}
            }
        else:
            state["views"][view_name] = {
                "available": False,
                "frameCount": 0,
                "events": {}
            }
    
    state["complete"] = is_tagging_complete()
    return state
