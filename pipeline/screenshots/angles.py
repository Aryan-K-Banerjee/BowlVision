"""
Angle point extractors for screenshot overlays.

Each function takes landmarks and returns the 3 points needed to draw an angle arc.
"""

from typing import List, Tuple, Optional


def get_front_knee_points(landmarks: List[Tuple], frame_shape: Tuple[int, int]) -> Optional[Tuple]:
    """Get points for front knee angle visualization.
    
    Uses landmarks: 23 (left hip), 25 (left knee), 27 (left ankle).
    
    Args:
        landmarks: List of (x, y, z, vis) tuples in pixel coordinates
        frame_shape: (height, width) of frame
        
    Returns:
        Tuple of (p1, p2, p3) where p2 is vertex (knee), or None if invalid
    """
    if not landmarks or len(landmarks) < 28:
        return None
    
    hip = landmarks[23]
    knee = landmarks[25]
    ankle = landmarks[27]
    
    # Check visibility
    if hip[3] < 0.2 or knee[3] < 0.2 or ankle[3] < 0.2:
        return None
    
    # Return hip, knee (vertex), ankle
    p1 = (hip[0], hip[1])
    p2 = (knee[0], knee[1])
    p3 = (ankle[0], ankle[1])
    
    return (p1, p2, p3)


def get_back_knee_points(landmarks: List[Tuple], frame_shape: Tuple[int, int]) -> Optional[Tuple]:
    """Get points for back knee angle visualization.
    
    Uses landmarks: 24 (right hip), 26 (right knee), 28 (right ankle).
    
    Args:
        landmarks: List of (x, y, z, vis) tuples in pixel coordinates
        frame_shape: (height, width) of frame
        
    Returns:
        Tuple of (p1, p2, p3) where p2 is vertex (knee), or None if invalid
    """
    if not landmarks or len(landmarks) < 29:
        return None
    
    hip = landmarks[24]
    knee = landmarks[26]
    ankle = landmarks[28]
    
    # Check visibility
    if hip[3] < 0.2 or knee[3] < 0.2 or ankle[3] < 0.2:
        return None
    
    # Return hip, knee (vertex), ankle
    p1 = (hip[0], hip[1])
    p2 = (knee[0], knee[1])
    p3 = (ankle[0], ankle[1])
    
    return (p1, p2, p3)


def get_back_foot_points(landmarks: List[Tuple], frame_shape: Tuple[int, int]) -> Optional[Tuple]:
    """Get points for back foot angle visualization.
    
    Uses landmarks: 30 (right heel), 32 (right toe) with a horizontal reference.
    
    Args:
        landmarks: List of (x, y, z, vis) tuples in pixel coordinates
        frame_shape: (height, width) of frame
        
    Returns:
        Tuple of (p1, p2, p3) where p2 is vertex (heel), or None if invalid
    """
    if not landmarks or len(landmarks) < 33:
        return None
    
    heel = landmarks[30]
    toe = landmarks[32]
    
    # Check visibility
    if heel[3] < 0.2 or toe[3] < 0.2:
        return None
    
    # Create horizontal reference point from heel
    p1 = (heel[0] + 50, heel[1])  # Point to the right (horizontal reference)
    p2 = (heel[0], heel[1])       # Heel (vertex)
    p3 = (toe[0], toe[1])         # Toe
    
    return (p1, p2, p3)


def get_lateral_flexion_points(landmarks: List[Tuple], frame_shape: Tuple[int, int]) -> Optional[Tuple]:
    """Get points for lateral flexion angle visualization.
    
    Uses mid-hip as vertex, with vertical reference and head position.
    
    Args:
        landmarks: List of (x, y, z, vis) tuples in pixel coordinates
        frame_shape: (height, width) of frame
        
    Returns:
        Tuple of (p1, p2, p3) where p2 is vertex (mid-hip), or None if invalid
    """
    if not landmarks or len(landmarks) < 25:
        return None
    
    nose = landmarks[0]
    left_hip = landmarks[23]
    right_hip = landmarks[24]
    
    # Check visibility
    if nose[3] < 0.2 or left_hip[3] < 0.2 or right_hip[3] < 0.2:
        return None
    
    # Mid-point of hips
    mid_hip_x = (left_hip[0] + right_hip[0]) / 2
    mid_hip_y = (left_hip[1] + right_hip[1]) / 2
    
    # Vertical reference point (straight up)
    p1 = (mid_hip_x, mid_hip_y - 100)  # Vertical reference
    p2 = (mid_hip_x, mid_hip_y)         # Mid-hip (vertex)
    p3 = (nose[0], nose[1])             # Head
    
    return (p1, p2, p3)


def get_bowling_arm_points(landmarks: List[Tuple], frame_shape: Tuple[int, int]) -> Optional[Tuple]:
    """Get points for bowling arm angle visualization.
    
    Uses right shoulder as vertex, with horizontal reference and wrist position.
    
    Args:
        landmarks: List of (x, y, z, vis) tuples in pixel coordinates
        frame_shape: (height, width) of frame
        
    Returns:
        Tuple of (p1, p2, p3) where p2 is vertex (shoulder), or None if invalid
    """
    if not landmarks or len(landmarks) < 17:
        return None
    
    shoulder = landmarks[12]
    wrist = landmarks[16]
    
    # Check visibility
    if shoulder[3] < 0.2 or wrist[3] < 0.2:
        return None
    
    # Horizontal reference point
    p1 = (shoulder[0] + 100, shoulder[1])  # Horizontal reference
    p2 = (shoulder[0], shoulder[1])         # Shoulder (vertex)
    p3 = (wrist[0], wrist[1])               # Wrist
    
    return (p1, p2, p3)


def get_non_bowling_arm_points(landmarks: List[Tuple], frame_shape: Tuple[int, int]) -> Optional[Tuple]:
    """Get points for non-bowling arm angle visualization.
    
    Uses left elbow as vertex, with shoulder and wrist positions.
    
    Args:
        landmarks: List of (x, y, z, vis) tuples in pixel coordinates
        frame_shape: (height, width) of frame
        
    Returns:
        Tuple of (p1, p2, p3) where p2 is vertex (elbow), or None if invalid
    """
    if not landmarks or len(landmarks) < 16:
        return None
    
    shoulder = landmarks[11]
    elbow = landmarks[13]
    wrist = landmarks[15]
    
    # Check visibility
    if shoulder[3] < 0.2 or elbow[3] < 0.2 or wrist[3] < 0.2:
        return None
    
    p1 = (shoulder[0], shoulder[1])  # Shoulder
    p2 = (elbow[0], elbow[1])        # Elbow (vertex)
    p3 = (wrist[0], wrist[1])        # Wrist
    
    return (p1, p2, p3)


# Angle registry
ANGLE_REGISTRY = {
    'front_knee': get_front_knee_points,
    'back_knee': get_back_knee_points,
    'back_foot': get_back_foot_points,
    'lateral_flexion': get_lateral_flexion_points,
    'bowling_arm': get_bowling_arm_points,
    'non_bowling_arm': get_non_bowling_arm_points,
}


def get_angle_function(angle_name: str):
    """Get angle point extractor function by name.
    
    Args:
        angle_name: Name of angle (e.g., 'front_knee', 'back_knee')
        
    Returns:
        Angle function, or None if not found
    """
    return ANGLE_REGISTRY.get(angle_name)


def get_all_angles():
    """Get list of all registered angle names."""
    return list(ANGLE_REGISTRY.keys())
