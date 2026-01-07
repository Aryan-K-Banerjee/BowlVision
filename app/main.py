from flask import Flask, render_template, redirect, url_for, request, jsonify, send_file, send_from_directory, Response
from dotenv import load_dotenv
from services.upload import setup_dir, save_metadata_and_videos
from services.tagging import get_tagging_state, get_frame_path, save_events, is_tagging_complete, get_available_views
from services.progress import start_pipeline, get_pipeline_state, stream_logs
from services.report import (
    load_report_data, format_date, generate_score_dial_html,
    generate_thumbnails_html, generate_classification_cards_html,
    generate_metric_cards_html, get_quick_prompts
)
from services.coach import get_coach_service, reset_coach_service
from pathlib import Path
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Route to serve JavaScript files from the services directory
@app.route('/services/<path:filename>')
def services(filename):
    services_dir = Path(__file__).parent / 'services'
    return send_from_directory(services_dir, filename)

@app.route('/')
def landing_page():
    return render_template('LandingPage.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
    
    if request.method == 'POST':
        # The meta data
        bowler_name = request.form.get('bowler_name', "").strip()
        bowler_hand = request.form.get('bowler_hand', "Right").strip()
        bowler_description = request.form.get('bowler_description', "").strip()
        bowler_image = request.files.get('bowler_image')

        session_name = request.form.get('session_name', "").strip()
        session_date = request.form.get('session_date', "").strip()
        session_description = request.form.get('session_description', "").strip()

        # Videos
        input_back_view = request.files.get('back_view')
        input_side_view = request.files.get('side_view')

        # Ensuring the videos exist using their objects and filenames
        if not (input_back_view and input_back_view.filename) and not (input_side_view and input_side_view.filename):
            return render_template(
                'UploadPage.html',
                error="Need at least one video to Analyze.",
                bowler_name=bowler_name,
                bowler_hand=bowler_hand,
                bowler_description=bowler_description,
                session_name=session_name,
                session_date=session_date,
                session_description=session_description
            )

        # Setting up the directory
        setup_dir()

        # Saving the metadata and videos in the right location
        save_metadata_and_videos(
            bowler_name,
            bowler_hand,
            bowler_description,
            bowler_image,
            session_name,
            session_date,
            session_description,
            input_back_view,
            input_side_view
        )
        # Redirect to Tagging Page on the analyze button press
        return redirect(url_for('tagging_page'))
        
    return render_template('UploadPage.html')

@app.route('/tagging')
def tagging_page():
    # Check if any videos exist
    views = get_available_views()
    if not views['back'] and not views['side']:
        # No videos, redirect to upload
        return redirect(url_for('upload_page'))
    
    # Get full tagging state
    tagging_state = get_tagging_state()
    return render_template('TaggingPage.html', tagging_state=tagging_state)


@app.route('/progress')
def progress_page():
    # Check if tagging is complete before allowing access
    if not is_tagging_complete():
        return redirect(url_for('tagging_page'))
    
    return render_template('ProgressPage.html')


@app.route('/report')
def report_page():
    """Render the report page with coach chat."""
    # Reset coach service to reload data
    reset_coach_service()
    
    # Load report data
    report_data, error = load_report_data()
    
    if error or report_data is None:
        return render_template('ReportPage.html', 
                             title='Report Not Available',
                             error=error or 'Report data not found')
    
    # Extract data
    header = report_data.get('header', {})
    bowler = header.get('bowler', {})
    session = header.get('session', {})
    video_summary = header.get('video_summary', {})
    score_summary = header.get('score_summary', {})
    classifications = report_data.get('classifications', [])
    metrics = report_data.get('metrics', [])
    
    # Format date
    created_at = header.get('created_at', '')
    formatted_date = format_date(created_at)
    
    # Generate HTML components
    overall_score = score_summary.get('overall_score', 0)
    score_dial_html = generate_score_dial_html(overall_score)
    thumbnails_html = generate_thumbnails_html(video_summary)
    classification_cards_html = generate_classification_cards_html(classifications)
    metric_cards_html = generate_metric_cards_html(metrics)
    
    # Get quick prompts and check coach availability
    quick_prompts = get_quick_prompts()
    coach_service = get_coach_service()
    coach_available = coach_service.is_available
    
    return render_template('ReportPage.html',
                         title=header.get('title', 'Bowling Analysis Report'),
                         header=header,
                         bowler=bowler,
                         session=session,
                         formatted_date=formatted_date,
                         score_dial_html=score_dial_html,
                         thumbnails_html=thumbnails_html,
                         classifications=classifications,
                         metrics=metrics,
                         classification_cards_html=classification_cards_html,
                         metric_cards_html=metric_cards_html,
                         quick_prompts=quick_prompts,
                         coach_available=coach_available,
                         error=None)


@app.route('/report-asset/<path:filepath>')
def report_asset(filepath):
    """Serve assets for the report page (images, screenshots, etc.)."""
    # Serve files from the project root or from data/run/results
    base_path = Path(__file__).parent.parent
    
    # Try the provided path first
    full_path = base_path / filepath
    
    # If not found and starts with 'screenshots/', try data/run/results/screenshots/
    if not full_path.exists() and filepath.startswith('screenshots/'):
        full_path = base_path / 'data' / 'run' / 'results' / filepath
    
    if not full_path.exists():
        return jsonify({"error": "Asset not found"}), 404
    
    return send_file(full_path)


# ============== API Routes ==============

@app.route('/api/tagging/state')
def api_tagging_state():
    """Return the current tagging state as JSON."""
    return jsonify(get_tagging_state())


@app.route('/api/frames/<view>/<int:frame_num>')
def api_get_frame(view, frame_num):
    """Serve a single frame image."""
    if view not in ['back', 'side']:
        return jsonify({"error": "Invalid view"}), 400
    
    frame_path = get_frame_path(view, frame_num)
    if not frame_path:
        return jsonify({"error": "Frame not found"}), 404
    
    return send_file(frame_path, mimetype='image/jpeg')


@app.route('/api/tagging/save', methods=['POST'])
def api_save_tagging():
    """Save tagged events for a view."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    view = data.get('view')
    events = data.get('events')
    
    if view not in ['back', 'side']:
        return jsonify({"error": "Invalid view"}), 400
    
    if not events:
        return jsonify({"error": "No events provided"}), 400
    
    success = save_events(view, events)
    if success:
        return jsonify({"success": True, "complete": is_tagging_complete()})
    else:
        return jsonify({"error": "Failed to save events"}), 500


# ============== Pipeline API Routes ==============

@app.route('/api/pipeline/start', methods=['POST'])
def api_start_pipeline():
    """Start the pipeline execution."""
    result = start_pipeline()
    return jsonify(result)


@app.route('/api/pipeline/state')
def api_pipeline_state():
    """Get current pipeline state."""
    return jsonify(get_pipeline_state())


@app.route('/api/pipeline/stream')
def api_pipeline_stream():
    """Stream pipeline logs via Server-Sent Events."""
    return Response(
        stream_logs(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


# ============== Coach API Routes ==============

@app.route('/api/coach/start', methods=['POST'])
def api_coach_start():
    """Get the initial coach message."""
    logger.info("Coach: /api/coach/start called")
    
    coach_service = get_coach_service()
    
    if not coach_service.is_available:
        logger.warning("Coach: Service not available")
        return jsonify({
            'ok': False,
            'message': 'Coach service not available. Report may be missing.',
            'history': []
        })
    
    result = coach_service.get_initial_message()
    return jsonify(result)


@app.route('/api/coach/chat', methods=['POST'])
def api_coach_chat():
    """Handle a chat message from the user."""
    data = request.get_json()
    if not data:
        return jsonify({'ok': False, 'message': 'No data provided', 'history': []}), 400
    
    user_message = data.get('message', '').strip()
    history = data.get('history', [])
    
    if not user_message:
        return jsonify({'ok': False, 'message': 'Empty message', 'history': history}), 400
    
    logger.info(f"Coach: /api/coach/chat called with message: {user_message[:50]}...")
    
    coach_service = get_coach_service()
    
    if not coach_service.is_available:
        logger.warning("Coach: Service not available")
        return jsonify({
            'ok': False,
            'message': 'Coach service not available. Report may be missing.',
            'history': history
        })
    
    result = coach_service.chat(user_message, history)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
