"""
Bowling Arm Delay Metric

Measures the bowling arm position relative to horizontal at FFC.
A delayed bowling arm (below horizontal) allows for a longer delivery arc.

Rating rules:
- excellent: < -30° (arm well below horizontal - great delay)
- good: -30° to -10° (arm below horizontal)
- moderate: -10° to 10° (arm near horizontal)
- poor: > 10° (arm already above horizontal - no delay)
"""

from typing import Dict, Any, List, Optional
from pipeline.metrics.base_metric import BaseMetric
from pipeline.angles import calculate_bowling_arm_delay_angle


class BowlingArmDelay(BaseMetric):
    """Bowling Arm Delay metric measuring arm position at FFC."""
    
    id = "bowling_arm_delay"
    name = "Bowling Arm Delay"
    group = "Metric"
    description = "Measures bowling arm position relative to horizontal at FFC - below is better"
    unit = "degrees"
    
    # Rating thresholds (negative = below horizontal = good)
    EXCELLENT_THRESHOLD = -30.0
    GOOD_THRESHOLD = -10.0
    MODERATE_THRESHOLD = 10.0
    
    def __init__(self, session_dir: str):
        super().__init__(session_dir)
        self.angle_at_ffc: Optional[float] = None
        self.ffc_frame: Optional[int] = None
    
    def extract(self) -> bool:
        """Extract bowling arm angle at FFC from side view."""
        # Side view is best for seeing arm position
        self.side_keypoints = self.load_keypoints('side')
        self.side_events = self.load_events('side')
        
        if not self.side_keypoints or not self.side_events:
            return False
        
        self.ffc_frame = self.get_event_frame(self.side_events, 'FFC')
        if self.ffc_frame is None:
            return False
        
        self.angle_at_ffc = calculate_bowling_arm_delay_angle(
            self.side_keypoints, self.ffc_frame
        )
        
        # 0.0 is a valid angle, but we need actual detection
        return self.angle_at_ffc is not None
    
    def analyze(self) -> bool:
        """Analyze arm delay and assign rating."""
        if self.angle_at_ffc is None:
            return False
        
        self.value = self.angle_at_ffc
        
        # Assign rating (more negative = better delay)
        if self.angle_at_ffc <= self.EXCELLENT_THRESHOLD:
            self.rating = "excellent"
            rating_text = "Excellent"
        elif self.angle_at_ffc <= self.GOOD_THRESHOLD:
            self.rating = "good"
            rating_text = "Good"
        elif self.angle_at_ffc <= self.MODERATE_THRESHOLD:
            self.rating = "moderate"
            rating_text = "Moderate"
        else:
            self.rating = "poor"
            rating_text = "Poor"
        
        # Calculate score (0-100)
        # -60° = 100 (excellent delay), +30° = 0 (no delay)
        raw_score = max(0, min(100, 100 - ((self.angle_at_ffc + 60) / 90 * 100)))
        # Invert: more negative angle = higher score
        raw_score = max(0, min(100, (60 - self.angle_at_ffc) / 90 * 100))
        self.score = round(raw_score, 1)
        
        self.extra_data = {
            "score": self.score,
            "angle_at_ffc": self.angle_at_ffc,
            "ffc_frame": self.ffc_frame
        }
        
        # Build analysis text
        position = "below" if self.angle_at_ffc < 0 else "above"
        self.analysis = (
            f"Bowling arm at FFC: {abs(self.angle_at_ffc):.1f}° {position} horizontal. "
            f"Rating: {rating_text}. Below horizontal = good delay."
        )
        
        return True
    
    def get_screenshots(self) -> List[Dict]:
        """Get screenshot specs for FFC frame."""
        screenshots = []
        
        # Side view at FFC - focus on bowling arm
        if self.ffc_frame is not None:
            screenshots.append({
                "view": "side",
                "frames": [self.ffc_frame],
                "blended": False,
                "types": ["original", "skeleton", "overlay"],
                "angles": ["bowling_arm"],
                "angle_value": self.angle_at_ffc,
                "crop_strategy": "bowling_arm_focus",
                "output_name": "metric_bowling_arm_delay_ffc"
            })
        
        return screenshots
