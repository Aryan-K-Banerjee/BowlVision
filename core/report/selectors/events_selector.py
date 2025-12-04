# core/report/selectors/events_selector.py
"""Select frames for event-based panels (jump, bfc, ffc, release)."""

from typing import Dict, Any, Optional


class RenderTarget:
    """Represents a resolved render target for a panel."""
    def __init__(self, exists: bool, view: str, frame: int):
        self.exists = exists
        self.view = view
        self.frame = frame
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "exists": self.exists,
            "view": self.view,
            "frame": self.frame,
        }


def select(view: str, event_key: str, videos_data: Dict[str, Any]) -> RenderTarget:
    """Select a frame for an event-based panel.
    
    Args:
        view: "back" or "side"
        event_key: "jump", "bfc", "ffc", or "release"
        videos_data: the videos_data section from analysis_results.json
    
    Returns:
        RenderTarget with exists=False if view missing, else the event frame
    """
    view_key = f"{view}_view"
    view_data = videos_data.get(view_key, {})
    
    if not view_data.get("exists", False):
        return RenderTarget(exists=False, view=view, frame=-1)
    
    events = view_data.get("events", {})
    event_data = events.get(event_key)
    
    if not event_data:
        return RenderTarget(exists=False, view=view, frame=-1)
    
    try:
        frame = int(event_data.get("frame", -1))
        if frame < 0:
            return RenderTarget(exists=False, view=view, frame=-1)
        return RenderTarget(exists=True, view=view, frame=frame)
    except Exception:
        return RenderTarget(exists=False, view=view, frame=-1)
