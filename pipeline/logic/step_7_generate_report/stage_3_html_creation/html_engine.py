"""
Stage 3 - HTML Creation Engine

Renders final HTML report from report.json and generated screenshots.
"""

import json
import shutil
from pathlib import Path


def generate_html_report(session_dir: str, report_json_path: str) -> str:
    """Generate HTML report from report.json.
    
    Args:
        session_dir: Path to session directory
        report_json_path: Path to report.json
        
    Returns:
        Path to generated report.html
    """
    session_dir = Path(session_dir)
    
    print("    HTML_ENGINE: Starting HTML generation...")
    
    # Load report.json
    with open(report_json_path, 'r') as f:
        report_data = json.load(f)
    
    # Load HTML template
    template_path = Path(__file__).parent / 'templates' / 'report_template.html'
    with open(template_path, 'r') as f:
        template = f.read()
    
    # Copy CSS to results directory
    css_source = Path(__file__).parent / 'static' / 'report.css'
    css_dest = session_dir / 'results' / 'static' / 'report.css'
    css_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(css_source, css_dest)
    
    # Extract header data for template placeholders
    header = report_data.get('header', {})
    session_info = header.get('session_info', {})
    bowler_info = header.get('bowler_info', {})
    
    # Replace placeholders
    replacements = {
        '{{ session_name }}': session_info.get('name', 'Unknown Session'),
        '{{ session_description }}': session_info.get('description', 'No description'),
        '{{ session_date }}': session_info.get('date', 'N/A'),
        '{{ bowler_name }}': bowler_info.get('name', 'Unknown Bowler'),
        '{{ bowler_type }}': bowler_info.get('type', 'Unknown'),
        '{{ bowler_hand }}': bowler_info.get('hand', 'Unknown'),
        '{{ score_summary }}': header.get('score_summary', 'No scores'),
        '__REPORT_JSON__': json.dumps(report_data)
    }
    
    html = template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, str(value))
    
    # Write HTML report
    output_path = session_dir / 'results' / 'report.html'
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"    HTML_ENGINE: Generated {output_path}")
    
    return str(output_path)
