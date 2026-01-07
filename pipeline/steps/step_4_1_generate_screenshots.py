"""
Step 4.1: Generate Screenshots

Reads the screenshot specs from results.json and generates all screenshot images.
"""

from pathlib import Path
from pipeline.screenshots import generate_screenshots


def run_step_4_1_generate_screenshots(session_dir: str, generator=None):
    """Generate all screenshots from results.json specs.
    
    Args:
        session_dir: Path to session directory
        generator: Optional SSE generator for progress updates
        
    Returns:
        List of generated screenshot paths
    """
    session_dir = Path(session_dir)
    results_json_path = session_dir / 'results' / 'results.json'
    
    print(f"  Step 4.1: Generating screenshots...")
    
    if not results_json_path.exists():
        print(f"    ERROR: results.json not found at {results_json_path}")
        return []
    
    # Generate screenshots using the engine
    paths = generate_screenshots(str(session_dir), str(results_json_path))
    
    print(f"  Step 4.1: Generated {len(paths)} screenshots")
    
    return paths


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        session_dir = sys.argv[1]
    else:
        session_dir = "data/run"
    
    run_step_4_1_generate_screenshots(session_dir)
