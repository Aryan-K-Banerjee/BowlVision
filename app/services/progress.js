/**
 * BowlVision Progress Page - Pipeline Log Streaming
 * Handles SSE log streaming, auto-scroll, and UI state management
 */

(function () {
    'use strict';

    // ============== DOM Elements ==============
    const terminalBody = document.getElementById('terminal_body');
    const terminalStatus = document.getElementById('terminal_status');
    const statusHint = document.getElementById('status_hint');
    const actionBar = document.getElementById('action_bar');
    const btnCancel = document.getElementById('btn_cancel');
    const btnResults = document.getElementById('btn_results');

    // ============== State ==============
    let state = {
        status: 'idle',        // idle, running, success, error
        autoScroll: true,      // Auto-scroll to bottom
        eventSource: null      // SSE connection
    };

    // ============== Initialization ==============
    function init() {
        // Bind scroll event for auto-scroll detection
        terminalBody.addEventListener('scroll', handleScroll);

        // Start the pipeline
        startPipeline();
    }

    // ============== Pipeline Control ==============
    async function startPipeline() {
        try {
            // Start pipeline on server
            const response = await fetch('/api/pipeline/start', { method: 'POST' });
            const data = await response.json();

            if (data.started) {
                // Connect to SSE stream
                connectToStream();
            } else {
                // Pipeline already running, just connect to stream
                connectToStream();
            }
        } catch (error) {
            console.error('Failed to start pipeline:', error);
            addLog('✖ Failed to connect to pipeline server', 1, 'error');
            updateStatus('error');
        }
    }

    function connectToStream() {
        // Close any existing connection
        if (state.eventSource) {
            state.eventSource.close();
        }

        updateStatus('running');

        // Connect to SSE endpoint
        state.eventSource = new EventSource('/api/pipeline/stream');

        state.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleStreamMessage(data);
            } catch (e) {
                console.error('Failed to parse SSE message:', e);
            }
        };

        state.eventSource.onerror = (error) => {
            console.error('SSE connection error:', error);
            state.eventSource.close();
            
            // Only show error if we weren't already done
            if (state.status === 'running') {
                addLog('✖ Connection lost', 1, 'error');
                updateStatus('error');
            }
        };
    }

    function handleStreamMessage(data) {
        switch (data.type) {
            case 'connected':
                // Initial connection - state already known
                break;

            case 'log':
                addLog(data.message, data.level, data.log_type);
                break;

            case 'status':
                if (data.status === 'success') {
                    updateStatus('success');
                } else if (data.status === 'error') {
                    updateStatus('error');
                }
                break;

            case 'complete':
                // Pipeline finished
                if (state.eventSource) {
                    state.eventSource.close();
                }
                if (data.state) {
                    updateStatus(data.state.status);
                }
                break;
        }
    }

    // ============== Logging ==============
    function addLog(message, level = 1, logType = 'info') {
        // Skip empty messages (spacers)
        if (!message && level === 0) {
            const spacer = document.createElement('div');
            spacer.className = 'log_line';
            spacer.innerHTML = '&nbsp;';
            terminalBody.appendChild(spacer);
            autoScrollToBottom();
            return;
        }

        const line = document.createElement('div');
        line.className = `log_line level_${level}`;

        // Add type class
        if (logType === 'success' || message.startsWith('✓')) {
            line.classList.add('success');
        } else if (logType === 'warning' || message.startsWith('!')) {
            line.classList.add('warning');
        } else if (logType === 'error' || message.startsWith('✖')) {
            line.classList.add('error');
        }

        line.textContent = message;
        terminalBody.appendChild(line);

        autoScrollToBottom();
    }

    // ============== Auto-Scroll ==============
    function handleScroll() {
        // Check if user scrolled away from bottom
        const scrollBottom = terminalBody.scrollHeight - terminalBody.scrollTop - terminalBody.clientHeight;
        
        // If user scrolled more than 50px from bottom, pause auto-scroll
        if (scrollBottom > 50) {
            state.autoScroll = false;
        } else {
            state.autoScroll = true;
        }
    }

    function autoScrollToBottom() {
        if (state.autoScroll) {
            terminalBody.scrollTop = terminalBody.scrollHeight;
        }
    }

    // ============== UI Updates ==============
    function updateStatus(status) {
        state.status = status;

        // Update status indicator
        const statusDot = terminalStatus.querySelector('.status_dot');
        const statusText = terminalStatus.querySelector('.status_text');

        statusDot.classList.remove('running', 'success', 'error');
        statusDot.classList.add(status);

        switch (status) {
            case 'running':
                statusText.textContent = 'Running';
                statusHint.textContent = 'Pipeline running — do not close this tab.';
                actionBar.classList.remove('success_state', 'error_state');
                btnResults.disabled = true;
                break;

            case 'success':
                statusText.textContent = 'Complete';
                statusHint.textContent = 'Pipeline complete.';
                actionBar.classList.remove('error_state');
                actionBar.classList.add('success_state');
                btnResults.disabled = false;
                btnCancel.textContent = 'Cancel';
                break;

            case 'error':
                statusText.textContent = 'Failed';
                statusHint.textContent = 'Pipeline failed — see log.';
                actionBar.classList.remove('success_state');
                actionBar.classList.add('error_state');
                btnResults.disabled = true;
                btnCancel.textContent = 'Back to Tagging';
                btnCancel.classList.add('btn_warning');
                break;
        }
    }

    // ============== Start ==============
    init();
})();
