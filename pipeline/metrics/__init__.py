"""
Metrics Package

Contains all metrics and classifications for bowling analysis.
Each metric is self-contained with extraction, analysis, and screenshot specs.
"""

from pipeline.metrics.base_metric import BaseMetric
from pipeline.metrics.classifications import HipVsKneeDominance, BowlerAlignment
from pipeline.metrics.scores import (
    FrontLegBrace,
    BackFootStiffness,
    LateralFlexion,
    BowlingArmDelay,
    NonBowlingArmExtension,
)

# Registry of all available metrics
METRIC_REGISTRY = {
    # Classifications
    'hip_vs_knee_dominance': HipVsKneeDominance,
    'bowler_alignment': BowlerAlignment,
    # Scores
    'front_leg_brace': FrontLegBrace,
    'back_foot_stiffness': BackFootStiffness,
    'lateral_flexion': LateralFlexion,
    'bowling_arm_delay': BowlingArmDelay,
    'non_bowling_arm_extension': NonBowlingArmExtension,
}

# Ordered list for processing
ALL_METRICS = [
    HipVsKneeDominance,
    BowlerAlignment,
    FrontLegBrace,
    BackFootStiffness,
    LateralFlexion,
    BowlingArmDelay,
    NonBowlingArmExtension,
]

__all__ = [
    'BaseMetric',
    'HipVsKneeDominance',
    'BowlerAlignment',
    'FrontLegBrace',
    'BackFootStiffness',
    'LateralFlexion',
    'BowlingArmDelay',
    'NonBowlingArmExtension',
    'METRIC_REGISTRY',
    'ALL_METRICS',
]
