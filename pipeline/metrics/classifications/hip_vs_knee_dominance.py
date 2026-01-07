"""
Hip vs Knee Dominance Classification

Classifies bowlers as hip dominant or knee dominant based on 
their back knee angle at BFC (Back Foot Contact).

Classification rules:
- If either back knee angle < 150°: knee_dominant
- Otherwise: hip_dominant
"""

from typing import Dict, Any, List, Optional
from pipeline.metrics.base_metric import BaseMetric
from pipeline.angles import calculate_back_knee_angle


class HipVsKneeDominance(BaseMetric):
    """Hip vs Knee Dominance classification."""
    
    id = "hip_vs_knee_dominance"
    name = "Hip vs Knee Dominance"
    group = "Classification"
    description = "Classifies bowler as hip dominant or knee dominant based on back knee flexion at BFC"
    unit = "degrees"
    
    # Classification threshold
    KNEE_DOMINANT_THRESHOLD = 150.0
    
    def __init__(self, session_dir: str):
        super().__init__(session_dir)
        self.back_angle_back_view: Optional[float] = None
        self.back_angle_side_view: Optional[float] = None
        self.bfc_frame_back: Optional[int] = None
        self.bfc_frame_side: Optional[int] = None
        self.classification: Optional[str] = None
    
    def extract(self) -> bool:
        """Extract back knee angles at BFC from both views."""
        # Load keypoints and events
        self.back_keypoints = self.load_keypoints('back')
        self.side_keypoints = self.load_keypoints('side')
        self.back_events = self.load_events('back')
        self.side_events = self.load_events('side')
        
        # Get BFC frames
        self.bfc_frame_back = self.get_event_frame(self.back_events, 'BFC')
        self.bfc_frame_side = self.get_event_frame(self.side_events, 'BFC')
        
        # Extract angles
        if self.back_keypoints and self.bfc_frame_back is not None:
            self.back_angle_back_view = calculate_back_knee_angle(
                self.back_keypoints, self.bfc_frame_back
            )
        
        if self.side_keypoints and self.bfc_frame_side is not None:
            self.back_angle_side_view = calculate_back_knee_angle(
                self.side_keypoints, self.bfc_frame_side
            )
        
        # Need at least one valid angle
        return (self.back_angle_back_view is not None and self.back_angle_back_view > 0) or \
               (self.back_angle_side_view is not None and self.back_angle_side_view > 0)
    
    def analyze(self) -> bool:
        """Classify as hip or knee dominant."""
        angles = []
        
        if self.back_angle_back_view and self.back_angle_back_view > 0:
            angles.append(self.back_angle_back_view)
        if self.back_angle_side_view and self.back_angle_side_view > 0:
            angles.append(self.back_angle_side_view)
        
        if not angles:
            return False
        
        # Use minimum angle for classification
        min_angle = min(angles)
        self.value = min_angle
        
        # Classify
        if min_angle < self.KNEE_DOMINANT_THRESHOLD:
            self.classification = "knee_dominant"
            self.rating = "knee_dominant"
        else:
            self.classification = "hip_dominant"
            self.rating = "hip_dominant"
        
        # Build analysis text
        parts = []
        if self.back_angle_back_view and self.back_angle_back_view > 0:
            parts.append(f"Back view: {self.back_angle_back_view:.1f}°")
        if self.back_angle_side_view and self.back_angle_side_view > 0:
            parts.append(f"Side view: {self.back_angle_side_view:.1f}°")
        
        self.analysis = f"Back knee at BFC - {', '.join(parts)}. Classification: {self.classification.replace('_', ' ').title()}"
        
        # Store extra data
        self.extra_data = {
            "classification": self.classification,
            "back_angle_back_view": self.back_angle_back_view,
            "back_angle_side_view": self.back_angle_side_view,
            "bfc_frame_back": self.bfc_frame_back,
            "bfc_frame_side": self.bfc_frame_side
        }
        
        return True
    
    def get_screenshots(self) -> List[Dict]:
        """Get screenshot specs for BFC frames."""
        screenshots = []
        
        # Back view screenshot
        if self.bfc_frame_back is not None:
            screenshots.append({
                "view": "back",
                "frames": [self.bfc_frame_back],
                "blended": False,
                "types": ["original", "skeleton", "overlay"],
                "angles": ["back_knee"],
                "angle_value": self.back_angle_back_view,
                "crop_strategy": "square_around_bowler",
                "output_name": "classification_hip_knee_back"
            })
        
        # Side view screenshot
        if self.bfc_frame_side is not None:
            screenshots.append({
                "view": "side",
                "frames": [self.bfc_frame_side],
                "blended": False,
                "types": ["original", "skeleton", "overlay"],
                "angles": ["back_knee"],
                "angle_value": self.back_angle_side_view,
                "crop_strategy": "square_around_bowler",
                "output_name": "classification_hip_knee_side"
            })
        
        return screenshots
