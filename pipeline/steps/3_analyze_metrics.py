'''
This module contains the functions to analyze the metrics from the extracted keypoints.

The structure of this is basically 1 main simple function which calls the metric registry and uses that to basically
analyze the keypoints and output the metrics. This means this file will not have to be changed when new metrics are added.

Each metric itself will handle the extraction of the data it needs from the keypoints and events. It will handle the actual
analysis logic as well. It will handle the writing to the results/report.json as well.

The structure of each metric folder should be something like this:
pipeline/metrics/<metric_name>/
    - <metric_name>.py  # Main module for the metric
    - extract_<metric_name>.py  # Function to extract necessary data from keypoints/events
    - analyze_<metric_name>.py  # Function to analyze the extracted data
    - add_screenshots_<metric_name>.py  # Function to add screenshots to report
    - add_html_<metric_name>.py  # Function to generate HTML snippet for report
    - <metric_name>.yaml  # Configuration/rules for the metric

For the screenshots, there will be a separate screenshot engine in Step 4.1 which will handle generating the screenshots based on
the instructions provided here. In the old pipeline this was step 7 stage 2.

So the structure of step 3 is that first the metadata is written to results/report.json. Then each metric is called in order
using the registry. Each metric extracts its own data, analyzes it, says which screenshots it wants and writes to the report.json.
At the end, the overall scoring function is also run which adds its section to the top.

This results thing should have a similar structure to the old pipeline's results/report.json(remember some things are optional):
Header:
- Bowler Info
- Bowler Image
- Session Info
- Score Summary(for now it has only one field which is overall score)
- Classification Summary
    - Name
    - Description
    - Analysis Text
    - Subsections(could be multiple)
        - Name
        - Description
        - Analysis Text
        - Data(will vary based on classification, could be angles over time, counts, etc)
- Video Summary(Has whether the videos were uploaded or not, and the events that were tagged, along with the screenshots)
Metrics(for each metric):
- Name
- Description
- Score
- Analysis Text
- Subsections(could be multiple)
    - Name
    - Description
    - Score
    - Analysis Text
    - Data(will vary based on metric, could be angles over time, counts, etc)
- Screenshots(will match up with the analyzed subsections)


All the screenshots have the specific format needed for the screenshot engine to pick them up and generate the images in Step 4.1.
'''