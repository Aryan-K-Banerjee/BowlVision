"""
Base Metric Class

All metrics and classifications inherit from this base class.
Each metric is self-contained: it extracts its own data, analyzes it,
defines its rules, specifies screenshots, and will generate HTML.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path


class BaseMetric(ABC):
    """Base class for all metrics and classifications."""
    
    # Subclasses must override these
    id: str = ""           # Unique identifier (e.g., "front_leg_brace")
    name: str = ""         # Display name (e.g., "Front Leg Brace")
    group: str = ""        # Category grouping (e.g., "Brace", "Classification")
    description: str = ""  # Brief description of what this metric measures
    
    def __init__(self, session_dir: str):
        """Initialize metric with session directory.
        
        Args:
            session_dir: Path to session directory (e.g., 'data/run/')
        """
        self.session_dir = Path(session_dir)
        self.clips_dir = self.session_dir / 'b_clips'
        self.keypoints_dir = self.session_dir / 'c_keypoints'
        self.results_dir = self.session_dir / 'results'
        
        # Data loaded during extraction
        self.side_keypoints: Optional[Dict] = None
        self.back_keypoints: Optional[Dict] = None
        self.side_events: Optional[Dict] = None
        self.back_events: Optional[Dict] = None
        
        # Results populated during analysis
        self.value: Optional[float] = None
        self.score: Optional[float] = None
        self.rating: Optional[str] = None
        self.analysis: Optional[str] = None
        self.tags: List[str] = []
        self.screenshots: List[Dict] = []
        self.extra_data: Dict[str, Any] = {}
    
    @abstractmethod
    def extract(self) -> bool:
        """Extract raw data needed for this metric.
        
        Returns:
            True if extraction succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    def analyze(self) -> bool:
        """Analyze extracted data and populate results.
        
        Returns:
            True if analysis succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    def get_screenshots(self) -> List[Dict]:
        """Get screenshot specifications for this metric.
        
        Returns:
            List of screenshot spec dicts for the screenshot engine
        """
        pass
    
    def run(self) -> bool:
        """Run full metric pipeline: extract → analyze → get screenshots.
        
        Returns:
            True if successful, False otherwise
        """
        # Extract data
        if not self.extract():
            return False
        
        # Analyze
        if not self.analyze():
            return False
        
        # Get screenshots
        self.screenshots = self.get_screenshots()
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric results to dict for results.json."""
        result = {
            "id": self.id,
            "name": self.name,
            "group": self.group,
            "value": self.value,
            "unit": getattr(self, 'unit', 'degrees'),
            "score": self.score,
            "rating": self.rating,
            "tags": self.tags,
            "description": self.description,
            "analysis": self.analysis,
            "screenshots": self.screenshots,
            "extra_data": self.extra_data
        }
        return result
    
    def _create_error_result(self, message: str) -> Dict[str, Any]:
        """Create error result dict."""
        return {
            "id": self.id,
            "name": self.name,
            "group": self.group,
            "value": None,
            "score": None,
            "rating": "error",
            "tags": [],
            "description": self.description,
            "analysis": f"Error: {message}",
            "screenshots": []
        }
    
    # Helper methods for loading data
    
    def load_keypoints(self, view: str) -> Optional[Dict]:
        """Load keypoints CSV for a view.
        
        Args:
            view: 'side' or 'back'
            
        Returns:
            Dict mapping frame -> list of (x, y, z, vis) tuples
        """
        import csv
        
        kp_path = self.keypoints_dir / f'{view}_view_keypoints.csv'
        if not kp_path.exists():
            return None
        
        keypoints = {}
        try:
            with open(kp_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    frame = int(row['frame'])
                    lms = []
                    for i in range(33):
                        x = float(row[f'lm{i}_x'])
                        y = float(row[f'lm{i}_y'])
                        z = float(row[f'lm{i}_z'])
                        vis = float(row[f'lm{i}_vis'])
                        lms.append((x, y, z, vis))
                    keypoints[frame] = lms
            return keypoints
        except Exception:
            return None
    
    def load_events(self, view: str) -> Optional[Dict]:
        """Load events JSON for a view.
        
        Args:
            view: 'side' or 'back'
            
        Returns:
            Dict with event names -> frame numbers
        """
        import json
        
        events_path = self.clips_dir / f'{view}_view_events.json'
        if not events_path.exists():
            return None
        
        try:
            with open(events_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Normalize event format
            if isinstance(data, dict):
                if 'events' in data:
                    return data['events']
                elif 'video' in data and 'events' in data['video']:
                    return data['video']['events']
                return data
            return None
        except Exception:
            return None
    
    def get_event_frame(self, events: Dict, event_name: str) -> Optional[int]:
        """Get frame number for an event (case-insensitive).
        
        Args:
            events: Events dict
            event_name: Event name (e.g., 'Jump', 'BFC', 'FFC', 'Release')
            
        Returns:
            Frame number or None if not found
        """
        if not events:
            return None
        
        # Try exact match first
        if event_name in events:
            return int(events[event_name])
        
        # Try case variations
        for key, val in events.items():
            if key.lower() == event_name.lower():
                return int(val)
        
        return None
