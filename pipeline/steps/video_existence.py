'''--------------------------------------------------------------
This file has a function that checks whether the input videos exist
in the session directory.
--------------------------------------------------------------'''

#imports
import os
from pipeline import location_constants as lc

def check_videos_exist(session_dir: str) -> tuple[bool, bool]:
    """Check whether the input videos exist in the session directory.
    
    Args:
        session_dir: Path to the session directory
        
    Returns:
        Tuple of (back_view_exists, side_view_exists)
    """
    #Construct full paths using location constants
    back_view_path = session_dir + lc.input_back_view
    side_view_path = session_dir + lc.input_side_view
    
    #Check existence
    back_exists = os.path.exists(back_view_path)
    side_exists = os.path.exists(side_view_path)
    
    #Log results
    print(f"    VIDEO_EXISTENCE: Back View {'exists' if back_exists else 'does not exist'}")
    print(f"    VIDEO_EXISTENCE: Side View {'exists' if side_exists else 'does not exist'}")
    
    return back_exists, side_exists