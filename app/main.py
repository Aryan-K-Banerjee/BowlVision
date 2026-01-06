from flask import Flask, render_template, redirect, url_for, request, jsonify, send_file, send_from_directory, Response
from services.upload import setup_dir, save_metadata_and_videos
from services.tagging import get_tagging_state, get_frame_path, save_events, is_tagging_complete, get_available_views
from services.progress import start_pipeline, get_pipeline_state, stream_logs
from pathlib import Path

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


if __name__ == '__main__':
    app.run(debug=True)
