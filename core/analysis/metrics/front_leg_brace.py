#core/analysis/metrics/front_leg_brace.py

"""Front leg brace metric extraction.

This module exposes a single function `extract_front_leg_brace` which accepts
angle data (mapping frame->angle) and event data (dict from events JSON) and
returns a dictionary containing the requested metrics. The function is
designed to be pure (no file IO) so the orchestrator (`extract_metrics`) can
call it and write results centrally.

Metric fields produced:
  - front_knee_angle_at_ffc
  - front_knee_angle_at_release
  - difference_ffc_release
  - max_difference_ffc_release
  - frame_of_max_difference

If required data is missing the function uses -1.0 as a sentinel value to
indicate not-available.
"""

from typing import Dict, Any


def extract_front_leg_brace(angles_by_frame: Dict[int, float], events: Dict[str, Any]) -> Dict[str, Any]:
    """Extract front leg brace metrics from angles and events.

    angles_by_frame: mapping frame_index -> front_knee_angle (float). Missing
      or unavailable frames should use a sentinel (e.g. -1.0).
    events: the contents of the events JSON (the 'video'->'events' mapping is
      expected or the function should be passed that mapping directly).

    Returns a dict with the structure described in the module docstring.
    """
    # Helper to safely read angles; treat None or <= -1 as not available
    def _angle_at(frame: int):
        try:
            val = angles_by_frame.get(int(frame))
            if val is None:
                return None
            # sentinel for not-visible is -1.0 (as used elsewhere)
            if isinstance(val, (int, float)) and float(val) <= -1.0:
                return None
            return float(val)
        except Exception:
            return None

    # events may be the full JSON or the inner mapping
    ev = events
    if isinstance(events, dict) and 'video' in events:
        ev = events.get('video', {}).get('events', {})

    ffc_ev = ev.get('ffc') if ev else None
    release_ev = ev.get('release') if ev else None

    # default sentinel
    SENTINEL = -1.0

    # extract frame indices
    try:
        ffc_frame = int(ffc_ev.get('frame')) if ffc_ev and 'frame' in ffc_ev else None
    except Exception:
        ffc_frame = None
    try:
        release_frame = int(release_ev.get('frame')) if release_ev and 'frame' in release_ev else None
    except Exception:
        release_frame = None

    # retrieve angles at those frames
    ffc_angle = _angle_at(ffc_frame) if ffc_frame is not None else None
    release_angle = _angle_at(release_frame) if release_frame is not None else None

    # compute simple metrics
    if ffc_angle is None:
        ffc_val = SENTINEL
    else:
        ffc_val = float(ffc_angle)

    if release_angle is None:
        release_val = SENTINEL
    else:
        release_val = float(release_angle)

    if ffc_angle is None or release_angle is None:
        diff_val = SENTINEL
    else:
        diff_val = float(release_angle - ffc_angle)

    # compute max difference from ffc within the interval [ffc, release]
    max_diff = -1.0
    max_diff_frame = -1
    if ffc_frame is not None and release_frame is not None and ffc_angle is not None:
        start = min(ffc_frame, release_frame)
        end = max(ffc_frame, release_frame)
        for fr in range(start, end + 1):
            a = _angle_at(fr)
            if a is None:
                continue
            d = abs(a - ffc_angle)
            if d > max_diff:
                max_diff = d
                max_diff_frame = fr

    if max_diff_frame == -1:
        max_diff_val = SENTINEL
        max_diff_frame_val = -1
    else:
        max_diff_val = float(max_diff)
        max_diff_frame_val = int(max_diff_frame)

    # determine knee angle at max difference frame if available
    try:
        if max_diff_frame_val != -1:
            knee_angle_at_max = _angle_at(max_diff_frame_val)
            knee_angle_val = knee_angle_at_max if knee_angle_at_max is not None else SENTINEL
        else:
            knee_angle_val = SENTINEL
    except Exception:
        knee_angle_val = SENTINEL

    # Build the structured output where each metric includes angle and frame
    def _wrap(angle_val, frame_val):
        return {"angle": (angle_val if angle_val is not None else SENTINEL), "frame": (frame_val if frame_val is not None else -1)}

    ffc_frame_out = ffc_frame if ffc_frame is not None else -1
    release_frame_out = release_frame if release_frame is not None else -1

    return {
        "front_leg_brace": {
            "front_knee_angle_at_ffc": _wrap(ffc_val, ffc_frame_out),
            "front_knee_angle_at_release": _wrap(release_val, release_frame_out),
            "difference_ffc_release": _wrap(diff_val, release_frame_out if release_frame_out != -1 else ffc_frame_out),
            "max_difference_ffc_release": {
                "angle": (max_diff_val if max_diff_val is not None else SENTINEL),
                "knee_angle": (knee_angle_val if knee_angle_val is not None else SENTINEL),
                "frame": (max_diff_frame_val if max_diff_frame_val is not None else -1),
            },
        }
    }

