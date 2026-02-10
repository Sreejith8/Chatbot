/**
 * mic_button_controller.js
 * Controls the UI interaction for continuous multimodal conversation sessions.
 */

document.addEventListener('DOMContentLoaded', () => {
    const micButton = document.getElementById('mic-button');
    const chatInput = document.getElementById('message-input');
    const chatBox = document.getElementById('messages');

    // Session State Management
    const SESSION_STATES = {
        IDLE: 'idle',
        ACTIVE: 'active',
        PROCESSING: 'processing'
    };

    let currentState = SESSION_STATES.IDLE;
    let sessionStartTime = null;
    let sessionTimerInterval = null;
    let sessionId = null; // Track backend session ID

    // Create Unified Multimodal UI Container
    let mmContainer = document.getElementById('multimodal-ui-container');
    if (!mmContainer) {
        mmContainer = document.createElement('div');
        mmContainer.id = 'multimodal-ui-container';
        mmContainer.className = 'multimodal-ui-container';
        // Initially hidden
        mmContainer.style.display = 'none';
        document.body.appendChild(mmContainer);
    }

    // Create Camera Preview Modal (inside container)
    let previewModal = document.getElementById('camera-preview-modal');
    if (!previewModal) {
        previewModal = document.createElement('div');
        previewModal.id = 'camera-preview-modal';
        previewModal.className = 'video-preview-modal';
        const video = document.createElement('video');
        video.id = 'preview-video';
        video.style.cssText = 'width: 100%; height: 100%; object-fit: cover; transform: scaleX(-1);'; // Mirror effect
        video.muted = true;
        video.autoplay = true;
        video.playsInline = true;
        previewModal.appendChild(video);
        mmContainer.appendChild(previewModal);
    }

    // Create Controls Helper Container (inside container)
    // We want the controls to be grouped
    let controlsGroup = document.createElement('div');
    controlsGroup.className = 'multimodal-controls-group';
    mmContainer.appendChild(controlsGroup);

    // Create Session Timer Display (inside controls)
    let sessionTimer = document.getElementById('session-timer');
    if (!sessionTimer) {
        sessionTimer = document.createElement('div');
        sessionTimer.id = 'session-timer';
        sessionTimer.className = 'session-timer-display';
        sessionTimer.innerText = '00:00';
        controlsGroup.appendChild(sessionTimer);
    }

    // Create Send Button (inside controls)
    let sendButton = document.getElementById('send-turn-button');
    if (!sendButton) {
        sendButton = document.createElement('button');
        sendButton.id = 'send-turn-button';
        sendButton.className = 'multimodal-send-btn';
        sendButton.innerHTML = '<ion-icon name="send"></ion-icon> Send';
        controlsGroup.appendChild(sendButton);
    }

    const previewVideo = document.getElementById('preview-video');
    const mediaCapture = new window.MediaCapture();

    // Mic Button Click Handler - Toggle Session
    if (micButton) {
        micButton.addEventListener('click', async () => {
            if (currentState === SESSION_STATES.IDLE) {
                await startSession();
            } else if (currentState === SESSION_STATES.ACTIVE) {
                await endSession();
            }
            // Ignore clicks during PROCESSING state
        });
    }

    // Send Button Click Handler
    if (sendButton) {
        sendButton.addEventListener('click', async () => {
            if (currentState === SESSION_STATES.ACTIVE) {
                await sendTurn();
            }
        });
    }

    /**
     * Start a new continuous conversation session
     */
    async function startSession() {
        try {
            console.log("[Session] Starting continuous session...");

            // Request permissions and start stream
            await mediaCapture.requestPermissions();

            // Update UI
            // Update UI
            // Show container
            mmContainer.classList.remove('hidden');
            mmContainer.style.display = 'flex';

            // Ensure children are visible (if they had display stylings)
            previewModal.style.display = 'block';
            sendButton.style.display = 'flex'; // Flex to align icon
            sessionTimer.style.display = 'block';
            micButton.classList.add('recording');
            micButton.innerHTML = '<ion-icon name="stop-circle"></ion-icon>';

            // Start continuous capture
            mediaCapture.startContinuousCapture(previewVideo);

            // Create backend session
            try {
                const response = await fetch('/api/multimodal_session/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await response.json();
                sessionId = data.session_id;
                console.log('[Session] Backend session created:', sessionId);
            } catch (err) {
                console.error('[Session] Failed to create backend session:', err);
                // Continue without session (fallback to standalone mode)
            }

            // Update state
            currentState = SESSION_STATES.ACTIVE;
            sessionStartTime = Date.now();

            // Start session timer
            updateSessionTimer();
            sessionTimerInterval = setInterval(updateSessionTimer, 1000);

            addMessage('System', 'Live session started. Speak and click "Send" when ready.', 'bot');

        } catch (err) {
            console.error("[Session] Failed to start:", err);
            alert(err.message);
            currentState = SESSION_STATES.IDLE;
        }
    }

    /**
     * Send current turn (capture buffer and submit to backend)
     */
    async function sendTurn() {
        if (currentState !== SESSION_STATES.ACTIVE) return;

        console.log("[Session] Sending turn...");
        currentState = SESSION_STATES.PROCESSING;
        sendButton.disabled = true;
        sendButton.style.opacity = '0.5';

        // Capture current buffer
        const data = await mediaCapture.captureCurrentBuffer();

        if (!data || !data.audioBlob || data.audioBlob.size === 0) {
            addMessage('System', 'No audio detected. Please speak and try again.', 'error');
            currentState = SESSION_STATES.ACTIVE;
            sendButton.disabled = false;
            sendButton.style.opacity = '1';
            return;
        }

        addMessage('You', 'Processing...', 'user');

        // Send to backend
        await sendMultimodalData(data);

        // Return to active state (ready for next turn)
        currentState = SESSION_STATES.ACTIVE;
        sendButton.disabled = false;
        sendButton.style.opacity = '1';
    }

    /**
     * End the continuous session
     */
    async function endSession() {
        console.log("[Session] Ending session...");

        // Stop timer
        if (sessionTimerInterval) {
            clearInterval(sessionTimerInterval);
            sessionTimerInterval = null;
        }

        // End backend session
        if (sessionId) {
            try {
                await fetch('/api/multimodal_session/end', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId })
                });
                console.log('[Session] Backend session ended:', sessionId);
            } catch (err) {
                console.error('[Session] Failed to end backend session:', err);
            }
            sessionId = null;
        }

        console.log("[Session] Ended.");
        // Stop capture and release resources
        mediaCapture.endSession();

        // Update UI
        mmContainer.classList.add('hidden');
        mmContainer.style.display = 'none';
        micButton.classList.remove('recording');
        micButton.innerHTML = '<ion-icon name="mic"></ion-icon>';

        // Reset state
        currentState = SESSION_STATES.IDLE;
        sessionStartTime = null;

        addMessage('System', 'Session ended.', 'bot');
    }

    /**
     * Update session timer display
     */
    function updateSessionTimer() {
        if (!sessionStartTime) return;

        const elapsed = Math.floor((Date.now() - sessionStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
        const seconds = (elapsed % 60).toString().padStart(2, '0');
        sessionTimer.innerText = `${minutes}:${seconds}`;
    }

    /**
     * Send multimodal data to backend
     */
    async function sendMultimodalData(data) {
        const formData = new FormData();
        formData.append('audio', data.audioBlob, 'input.webm');

        // Append all frames
        for (let i = 0; i < data.videoFrames.length; i++) {
            formData.append('frames', data.videoFrames[i], `frame_${i}.jpg`);
        }

        // Include session ID if available
        if (sessionId) {
            formData.append('session_id', sessionId);
            console.log('[Session] Sending turn with session ID:', sessionId);
        }

        // Append Metadata
        const metadata = {
            timestamp: new Date().toISOString(),
            session_mode: 'continuous'
        };
        formData.append('metadata', JSON.stringify(metadata));

        try {
            // Get JWT from storage if exists
            const token = localStorage.getItem('access_token');
            const headers = {};
            if (token) headers['Authorization'] = `Bearer ${token}`;

            const response = await fetch('/api/multimodal_input', {
                method: 'POST',
                headers: headers,
                body: formData
            });

            const result = await response.json();


            // Display Bot Response
            if (result.response) {
                // Use the global appendMessage function from app.js if available
                if (typeof appendMessage === 'function') {
                    appendMessage(result.response, 'bot', true, result.state, result.risk_level);
                } else {
                    // Fallback if app.js not loaded
                    addMessage('HybridBot', result.response, 'bot');
                }
            }

            // Update UI State/Risk Indicators
            if (result.state) {
                const stateElement = document.getElementById('current-state');
                if (stateElement) {
                    stateElement.textContent = result.state;
                }
            }

            if (result.risk_level) {
                const riskElement = document.getElementById('risk-level');
                if (riskElement) {
                    riskElement.textContent = result.risk_level;

                    // Update risk badge color based on level
                    const riskBadge = riskElement.closest('.risk-badge');
                    if (riskBadge) {
                        riskBadge.style.background =
                            result.risk_level === 'High' ? 'rgba(255, 0, 0, 0.3)' :
                                result.risk_level === 'Medium' ? 'rgba(255, 165, 0, 0.3)' :
                                    'rgba(0, 255, 0, 0.2)';
                    }
                }
            }

            // Update emotion tracker
            if (result.state && result.risk_level && typeof updateEmotionDisplay === 'function') {
                updateEmotionDisplay(result.state, result.risk_level);
            }


            // Display State/Risk Info (Debug)
            console.log("Predicted State:", result.state);
            console.log("Risk Level:", result.risk_level);
            if (result.transcription) {
                console.log("Transcription:", result.transcription);
            }

        } catch (err) {
            console.error("Upload failed:", err);
            addMessage('System', 'Error processing input. Please try again.', 'error');
        }
    }

    /**
     * Helper to add messages to chat UI
     */
    function addMessage(sender, text, type) {
        // Try to use global addChatBubble if available
        if (typeof window.addChatBubble === 'function') {
            window.addChatBubble(sender, text, type);
        } else {
            console.log(`${sender}: ${text}`);
            // Fallback DOM manipulation
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${type}`;
            msgDiv.innerText = `${sender}: ${text}`;
            chatBox.appendChild(msgDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    }
});
