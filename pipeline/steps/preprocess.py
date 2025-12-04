'''--------------------------------------------------------------------------
This file orchestrates the preprocessing of videos in the pipeline.

The preprocessing step:
1. Checks whether the back and side views exist
2. Trims the videos to 2 seconds before the jump and 2 seconds after the release
3. Updates the events.json file with adjusted frame numbers relative to trimmed clips
4. Flips the video horizontally if the bowler's hand is "Left"
5. Generates the final preprocessed videos and events files

This is the orchestrator - it calls the business logic functions from the logic folder.
--------------------------------------------------------------------------'''

#Imports
from pipeline.logic.step_2_preprocess.bowler_hand import get_bowler_hand, should_flip_video
from pipeline.logic.step_2_preprocess.trim_video import trim_and_process_video
from pipeline import location_constants as lc


def preprocess_videos(session_dir: str, back_view_exists: bool, side_view_exists: bool):
    """Orchestrate the preprocessing of videos.
    
    Args:
        session_dir: Path to the session directory
        back_view_exists: Whether the back view video exists
        side_view_exists: Whether the side view video exists
    """
    # Get bowler's hand to determine if we need to flip
    print("    PREPROCESS: Checking bowler hand...")
    bowler_hand = get_bowler_hand(session_dir)
    flip = should_flip_video(bowler_hand)
    
    if flip:
        print("    PREPROCESS: Will flip videos horizontally for left-handed bowler")
    else:
        print("    PREPROCESS: No flipping needed (right-handed or hand not specified)")
    
    # Preprocess back view
    if not back_view_exists:
        print("    PREPROCESS: Back View doesn't exist, skipping")
    else:
        print("    PREPROCESS: Preprocessing Back View...")
        back_video_input = session_dir + lc.input_back_view
        back_events_input = session_dir + lc.initial_back_events
        back_video_output = session_dir + lc.final_back_view
        back_events_output = session_dir + lc.final_back_events
        
        trim_and_process_video(
            back_video_input,
            back_events_input,
            back_video_output,
            back_events_output,
            flip_horizontal=flip
        )
    
    # Preprocess side view
    if not side_view_exists:
        print("    PREPROCESS: Side View doesn't exist, skipping")
    else:
        print("    PREPROCESS: Preprocessing Side View...")
        side_video_input = session_dir + lc.input_side_view
        side_events_input = session_dir + lc.initial_side_events
        side_video_output = session_dir + lc.final_side_view
        side_events_output = session_dir + lc.final_side_events
        
        trim_and_process_video(
            side_video_input,
            side_events_input,
            side_video_output,
            side_events_output,
            flip_horizontal=flip
        )
    
    print("    PREPROCESS: Preprocessing complete")