'''
This is the orchestrator for generating the final videos

It will first check whether the back/side videos exist using the values passed in
Then it will check whether the bowler was a lefty or righty, it can reuse the functions
used early in the pipeline for this and we can pass a flag into the individual video
functions and they can use the function to flip the video if needed which also exists
early in the pipeline.

It will generate 3 videos for now, all from the final back/side views:
    - Events video(pauses for 2 seconds at each event)
    - Green Skeleton video(with skeleton overlay, also pauses for 2 seconds at each event)
    - Overlay video(original final video with skeleton overlay, also pauses for 2 seconds at each event)

It will save these videos to the results/videos directory
'''