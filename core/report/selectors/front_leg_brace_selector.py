# core/report/selectors/front_leg_brace_selector.py
"""Select frames for front_leg_brace metric panels."""

from typing import Dict, Any
from core.report.selectors.events_selector import RenderTarget


def select(key: str, analysis: Dict[str, Any]) -> RenderTarget:
    """Select a frame for a front_leg_brace metric panel.
    
    Args:
        key: "ffc", "release", or "max_diff"
        analysis: the analysis section from analysis_results.json
    
    Returns:
        RenderTarget with the resolved frame
    """
    try:
        flb_metrics = analysis.get("front_leg_brace", {}).get("metrics", {})
    except Exception:
        return RenderTarget(exists=False, view="side", frame=-1)
    
    # Map keys to metric names
    metric_map = {
        "ffc": "front_knee_angle_at_ffc",
        "release": "front_knee_angle_at_release",
        "max_diff": "max_difference_ffc_release",
    }
    
    metric_name = metric_map.get(key)
    if not metric_name:
        return RenderTarget(exists=False, view="side", frame=-1)
    
    metric_data = flb_metrics.get(metric_name, {})
    value = metric_data.get("value", {})
    
    try:
        frame = int(value.get("frame", -1))
        if frame < 0:
            return RenderTarget(exists=False, view="side", frame=-1)
        return RenderTarget(exists=True, view="side", frame=frame)
    except Exception:
        return RenderTarget(exists=False, view="side", frame=-1)
