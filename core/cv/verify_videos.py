# core/cv/verify_videos.py
'''--------------------------------------------------------------------------
This module verifies the existence of input videos before processing.

Inputs:
- video_name: A string representing the name of the video (e.g., "Back View", "Side View").
- video_path: The file path to the video that needs to be verified.

Outputs:
- A boolean indicating whether the video exists (True) or not (False).
--------------------------------------------------------------------------'''

#imports
import os

#Function to verify video existence
def verify_video_exists(video_name: str, video_path: str) -> bool:
    if os.path.exists(video_path):
        print(f"{video_name} exists.")
        return True
    else:
        print(f"{video_name} does not exist.")
        return False