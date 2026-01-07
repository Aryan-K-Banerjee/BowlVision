/**
 * BowlVision Coach Chat Client
 * Handles coach drawer interactions and chat functionality.
 */

(function() {
    'use strict';

    // State
    let chatHistory = [];
    let isLoading = false;
    let isInitialized = false;

    // DOM Elements
    const drawerBackdrop = document.getElementById('coach_drawer_backdrop');
    const coachBody = document.getElementById('coach_body');
    const coachInput = document.getElementById('coach_input');
    const coachSend = document.getElementById('coach_send');
    const openCoachBtn = document.getElementById('btn_coach');
    const closeCoachBtn = document.getElementById('coach_close');
    const quickPrompts = document.querySelectorAll('.quick_prompt');

    // Initialize
    function init() {
        if (!drawerBackdrop) return;

        // Open drawer button
        if (openCoachBtn) {
            openCoachBtn.addEventListener('click', openDrawer);
        }

        // Close drawer button
        if (closeCoachBtn) {
            closeCoachBtn.addEventListener('click', closeDrawer);
        }

        // Backdrop click to close
        drawerBackdrop.addEventListener('click', (e) => {
            if (e.target === drawerBackdrop) {
                closeDrawer();
            }
        });

        // Send button
        if (coachSend) {
            coachSend.addEventListener('click', sendMessage);
        }

        // Enter key to send
        if (coachInput) {
            coachInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
        }

        // Quick prompts
        quickPrompts.forEach(chip => {
            chip.addEventListener('click', () => {
                const message = chip.textContent.trim();
                sendMessage(message);
            });
        });

        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && drawerBackdrop.classList.contains('open')) {
                closeDrawer();
            }
        });
    }

    // Open drawer
    function openDrawer() {
        drawerBackdrop.classList.add('open');
        document.body.style.overflow = 'hidden';

        // Initialize chat on first open
        if (!isInitialized) {
            initializeChat();
        }

        // Focus input
        setTimeout(() => {
            if (coachInput) coachInput.focus();
        }, 300);
    }

    // Close drawer
    function closeDrawer() {
        drawerBackdrop.classList.remove('open');
        document.body.style.overflow = '';
    }

    // Initialize chat (get initial message)
    async function initializeChat() {
        if (isLoading) return;

        isLoading = true;
        showLoading();

        try {
            const response = await fetch('/api/coach/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();
            hideLoading();

            if (data.ok) {
                chatHistory = data.history || [];
                addMessage('assistant', data.message);
                isInitialized = true;
            } else {
                addMessage('assistant', `⚠️ ${data.message || 'Failed to connect to coach.'}`);
            }
        } catch (error) {
            hideLoading();
            addMessage('assistant', '⚠️ Error connecting to coach. Please try again.');
            console.error('Coach init error:', error);
        }

        isLoading = false;
    }

    // Send message
    async function sendMessage(overrideMessage) {
        const message = overrideMessage || (coachInput ? coachInput.value.trim() : '');
        if (!message || isLoading) return;

        // Clear input
        if (coachInput && !overrideMessage) {
            coachInput.value = '';
        }

        // Add user message to chat
        addMessage('user', message);

        isLoading = true;
        showLoading();
        updateSendButton();

        try {
            const response = await fetch('/api/coach/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    history: chatHistory
                })
            });

            const data = await response.json();
            hideLoading();

            if (data.ok) {
                chatHistory = data.history || chatHistory;
                addMessage('assistant', data.message);
            } else {
                addMessage('assistant', `⚠️ ${data.message || 'Error from coach.'}`);
            }
        } catch (error) {
            hideLoading();
            addMessage('assistant', '⚠️ Error sending message. Please try again.');
            console.error('Coach chat error:', error);
        }

        isLoading = false;
        updateSendButton();

        // Focus input
        if (coachInput) coachInput.focus();
    }

    // Add message to chat
    function addMessage(role, content) {
        if (!coachBody) return;

        const bubble = document.createElement('div');
        bubble.className = `chat_bubble ${role}`;

        // Parse markdown-like content
        bubble.innerHTML = parseContent(content);

        coachBody.appendChild(bubble);
        scrollToBottom();
    }

    // Parse content (basic markdown)
    function parseContent(content) {
        if (!content) return '';

        // Escape HTML
        let html = content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Bold
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

        // Italic
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

        // Inline code
        html = html.replace(/`(.+?)`/g, '<code>$1</code>');

        // Line breaks
        html = html.replace(/\n\n/g, '</p><p>');
        html = html.replace(/\n/g, '<br>');

        // Bullet lists
        html = html.replace(/(<br>|<\/p><p>)[-•]\s+/g, '</li><li>');
        if (html.includes('</li><li>')) {
            html = '<ul><li>' + html.replace(/<\/li><li>/, '') + '</li></ul>';
            html = html.replace(/<ul><li><\/li>/g, '<ul>');
        }

        // Wrap in paragraph if not already
        if (!html.startsWith('<')) {
            html = '<p>' + html + '</p>';
        }

        return html;
    }

    // Show loading indicator
    function showLoading() {
        if (!coachBody) return;

        const loading = document.createElement('div');
        loading.className = 'chat_loading';
        loading.id = 'chat_loading';
        loading.innerHTML = '<span></span><span></span><span></span>';
        coachBody.appendChild(loading);
        scrollToBottom();
    }

    // Hide loading indicator
    function hideLoading() {
        const loading = document.getElementById('chat_loading');
        if (loading) loading.remove();
    }

    // Update send button state
    function updateSendButton() {
        if (coachSend) {
            coachSend.disabled = isLoading;
        }
    }

    // Scroll chat to bottom
    function scrollToBottom() {
        if (coachBody) {
            coachBody.scrollTop = coachBody.scrollHeight;
        }
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
