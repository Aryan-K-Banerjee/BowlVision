#core/analysis/extract_metrics.py
"""Orchestrate extraction of metrics from angles and events.

This module is responsible for calling individual metric extractors and
aggregating their results into a single `extracted_metrics.json` file.

The pipeline calls `extract_metrics(back_exists, side_exists, back_angles_location,
side_angles_location, back_events_location, side_events_location, extracted_metrics_location)`
so this wrapper will check availability flags and only run metrics for
available views. Individual metric modules are pure functions that accept
data (no file IO) and return dicts which are merged into the final output.
"""

import os
import json
import csv
from typing import Dict, Any

from core.analysis.metrics import front_leg_brace


def _read_angles_csv_as_map(path: str) -> Dict[int, float]:
    """Read an angles CSV and return a mapping frame->front_knee_angle.

    If the CSV or column is missing the function returns an empty dict. Rows
    with missing values will store the sentinel -1.0 (consistent with other
    modules).
    """
    out: Dict[int, float] = {}
    try:
        if not os.path.exists(path):
            return out
        with open(path, 'r', encoding='utf-8', newline='') as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            if not header:
                return out
            # find front_knee_angle column (fallback to second column)
            try:
                idx = header.index('front_knee_angle')
            except Exception:
                # fallback: assume second column is the angle
                idx = 1 if len(header) > 1 else None

            if idx is None:
                return out

            for row in reader:
                if not row:
                    continue
                try:
                    frame = int(float(row[0]))
                except Exception:
                    continue
                try:
                    val = float(row[idx])
                except Exception:
                    val = -1.0
                out[frame] = val
    except Exception:
        return {}
    return out


def _read_events_json(path: str) -> Dict[str, Any]:
    try:
        if not os.path.exists(path):
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # return the inner 'events' mapping if present
            if isinstance(data, dict) and 'video' in data:
                return data.get('video', {}).get('events', {})
            if isinstance(data, dict) and 'events' in data:
                return data.get('events', {})
            return data
    except Exception:
        return {}


def extract_metrics(back_exists: bool, side_exists: bool,
                    back_angles_location: str, side_angles_location: str,
                    back_events_location: str, side_events_location: str,
                    extracted_metrics_location: str) -> None:
    """Top-level orchestrator called by the pipeline.

    Checks view availability, runs view-specific metrics, aggregates results
    and writes `extracted_metrics_location`.
    """
    metrics: Dict[str, Any] = {"extracted_metrics": {}}

    # Side-view metrics (front_leg_brace) - only relevant to side view
    if not side_exists:
        metrics["extracted_metrics"]["front_leg_brace"] = {"note": "Side view not available"}
    else:
        angles_map = _read_angles_csv_as_map(side_angles_location)
        events_map = _read_events_json(side_events_location)
        # call metric extractor
        try:
            res = front_leg_brace.extract_front_leg_brace(angles_map, events_map)
            # res is expected to be {'front_leg_brace': {...}}
            metrics["extracted_metrics"].update(res)
        except Exception:
            metrics["extracted_metrics"]["front_leg_brace"] = {"error": "failed to compute metric"}

    # Back-view metrics can be added here in future; for now record note
    if not back_exists:
        metrics["extracted_metrics"]["back_view"] = {"note": "Back view not available"}

    # ensure output dir exists and write file
    try:
        out_dir = os.path.dirname(extracted_metrics_location)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        with open(extracted_metrics_location, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=4)
    except Exception:
        # best-effort: if writing fails we don't raise to keep pipeline stable
        pass

    print(f"Extracted metrics written to: {extracted_metrics_location}")


