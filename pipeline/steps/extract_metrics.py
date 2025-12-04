'''--------------------------------------------------------------
Extract Metrics Orchestrator

This module orchestrates the extraction of all metrics from the
calculated angles and events.

Architecture:
1. Pipeline calls this orchestrator
2. Orchestrator consults metrics_directory for which metrics to extract
3. Each metric function handles its own data access and calculation

This design allows new metrics to be added without modifying this file:
- Create the metric logic in pipeline/logic/metrics/
- Register it in metrics_directory.py
- It will automatically be extracted

All metrics are aggregated into a single extracted_metrics.json file.
--------------------------------------------------------------'''

import os
import json
from pipeline.logic.step_5_extract_metrics.metrics_directory import get_all_metrics
from pipeline import location_constants as lc


def extract_metrics(session_dir: str, back_view_exists: bool, side_view_exists: bool):
    """Orchestrate extraction of all metrics.
    
    Args:
        session_dir: Path to the session directory
        back_view_exists: Whether the back view video exists
        side_view_exists: Whether the side view video exists
    """
    print("    EXTRACT_METRICS: Starting metrics extraction...")
    
    # Get all registered metrics from the directory
    all_metrics = get_all_metrics()
    
    if not all_metrics:
        print("    EXTRACT_METRICS: No metrics registered in directory")
        return
    
    print(f"    EXTRACT_METRICS: Found {len(all_metrics)} metric(s) to extract")
    
    # Initialize result structure
    result = {"extracted_metrics": {}}
    
    # Extract each metric
    for metric_spec in all_metrics:
        metric_name = metric_spec['name']
        metric_func = metric_spec['function']
        
        print(f"    EXTRACT_METRICS: Extracting {metric_name}...")
        
        try:
            # Call the metric function (it handles its own data access)
            metric_data = metric_func(session_dir)
            
            # Merge into result
            if isinstance(metric_data, dict):
                result["extracted_metrics"].update(metric_data)
            else:
                print(f"    EXTRACT_METRICS: Warning - {metric_name} returned invalid data")
        
        except Exception as e:
            print(f"    EXTRACT_METRICS: Error extracting {metric_name}: {e}")
            result["extracted_metrics"][metric_name] = {"error": str(e)}
    
    # Write results to JSON
    output_path = session_dir + lc.extracted_metrics
    _write_metrics_json(output_path, result)
    
    print("    EXTRACT_METRICS: Metrics extraction complete")


def _write_metrics_json(path: str, data: dict) -> None:
    """Write metrics data to JSON file."""
    try:
        # Ensure output directory exists
        out_dir = os.path.dirname(path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        
        # Write JSON with nice formatting
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        
        print(f"    EXTRACT_METRICS: Wrote metrics to {path}")
    
    except Exception as e:
        print(f"    EXTRACT_METRICS: Error writing metrics file: {e}")