"""
Bowler Alignment Classification

Classifies bowler alignment based on foot orientation at FFC (Front Foot Contact).
Uses the back foot angle relative to the crease.

Classification rules:
- If back foot points towards off stump (outward): side_on
- If back foot points towards leg stump (inward): front_on
- If back foot is roughly parallel to crease: mixed
"""

from typing import Dict, Any, List, Optional
from pipeline.metrics.base_metric import BaseMetric
from pipeline.angles import calculate_back_foot_angle


class BowlerAlignment(BaseMetric):
    """Bowler Alignment classification based on foot orientation."""
    
    id = "bowler_alignment"
    name = "Bowler Alignment"
    group = "Classification"
    description = "Classifies bowler as side-on, front-on, or mixed based on foot orientation"
    unit = "degrees"
    
    # Classification thresholds (in degrees)
    SIDE_ON_THRESHOLD = 20.0    # Pointing outward
    FRONT_ON_THRESHOLD = -20.0   # Pointing inward
    # Between these values: mixed
    
    def __init__(self, session_dir: str):
        super().__init__(session_dir)
        self.foot_angle_back_view: Optional[float] = None
        self.foot_angle_side_view: Optional[float] = None
        self.ffc_frame_back: Optional[int] = None
        self.ffc_frame_side: Optional[int] = None
        self.classification: Optional[str] = None
    
    def extract(self) -> bool:
        """Extract foot orientation angles at FFC."""
        # Load keypoints and events
        self.back_keypoints = self.load_keypoints('back')
        self.side_keypoints = self.load_keypoints('side')
        self.back_events = self.load_events('back')
        self.side_events = self.load_events('side')
        
        # Get FFC frames
        self.ffc_frame_back = self.get_event_frame(self.back_events, 'FFC')
        self.ffc_frame_side = self.get_event_frame(self.side_events, 'FFC')
        
        # Extract angles from back view (best for alignment)
        if self.back_keypoints and self.ffc_frame_back is not None:
            self.foot_angle_back_view = calculate_back_foot_angle(
                self.back_keypoints, self.ffc_frame_back
            )
        
        # Can also get from side view as backup
        if self.side_keypoints and self.ffc_frame_side is not None:
            self.foot_angle_side_view = calculate_back_foot_angle(
                self.side_keypoints, self.ffc_frame_side
            )
        
        # Need at least one valid angle
        return self.foot_angle_back_view is not None or self.foot_angle_side_view is not None
    
    def analyze(self) -> bool:
        """Classify alignment based on foot angle."""
        # Prefer back view for alignment classification
        angle = self.foot_angle_back_view if self.foot_angle_back_view is not None else self.foot_angle_side_view
        
        if angle is None:
            return False
        
        self.value = angle
        
        # Classify based on foot orientation
        if angle > self.SIDE_ON_THRESHOLD:
            self.classification = "side_on"
            self.rating = "side_on"
        elif angle < self.FRONT_ON_THRESHOLD:
            self.classification = "front_on"
            self.rating = "front_on"
        else:
            self.classification = "mixed"
            self.rating = "mixed"
        
        # Build analysis text
        view_used = "back" if self.foot_angle_back_view is not None else "side"
        self.analysis = f"Back foot orientation at FFC: {angle:.1f}° ({view_used} view). Classification: {self.classification.replace('_', ' ').title()}"
        
        # Store extra data
        self.extra_data = {
            "classification": self.classification,
            "foot_angle_back_view": self.foot_angle_back_view,
            "foot_angle_side_view": self.foot_angle_side_view,
            "ffc_frame_back": self.ffc_frame_back,
            "ffc_frame_side": self.ffc_frame_side
        }
        
        return True
    
    def get_screenshots(self) -> List[Dict]:
        """Get screenshot specs for alignment visualization."""
        screenshots = []
        
        # Back view - best for showing foot orientation
        if self.ffc_frame_back is not None:
            screenshots.append({
                "view": "back",
                "frames": [self.ffc_frame_back],
                "blended": False,
                "types": ["original", "skeleton", "overlay"],
                "angles": ["back_foot"],
                "angle_value": self.foot_angle_back_view,
                "crop_strategy": "full_body",
                "output_name": "classification_alignment_back"
            })
        
        # Side view - alternative angle
        if self.ffc_frame_side is not None:
            screenshots.append({
                "view": "side",
                "frames": [self.ffc_frame_side],
                "blended": False,
                "types": ["original", "skeleton", "overlay"],
                "angles": ["back_foot"],
                "angle_value": self.foot_angle_side_view,
                "crop_strategy": "full_body",
                "output_name": "classification_alignment_side"
            })
        
        return screenshots
