/**
 * BowlVision Tagging Page - Frame-based Canvas Player
 * Handles frame preloading, playback, event tagging, zoom/pan
 */

(function () {
    'use strict';

    // ============== Constants ==============
    const EVENT_ORDER = ['Jump', 'BFC', 'FFC', 'Release'];
    const VIEW_ORDER = ['back', 'side'];
    const PLAYBACK_FPS = 30;
    const ZOOM_STEP = 0.25;
    const MIN_ZOOM = 0.5;
    const MAX_ZOOM = 4.0;

    // ============== DOM Elements ==============
    const canvas = document.getElementById('frame_canvas');
    const ctx = canvas.getContext('2d');
    const canvasContainer = document.getElementById('canvas_container');
    const loadingOverlay = document.getElementById('loading_overlay');
    const currentViewLabel = document.getElementById('current_view_label');
    const currentFrameEl = document.getElementById('current_frame');
    const totalFramesEl = document.getElementById('total_frames');
    const scrubber = document.getElementById('frame_scrubber');
    const btnPlayPause = document.getElementById('btn_play_pause');
    const btnStepBack = document.getElementById('btn_step_back');
    const btnStepForward = document.getElementById('btn_step_forward');
    const btnZoomIn = document.getElementById('btn_zoom_in');
    const btnZoomOut = document.getElementById('btn_zoom_out');
    const btnZoomReset = document.getElementById('btn_zoom_reset');
    const tagHint = document.getElementById('tag_hint');
    const currentEventName = document.getElementById('current_event_name');
    const analyzeButton = document.getElementById('analyze_button');
    const completeMessage = document.getElementById('complete_message');
    const viewRowBack = document.getElementById('view_row_back');
    const viewRowSide = document.getElementById('view_row_side');

    // ============== State ==============
    let state = {
        views: {},           // { back: { available, frameCount, frames: [], events: {} }, side: { ... } }
        activeView: null,    // 'back' or 'side'
        activeEventIndex: 0, // 0-3 (Jump, BFC, FFC, Release)
        currentFrame: 0,
        isPlaying: false,
        playbackInterval: null,
        isComplete: false,
        // Zoom/Pan state
        zoom: 1,
        panX: 0,
        panY: 0,
        isPanning: false,
        panStartX: 0,
        panStartY: 0,
        baseFitScale: 1      // Scale to fit video in container
    };

    // ============== Initialization ==============
    function init() {
        // Parse state from Flask
        parseTaggingState();

        // Determine initial active view
        determineActiveView();

        // Update UI immediately to show correct state during loading
        updateUI();

        // Bind events
        bindEvents();

        // Load frames for available views
        loadAllFrames().then(() => {
            hideLoading();
            calculateFitScale();
            applyTransform();
            renderFrame();
            updateUI();
        }).catch(err => {
            console.error('Error loading frames:', err);
            hideLoading();
        });
    }

    function parseTaggingState() {
        const flaskState = window.TAGGING_STATE || { views: {}, eventOrder: EVENT_ORDER };

        for (const viewName of VIEW_ORDER) {
            const viewData = flaskState.views[viewName] || { available: false, frameCount: 0, events: {} };
            state.views[viewName] = {
                available: viewData.available,
                frameCount: viewData.frameCount,
                frames: [],
                events: { ...viewData.events }
            };
        }

        state.isComplete = flaskState.complete || false;
    }

    function determineActiveView() {
        // Find first view that needs tagging
        for (const viewName of VIEW_ORDER) {
            const view = state.views[viewName];
            if (!view.available) continue;

            let untaggedEventIndex = -1;
            for (let i = 0; i < EVENT_ORDER.length; i++) {
                const eventName = EVENT_ORDER[i];
                if (view.events[eventName] === undefined || view.events[eventName] === null) {
                    untaggedEventIndex = i;
                    break;
                }
            }

            if (untaggedEventIndex >= 0) {
                state.activeView = viewName;
                state.activeEventIndex = untaggedEventIndex;
                return;
            }
        }

        // All views are fully tagged
        if (state.views.back.available || state.views.side.available) {
            state.activeView = state.views.back.available ? 'back' : 'side';
            state.activeEventIndex = 0;
            state.isComplete = checkAllTagged();
        }
    }

    // ============== Frame Loading ==============
    async function loadAllFrames() {
        const loadPromises = [];

        for (const viewName of VIEW_ORDER) {
            const view = state.views[viewName];
            if (view.available && view.frameCount > 0) {
                loadPromises.push(loadFramesForView(viewName));
            }
        }

        await Promise.all(loadPromises);
    }

    async function loadFramesForView(viewName) {
        const view = state.views[viewName];
        const frames = [];
        const batchSize = 20;

        for (let i = 0; i < view.frameCount; i += batchSize) {
            const batch = [];
            for (let j = i; j < Math.min(i + batchSize, view.frameCount); j++) {
                batch.push(loadSingleFrame(viewName, j));
            }
            const loadedBatch = await Promise.all(batch);
            frames.push(...loadedBatch);
            updateLoadingProgress(viewName, frames.length, view.frameCount);
        }

        view.frames = frames;
    }

    function loadSingleFrame(viewName, frameNum) {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = () => {
                console.warn(`Failed to load frame ${frameNum} for ${viewName}`);
                resolve(null);
            };
            img.src = `/api/frames/${viewName}/${frameNum}`;
        });
    }

    function updateLoadingProgress(viewName, loaded, total) {
        const loadingText = loadingOverlay.querySelector('.loading_text');
        if (loadingText) {
            const percent = Math.round((loaded / total) * 100);
            loadingText.textContent = `Loading ${viewName} view... ${percent}%`;
        }
    }

    function hideLoading() {
        loadingOverlay.style.display = 'none';
    }

    // ============== Zoom/Pan ==============
    function calculateFitScale() {
        const view = state.views[state.activeView];
        if (!view || !view.frames.length) return;

        const frame = view.frames[0];
        if (!frame) return;

        const containerRect = canvasContainer.getBoundingClientRect();
        const scaleX = containerRect.width / frame.width;
        const scaleY = containerRect.height / frame.height;
        
        // Use the larger scale to fill the container (prioritize height)
        state.baseFitScale = Math.max(scaleX, scaleY);
        
        // Set initial zoom to fill the container
        state.zoom = 1;
    }

    function resetZoom() {
        calculateFitScale();
        state.zoom = 1;
        state.panX = 0;
        state.panY = 0;
        applyTransform();
    }

    function zoomIn() {
        state.zoom = Math.min(state.zoom + ZOOM_STEP, MAX_ZOOM);
        applyTransform();
        renderFrame();
    }

    function zoomOut() {
        state.zoom = Math.max(state.zoom - ZOOM_STEP, MIN_ZOOM);
        // Reset pan if zoomed out to fit
        if (state.zoom <= 1) {
            state.panX = 0;
            state.panY = 0;
        }
        applyTransform();
        renderFrame();
    }

    function applyTransform() {
        // Apply CSS transform for zoom and pan
        const totalScale = state.baseFitScale * state.zoom;
        canvas.style.transform = `translate(${state.panX}px, ${state.panY}px) scale(${totalScale})`;
        canvas.style.transformOrigin = 'center';
        
        // Update cursor - always allow grab/pan
        canvasContainer.style.cursor = state.isPanning ? 'grabbing' : 'grab';
    }

    function startPan(e) {
        if (e.button !== 0) return; // Left mouse only
        
        e.preventDefault();
        state.isPanning = true;
        state.panStartX = e.clientX - state.panX;
        state.panStartY = e.clientY - state.panY;
        canvasContainer.style.cursor = 'grabbing';
    }

    function movePan(e) {
        if (!state.isPanning) return;
        
        e.preventDefault();
        state.panX = e.clientX - state.panStartX;
        state.panY = e.clientY - state.panStartY;
        applyTransform();
        renderFrame();
    }

    function endPan() {
        if (!state.isPanning) return;
        
        state.isPanning = false;
        canvasContainer.style.cursor = 'grab';
    }

    // ============== Rendering ==============
    function renderFrame() {
        const view = state.views[state.activeView];
        if (!view || !view.frames.length) return;

        const frame = view.frames[state.currentFrame];
        if (!frame) return;

        // Resize canvas to match frame dimensions
        if (canvas.width !== frame.width || canvas.height !== frame.height) {
            canvas.width = frame.width;
            canvas.height = frame.height;
        }

        // Clear canvas first
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw frame
        ctx.drawImage(frame, 0, 0);

        // Update frame counter
        currentFrameEl.textContent = state.currentFrame;
        totalFramesEl.textContent = view.frameCount - 1;

        // Update scrubber
        scrubber.max = view.frameCount - 1;
        scrubber.value = state.currentFrame;
    }

    // ============== Playback Controls ==============
    function play() {
        if (state.isPlaying) return;
        state.isPlaying = true;
        btnPlayPause.textContent = '⏸';
        btnPlayPause.classList.add('playing');

        state.playbackInterval = setInterval(() => {
            const view = state.views[state.activeView];
            if (state.currentFrame >= view.frameCount - 1) {
                pause();
                return;
            }
            state.currentFrame++;
            renderFrame();
        }, 1000 / PLAYBACK_FPS);
    }

    function pause() {
        if (!state.isPlaying) return;
        state.isPlaying = false;
        btnPlayPause.textContent = '▶';
        btnPlayPause.classList.remove('playing');

        if (state.playbackInterval) {
            clearInterval(state.playbackInterval);
            state.playbackInterval = null;
        }
    }

    function togglePlayPause() {
        if (state.isPlaying) {
            pause();
        } else {
            play();
        }
    }

    function stepForward() {
        pause();
        const view = state.views[state.activeView];
        if (state.currentFrame < view.frameCount - 1) {
            state.currentFrame++;
            renderFrame();
        }
    }

    function stepBack() {
        pause();
        if (state.currentFrame > 0) {
            state.currentFrame--;
            renderFrame();
        }
    }

    function seekTo(frameNum) {
        pause();
        const view = state.views[state.activeView];
        state.currentFrame = Math.max(0, Math.min(frameNum, view.frameCount - 1));
        renderFrame();
    }

    // ============== View/Event Navigation ==============
    function switchToView(viewName) {
        if (!state.views[viewName].available) return;
        if (state.activeView === viewName) return;

        pause();
        state.activeView = viewName;
        state.currentFrame = 0;
        state.activeEventIndex = findFirstUntaggedEvent(viewName);

        // Reset zoom/pan when switching views
        resetZoom();
        
        // Force immediate render to ensure view switches
        renderFrame();
        updateUI();
    }

    function switchToEvent(viewName, eventIndex) {
        if (!state.views[viewName].available) return;

        pause();
        state.activeView = viewName;
        state.activeEventIndex = eventIndex;

        const view = state.views[viewName];
        const eventName = EVENT_ORDER[eventIndex];

        // Jump to tagged frame if exists, otherwise frame 0 or previous event's frame
        if (view.events[eventName] !== undefined && view.events[eventName] !== null) {
            state.currentFrame = view.events[eventName];
        } else if (eventIndex > 0) {
            // Jump to previous event's frame if it exists
            const prevEventName = EVENT_ORDER[eventIndex - 1];
            if (view.events[prevEventName] !== undefined && view.events[prevEventName] !== null) {
                state.currentFrame = view.events[prevEventName];
            } else {
                state.currentFrame = 0;
            }
        } else {
            state.currentFrame = 0;
        }

        // Reset zoom/pan when switching events
        if (state.activeView !== viewName) {
            resetZoom();
        }
        renderFrame();
        updateUI();
    }

    function findFirstUntaggedEvent(viewName) {
        const view = state.views[viewName];
        for (let i = 0; i < EVENT_ORDER.length; i++) {
            const eventName = EVENT_ORDER[i];
            if (view.events[eventName] === undefined || view.events[eventName] === null) {
                return i;
            }
        }
        return 0; // All tagged, default to first
    }

    // ============== Tagging ==============
    function tagCurrentEvent() {
        if (state.activeEventIndex >= EVENT_ORDER.length) return;

        const view = state.views[state.activeView];
        const eventName = EVENT_ORDER[state.activeEventIndex];

        // Store the tag (works for both new and re-tagging)
        view.events[eventName] = state.currentFrame;

        // Save to server
        saveEvents(state.activeView, view.events);

        // Auto-advance to next untagged event
        advanceToNextEvent();
    }

    function advanceToNextEvent() {
        const currentView = state.views[state.activeView];

        // Find next untagged event in current view
        for (let i = state.activeEventIndex + 1; i < EVENT_ORDER.length; i++) {
            const eventName = EVENT_ORDER[i];
            if (currentView.events[eventName] === undefined || currentView.events[eventName] === null) {
                state.activeEventIndex = i;
                updateUI();
                return;
            }
        }

        // Current view fully tagged, try to move to next view
        const currentViewIndex = VIEW_ORDER.indexOf(state.activeView);
        for (let i = currentViewIndex + 1; i < VIEW_ORDER.length; i++) {
            const nextView = VIEW_ORDER[i];
            if (state.views[nextView].available) {
                const untaggedIndex = findFirstUntaggedEvent(nextView);
                if (untaggedIndex < EVENT_ORDER.length &&
                    (state.views[nextView].events[EVENT_ORDER[untaggedIndex]] === undefined ||
                        state.views[nextView].events[EVENT_ORDER[untaggedIndex]] === null)) {
                    state.activeView = nextView;
                    state.activeEventIndex = untaggedIndex;
                    state.currentFrame = 0;
                    resetZoom();
                    renderFrame();
                    updateUI();
                    return;
                }
            }
        }

        // Check if all tagged
        state.isComplete = checkAllTagged();
        updateUI();
    }

    function checkAllTagged() {
        for (const viewName of VIEW_ORDER) {
            const view = state.views[viewName];
            if (!view.available) continue;

            for (const eventName of EVENT_ORDER) {
                if (view.events[eventName] === undefined || view.events[eventName] === null) {
                    return false;
                }
            }
        }
        return true;
    }

    async function saveEvents(viewName, events) {
        try {
            const response = await fetch('/api/tagging/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ view: viewName, events: events })
            });
            const data = await response.json();

            if (data.complete) {
                state.isComplete = true;
                updateUI();
            }
        } catch (error) {
            console.error('Failed to save events:', error);
        }
    }

    // ============== UI Updates ==============
    function updateUI() {
        updateViewRows();
        updateEventCells();
        updateViewLabel();
        updateHint();
        updateAnalyzeButton();
    }

    function updateViewRows() {
        // Back view row
        if (state.views.back.available) {
            viewRowBack.classList.remove('disabled');
            viewRowBack.classList.toggle('active', state.activeView === 'back');
        } else {
            viewRowBack.classList.add('disabled');
            viewRowBack.classList.remove('active');
        }

        // Side view row
        if (state.views.side.available) {
            viewRowSide.classList.remove('disabled');
            viewRowSide.classList.toggle('active', state.activeView === 'side');
        } else {
            viewRowSide.classList.add('disabled');
            viewRowSide.classList.remove('active');
        }
    }

    function updateEventCells() {
        for (const viewName of VIEW_ORDER) {
            const row = viewName === 'back' ? viewRowBack : viewRowSide;
            const view = state.views[viewName];
            const eventCells = row.querySelectorAll('.event');

            eventCells.forEach((cell, index) => {
                const eventName = EVENT_ORDER[index];
                cell.classList.remove('active', 'done');

                if (!view.available) return;

                // Check if this event is tagged (done = green)
                if (view.events[eventName] !== undefined && view.events[eventName] !== null) {
                    cell.classList.add('done');
                }

                // Check if this is the currently active event (active = blue)
                if (viewName === state.activeView && index === state.activeEventIndex) {
                    cell.classList.add('active');
                }
            });
        }
    }

    function updateViewLabel() {
        const viewName = state.activeView === 'back' ? 'Back View' : 'Side View';
        currentViewLabel.textContent = viewName;
    }

    function updateHint() {
        if (state.isComplete) {
            tagHint.innerHTML = '<strong>All events tagged!</strong> Ready to analyze.';
        } else {
            const eventName = EVENT_ORDER[state.activeEventIndex];
            const view = state.views[state.activeView];
            const isRetagging = view.events[eventName] !== undefined && view.events[eventName] !== null;

            if (isRetagging) {
                tagHint.innerHTML = `Press <strong>Enter</strong> to re-tag <strong>${eventName}</strong> (currently frame ${view.events[eventName]})`;
            } else {
                currentEventName.textContent = eventName;
                tagHint.innerHTML = `Press <strong>Enter</strong> to tag <strong>${eventName}</strong>`;
            }
        }
    }

    function updateAnalyzeButton() {
        state.isComplete = checkAllTagged();
        analyzeButton.disabled = !state.isComplete;
        completeMessage.classList.toggle('visible', state.isComplete);
    }

    // ============== Event Binding ==============
    function bindEvents() {
        // Playback controls
        btnPlayPause.addEventListener('click', togglePlayPause);
        btnStepBack.addEventListener('click', stepBack);
        btnStepForward.addEventListener('click', stepForward);

        // Zoom controls
        btnZoomIn.addEventListener('click', zoomIn);
        btnZoomOut.addEventListener('click', zoomOut);
        btnZoomReset.addEventListener('click', resetZoom);

        // Scrubber
        scrubber.addEventListener('input', (e) => {
            seekTo(parseInt(e.target.value, 10));
        });

        // Canvas panning
        canvasContainer.addEventListener('mousedown', startPan);
        document.addEventListener('mousemove', movePan);
        document.addEventListener('mouseup', endPan);

        // Mouse wheel zoom
        canvasContainer.addEventListener('wheel', (e) => {
            e.preventDefault();
            if (e.deltaY < 0) {
                zoomIn();
            } else {
                zoomOut();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            switch (e.code) {
                case 'Space':
                    e.preventDefault();
                    togglePlayPause();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    stepBack();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    stepForward();
                    break;
                case 'Enter':
                    e.preventDefault();
                    tagCurrentEvent();
                    break;
                case 'Equal':
                case 'NumpadAdd':
                    e.preventDefault();
                    zoomIn();
                    break;
                case 'Minus':
                case 'NumpadSubtract':
                    e.preventDefault();
                    zoomOut();
                    break;
                case 'Digit0':
                case 'Numpad0':
                    e.preventDefault();
                    resetZoom();
                    break;
            }
        });

        // Analyze button
        analyzeButton.addEventListener('click', () => {
            if (state.isComplete) {
                // Redirect to progress page to start pipeline
                window.location.href = '/progress';
            }
        });

        // View label clicks (click label area to switch view at frame 0)
        viewRowBack.querySelector('label').addEventListener('click', (e) => {
            e.stopPropagation();
            if (state.views.back.available) {
                switchToView('back');
            }
        });

        viewRowSide.querySelector('label').addEventListener('click', (e) => {
            e.stopPropagation();
            if (state.views.side.available) {
                switchToView('side');
            }
        });

        // Event cell clicks (click to navigate to that event)
        document.querySelectorAll('.event').forEach(cell => {
            cell.addEventListener('click', (e) => {
                e.stopPropagation();
                const viewRow = cell.closest('.view_row');
                const viewName = viewRow.dataset.view;
                const eventName = cell.dataset.event;
                const eventIndex = EVENT_ORDER.indexOf(eventName);

                if (state.views[viewName].available && eventIndex >= 0) {
                    switchToEvent(viewName, eventIndex);
                }
            });
        });
    }

    // ============== Start ==============
    init();
})();
