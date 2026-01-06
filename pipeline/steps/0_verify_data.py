"""
Step 0: Verify Inputs

This step verifies that the required documents exist under data/run/a_inputs/
and determines how many videos are available for processing based on metadata.json.

The module should be written with a simple top-level function which calls other
functions to do the business logic.
"""

import json
from pathlib import Path
from typing import Callable, Optional


def verify_data(session_dir: str, log: Optional[Callable[[str, int, str], None]] = None) -> dict:
    """
    Main verification function.
    
    Args:
        session_dir: Path to the session directory (e.g., 'data/run/')
        log: Optional logging callback with signature (message, level, type)
             level: 0 = major step, 1 = sub-step, 2 = detail
             type: 'info', 'success', 'warning', 'error'
    
    Returns:
        dict with keys:
            - available_views: list of valid views ['back', 'side']
            - missing_files: list of missing expected file paths
            - can_proceed: boolean indicating if pipeline can continue
            - video_count: number of views to process (0-2)
    """
    # Default no-op logger if none provided
    if log is None:
        log = lambda msg, level=1, type='info': None
    
    log("> Step 0: Verify inputs", 0, 'info')
    
    inputs_dir = Path(session_dir) / 'a_inputs'
    
    result = {
        'available_views': [],
        'missing_files': [],
        'can_proceed': False,
        'video_count': 0
    }
    
    # Check metadata.json first
    metadata_path = inputs_dir / 'metadata.json'
    metadata = _check_metadata(metadata_path, log)
    
    if metadata is None:
        log("✖ Cannot proceed. Missing required files.", 1, 'error')
        log(str(metadata_path), 2, 'error')
        return result
    
    log("✓ metadata.json found", 1, 'success')
    
    # Check each view based on metadata
    views_to_check = [
        ('back', 'backView'),
        ('side', 'sideView')
    ]
    
    for view_name, metadata_key in views_to_check:
        view_result = _check_view(
            view_name, 
            metadata_key, 
            metadata, 
            inputs_dir, 
            log
        )
        
        if view_result['required']:
            if view_result['valid']:
                result['available_views'].append(view_name)
            else:
                result['missing_files'].extend(view_result['missing'])
    
    # Determine if we can proceed
    result['video_count'] = len(result['available_views'])
    result['can_proceed'] = result['video_count'] > 0 and len(result['missing_files']) == 0
    
    # Final summary
    if result['can_proceed']:
        log("✓ Verification complete", 1, 'success')
        log(f"- Videos to process: {result['video_count']}", 1, 'info')
    else:
        log("✖ Cannot proceed. Missing required files.", 1, 'error')
        for missing in result['missing_files']:
            log(str(missing), 2, 'error')
    
    return result


def _check_metadata(metadata_path: Path, log: Callable) -> Optional[dict]:
    """
    Check if metadata.json exists and is valid JSON.
    
    Returns:
        Parsed metadata dict, or None if missing/invalid
    """
    if not metadata_path.exists():
        log("✖ metadata.json not found", 1, 'error')
        return None
    
    try:
        with open(metadata_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log(f"✖ metadata.json is invalid: {e}", 1, 'error')
        return None


def _check_view(
    view_name: str, 
    metadata_key: str, 
    metadata: dict, 
    inputs_dir: Path,
    log: Callable
) -> dict:
    """
    Check if a view's required files exist.
    
    Returns:
        dict with keys:
            - required: bool - whether this view is required by metadata
            - valid: bool - whether all required files exist
            - missing: list - paths of missing files
    """
    result = {
        'required': False,
        'valid': False,
        'missing': []
    }
    
    # Check if view is provided in metadata
    inputs_config = metadata.get('inputs', {})
    view_config = inputs_config.get(metadata_key, {})
    
    if not view_config.get('provided', False):
        log(f"- {view_name.capitalize()} view not required by metadata", 1, 'info')
        return result
    
    result['required'] = True
    log(f"- {view_name.capitalize()} view required by metadata", 1, 'info')
    
    # Check for video file
    video_path = inputs_dir / f'input_{view_name}_view.mp4'
    if video_path.exists():
        log(f"  input_{view_name}_view.mp4 found", 2, 'success')
    else:
        log(f"  input_{view_name}_view.mp4 missing", 2, 'error')
        result['missing'].append(str(video_path))
    
    # Check for events file
    events_path = inputs_dir / f'input_{view_name}_events.json'
    if events_path.exists():
        log(f"  input_{view_name}_events.json found", 2, 'success')
    else:
        log(f"  input_{view_name}_events.json missing", 2, 'error')
        result['missing'].append(str(events_path))
    
    result['valid'] = len(result['missing']) == 0
    return result