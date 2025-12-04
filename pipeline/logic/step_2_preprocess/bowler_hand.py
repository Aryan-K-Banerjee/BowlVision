'''--------------------------------------------------------------
This file contains the business logic to check the bowler's hand
and flip the video horizontally if needed.

The bowler_info.json file contains a "hand" field that can be "Left" or "Right".
If the bowler is left-handed, we flip the video horizontally when preprocessing.
This allows the analysis to work with a standardized orientation (right-handed).
At the end of the pipeline, we can flip it back if needed.
--------------------------------------------------------------'''

#Imports
import json
import os
from typing import Optional


def get_bowler_hand(session_dir: str) -> Optional[str]:
    """Get the bowler's hand from bowler_info.json.
    
    Args:
        session_dir: Path to the session directory
        
    Returns:
        "Left" or "Right" if found, None if file doesn't exist or hand not specified
    """
    bowler_info_path = os.path.join(session_dir, "bowler_info.json")
    
    if not os.path.exists(bowler_info_path):
        print(f"        BOWLER_HAND: bowler_info.json not found at {bowler_info_path}")
        return None
    
    try:
        with open(bowler_info_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        hand = data.get('hand')
        if hand:
            print(f"        BOWLER_HAND: Bowler is {hand}-handed")
            return hand
        else:
            print(f"        BOWLER_HAND: Hand not specified in bowler_info.json")
            return None
            
    except Exception as e:
        print(f"        BOWLER_HAND: Error reading bowler_info.json: {e}")
        return None


def should_flip_video(hand: Optional[str]) -> bool:
    """Determine if the video should be flipped based on bowler's hand.
    
    Args:
        hand: Bowler's hand ("Left" or "Right")
        
    Returns:
        True if video should be flipped (left-handed bowler), False otherwise
    """
    if hand is None:
        return False
    
    return hand.lower() == "left"
