"""
Back Foot Stiffness Metric

Measures the back foot heel elevation angle at two key events:
- BFC (Back Foot Contact): Initial contact angle
- FFC (Front Foot Contact): Mid-delivery angle

Stiffness refers to how flat the back foot stays during the delivery stride.
A stiffer (flatter) foot often indicates better power transfer.

Rating rules:
- stiff: Heel elevation < 15° (foot stays relatively flat)
- moderate: Heel elevation 15-30° (some heel lift)
- flexible: Heel elevation > 30° (significant heel lift)
"""

from typing import Dict, Any, List, Optional
from pipeline.metrics.base_metric import BaseMetric
from pipeline.angles import calculate_back_foot_angle


class BackFootStiffness(BaseMetric):
    """Back Foot Stiffness metric measuring heel elevation during delivery."""
    
    id = "back_foot_stiffness"
    name = "Back Foot Stiffness"
    group = "Metric"
    description = "Measures back foot heel elevation from BFC to FFC"
    unit = "degrees"
    
    # Rating thresholds (degrees of heel elevation)
    STIFF_THRESHOLD = 15.0
    MODERATE_THRESHOLD = 30.0
    
    def __init__(self, session_dir: str):
        super().__init__(session_dir)
        # Data from both views
        self.angle_at_bfc_side: Optional[float] = None
        self.angle_at_ffc_side: Optional[float] = None
        self.angle_at_bfc_back: Optional[float] = None
        self.angle_at_ffc_back: Optional[float] = None
        self.bfc_frame_side: Optional[int] = None
        self.ffc_frame_side: Optional[int] = None
        self.bfc_frame_back: Optional[int] = None
        self.ffc_frame_back: Optional[int] = None
        self.max_elevation: Optional[float] = None
    
    def extract(self) -> bool:
        """Extract back foot angles at BFC and FFC from both views."""
        # Load side view data
        self.side_keypoints = self.load_keypoints('side')
        self.side_events = self.load_events('side')
        
        # Load back view data
        self.back_keypoints = self.load_keypoints('back')
        self.back_events = self.load_events('back')
        
        success = False
        
        # Extract from side view
        if self.side_keypoints and self.side_events:
            self.bfc_frame_side = self.get_event_frame(self.side_events, 'BFC')
            self.ffc_frame_side = self.get_event_frame(self.side_events, 'FFC')
            
            if self.bfc_frame_side is not None:
                self.angle_at_bfc_side = calculate_back_foot_angle(
                    self.side_keypoints, self.bfc_frame_side
                )
                if self.angle_at_bfc_side is not None:
                    success = True
            
            if self.ffc_frame_side is not None:
                self.angle_at_ffc_side = calculate_back_foot_angle(
                    self.side_keypoints, self.ffc_frame_side
                )
        
        # Extract from back view
        if self.back_keypoints and self.back_events:
            self.bfc_frame_back = self.get_event_frame(self.back_events, 'BFC')
            self.ffc_frame_back = self.get_event_frame(self.back_events, 'FFC')
            
            if self.bfc_frame_back is not None:
                self.angle_at_bfc_back = calculate_back_foot_angle(
                    self.back_keypoints, self.bfc_frame_back
                )
                if self.angle_at_bfc_back is not None:
                    success = True
            
            if self.ffc_frame_back is not None:
                self.angle_at_ffc_back = calculate_back_foot_angle(
                    self.back_keypoints, self.ffc_frame_back
                )
        
        return success
    
    def analyze(self) -> bool:
        """Analyze foot stiffness and assign rating."""
        # Collect all valid angles
        angles = []
        
        if self.angle_at_bfc_side is not None:
            angles.append(abs(self.angle_at_bfc_side))
        if self.angle_at_ffc_side is not None:
            angles.append(abs(self.angle_at_ffc_side))
        if self.angle_at_bfc_back is not None:
            angles.append(abs(self.angle_at_bfc_back))
        if self.angle_at_ffc_back is not None:
            angles.append(abs(self.angle_at_ffc_back))
        
        if not angles:
            return False
        
        # Use maximum heel elevation for rating
        self.max_elevation = max(angles)
        self.value = self.max_elevation
        
        # Assign rating based on max elevation
        if self.max_elevation <= self.STIFF_THRESHOLD:
            self.rating = "stiff"
            rating_text = "Stiff"
        elif self.max_elevation <= self.MODERATE_THRESHOLD:
            self.rating = "moderate"
            rating_text = "Moderate"
        else:
            self.rating = "flexible"
            rating_text = "Flexible"
        
        # Calculate score (0-100)
        # Stiff (0°) = 100, Very flexible (45°) = 0
        score = max(0, 100 - (self.max_elevation / 45 * 100))
        
        self.extra_data = {
            "score": round(score, 1),
            "angle_at_bfc_side": self.angle_at_bfc_side,
            "angle_at_ffc_side": self.angle_at_ffc_side,
            "angle_at_bfc_back": self.angle_at_bfc_back,
            "angle_at_ffc_back": self.angle_at_ffc_back,
            "max_elevation": self.max_elevation,
            "bfc_frame_side": self.bfc_frame_side,
            "ffc_frame_side": self.ffc_frame_side,
            "bfc_frame_back": self.bfc_frame_back,
            "ffc_frame_back": self.ffc_frame_back
        }
        
        # Build analysis text
        parts = []
        if self.angle_at_bfc_side is not None:
            parts.append(f"BFC (side): {self.angle_at_bfc_side:.1f}°")
        if self.angle_at_ffc_side is not None:
            parts.append(f"FFC (side): {self.angle_at_ffc_side:.1f}°")
        
        self.analysis = (
            f"Back foot elevation - {', '.join(parts)}. "
            f"Max elevation: {self.max_elevation:.1f}°. Rating: {rating_text}"
        )
        
        return True
    
    def get_screenshots(self) -> List[Dict]:
        """Get screenshot specs for back foot at BFC and FFC."""
        screenshots = []
        
        # Side view at BFC
        if self.bfc_frame_side is not None:
            screenshots.append({
                "view": "side",
                "frames": [self.bfc_frame_side],
                "blended": False,
                "types": ["original", "skeleton", "overlay"],
                "angles": ["back_foot"],
                "angle_value": self.angle_at_bfc_side,
                "crop_strategy": "back_foot_focus",
                "output_name": "metric_back_foot_stiffness_bfc"
            })
        
        # Side view at FFC
        if self.ffc_frame_side is not None:
            screenshots.append({
                "view": "side",
                "frames": [self.ffc_frame_side],
                "blended": False,
                "types": ["original", "skeleton", "overlay"],
                "angles": ["back_foot"],
                "angle_value": self.angle_at_ffc_side,
                "crop_strategy": "back_foot_focus",
                "output_name": "metric_back_foot_stiffness_ffc"
            })
        
        # Back view at BFC (if available)
        if self.bfc_frame_back is not None:
            screenshots.append({
                "view": "back",
                "frames": [self.bfc_frame_back],
                "blended": False,
                "types": ["original", "skeleton", "overlay"],
                "angles": ["back_foot"],
                "angle_value": self.angle_at_bfc_back,
                "crop_strategy": "full_body",
                "output_name": "metric_back_foot_stiffness_bfc_back"
            })
        
        return screenshots
