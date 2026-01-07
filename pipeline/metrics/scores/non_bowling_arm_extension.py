"""
Non-Bowling Arm Extension Metric

Measures the maximum extension of the non-bowling (left) arm 
between BFC and FFC. A fully extended arm helps with balance and timing.

Rating rules:
- excellent: >= 165° (nearly fully extended)
- good: 150-165° (well extended)
- moderate: 135-150° (partial extension)
- poor: < 135° (not extended)
"""

from typing import Dict, Any, List, Optional
from pipeline.metrics.base_metric import BaseMetric
from pipeline.angles import calculate_max_non_bowling_arm_angle


class NonBowlingArmExtension(BaseMetric):
    """Non-Bowling Arm Extension metric measuring arm extension between BFC and FFC."""
    
    id = "non_bowling_arm_extension"
    name = "Non-Bowling Arm Extension"
    group = "Metric"
    description = "Measures maximum extension of non-bowling arm between BFC and FFC"
    unit = "degrees"
    
    # Rating thresholds
    EXCELLENT_THRESHOLD = 165.0
    GOOD_THRESHOLD = 150.0
    MODERATE_THRESHOLD = 135.0
    
    def __init__(self, session_dir: str):
        super().__init__(session_dir)
        self.max_angle: Optional[float] = None
        self.max_angle_frame: Optional[int] = None
        self.bfc_frame: Optional[int] = None
        self.ffc_frame: Optional[int] = None
    
    def extract(self) -> bool:
        """Extract maximum arm extension between BFC and FFC from side view."""
        # Side view is best for seeing arm extension
        self.side_keypoints = self.load_keypoints('side')
        self.side_events = self.load_events('side')
        
        if not self.side_keypoints or not self.side_events:
            return False
        
        self.bfc_frame = self.get_event_frame(self.side_events, 'BFC')
        self.ffc_frame = self.get_event_frame(self.side_events, 'FFC')
        
        if self.bfc_frame is None or self.ffc_frame is None:
            return False
        
        # Find maximum extension between BFC and FFC
        self.max_angle, self.max_angle_frame = calculate_max_non_bowling_arm_angle(
            self.side_keypoints, self.bfc_frame, self.ffc_frame
        )
        
        return self.max_angle > 0
    
    def analyze(self) -> bool:
        """Analyze arm extension and assign rating."""
        if self.max_angle is None or self.max_angle <= 0:
            return False
        
        self.value = self.max_angle
        
        # Assign rating (higher = better)
        if self.max_angle >= self.EXCELLENT_THRESHOLD:
            self.rating = "excellent"
            rating_text = "Excellent"
        elif self.max_angle >= self.GOOD_THRESHOLD:
            self.rating = "good"
            rating_text = "Good"
        elif self.max_angle >= self.MODERATE_THRESHOLD:
            self.rating = "moderate"
            rating_text = "Moderate"
        else:
            self.rating = "poor"
            rating_text = "Poor"
        
        # Calculate score (0-100)
        # 180° = 100 (fully extended), 90° = 0 (bent at 90°)
        raw_score = max(0, min(100, (self.max_angle - 90) / 90 * 100))
        self.score = round(raw_score, 1)
        
        self.extra_data = {
            "score": self.score,
            "max_angle": self.max_angle,
            "max_angle_frame": self.max_angle_frame,
            "bfc_frame": self.bfc_frame,
            "ffc_frame": self.ffc_frame
        }
        
        # Build analysis text
        self.analysis = (
            f"Maximum non-bowling arm extension: {self.max_angle:.1f}° "
            f"at frame {self.max_angle_frame}. "
            f"Rating: {rating_text}. Fuller extension = better."
        )
        
        return True
    
    def get_screenshots(self) -> List[Dict]:
        """Get screenshot specs for max extension frame."""
        screenshots = []
        
        # Side view at max extension frame
        if self.max_angle_frame is not None:
            screenshots.append({
                "view": "side",
                "frames": [self.max_angle_frame],
                "blended": False,
                "types": ["original", "skeleton", "overlay"],
                "angles": ["non_bowling_arm"],
                "angle_value": self.max_angle,
                "crop_strategy": "non_bowling_arm_focus",
                "output_name": "metric_non_bowling_arm_max"
            })
        
        # Comparison: BFC and FFC overlay
        if self.bfc_frame is not None and self.ffc_frame is not None:
            screenshots.append({
                "view": "side",
                "frames": [self.bfc_frame, self.ffc_frame],
                "blended": True,
                "types": ["original", "skeleton", "overlay"],
                "angles": [],
                "crop_strategy": "upper_body",
                "output_name": "metric_non_bowling_arm_comparison"
            })
        
        return screenshots
