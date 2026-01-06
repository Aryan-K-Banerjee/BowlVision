"""
Progress Service

Handles pipeline execution and log streaming via Server-Sent Events (SSE).
"""

import sys
import json
import time
import threading
import queue
from pathlib import Path
from typing import Generator

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class PipelineRunner:
    """
    Manages pipeline execution in a background thread with log streaming.
    """
    
    def __init__(self):
        self.log_queue = queue.Queue()
        self.status = 'idle'  # idle, running, success, error
        self.current_step = -1
        self.message = ''
        self.thread = None
        self.is_running = False
    
    def start(self):
        """Start the pipeline in a background thread."""
        if self.is_running:
            return False
        
        self.is_running = True
        self.status = 'running'
        self.current_step = -1
        self.message = 'Starting pipeline...'
        
        # Clear any old logs
        while not self.log_queue.empty():
            try:
                self.log_queue.get_nowait()
            except queue.Empty:
                break
        
        self.thread = threading.Thread(target=self._run_pipeline, daemon=True)
        self.thread.start()
        return True
    
    def _run_pipeline(self):
        """Run the pipeline and send logs to the queue."""
        try:
            # Import here to avoid circular imports
            from pipeline.run_pipeline import run_pipeline
            
            def log_callback(message: str, level: int = 1, log_type: str = 'info'):
                """Send logs to the queue."""
                self.log_queue.put({
                    'type': 'log',
                    'message': message,
                    'level': level,
                    'log_type': log_type
                })
            
            # Run the pipeline generator
            for update in run_pipeline(log_callback):
                if update['type'] == 'status':
                    self.status = update['status']
                    self.current_step = update.get('step', self.current_step)
                    self.message = update.get('message', '')
                    
                    # Send status update to queue
                    self.log_queue.put(update)
            
            self.is_running = False
            
        except Exception as e:
            self.status = 'error'
            self.message = str(e)
            self.log_queue.put({
                'type': 'log',
                'message': f"✖ Pipeline error: {e}",
                'level': 1,
                'log_type': 'error'
            })
            self.log_queue.put({
                'type': 'status',
                'status': 'error',
                'step': self.current_step,
                'message': str(e)
            })
            self.is_running = False
    
    def get_logs(self, timeout: float = 0.5) -> list:
        """Get any pending logs from the queue."""
        logs = []
        try:
            while True:
                log = self.log_queue.get(timeout=timeout if not logs else 0.01)
                logs.append(log)
        except queue.Empty:
            pass
        return logs
    
    def get_state(self) -> dict:
        """Get current pipeline state."""
        return {
            'status': self.status,
            'step': self.current_step,
            'message': self.message,
            'is_running': self.is_running
        }


# Global pipeline runner instance
_runner = None


def get_runner() -> PipelineRunner:
    """Get or create the global pipeline runner."""
    global _runner
    if _runner is None:
        _runner = PipelineRunner()
    return _runner


def start_pipeline() -> dict:
    """Start the pipeline and return initial state."""
    runner = get_runner()
    started = runner.start()
    return {
        'started': started,
        'state': runner.get_state()
    }


def get_pipeline_state() -> dict:
    """Get current pipeline state."""
    runner = get_runner()
    return runner.get_state()


def stream_logs() -> Generator[str, None, None]:
    """
    Generator that yields SSE-formatted log messages.
    Use this for the /api/pipeline/stream endpoint.
    """
    runner = get_runner()
    
    # Send initial connection message
    yield f"data: {json.dumps({'type': 'connected', 'state': runner.get_state()})}\n\n"
    
    # Stream logs until pipeline finishes
    while runner.is_running or not runner.log_queue.empty():
        logs = runner.get_logs(timeout=0.5)
        for log in logs:
            yield f"data: {json.dumps(log)}\n\n"
        
        # Small delay to prevent busy loop
        if not logs:
            time.sleep(0.1)
    
    # Send final state
    yield f"data: {json.dumps({'type': 'complete', 'state': runner.get_state()})}\n\n"
