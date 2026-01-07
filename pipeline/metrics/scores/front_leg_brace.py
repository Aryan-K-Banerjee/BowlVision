"""
Front Leg Brace Metric

Measures the front knee angle at two key events:
- FFC (Front Foot Contact): Initial landing angle
- Release: Final braced angle

The difference indicates how much the knee extends during the delivery stride.

Rating rules:
- full_brace: Release angle >= 170° (nearly straight leg)
- partial_brace: Release angle 150-170° (some flex)
- no_brace: Release angle < 150° (significant flex)
"""

from typing import Dict, Any, List, Optional
from pipeline.metrics.base_metric import BaseMetric
from pipeline.angles import calculate_front_knee_angle


class FrontLegBrace(BaseMetric):
    """Front Leg Brace metric measuring knee extension at delivery."""
    
    id = "front_leg_brace"
    name = "Front Leg Brace"
    group = "Metric"
    description = "Measures front knee extension from FFC to release"
    unit = "degrees"
    
    # Rating thresholds
    FULL_BRACE_THRESHOLD = 170.0
    PARTIAL_BRACE_THRESHOLD = 150.0
    
    def __init__(self, session_dir: str):
        super().__init__(session_dir)
        # Side view data (primary for this metric)
        self.angle_at_ffc: Optional[float] = None
        self.angle_at_release: Optional[float] = None
        self.ffc_frame: Optional[int] = None
        self.release_frame: Optional[int] = None
        self.angle_change: Optional[float] = None
    
    def extract(self) -> bool:
        """Extract front knee angles at FFC and Release."""
        # Load side view data (best for seeing knee angle)
        self.side_keypoints = self.load_keypoints('side')
        self.side_events = self.load_events('side')
        
        if not self.side_keypoints or not self.side_events:
            return False
        
        # Get event frames
        self.ffc_frame = self.get_event_frame(self.side_events, 'FFC')
        self.release_frame = self.get_event_frame(self.side_events, 'Release')
        
        if self.ffc_frame is None or self.release_frame is None:
            return False
        
        # Extract angles at both events
        self.angle_at_ffc = calculate_front_knee_angle(
            self.side_keypoints, self.ffc_frame
        )
        self.angle_at_release = calculate_front_knee_angle(
            self.side_keypoints, self.release_frame
        )
        
        if self.angle_at_ffc is None or self.angle_at_release is None:
            return False
        if self.angle_at_ffc <= 0 or self.angle_at_release <= 0:
            return False
        
        # Calculate change
        self.angle_change = self.angle_at_release - self.angle_at_ffc
        
        return True
    
    def analyze(self) -> bool:
        """Analyze brace quality and assign rating."""
        if self.angle_at_release is None:
            return False
        
        # Primary value is release angle (final brace position)
        self.value = self.angle_at_release
        
        # Assign rating based on release angle
        if self.angle_at_release >= self.FULL_BRACE_THRESHOLD:
            self.rating = "full_brace"
            rating_text = "Full Brace"
        elif self.angle_at_release >= self.PARTIAL_BRACE_THRESHOLD:
            self.rating = "partial_brace"
            rating_text = "Partial Brace"
        else:
            self.rating = "no_brace"
            rating_text = "No Brace"
        
        # Calculate score (0-100)
        # Full brace (180°) = 100, No brace (120°) = 0
        score = min(100, max(0, (self.angle_at_release - 120) / 60 * 100))
        self.extra_data = {
            "score": round(score, 1),
            "angle_at_ffc": self.angle_at_ffc,
            "angle_at_release": self.angle_at_release,
            "angle_change": self.angle_change,
            "ffc_frame": self.ffc_frame,
            "release_frame": self.release_frame
        }
        
        # Build analysis text
        change_text = f"+{self.angle_change:.1f}°" if self.angle_change >= 0 else f"{self.angle_change:.1f}°"
        self.analysis = (
            f"Front knee at FFC: {self.angle_at_ffc:.1f}°, "
            f"at Release: {self.angle_at_release:.1f}° ({change_text}). "
            f"Rating: {rating_text}"
        )
        
        return True
    
    def get_screenshots(self) -> List[Dict]:
        """Get screenshot specs for FFC and Release comparison."""
        screenshots = []
        
        # Side view at FFC
        if self.ffc_frame is not None:
            screenshots.append({
                "view": "side",
                "frames": [self.ffc_frame],
                "blended": False,
                "types": ["original", "skeleton", "overlay"],
                "angles": ["front_knee"],
                "angle_value": self.angle_at_ffc,
                "crop_strategy": "front_leg_focus",
                "output_name": "metric_front_leg_brace_ffc"
            })
        
        # Side view at Release
        if self.release_frame is not None:
            screenshots.append({
                "view": "side",
                "frames": [self.release_frame],
                "blended": False,
                "types": ["original", "skeleton", "overlay"],
                "angles": ["front_knee"],
                "angle_value": self.angle_at_release,
                "crop_strategy": "front_leg_focus",
                "output_name": "metric_front_leg_brace_release"
            })
        
        # Blended comparison (FFC + Release overlay)
        if self.ffc_frame is not None and self.release_frame is not None:
            screenshots.append({
                "view": "side",
                "frames": [self.ffc_frame, self.release_frame],
                "blended": True,
                "types": ["original", "skeleton", "overlay"],
                "angles": ["front_knee"],
                "angle_value": None,  # Multiple angles
                "crop_strategy": "front_leg_focus",
                "output_name": "metric_front_leg_brace_comparison"
            })
        
        return screenshots
