"""
Step 4.3: Generate HTML Report
Generates results.html and results.css from results.json.
The report is a standalone page that displays all analysis data.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional


def generate_report(session_dir: str, log: Optional[Callable] = None) -> dict:
    """
    Generate HTML report from results.json.
    
    Args:
        session_dir: Path to session directory (e.g., 'data/run/')
        log: Optional logging callback
        
    Returns:
        dict with 'success' and 'output_paths' keys
    """
    def _log(msg: str, level: int = 1, log_type: str = 'info'):
        if log:
            log(msg, level, log_type)
        else:
            print(f"{'  ' * level}{msg}")
    
    _log("> Step 4.3: Generate report", 0, 'info')
    
    session_path = Path(session_dir)
    results_dir = session_path / 'results'
    results_json_path = results_dir / 'results.json'
    
    # Load results.json
    if not results_json_path.exists():
        _log(f"  ✗ results.json not found at {results_json_path}", 1, 'error')
        return {'success': False, 'output_paths': []}
    
    with open(results_json_path, 'r') as f:
        data = json.load(f)
    
    _log("  - Generating HTML report...", 1, 'info')
    
    # Generate CSS
    css_content = _generate_css()
    css_path = results_dir / 'results.css'
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_content)
    _log(f"      ✓ Generated {css_path.name}", 2, 'success')
    
    # Generate HTML
    html_content = _generate_html(data)
    html_path = results_dir / 'results.html'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    _log(f"      ✓ Generated {html_path.name}", 2, 'success')
    
    _log("  ✓ Report generation complete", 1, 'success')
    
    return {
        'success': True,
        'output_paths': [str(html_path), str(css_path)]
    }


def _generate_css() -> str:
    """Generate the CSS for the report page."""
    return '''/* ============== BowlVision Report Styles ============== */
:root {
  --bg: #0F1116;
  --card: #171A21;
  --card2: #1A1D26;
  --border: rgba(255, 255, 255, 0.12);
  --border-light: rgba(255, 255, 255, 0.08);
  --text: #EAEAF0;
  --muted: #B6BCCF;
  --muted2: #9AA0B5;
  --accent: #6EE7FF;
  --accent2: #A78BFA;
  --success: #4ADE80;
  --warning: #FBBF24;
  --error: #F87171;
  --shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
  --shadow-sm: 0 4px 12px rgba(0, 0, 0, 0.25);
}

*, *::before, *::after {
  box-sizing: border-box;
}

html { scroll-behavior: smooth; }

body {
  margin: 0;
  min-height: 100vh;
  background: radial-gradient(1400px 700px at 50% -300px, rgba(110, 231, 255, 0.08), transparent 60%), var(--bg);
  color: var(--text);
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.5;
}

/* ============== Navbar ============== */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
  padding: 0 24px;
  background-color: #181721;
  border-bottom: 1px solid #282835;
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar_left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bowlvision_logo {
  height: 50px;
  width: 50px;
}

.navbar_title {
  font-size: 25px;
  font-weight: 600;
  color: var(--text);
}

.navbar_right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.lfc_shoutout {
  font-size: 14px;
  font-weight: 400;
  color: var(--muted);
  white-space: nowrap;
}

.lfc_logo {
  height: 40px;
  width: 40px;
}

.progress_bar {
  display: flex;
  align-items: center;
}

.step, .active_step, .completed_step {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 30px;
  font-size: 15px;
  border-radius: 999px;
}

.step {
  color: var(--muted);
  padding: 4px 10px;
  background: #2A2A34;
}

.active_step {
  color: #181721;
  padding: 4px 12px;
  background: #84F0FA;
  font-weight: 600;
}

.completed_step {
  color: #84F0FA;
  padding: 4px 10px;
  background: #22343A;
  font-weight: 500;
}

.bar, .completed_bar {
  width: 28px;
  height: 10px;
}

.bar { background: #3A3A44; }
.completed_bar { background: #22343A; }

/* ============== Type Toggle (Sticky) ============== */
.type_toggle_container {
  position: sticky;
  top: 60px;
  z-index: 90;
  background: linear-gradient(180deg, var(--bg) 0%, var(--bg) 70%, transparent 100%);
  padding: 12px 0 20px;
  display: flex;
  justify-content: center;
}

.type_toggle {
  display: flex;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 4px;
  gap: 4px;
}

.type_btn {
  padding: 8px 20px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.type_btn:hover {
  color: var(--text);
  background: rgba(255, 255, 255, 0.05);
}

.type_btn.active {
  background: var(--accent);
  color: #181721;
}

/* ============== Main Container ============== */
.report_container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 24px 100px;
}

/* ============== Cards ============== */
.card {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.01));
  background-color: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: var(--shadow);
  margin-bottom: 24px;
  overflow: hidden;
}

.card_header {
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  gap: 12px;
}

.card_title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.card_subtitle {
  font-size: 13px;
  color: var(--muted);
  margin-left: auto;
}

.card_body {
  padding: 24px;
}

/* ============== Header Section ============== */
.header_grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.bowler_block, .session_block {
  display: flex;
  gap: 16px;
}

.bowler_image {
  width: 80px;
  height: 80px;
  border-radius: 12px;
  object-fit: cover;
  border: 2px solid var(--border);
  flex-shrink: 0;
}

.bowler_info h3, .session_info h3 {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.bowler_info .hand_badge {
  display: inline-block;
  padding: 2px 8px;
  background: rgba(110, 231, 255, 0.15);
  border: 1px solid rgba(110, 231, 255, 0.3);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--accent);
  margin-left: 8px;
}

.bowler_info p, .session_info p {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--muted);
}

.session_date {
  font-size: 12px;
  color: var(--muted2);
  margin-top: 4px !important;
}

/* ============== Summary Section (Merged Score + Video) ============== */
.summary_grid {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 32px;
  align-items: center;
}

.score_dial_container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 16px;
}

.score_dial_title {
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--muted);
  text-align: center;
}

.score_dial {
  position: relative;
  width: 250px;
  height: 250px;
}

.score_dial svg {
  transform: rotate(-90deg);
}

.dial_bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.1);
  stroke-width: 12;
}

.dial_fill {
  fill: none;
  stroke: var(--accent);
  stroke-width: 12;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.8s ease;
}

.score_value {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.score_number {
  font-size: 50px;
  font-weight: 700;
  color: var(--text);
}

.score_max {
  font-size: 14px;
  color: var(--muted);
}

.grade_badge {
  font-size: 20px;
  font-weight: 700;
  padding: 6px 16px;
  border-radius: 8px;
}

.grade_badge.A { background: rgba(74, 222, 128, 0.2); color: #4ADE80; border: 1px solid rgba(74, 222, 128, 0.3); }
.grade_badge.B { background: rgba(110, 231, 255, 0.2); color: #6EE7FF; border: 1px solid rgba(110, 231, 255, 0.3); }
.grade_badge.C { background: rgba(251, 191, 36, 0.2); color: #FBBF24; border: 1px solid rgba(251, 191, 36, 0.3); }
.grade_badge.D { background: rgba(251, 146, 60, 0.2); color: #FB923C; border: 1px solid rgba(251, 146, 60, 0.3); }
.grade_badge.F { background: rgba(248, 113, 113, 0.2); color: #F87171; border: 1px solid rgba(248, 113, 113, 0.3); }

/* Thumbnails Grid (2 rows x 4 cols) */
.thumbnails_grid_compact {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.thumbnail_row_wrapper {
  display: flex;
  align-items: stretch;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  overflow: hidden;
}

.thumbnail_row_wrapper.disabled {
  opacity: 0.4;
  pointer-events: none;
}

.row_label_box {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(110, 231, 255, 0.08);
  border-right: 1px solid var(--border-light);
  padding: 0 8px;
  min-width: 32px;
}

.row_label_text {
  font-size: 10px;
  color: var(--accent);
  font-weight: 700;
  writing-mode: vertical-lr;
  text-orientation: mixed;
  transform: rotate(180deg);
  letter-spacing: 1px;
}

.thumbnail_row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2px;
  padding: 4px;
  flex: 1;
}

.thumbnail {
  position: relative;
  aspect-ratio: 1;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.15s ease;
  max-width: 140px;
}

.thumbnail:hover {
  border-color: rgba(110, 231, 255, 0.6);
  transform: scale(1.08);
  z-index: 5;
}

.thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail .event_label {
  position: absolute;
  top: 3px;
  left: 3px;
  padding: 2px 6px;
  background: rgba(0, 0, 0, 0.8);
  border-radius: 3px;
  font-size: 10px;
  font-weight: 600;
  color: var(--text);
}

/* Video Panel */
.video_panel {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.video_panel video {
  width: 100%;
  aspect-ratio: 9/16;
  max-height: 210px;
  object-fit: contain;
  background: #000;
}

.video_controls {
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: var(--card2);
}

.view_selector {
  display: flex;
  gap: 4px;
}

.view_btn {
  padding: 5px 10px;
  border: 1px solid var(--border);
  border-radius: 5px;
  background: transparent;
  color: var(--muted);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.view_btn:hover { border-color: var(--accent); color: var(--text); }
.view_btn.active { background: var(--accent); color: #181721; border-color: var(--accent); }
.view_btn:disabled { opacity: 0.4; cursor: not-allowed; }

.rating.excellent { background: rgba(74, 222, 128, 0.15); color: #4ADE80; }
.rating.good { background: rgba(110, 231, 255, 0.15); color: #6EE7FF; }
.rating.moderate { background: rgba(251, 191, 36, 0.15); color: #FBBF24; }
.rating.poor { background: rgba(248, 113, 113, 0.15); color: #F87171; }
.rating.full_brace { background: rgba(74, 222, 128, 0.15); color: #4ADE80; }
.rating.partial_brace { background: rgba(251, 191, 36, 0.15); color: #FBBF24; }
.rating.no_brace { background: rgba(248, 113, 113, 0.15); color: #F87171; }
.rating.stiff { background: rgba(74, 222, 128, 0.15); color: #4ADE80; }
.rating.moderate_stiff { background: rgba(251, 191, 36, 0.15); color: #FBBF24; }
.rating.flexible { background: rgba(248, 113, 113, 0.15); color: #F87171; }

/* ============== Classifications & Metrics Cards ============== */
.items_grid {
  display: grid;
  gap: 12px;
}

.item_card {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 16px;
  align-items: center;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.item_card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(110, 231, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.item_chip {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  text-transform: capitalize;
  white-space: nowrap;
}

.chip_classification {
  background: rgba(167, 139, 250, 0.15);
  color: var(--accent2);
  border: 1px solid rgba(167, 139, 250, 0.3);
}

.item_info h4 {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.item_info p {
  margin: 0;
  font-size: 13px;
  color: var(--muted);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item_score {
  text-align: right;
}

.item_score .value {
  font-size: 20px;
  font-weight: 700;
  color: var(--accent);
}

.item_score .unit {
  font-size: 11px;
  color: var(--muted);
}

/* Mini dial for metrics */
.mini_dial {
  position: relative;
  width: 48px;
  height: 48px;
  flex-shrink: 0;
}

.mini_dial svg {
  transform: rotate(-90deg);
}

.mini_dial .dial_bg {
  stroke-width: 5;
}

.mini_dial .dial_fill {
  stroke-width: 5;
}

.mini_dial .mini_score {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 12px;
  font-weight: 700;
  color: var(--text);
}

/* ============== Modal ============== */
.modal_backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  padding: 20px;
}

.modal_backdrop.open {
  opacity: 1;
  visibility: visible;
}

.modal {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.5);
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  transform: scale(0.95);
  transition: transform 0.2s ease;
}

.modal_backdrop.open .modal {
  transform: scale(1);
}

.modal_header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-light);
}

.modal_title_group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal_title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.modal_close {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--muted);
  font-size: 18px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.modal_close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text);
}

.modal_body {
  padding: 24px;
}

.modal_section {
  margin-bottom: 24px;
}

.modal_section:last-child {
  margin-bottom: 0;
}

.modal_section h5 {
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 12px;
}

.modal_section p {
  margin: 0;
  font-size: 14px;
  color: var(--text);
  line-height: 1.6;
}

.details_grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}

.detail_item {
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-light);
  border-radius: 8px;
}

.detail_item .label {
  font-size: 11px;
  color: var(--muted);
  text-transform: capitalize;
}

.detail_item .value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin-top: 2px;
}

.screenshots_gallery {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.gallery_item {
  flex-shrink: 0;
  width: 200px;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.15s ease;
}

.gallery_item:hover {
  border-color: var(--accent);
  transform: scale(1.02);
}

.gallery_item img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
}

/* ============== Lightbox ============== */
.lightbox {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
}

.lightbox.open {
  opacity: 1;
  visibility: visible;
}

.lightbox img {
  max-width: 90vw;
  max-height: 90vh;
  object-fit: contain;
  border-radius: 8px;
}

.lightbox_close {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 20px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.lightbox_close:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* ============== Bottom Bar ============== */
.bottom_bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(90deg, rgba(110, 231, 255, 0.12), rgba(255, 255, 255, 0.02));
  border-top: 1px solid rgba(110, 231, 255, 0.25);
  padding: 12px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 50;
}

.bottom_bar_info {
  font-size: 13px;
  color: var(--muted);
}

.bottom_bar_actions {
  display: flex;
  gap: 8px;
}

.btn {
  height: 36px;
  padding: 0 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn_secondary {
  color: var(--text);
  background: rgba(255, 255, 255, 0.03);
  border-color: var(--border);
}

.btn_secondary:hover {
  border-color: var(--accent);
}

.btn_primary {
  background: var(--accent);
  color: #181721;
  box-shadow: 0 8px 20px rgba(110, 231, 255, 0.15);
}

.btn_primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 28px rgba(110, 231, 255, 0.25);
}

/* ============== Utilities ============== */
.placeholder {
  background: rgba(255, 255, 255, 0.05);
  border: 1px dashed var(--border);
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  color: var(--muted);
  font-size: 13px;
}

/* ============== Responsive ============== */
@media (max-width: 1100px) {
  .summary_grid { 
    grid-template-columns: 1fr; 
    gap: 20px;
  }
  .score_dial_container { 
    flex-direction: row; 
    justify-content: center;
    gap: 20px;
  }
  .thumbnails_grid_compact {
    max-width: 500px;
    margin: 0 auto;
  }
  .video_panel {
    max-width: 100%;
    margin: 0 auto;
  }
  .video_panel video {
    max-height: 280px;
  }
  .thumbnail {
    max-width: 55px;
  }
}

@media (max-width: 900px) {
  .header_grid { grid-template-columns: 1fr; }
}

@media (max-width: 600px) {
  .navbar { padding: 0 12px; }
  .progress_bar { display: none; }
  .report_container { padding: 0 12px 100px; }
  .card_body { padding: 16px; }
  .thumbnail { max-width: 45px; }
  .thumbnail .event_label { font-size: 6px; padding: 1px 2px; }
  .row_label_text { font-size: 7px; }
  .row_label_box { min-width: 20px; padding: 0 3px; }
}
'''


def _generate_html(data: dict) -> str:
    """Generate the HTML for the report page."""
    header = data.get('header', {})
    classifications = data.get('classifications', [])
    metrics = data.get('metrics', [])
    summary = data.get('summary', {})
    
    # Extract header info
    bowler = header.get('bowler', {})
    session = header.get('session', {})
    video_summary = header.get('video_summary', {})
    score_summary = header.get('score_summary', {})
    
    overall_score = score_summary.get('overall_score', 0)
    grade = score_summary.get('grade', 'N/A')
    metric_scores = score_summary.get('metric_scores', {})
    
    # Format date
    created_at = header.get('created_at', '')
    try:
        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        formatted_date = dt.strftime('%B %d, %Y at %I:%M %p')
    except:
        formatted_date = created_at
    
    # Build HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{header.get('title', 'BowlVision Report')}</title>
  <link rel="stylesheet" href="results.css">
</head>
<body>
  <!-- Navbar -->
  <header class="navbar">
    <div class="navbar_left">
      <div class="navbar_title">🎳 BowlVision</div>
    </div>
    <div class="progress_bar">
      <div class="completed_step">Upload</div>
      <div class="completed_bar"></div>
      <div class="completed_step">Tagging</div>
      <div class="completed_bar"></div>
      <div class="completed_step">Analyze</div>
      <div class="completed_bar"></div>
      <div class="active_step">Results</div>
    </div>
    <div class="navbar_right">
      <div class="lfc_shoutout">Developed by Left Field Cricket</div>
    </div>
  </header>

  <!-- Type Toggle -->
  <div class="type_toggle_container">
    <div class="type_toggle">
      <button class="type_btn" data-type="original">Original</button>
      <button class="type_btn active" data-type="skeleton">Skeleton</button>
      <button class="type_btn" data-type="overlay">Overlay</button>
    </div>
  </div>

  <!-- Main Content -->
  <main class="report_container">
    <!-- Header Card -->
    <section class="card">
      <div class="card_header">
        <h2 class="card_title">{header.get('title', 'Bowling Analysis Report')}</h2>
        <span class="card_subtitle">{formatted_date}</span>
      </div>
      <div class="card_body">
        <div class="header_grid">
          <div class="bowler_block">
            <img src="{_get_relative_path(bowler.get('image_path', ''))}" alt="Bowler" class="bowler_image" onerror="this.style.display='none'">
            <div class="bowler_info">
              <h3>{bowler.get('name', 'Unknown Bowler')}<span class="hand_badge">{bowler.get('hand', 'N/A')}-handed</span></h3>
              <p>{bowler.get('description', '')}</p>
            </div>
          </div>
          <div class="session_block">
            <div class="session_info">
              <h3>📍 {session.get('name', 'Practice Session')}</h3>
              <p>{session.get('description', '')}</p>
              <p class="session_date">{session.get('date', '')}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Summary Card (Score + Thumbnails) -->
    <section class="card">
      <div class="card_header">
        <h2 class="card_title">Summary</h2>
      </div>
      <div class="card_body">
        <div class="summary_grid">
          <!-- Score Dial -->
          <div class="score_dial_container">
            <div class="score_dial_title">Biomechanical Rating</div>
            {_generate_score_dial(overall_score, 250)}
          </div>
          
          <!-- Thumbnails Grid (2 rows x 4 cols) -->
          {_generate_compact_thumbnails(video_summary)}
        </div>
      </div>
    </section>

    <!-- Classifications Card -->
    <section class="card">
      <div class="card_header">
        <h2 class="card_title">Classifications</h2>
        <span class="card_subtitle">{len(classifications)} identified</span>
      </div>
      <div class="card_body">
        <div class="items_grid">
          {_generate_classification_cards(classifications)}
        </div>
      </div>
    </section>

    <!-- Metrics Card -->
    <section class="card">
      <div class="card_header">
        <h2 class="card_title">Metrics</h2>
        <span class="card_subtitle">{len(metrics)} analyzed</span>
      </div>
      <div class="card_body">
        <div class="items_grid">
          {_generate_metric_cards(metrics)}
        </div>
      </div>
    </section>
  </main>

  <!-- Bottom Bar -->
  <div class="bottom_bar">
    <div class="bottom_bar_info">
      BowlVision Analysis Report • Generated {formatted_date}
    </div>
    <div class="bottom_bar_actions">
      <button class="btn btn_secondary" onclick="window.print()">🖨️ Print</button>
      <a href="results.json" download class="btn btn_secondary">📥 Download JSON</a>
    </div>
  </div>

  <!-- Modal Container -->
  <div class="modal_backdrop" id="modal_backdrop">
    <div class="modal" id="modal">
      <div class="modal_header">
        <div class="modal_title_group">
          <h3 class="modal_title" id="modal_title">Details</h3>
          <span class="item_chip" id="modal_chip"></span>
        </div>
        <button class="modal_close" id="modal_close">×</button>
      </div>
      <div class="modal_body" id="modal_body">
        <!-- Dynamic content -->
      </div>
    </div>
  </div>

  <!-- Lightbox -->
  <div class="lightbox" id="lightbox">
    <button class="lightbox_close" id="lightbox_close">×</button>
    <img id="lightbox_img" src="" alt="Full size image">
  </div>

  <!-- Data for JS -->
  <script>
    const reportData = {json.dumps(data, indent=2)};
  </script>

  <!-- Report JS -->
  <script>
{_generate_javascript()}
  </script>
</body>
</html>
'''
    return html


def _get_relative_path(path: str) -> str:
    """Convert absolute path to relative path for the report."""
    if not path:
        return ''
    # The bowler image is relative to results folder
    # data/run/a_inputs/bowler_image.jpg -> ../../a_inputs/bowler_image.jpg
    if 'a_inputs' in path:
        return '../../a_inputs/' + path.split('a_inputs/')[-1]
    return path


def _generate_score_dial(score: float, size: int = 160) -> str:
    """Generate SVG score dial."""
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


def _generate_metric_score_rows(metric_scores: dict) -> str:
    """Generate metric score breakdown rows."""
    rows = []
    for metric_id, info in metric_scores.items():
        name = metric_id.replace('_', ' ').title()
        score = info.get('score', 0)
        rating = info.get('rating', 'N/A')
        rating_class = rating.replace(' ', '_').lower()
        
        rows.append(f'''<div class="metric_score_row">
          <span class="name">{name}</span>
          <span class="rating {rating_class}">{rating.replace('_', ' ')}</span>
          <span class="score">{score:.0f}</span>
        </div>''')
    
    return '\n'.join(rows)


def _generate_view_thumbnails(video_summary: dict, view: str) -> str:
    """Generate thumbnail grid for a view."""
    view_data = video_summary.get(f'{view}_view', {})
    exists = view_data.get('exists', False)
    events = view_data.get('events', {})
    
    disabled_class = '' if exists else 'disabled'
    
    thumbnails = []
    event_names = ['Jump', 'BFC', 'FFC', 'Release']
    
    for event in event_names:
        event_lower = event.lower()
        output_name = f'video_summary_{view}_{event_lower}'
        
        thumbnails.append(f'''<div class="thumbnail" data-view="{view}" data-event="{event_lower}" data-output="{output_name}">
          <img class="switchable-image" data-base="screenshots/{output_name}" src="screenshots/{output_name}_skeleton.png" alt="{event}">
          <span class="event_label">{event}</span>
        </div>''')
    
    return f'''<div class="view_thumbnails {disabled_class}">
      <div class="view_label">{view.upper()} VIEW</div>
      <div class="thumbnails_grid">
        {''.join(thumbnails)}
      </div>
    </div>'''


def _generate_compact_thumbnails(video_summary: dict) -> str:
    """Generate compact 2x4 thumbnail grid (side row + back row)."""
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
              <img class="switchable-image" data-base="screenshots/{output_name}" src="screenshots/{output_name}_skeleton.png" alt="{event}">
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


def _generate_classification_cards(classifications: list) -> str:
    """Generate classification card HTML."""
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
    
    return '\n'.join(cards) if cards else '<div class="placeholder">No classifications available</div>'


def _generate_metric_cards(metrics: list) -> str:
    """Generate metric card HTML."""
    cards = []
    for i, m in enumerate(metrics):
        score = m.get('score', 0) or 0
        rating = m.get('rating', 'N/A')
        rating_display = rating.replace('_', ' ')
        rating_class = rating.replace(' ', '_').lower()
        
        # Generate mini dial
        radius = 19
        circumference = 2 * 3.14159 * radius
        offset = circumference - (score / 100) * circumference
        
        mini_dial = f'''<div class="mini_dial">
          <svg width="48" height="48">
            <circle class="dial_bg" cx="24" cy="24" r="{radius}"/>
            <circle class="dial_fill" cx="24" cy="24" r="{radius}" 
                    stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"/>
          </svg>
          <span class="mini_score">{score:.0f}</span>
        </div>'''
        
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
    
    return '\n'.join(cards) if cards else '<div class="placeholder">No metrics available</div>'


def _generate_javascript() -> str:
    """Generate JavaScript for interactivity."""
    return '''
    // State
    let currentType = 'skeleton';
    let currentView = 'side';
    
    // DOM Elements
    const typeButtons = document.querySelectorAll('.type_btn');
    const viewButtons = document.querySelectorAll('.view_btn');
    const video = document.getElementById('preview_video');
    const modalBackdrop = document.getElementById('modal_backdrop');
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modal_title');
    const modalChip = document.getElementById('modal_chip');
    const modalBody = document.getElementById('modal_body');
    const modalClose = document.getElementById('modal_close');
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightbox_img');
    const lightboxClose = document.getElementById('lightbox_close');
    const thumbnails = document.querySelectorAll('.thumbnail');
    const itemCards = document.querySelectorAll('.item_card');
    
    // Type toggle
    typeButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        typeButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentType = btn.dataset.type;
        updateAllImages();
        updateVideo();
      });
    });
    
    // Update all switchable images
    function updateAllImages() {
      document.querySelectorAll('.switchable-image').forEach(img => {
        const base = img.dataset.base;
        if (base) {
          img.src = `${base}_${currentType}.png`;
        }
      });
    }
    
    // Update video
    function updateVideo() {
      const source = video.querySelector('source');
      source.src = `videos/${currentView}_view_${currentType}.mp4`;
      video.load();
    }
    
    // View selector (video only)
    viewButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        if (btn.disabled) return;
        viewButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentView = btn.dataset.view;
        updateVideo();
      });
    });
    
    // Thumbnail click -> open lightbox (independent of video)
    thumbnails.forEach(thumb => {
      thumb.addEventListener('click', () => {
        const img = thumb.querySelector('img');
        if (img) {
          openLightbox(img.src);
        }
      });
    });
    
    // Item card click -> open modal
    itemCards.forEach(card => {
      card.addEventListener('click', () => {
        const type = card.dataset.type;
        const index = parseInt(card.dataset.index);
        
        const items = type === 'classification' ? reportData.classifications : reportData.metrics;
        const item = items[index];
        
        if (!item) return;
        
        // Populate modal
        modalTitle.textContent = item.name;
        modalChip.textContent = item.rating?.replace(/_/g, ' ') || 'N/A';
        modalChip.className = `item_chip ${type === 'classification' ? 'chip_classification' : 'rating ' + (item.rating || '').replace(/ /g, '_').toLowerCase()}`;
        
        let bodyHTML = '';
        
        // Description
        if (item.description) {
          bodyHTML += `<div class="modal_section"><h5>Description</h5><p>${item.description}</p></div>`;
        }
        
        // Analysis
        if (item.analysis) {
          bodyHTML += `<div class="modal_section"><h5>Analysis</h5><p>${item.analysis}</p></div>`;
        }
        
        // Extra data
        if (item.extra_data && Object.keys(item.extra_data).length > 0) {
          let detailsHTML = '<div class="details_grid">';
          for (const [key, value] of Object.entries(item.extra_data)) {
            const label = key.replace(/_/g, ' ');
            const displayValue = typeof value === 'number' ? value.toFixed(2) : value;
            detailsHTML += `<div class="detail_item"><div class="label">${label}</div><div class="value">${displayValue}</div></div>`;
          }
          detailsHTML += '</div>';
          bodyHTML += `<div class="modal_section"><h5>Details</h5>${detailsHTML}</div>`;
        }
        
        // Screenshots
        if (item.screenshots && item.screenshots.length > 0) {
          let galleryHTML = '<div class="screenshots_gallery">';
          item.screenshots.forEach(ss => {
            const src = `screenshots/${ss.output_name}_${currentType}.png`;
            galleryHTML += `<div class="gallery_item" onclick="openLightbox('${src}')"><img class="switchable-image" data-base="screenshots/${ss.output_name}" src="${src}" alt="${ss.output_name}"></div>`;
          });
          galleryHTML += '</div>';
          bodyHTML += `<div class="modal_section"><h5>Screenshots</h5>${galleryHTML}</div>`;
        }
        
        modalBody.innerHTML = bodyHTML;
        modalBackdrop.classList.add('open');
      });
    });
    
    // Close modal
    function closeModal() {
      modalBackdrop.classList.remove('open');
    }
    
    modalClose.addEventListener('click', closeModal);
    modalBackdrop.addEventListener('click', (e) => {
      if (e.target === modalBackdrop) closeModal();
    });
    
    // Lightbox
    function openLightbox(src) {
      lightboxImg.src = src;
      lightbox.classList.add('open');
    }
    
    function closeLightbox() {
      lightbox.classList.remove('open');
    }
    
    window.openLightbox = openLightbox;
    
    lightboxClose.addEventListener('click', closeLightbox);
    lightbox.addEventListener('click', (e) => {
      if (e.target === lightbox) closeLightbox();
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        if (lightbox.classList.contains('open')) {
          closeLightbox();
        } else if (modalBackdrop.classList.contains('open')) {
          closeModal();
        }
      }
    });
    
    // Initialize
    updateAllImages();
'''


# Entry point for pipeline
def run_step_4_3_generate_report(session_dir: str) -> list:
    """Entry point for pipeline integration."""
    result = generate_report(session_dir)
    return result.get('output_paths', [])


if __name__ == '__main__':
    result = generate_report('data/run/')
    print(f"Generated: {result['output_paths']}")
