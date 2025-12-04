'''--------------------------------------------------------------
This file contains the orchestration function to extract keypoints 
from videos in the pipeline.

The skeleton extraction step:
1. Checks which videos exist (back/side views)
2. Uses MediaPipe Pose to extract 33 landmarks per frame
3. Saves keypoints to CSV files in c_keypoints/ directory

This is the orchestrator - it calls the business logic from the logic folder.
--------------------------------------------------------------'''

#Imports
from pipeline.logic.step_3_get_skeleton.extract_skeleton import extract_skeleton_keypoints
from pipeline import location_constants as lc


def get_skeletons(session_dir: str, back_view_exists: bool, side_view_exists: bool):
    """Orchestrate the extraction of skeleton keypoints from videos.
    
    Args:
        session_dir: Path to the session directory
        back_view_exists: Whether the back view video exists
        side_view_exists: Whether the side view video exists
    """
    # Extract keypoints from back view
    if not back_view_exists:
        print("    GET_SKELETONS: Back View doesn't exist, skipping")
    else:
        print("    GET_SKELETONS: Extracting keypoints from Back View...")
        back_video = session_dir + lc.final_back_view
        back_keypoints = session_dir + lc.back_view_keypoints
        
        extract_skeleton_keypoints(back_video, back_keypoints)
    
    # Extract keypoints from side view
    if not side_view_exists:
        print("    GET_SKELETONS: Side View doesn't exist, skipping")
    else:
        print("    GET_SKELETONS: Extracting keypoints from Side View...")
        side_video = session_dir + lc.final_side_view
        side_keypoints = session_dir + lc.side_view_keypoints
        
        extract_skeleton_keypoints(side_video, side_keypoints)
    
    print("    GET_SKELETONS: Skeleton extraction complete")