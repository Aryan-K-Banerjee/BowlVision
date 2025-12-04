# core/pipeline.py
'''--------------------------------------------------------------------------
This has the main pipeline which is run on videos after
they're uploaded and the directory is setup.
-------------------------------------------------------------------------'''

#importing modules
from pathlib import Path
from core.cv.verify_videos import verify_video_exists
from core.cv.tag_events import tag_events
from core.cv.preprocess_videos import trim_video
from core.cv.extract_joints import extract_joints
from core.angles.calculate_angles import calculate_angles
from core.analysis.extract_metrics import extract_metrics
from core.analysis.analyzer import analyze_metrics
from core.report.build import build_report

#The main pipeline function
def pipeline(session_dir: str):
    print(f"Starting pipeline for session: {session_dir}\n")
    
    #Locations
    session_metadata_location = f"{session_dir}/session_info.json"
    bowler_metadata_location = f"{session_dir}/bowler_info.json"
    back_view_location_initial = f"{session_dir}/a_inputs/back_view_input.mp4"
    side_view_location_initial = f"{session_dir}/a_inputs/side_view_input.mp4"
    back_view_events_initial = f"{session_dir}/b_events/back_view_events_initial.json"
    side_view_events_initial = f"{session_dir}/b_events/side_view_events_initial.json"
    
    back_view_location = f"{session_dir}/c_clips/back_view.mp4"
    side_view_location = f"{session_dir}/c_clips/side_view.mp4"
    back_view_events_location = f"{session_dir}/c_clips/back_view_events.json"
    side_view_events_location = f"{session_dir}/c_clips/side_view_events.json"
    back_view_keypoints_location = f"{session_dir}/d_keypoints/back_view_keypoints.csv"
    side_view_keypoints_location = f"{session_dir}/d_keypoints/side_view_keypoints.csv"
    back_view_angles_location = f"{session_dir}/e_angles/back_view_angles.csv"
    side_view_angles_location = f"{session_dir}/e_angles/side_view_angles.csv"
    extracted_metrics_location = f"{session_dir}/f_analysis/extracted_metrics.json"
    analysis_results_location = f"{session_dir}/f_analysis/analysis_results.json"


    # Step 0: Verify the videos exist
    print("Step 0: Verifying input videos...")
    back_view_exists = verify_video_exists("Back View", back_view_location_initial)
    side_view_exists = verify_video_exists("Side View", side_view_location_initial)

    # Step 1: Tag events in both videos
    print("Step 1: Tagging events in videos...")
    # tag_events("Back View", back_view_exists, back_view_location_initial, back_view_events_initial)
    # tag_events("Side View", side_view_exists, side_view_location_initial, side_view_events_initial)

    # Step 2: Trim the video 2 seconds on either side of the 2 events and save updated events JSON
    print("Step 2: Trimming videos based on tagged events...")
    # trim_video("Back View", back_view_exists,back_view_location_initial, back_view_events_initial, back_view_location, back_view_events_location)
    # trim_video("Side View", side_view_exists, side_view_location_initial, side_view_events_initial, side_view_location, side_view_events_location)

    # Step 3: get the bowlers joints from the trimmed videos
    print("Step 3: Extracting joints from trimmed videos...")
    # extract_joints("Back View", back_view_exists, back_view_location, back_view_keypoints_location)
    # extract_joints("Side View", side_view_exists, side_view_location, side_view_keypoints_location)

    # Step 4: Calculate angles from keypoints
    print("Step 4: Calculating angles from extracted keypoints...")
    calculate_angles(back_view_exists, side_view_exists, back_view_keypoints_location, side_view_keypoints_location, back_view_angles_location, side_view_angles_location)

    # Step 5: Extract metrics from angles
    print("Step 5: Extracting metrics from calculated angles...")
    extract_metrics(back_view_exists, side_view_exists, back_view_angles_location, side_view_angles_location, back_view_events_location, side_view_events_location, extracted_metrics_location)
    
    # Step 6: Analyze the extracted metrics
    print("Step 6: Analyzing extracted metrics...")
    analyze_metrics(session_metadata_location, bowler_metadata_location, back_view_exists, side_view_exists, back_view_events_location, side_view_events_location, extracted_metrics_location, analysis_results_location)
    
    # Step 7: Generate HTML report
    print("Step 7: Generating HTML report...")
    back_video_path = Path(back_view_location) if back_view_exists else None
    side_video_path = Path(side_view_location) if side_view_exists else None
    back_joints_path = Path(back_view_keypoints_location) if back_view_exists else None
    side_joints_path = Path(side_view_keypoints_location) if side_view_exists else None
    back_angles_path = Path(back_view_angles_location) if back_view_exists else None
    side_angles_path = Path(side_view_angles_location) if side_view_exists else None
    
    report_path = build_report(
        Path(session_dir),
        Path(analysis_results_location),
        back_video_path,
        side_video_path,
        back_joints_path,
        side_joints_path,
        back_angles_path,
        side_angles_path
    )
    print(f"Report generated: {report_path}")
    
    print(f"\n✓ Pipeline completed successfully for session: {session_dir}")