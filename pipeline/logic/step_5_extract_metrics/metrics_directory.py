'''--------------------------------------------------------------
Metrics Directory

This registry keeps track of all metrics that need to be extracted.
Each metric function handles its own data access and calculation logic.

To add a new metric:
1. Create the business logic file in pipeline/logic/metrics/
2. Add it to the METRICS list below
3. The orchestrator will automatically extract it

Format:
Each metric entry is a dict with:
- 'name': str - Unique metric name (for JSON output)
- 'function': callable - Function that accepts session_dir and returns metric dict
- 'description': str - Brief description of what the metric measures
--------------------------------------------------------------'''

from pipeline.logic.step_5_extract_metrics.metrics.front_leg_brace import extract_front_leg_brace
from pipeline.logic.step_5_extract_metrics.metrics.hip_vs_knee_dominance import extract_hip_vs_knee_dominance
from pipeline.logic.step_5_extract_metrics.metrics.bowler_alignment import extract_bowler_alignment


# List of all metrics to be extracted
# Each metric function receives session_dir and returns a dict
METRICS = [
    {
        'name': 'front_leg_brace',
        'function': extract_front_leg_brace,
        'description': 'Front knee angle at FFC and release, measuring front leg brace quality'
    },
    {
        'name': 'hip_vs_knee_dominance',
        'function': extract_hip_vs_knee_dominance,
        'description': 'Back knee angle at BFC from both views, classifying hip vs knee dominance'
    },
    {
        'name': 'bowler_alignment',
        'function': extract_bowler_alignment,
        'description': 'Back foot orientation angle at BFC, classifying front-on vs side-on alignment'
    }
    # Add more metrics here as needed
]


def get_all_metrics() -> list:
    """Get the list of all registered metrics.
    
    Returns:
        List of metric dictionaries
    """
    return METRICS