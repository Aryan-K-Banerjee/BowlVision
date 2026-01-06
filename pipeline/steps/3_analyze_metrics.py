'''
This module contains the functions to analyze the metrics from the extracted keypoints.

The structure of this is basically 1 main simple function which calls the metric registry and uses that to basically
analyze the keypoints and output the metrics. This means this file will not have to be changed when new metrics are added.

Each metric itself will handle the extraction of the data it needs from the keypoints and events. It will handle the actual
analysis logic as well. It will handle the writing to the results/report.json as well.
'''