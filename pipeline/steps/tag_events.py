'''--------------------------------------------------------------
This file orchestrates the tagging of events in the pipeline.
It will get the session directory and call the necessary functions
to tag events in the videos based on their existence.
'''
#Imports
from pipeline.logic.step_1_tag_events.tag_videos import tag_video
from pipeline import location_constants as lc

def tag_events(session_dir: str, back_view_exists: bool, side_view_exists: bool):
    """Orchestrate the tagging of events for back and side views.
    
    Args:
        session_dir: Path to the session directory
        back_view_exists: Whether the back view video exists
        side_view_exists: Whether the side view video exists
    """
    #Tagging back view
    if not back_view_exists:
        print("    TAG_EVENTS: Back View doesn't exist, skipping")
    else:
        print("    TAG_EVENTS: Tagging events for Back View...")
        back_video_path = session_dir + lc.input_back_view
        back_events_path = session_dir + lc.initial_back_events
        tag_video(back_video_path, back_events_path)
    
    #Tagging side view
    if not side_view_exists:
        print("    TAG_EVENTS: Side View doesn't exist, skipping")
    else:
        print("    TAG_EVENTS: Tagging events for Side View...")
        side_video_path = session_dir + lc.input_side_view
        side_events_path = session_dir + lc.initial_side_events
        tag_video(side_video_path, side_events_path)