def analyze_front_leg_brace(extracted_metrics: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze front leg brace metrics against rules.

    Takes extracted metrics and rules YAML data, evaluates each metric
    against thresholds, and returns a structured analysis including:
      - original metric values
      - qualitative assessment (ideal/good/okay/poor)
      - threshold descriptions

    Args:
        extracted_metrics: the full extracted_metrics dict (with 'extracted_metrics' top key)
        rules: the loaded rules.yaml dict (with 'metrics' top key)

    Returns:
        A dict containing the analyzed front_leg_brace with assessments.
    """
    # Helper to evaluate a single metric value against thresholds
    def _evaluate_metric(value: float, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Return qualitative assessment and description for a metric value."""
        if value <= -1.0:
            return {
                "assessment": "unavailable",
                "description": "Data not available",
            }

        compare = rule.get('compare', 'greater_equal')
        thresholds = rule.get('thresholds', {})

        # Extract threshold values
        ideal_thresh = thresholds.get('ideal', {})
        good_thresh = thresholds.get('good', {})
        okay_thresh = thresholds.get('okay', {})
        poor_thresh = thresholds.get('poor', {})

        ideal_val = ideal_thresh.get('value', 0)
        good_val = good_thresh.get('value', 0)
        okay_val = okay_thresh.get('value', 0)

        if compare == 'greater_equal':
            # Higher is better
            if value >= ideal_val:
                return {
                    "assessment": "ideal",
                    "description": ideal_thresh.get('description', 'Ideal'),
                }
            elif value >= good_val:
                return {
                    "assessment": "good",
                    "description": good_thresh.get('description', 'Good'),
                }
            elif value >= okay_val:
                return {
                    "assessment": "okay",
                    "description": okay_thresh.get('description', 'Okay'),
                }
            else:
                return {
                    "assessment": "poor",
                    "description": poor_thresh.get('description', 'Poor'),
                }
        else:  # less_equal
            # Lower is better
            if value <= ideal_val:
                return {
                    "assessment": "ideal",
                    "description": ideal_thresh.get('description', 'Ideal'),
                }
            elif value <= good_val:
                return {
                    "assessment": "good",
                    "description": good_thresh.get('description', 'Good'),
                }
            elif value <= okay_val:
                return {
                    "assessment": "okay",
                    "description": okay_thresh.get('description', 'Okay'),
                }
            else:
                return {
                    "assessment": "poor",
                    "description": poor_thresh.get('description', 'Poor'),
                }

    # Extract the front_leg_brace metrics
    try:
        flb_metrics = extracted_metrics.get('extracted_metrics', {}).get('front_leg_brace', {})
    except Exception:
        flb_metrics = {}

    if not flb_metrics:
        return {
            "front_leg_brace": {
                "error": "No front_leg_brace metrics found in extracted_metrics"
            }
        }

    # Load rules for front_leg_brace
    try:
        flb_rules = rules.get('metrics', {}).get('front_leg_brace', {}).get('rules', {})
    except Exception:
        flb_rules = {}

    if not flb_rules:
        return {
            "front_leg_brace": {
                "error": "No rules found for front_leg_brace"
            }
        }

    # Build the analysis result
    analysis = {}

    # Analyze each metric
    metric_keys = [
        'front_knee_angle_at_ffc',
        'front_knee_angle_at_release',
        'difference_ffc_release',
        'max_difference_ffc_release',
    ]

    for key in metric_keys:
        metric_data = flb_metrics.get(key, {})
        rule = flb_rules.get(key, {})

        if not metric_data or not rule:
            analysis[key] = {
                "value": metric_data,
                "assessment": "unavailable",
                "description": "Data or rule not available",
            }
            continue

        # Get the angle value (for max_difference it's the 'angle' field, not 'knee_angle')
        angle_val = metric_data.get('angle', -1.0)
        
        # Evaluate
        eval_result = _evaluate_metric(angle_val, rule)

        # Build result including original data + assessment
        analysis[key] = {
            "value": metric_data,
            "assessment": eval_result['assessment'],
            "description": eval_result['description'],
        }

    # Compute an overall assessment for front_leg_brace
    # Simple heuristic: if any metric is 'poor', overall is poor; if all ideal, overall is ideal, etc.
    assessments = [analysis[k].get('assessment', 'unavailable') for k in metric_keys if k in analysis]
    
    if 'poor' in assessments:
        overall = 'poor'
    elif 'okay' in assessments:
        overall = 'okay'
    elif 'good' in assessments:
        overall = 'good'
    elif all(a == 'ideal' for a in assessments):
        overall = 'ideal'
    else:
        overall = 'unavailable'

    return {
        "front_leg_brace": {
            "overall_assessment": overall,
            "metrics": analysis,
        }
    }