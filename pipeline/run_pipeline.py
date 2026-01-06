"""
This is the main run_pipeline script.
It runs directly on the data/run folder.

The pipeline supports streaming logs via a callback function for real-time
updates to the Progress Page.
"""

import sys
from pathlib import Path
from typing import Callable, Generator, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import step modules (using importlib for numbered filenames)
import importlib.util

def _import_step(step_name: str):
    """Import a pipeline step module by filename."""
    step_path = Path(__file__).parent / 'steps' / f'{step_name}.py'
    spec = importlib.util.spec_from_file_location(step_name, step_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load step modules
step_0 = _import_step('0_verify_data')
step_1 = _import_step('1_preprocess')
step_2 = _import_step('2_extract_keypoints')
step_4_2 = _import_step('4.2_generate_videos')


SESSION_DIR = 'data/run/'


def run_pipeline(log: Optional[Callable[[str, int, str], None]] = None) -> Generator[dict, None, None]:
    """
    Run the BowlVision pipeline with streaming log output.
    
    Args:
        log: Optional logging callback with signature (message, level, type)
             level: 0 = major step, 1 = sub-step, 2 = detail
             type: 'info', 'success', 'warning', 'error'
    
    Yields:
        dict with pipeline state updates:
            - type: 'log' | 'status'
            - For 'log': message, level, log_type
            - For 'status': status ('running', 'success', 'error'), step, message
    """
    logs = []
    
    def collect_log(message: str, level: int = 1, log_type: str = 'info'):
        """Collect logs and optionally forward to callback."""
        log_entry = {
            'type': 'log',
            'message': message,
            'level': level,
            'log_type': log_type
        }
        logs.append(log_entry)
        if log:
            log(message, level, log_type)
    
    # Initialize
    collect_log("> Initializing pipeline…", 0, 'info')
    
    yield {'type': 'status', 'status': 'running', 'step': 0, 'message': 'Verifying inputs'}
    
    # Step 0: Verify data + videos
    result = step_0.verify_data(SESSION_DIR, collect_log)
    
    if not result['can_proceed']:
        yield {
            'type': 'status', 
            'status': 'error', 
            'step': 0, 
            'message': 'Verification failed - missing required files'
        }
        return
    
    # Store verification result for later steps
    available_views = result['available_views']
    
    # Step 1: Preprocess videos
    collect_log("", 0, 'info')  # Empty line for spacing
    yield {'type': 'status', 'status': 'running', 'step': 1, 'message': 'Preprocessing videos'}
    
    preprocess_result = step_1.preprocess(SESSION_DIR, collect_log)
    
    if not preprocess_result['success']:
        yield {
            'type': 'status',
            'status': 'error',
            'step': 1,
            'message': 'Preprocessing failed'
        }
        return
    
    # Step 2: Extract keypoints
    collect_log("", 0, 'info')  # Empty line for spacing
    yield {'type': 'status', 'status': 'running', 'step': 2, 'message': 'Extracting keypoints'}
    
    keypoints_result = step_2.extract_keypoints(SESSION_DIR, collect_log)
    
    if not keypoints_result['success']:
        yield {
            'type': 'status',
            'status': 'error',
            'step': 2,
            'message': 'Keypoint extraction failed'
        }
        return
    
    # Step 4.2: Generate videos (validation)
    collect_log("", 0, 'info')  # Empty line for spacing
    yield {'type': 'status', 'status': 'running', 'step': 4, 'message': 'Generating validation videos'}
    
    videos_result = step_4_2.generate_videos(SESSION_DIR, collect_log)
    
    if not videos_result['success']:
        yield {
            'type': 'status',
            'status': 'error',
            'step': 4,
            'message': 'Video generation failed'
        }
        return
    
    # Success - Steps 1, 2, and 4.2 complete
    collect_log("", 0, 'info')  # Empty line
    collect_log("> Pipeline complete (Steps 0, 1, 2, 4.2)", 0, 'info')
    collect_log("- Steps 3, 4.1 not yet implemented", 1, 'info')
    
    yield {
        'type': 'status', 
        'status': 'success', 
        'step': 4, 
        'message': 'Steps 1, 2, 4.2 complete'
    }


# Legacy function for backwards compatibility
def run_pipeline_sync():
    """
    Synchronous version that prints to console.
    Kept for backwards compatibility with direct script execution.
    """
    def print_log(message: str, level: int = 1, log_type: str = 'info'):
        indent = "  " * level
        print(f"{indent}{message}")
    
    for update in run_pipeline(print_log):
        if update['type'] == 'status':
            print(f"\n[STATUS] {update['status']}: {update['message']}")


if __name__ == '__main__':
    run_pipeline_sync()