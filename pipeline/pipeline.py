#pipeline/pipeline.py
'''--------------------------------------------------------------------------
This is the main pipeline running file. It calls each steps orchestrator.
Each steps orchestrator calls the relevant code functions to perform its task.

The Flow:
1: The frontend allows the user to create a session and upload 1-2 videos.
2: The frontend sets up the session directory with the correct structure.
    {session_dir}/
        bowler_info.json
        session_info.json
        a_inputs/
            input_back_view.mp4
            input_side_view.mp4
        b_clips/
        c_keypoints/
        d_analysis/
        results/
            #this will have the final report, the screenshots, and videos
(We are implementing the next part)
3: The pipeline is called with the session directory path.
    Luckily the pipeline already works, we are doing a major refactor to improve
    code structure, readability, and maintainability. And just improve overall quality.
    However it is important to understand it is only a refactor, the overall flow 
    remains the same.

    The new flow will have the same steps but now, we will basically feed in the session_dir
    and each step will derive the file locations from there. This way we avoid
    passing too many parameters around. And we will feed in whether the back/side videos
    exist at the start of the pipeline and pass those flags down to the relevant steps.

    Each orchestrator function will get the locations it needs from the session_dir
    and the location_constants module. This will make it easier to manage file locations
    and avoid hardcoding paths all over the codebase. And we will pass in the existence flags
    to the relevant steps so they can decide whether to process a view or skip it. If the video
    exists, the step will process it, otherwise it will skip it gracefully. And the orchestrator
    files will not have the actual processing logic, just the orchestration logic, so the actual
    logic will be in seperate files and that will again check if the view exists before processing
    but the orchestrator will directly pass the locations in.
    
    Already refactored:
        -Verify video existence
        -Tag events
        -Preprocess videos
        -Extract keypoints
        -Calculate angles
        -Extract metrics
    
    Next Goal:
        -Refactor the analyzer step
        -Refactor the report building step
------------------------------------------------------------------------'''

#imports
from pipeline.steps.video_existence import check_videos_exist
from pipeline.steps.tag_events import tag_events
from pipeline.steps.preprocess import preprocess_videos
from pipeline.steps.get_skeleton import get_skeletons
from pipeline.steps.calculate_angles import calculate_angles
from pipeline.steps.extract_metrics import extract_metrics
from pipeline.steps.analyze import run_analysis
from pipeline.steps.generate_report import generate_report

def run_pipeline(session_dir: str):
    print("PIPELINE: Starting analysis pipeline for session:", session_dir)

    #Step 0: Verify videos exist
    print("PIPELINE: Step 0 - Verifying video existence")
    back_exists, side_exists = check_videos_exist(session_dir)

    #Step 1: Tag events
    print("PIPELINE: Step 1 - Tagging events in videos")
    tag_events(session_dir, back_exists, side_exists)

    #Step 2: Preprocess videos
    print("PIPELINE: Step 2 - Preprocessing videos")
    preprocess_videos(session_dir, back_exists, side_exists)

    #Step 3: Extract keypoints
    print("PIPELINE: Step 3 - Extracting keypoints")
    get_skeletons(session_dir, back_exists, side_exists)

    #Step 4: Calculate angles
    print("PIPELINE: Step 4 - Calculating angles")
    calculate_angles(session_dir, back_exists, side_exists)

    #Step 5: Extract metrics
    print("PIPELINE: Step 5 - Extracting metrics")
    extract_metrics(session_dir, back_exists, side_exists)

    #Step 6: Run Analysis
    print("PIPELINE: Step 6 - Running analysis")
    run_analysis(session_dir, back_exists, side_exists)

    #Step 7: Generate Final Artifacts
    print("PIPELINE: Step 7 - Generating final artifacts")
    print("    PIPELINE: Step 7.1 - Generating videos")
    generate_videos(session_dir, back_exists, side_exists)
    print("    PIPELINE: Step 7.2 - Generating report")
    generate_report(session_dir, back_exists, side_exists)





