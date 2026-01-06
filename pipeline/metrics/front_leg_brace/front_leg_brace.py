'''
This module contains the top level function to analyze the front leg brace metric and generate the screenshots and html snippets.

Analyzing the front leg brace metric involves the following steps:
    1. Calls the extract front leg brace from extract_front_leg_brace.py to get the necessary front leg brace data.
    2. Calls the analyze front leg brace from analyze_front_leg_brace.py to do the actual analysis of the front leg brace data
       using the front_leg_brace.yaml file.
    3. Saves the results to the results/report.json file.
    4. Generates the screenshots and html snippets for the front leg brace metric which are in screenshots_front_leg_brace.py
       and html_front_leg_brace.py and will go into results/screenshots and report.html.
'''