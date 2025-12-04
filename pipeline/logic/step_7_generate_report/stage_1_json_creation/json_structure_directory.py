"""
JSON Structure Directory - Registry for section and metric builders.

Maps section/metric names to their builder functions.
"""

from pipeline.logic.step_7_generate_report.stage_1_json_creation.structure import (
    header,
    video_events,
    scores,
    metrics_front_leg_brace,
    metrics_hip_vs_knee_dominance,
    metrics_bowler_alignment
)


# Registry mapping section/metric names to builder functions
STRUCTURE_REGISTRY = {
    'header': header.build,
    'video_events': video_events.build,
    'scores': scores.build,
    'metric_front_leg_brace': metrics_front_leg_brace.build,
    'metric_hip_vs_knee_dominance': metrics_hip_vs_knee_dominance.build,
    'metric_bowler_alignment': metrics_bowler_alignment.build,
}


def get_structure_builder(name: str):
    """Get structure builder function by name.
    
    Args:
        name: Section or metric name
        
    Returns:
        Builder function, or None if not found
    """
    return STRUCTURE_REGISTRY.get(name)


def get_all_builders():
    """Get list of all registered builder names."""
    return list(STRUCTURE_REGISTRY.keys())
