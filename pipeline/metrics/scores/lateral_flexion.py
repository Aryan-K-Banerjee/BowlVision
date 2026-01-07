"""
Lateral Flexion Metric

Measures the lateral flexion of the spine at Release.
The angle compares the head position to a vertical line from the base of spine.

Rating rules:
- good: < 20° flexion (close to upright)
- moderate: 20-35° flexion
- poor: > 35° flexion (significant lean)
"""

from typing import Dict, Any, List, Optional
from pipeline.metrics.base_metric import BaseMetric
from pipeline.angles import calculate_lateral_flexion_angle


class LateralFlexion(BaseMetric):
    """Lateral Flexion metric measuring spine tilt at release."""
    
    id = "lateral_flexion"
    name = "Lateral Flexion"
    group = "Metric"
    description = "Measures spine lateral flexion at release - how much the bowler leans sideways"
    unit = "degrees"
    
    # Rating thresholds
    GOOD_THRESHOLD = 20.0
    MODERATE_THRESHOLD = 35.0
    
    def __init__(self, session_dir: str):
        super().__init__(session_dir)
        self.angle_at_release_side: Optional[float] = None
        self.angle_at_release_back: Optional[float] = None
        self.release_frame_side: Optional[int] = None
        self.release_frame_back: Optional[int] = None
    
    def extract(self) -> bool:
        """Extract lateral flexion angle at Release."""
        # Load side view (primary for this metric)
        self.side_keypoints = self.load_keypoints('side')
        self.side_events = self.load_events('side')
        
        # Load back view (secondary)
        self.back_keypoints = self.load_keypoints('back')
        self.back_events = self.load_events('back')
        
        success = False
        
        # Extract from side view
        if self.side_keypoints and self.side_events:
            self.release_frame_side = self.get_event_frame(self.side_events, 'Release')
            if self.release_frame_side is not None:
                self.angle_at_release_side = calculate_lateral_flexion_angle(
                    self.side_keypoints, self.release_frame_side
                )
                if self.angle_at_release_side > 0:
                    success = True
        
        # Extract from back view
        if self.back_keypoints and self.back_events:
            self.release_frame_back = self.get_event_frame(self.back_events, 'Release')
            if self.release_frame_back is not None:
                self.angle_at_release_back = calculate_lateral_flexion_angle(
                    self.back_keypoints, self.release_frame_back
                )
                if self.angle_at_release_back > 0:
                    success = True
        
        return success
    
    def analyze(self) -> bool:
        """Analyze lateral flexion and assign rating."""
        # Use side view as primary (better for seeing spine angle)
        angle = self.angle_at_release_side if self.angle_at_release_side and self.angle_at_release_side > 0 else self.angle_at_release_back
        
        if not angle or angle <= 0:
            return False
        
        self.value = angle
        
        # Assign rating based on flexion angle (less is better)
        if angle <= self.GOOD_THRESHOLD:
            self.rating = "good"
            rating_text = "Good"
        elif angle <= self.MODERATE_THRESHOLD:
            self.rating = "moderate"
            rating_text = "Moderate"
        else:
            self.rating = "poor"
            rating_text = "Poor"
        
        # Calculate score (0-100) - less flexion is better
        # 0° = 100, 45° = 0
        raw_score = max(0, 100 - (angle / 45 * 100))
        self.score = round(raw_score, 1)
        
        self.extra_data = {
            "score": self.score,
            "angle_at_release_side": self.angle_at_release_side,
            "angle_at_release_back": self.angle_at_release_back,
            "release_frame_side": self.release_frame_side,
            "release_frame_back": self.release_frame_back
        }
        
        # Build analysis text
        view_used = "side" if self.angle_at_release_side and self.angle_at_release_side > 0 else "back"
        self.analysis = (
            f"Lateral flexion at release: {angle:.1f}° ({view_used} view). "
            f"Rating: {rating_text}. Less lean = better alignment."
        )
        
        return True
    
    def get_screenshots(self) -> List[Dict]:
        """Get screenshot specs for release frame."""
        screenshots = []
        
        # Side view at Release (cropped to upper body)
        if self.release_frame_side is not None:
            screenshots.append({
                "view": "side",
                "frames": [self.release_frame_side],
                "blended": False,
                "types": ["original", "skeleton", "overlay"],
                "angles": ["lateral_flexion"],
                "angle_value": self.angle_at_release_side,
                "crop_strategy": "upper_body",
                "output_name": "metric_lateral_flexion_side"
            })
        
        # Back view at Release
        if self.release_frame_back is not None:
            screenshots.append({
                "view": "back",
                "frames": [self.release_frame_back],
                "blended": False,
                "types": ["original", "skeleton", "overlay"],
                "angles": ["lateral_flexion"],
                "angle_value": self.angle_at_release_back,
                "crop_strategy": "upper_body",
                "output_name": "metric_lateral_flexion_back"
            })
        
        return screenshots
