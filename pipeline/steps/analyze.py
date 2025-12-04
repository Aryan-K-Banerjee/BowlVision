'''--------------------------------------------------------------
Analyze Orchestrator

This module orchestrates the analysis step of the pipeline.

Currently includes:
- analyze_metrics: Compare extracted metrics against rules.yaml
- collect_scores: Calculate weighted scores based on weights.yaml

More analysis steps can be added here in the future.
--------------------------------------------------------------'''

from pipeline.logic.step_6_analyze.analyze_metrics import analyze_metrics
from pipeline.logic.step_6_analyze.collect_scores import collect_scores


def run_analysis(session_dir: str, back_view_exists: bool, side_view_exists: bool):
    """Orchestrate the analysis step.
    
    Args:
        session_dir: Path to the session directory
        back_view_exists: Whether the back view video exists
        side_view_exists: Whether the side view video exists
    """
    print("    ANALYZE: Starting analysis...")
    
    # Step 6.1: Analyze extracted metrics against rules
    print("    ANALYZE: Comparing metrics against rules...")
    analyze_metrics(session_dir)
    
    # Step 6.2: Calculate scores based on weights
    print("    ANALYZE: Calculating weighted scores...")
    collect_scores(session_dir)
    
    # Future steps can be added here:
    # - Generate recommendations
    # - Create visualizations
    # - etc.
    
    print("    ANALYZE: Analysis complete")
