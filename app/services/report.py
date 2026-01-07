"""
Report Service
Handles report data loading and rendering for the report page.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple


SESSION_DIR = 'data/run'


def get_report_path() -> Path:
    """Get the path to the current run's report JSON."""
    return Path(SESSION_DIR) / 'results' / 'results.json'


def load_report_data() -> Tuple[Optional[dict], Optional[str]]:
    """
    Load report data from the current run.
    
    Returns:
        Tuple of (report_data, error_message)
    """
    report_path = get_report_path()
    
    if not report_path.exists():
        return None, f"Report not found at {report_path}"
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data, None
    except Exception as e:
        return None, f"Error loading report: {str(e)}"


def format_date(date_str: str) -> str:
    """Format ISO date string for display."""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%B %d, %Y at %I:%M %p')
    except:
        return date_str


def get_relative_path(path: str) -> str:
    """Convert absolute path to relative path for the report page."""
    if not path:
        return ''
    
    # If already relative or starts with results folder, adjust
    path_obj = Path(path)
    
    # Handle paths like "data/run/results/screenshots/..."
    if 'results' in path_obj.parts:
        idx = list(path_obj.parts).index('results')
        return '/'.join(path_obj.parts[idx + 1:])
    
    # Handle paths like "data/run/a_inputs/..."
    if 'a_inputs' in path_obj.parts:
        return f"/report-asset/{path}"
    
    return path


def generate_score_dial_html(score: float, size: int = 250) -> str:
    """Generate SVG score dial HTML."""
    radius = (size - 24) / 2
    circumference = 2 * 3.14159 * radius
    offset = circumference - (score / 100) * circumference
    
    return f'''<div class="score_dial">
      <svg width="{size}" height="{size}">
        <circle class="dial_bg" cx="{size/2}" cy="{size/2}" r="{radius}"/>
        <circle class="dial_fill" cx="{size/2}" cy="{size/2}" r="{radius}" 
                stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"/>
      </svg>
      <div class="score_value">
        <div class="score_number">{score:.1f}</div>
        <div class="score_max">/ 100</div>
      </div>
    </div>'''


def generate_mini_dial_html(score: float) -> str:
    """Generate mini dial HTML for metric cards."""
    radius = 19
    circumference = 2 * 3.14159 * radius
    offset = circumference - (score / 100) * circumference
    
    return f'''<div class="mini_dial">
      <svg width="48" height="48">
        <circle class="dial_bg" cx="24" cy="24" r="{radius}"/>
        <circle class="dial_fill" cx="24" cy="24" r="{radius}" 
                stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"/>
      </svg>
      <span class="mini_score">{score:.0f}</span>
    </div>'''


def generate_thumbnails_html(video_summary: dict) -> str:
    """Generate compact thumbnails grid HTML."""
    event_names = ['Jump', 'BFC', 'FFC', 'Release']
    
    def make_row(view: str) -> str:
        view_data = video_summary.get(f'{view}_view', {})
        exists = view_data.get('exists', False)
        disabled_class = 'disabled' if not exists else ''
        
        thumbnails = []
        for event in event_names:
            event_lower = event.lower()
            output_name = f'video_summary_{view}_{event_lower}'
            
            thumbnails.append(f'''<div class="thumbnail" data-output="{output_name}">
              <img class="switchable-image" data-base="/report-asset/data/run/results/screenshots/{output_name}" 
                   src="/report-asset/data/run/results/screenshots/{output_name}_skeleton.png" alt="{event}">
              <span class="event_label">{event}</span>
            </div>''')
        
        return f'''<div class="thumbnail_row_wrapper {disabled_class}">
          <div class="row_label_box"><span class="row_label_text">{view.upper()}</span></div>
          <div class="thumbnail_row">{''.join(thumbnails)}</div>
        </div>'''
    
    return f'''<div class="thumbnails_grid_compact">
      {make_row('side')}
      {make_row('back')}
    </div>'''


def generate_classification_cards_html(classifications: list) -> str:
    """Generate classification card HTML."""
    if not classifications:
        return '<div class="placeholder">No classifications available</div>'
    
    cards = []
    for i, c in enumerate(classifications):
        rating = c.get('rating', 'N/A')
        rating_display = rating.replace('_', ' ')
        value = c.get('value')
        unit = c.get('unit', '')
        
        value_html = ''
        if value is not None:
            value_html = f'''<div class="item_score">
          <div class="value">{value:.1f}</div>
          <div class="unit">{unit}</div>
        </div>'''
        
        cards.append(f'''<div class="item_card" data-type="classification" data-index="{i}">
        <span class="item_chip chip_classification">{rating_display}</span>
        <div class="item_info">
          <h4>{c.get('name', 'Unknown')}</h4>
          <p>{c.get('description', '')}</p>
        </div>
        {value_html}
      </div>''')
    
    return '\n'.join(cards)


def generate_metric_cards_html(metrics: list) -> str:
    """Generate metric card HTML."""
    if not metrics:
        return '<div class="placeholder">No metrics available</div>'
    
    cards = []
    for i, m in enumerate(metrics):
        score = m.get('score', 0) or 0
        rating = m.get('rating', 'N/A')
        rating_display = rating.replace('_', ' ')
        rating_class = rating.replace(' ', '_').lower()
        
        mini_dial = generate_mini_dial_html(score)
        
        cards.append(f'''<div class="item_card" data-type="metric" data-index="{i}">
        {mini_dial}
        <div class="item_info">
          <h4>{m.get('name', 'Unknown')}</h4>
          <p>{m.get('description', '')}</p>
        </div>
        <div class="item_score">
          <div class="value">{score:.1f}</div>
          <span class="rating {rating_class}">{rating_display}</span>
        </div>
      </div>''')
    
    return '\n'.join(cards)


def get_quick_prompts() -> list:
    """Get quick prompts from knowledge.json."""
    try:
        knowledge_path = Path('rag/knowledge.json')
        with open(knowledge_path, 'r', encoding='utf-8') as f:
            knowledge = json.load(f)
        return knowledge.get('ui_copy', {}).get('quick_prompts', [])
    except:
        return [
            "Summarize my action in 5 bullets",
            "Top 3 fixes with drills",
            "Give me a 2-week plan"
        ]
