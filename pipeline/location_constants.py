#pipeline/location_constants.py
'''--------------------------------------------------------------------------
This module contains constants for file locations used in the pipeline.
-------------------------------------------------------------------------'''

#Locations

#The metadata files
session_metadata = f"/session_info.json"
bowler_metadata = f"/bowler_info.json"
bowler_image = f"/bowler_image.jpg"

#The input videos and initial events
input_back_view = f"/a_inputs/input_back_view.mp4"
input_side_view = f"/a_inputs/input_side_view.mp4"
initial_back_events = f"/a_inputs/input_back_events.json"
initial_side_events = f"/a_inputs/input_side_events.json"

#Preprocessed videos and events
final_back_view = f"/b_clips/back_view.mp4"
final_side_view = f"/b_clips/side_view.mp4"
final_back_events = f"/b_clips/back_view_events.json"
final_side_events = f"/b_clips/side_view_events.json"

#Keypoints and angles
back_view_keypoints = f"/c_keypoints/back_view_keypoints.csv"
side_view_keypoints = f"/c_keypoints/side_view_keypoints.csv"
back_view_angles = f"/c_keypoints/back_view_angles.csv"
side_view_angles = f"/c_keypoints/side_view_angles.csv"

#Analysis results
extracted_metrics = f"/d_analysis/extracted_metrics.json"
analyzed_metrics = f"/d_analysis/analyzed_metrics.json"
scores = f"/d_analysis/scores.json"

#The results
report_json = f"/results/report.json"
report_html = f"/results/report.html"
screenshots = f"/results/screenshots"  # Base directory for all screenshots
#feel free to add more
