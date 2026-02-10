const API_URL = "";
let token = localStorage.getItem('access_token');

// Chat History Configuration
const CHAT_CONFIG = {
    MAX_MESSAGES: 100,           // Maximum messages to store
    CLEAR_ON_LOGOUT: false,      // Whether to clear history on logout
    ENABLE_PERSISTENCE: true     // Master switch for persistence
};

// Get username from JWT token
function getCurrentUsername() {
    if (!token) return null;
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.sub || payload.username || payload.identity;
    } catch (e) {
        console.error('[ChatHistory] Failed to decode token:', e);
        return null;
    }
}

// Save chat history to localStorage
function saveChatHistory(message, sender, state = null, risk_level = null) {
    if (!CHAT_CONFIG.ENABLE_PERSISTENCE) return;

    const username = getCurrentUsername();
    if (!username) return;

    try {
        const key = `chat_history_${username}`;
        let history = JSON.parse(localStorage.getItem(key) || '{"messages": []}');

        history.messages.push({
            text: message,
            sender: sender,
            timestamp: new Date().toISOString(),
            state: state,
            risk_level: risk_level
        });

        // Limit to MAX_MESSAGES
        if (history.messages.length > CHAT_CONFIG.MAX_MESSAGES) {
            history.messages = history.messages.slice(-CHAT_CONFIG.MAX_MESSAGES);
        }

        history.username = username;
        history.lastUpdated = new Date().toISOString();

        localStorage.setItem(key, JSON.stringify(history));
    } catch (e) {
        console.error('[ChatHistory] Failed to save:', e);
    }
}

// Load chat history from API (fallback to localStorage)
async function loadChatHistory() {
    if (!token) return;

    try {
        const res = await fetch(`${API_URL}/api/chat_history`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.ok) {
            const data = await res.json();
            const area = document.getElementById('messages');
            if (!area) return;
            area.innerHTML = ''; // Clear

            const emotionPoints = [];
            data.messages.forEach(msg => {
                appendMessage(msg.text, msg.sender, false); // Don't save to local again

                // Update state/risk from last bot message
                if (msg.sender === 'bot' && (msg.state || msg.risk_level)) {
                    updateStatusDisplay(msg.state, msg.risk_level);
                    if (msg.state) {
                        emotionPoints.push({
                            state: msg.state,
                            risk_level: msg.risk_level,
                            timestamp: msg.timestamp
                        });
                    }
                }
            });

            // Hydrate Emotion Tracker
            if (window.hydrateEmotionHistory && emotionPoints.length > 0) {
                setTimeout(() => window.hydrateEmotionHistory(emotionPoints), 500);
            }

            console.log(`[ChatHistory] Loaded ${data.messages.length} messages from API`);
            return; // Success
        }
    } catch (e) {
        console.error('[ChatHistory] API load failed, trying local:', e);
    }

    // Fallback to LocalStorage
    if (!CHAT_CONFIG.ENABLE_PERSISTENCE) return;

    const username = getCurrentUsername();
    if (!username) return;

    try {
        const key = `chat_history_${username}`;
        const history = JSON.parse(localStorage.getItem(key) || '{"messages": []}');

        const area = document.getElementById('messages');
        if (!area) return;
        area.innerHTML = '';

        history.messages.forEach(msg => {
            appendMessage(msg.text, msg.sender, false);
            if (msg.sender === 'bot' && msg.state) {
                updateStatusDisplay(msg.state, msg.risk_level);
            }
        });
    } catch (e) {
        console.error('[ChatHistory] Local load failed:', e);
    }
}

function updateStatusDisplay(state, risk) {
    const stateEl = document.getElementById('state-display') || document.getElementById('current-state');
    const riskEl = document.getElementById('risk-display') || document.getElementById('risk-level');

    if (stateEl && state) stateEl.innerText = state;
    if (riskEl && risk) {
        riskEl.innerText = risk;
        // Update badge color
        const badge = document.getElementById('risk-badge');
        if (badge) {
            badge.style.background = risk === 'High' ? 'rgba(239, 68, 68, 0.4)' :
                risk === 'Medium' ? 'rgba(251, 146, 60, 0.4)' :
                    'rgba(74, 222, 128, 0.2)';
        }
    }

    // Also update emotion tracker if present
    if (typeof updateEmotionDisplay === 'function' && state) {
        // We don't want to re-add points for history loading usually, 
        // but for now let's just update the label
        const emotionLabel = document.getElementById('current-emotion-text');
        if (emotionLabel) {
            emotionLabel.textContent = state;
            // Color map is in emotion_tracker.js, tedious to duplicate here.
            // We'll trust the tracker handles live updates.
        }
    }
}

// Clear chat history
function clearChatHistory() {
    const username = getCurrentUsername();
    if (!username) return;

    try {
        const key = `chat_history_${username}`;
        localStorage.removeItem(key);
        console.log(`[ChatHistory] Cleared history for ${username}`);
    } catch (e) {
        console.error('[ChatHistory] Failed to clear:', e);
    }
}

function updateView() {
    if (token) {
        document.getElementById('auth-container').classList.add('hidden');
        document.getElementById('chat-container').classList.remove('hidden');

        // Show Admin Link if applicable
        const role = localStorage.getItem('user_role');
        const adminLink = document.getElementById('admin-link');
        if (adminLink) {
            adminLink.style.display = (role === 'Admin') ? 'block' : 'none';
        }
    } else {
        document.getElementById('auth-container').classList.remove('hidden');
        document.getElementById('chat-container').classList.add('hidden');
    }
}

async function login() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    const res = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });

    const data = await res.json();
    if (res.ok) {
        token = data.access_token;
        localStorage.setItem('access_token', token);

        // Store Role
        if (data.is_admin) {
            localStorage.setItem('user_role', 'Admin');
        } else {
            localStorage.setItem('user_role', 'User');
        }

        updateView();
        loadChatHistory(); // Load chat history after login

        // Initialize emotion tracker
        if (typeof initEmotionTracker === 'function') {
            initEmotionTracker();
        }
    } else {
        alert(data.msg);
    }
}

async function register() {
    const username = document.getElementById('reg-username').value;
    const password = document.getElementById('reg-password').value;

    const res = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });

    const data = await res.json();
    alert(data.msg);
}

function logout() {
    // Reset emotion tracker
    if (typeof resetEmotionTracker === 'function') {
        resetEmotionTracker();
    }

    // Optional: Clear chat history on logout
    if (CHAT_CONFIG.CLEAR_ON_LOGOUT) {
        clearChatHistory();
    }

    localStorage.removeItem('access_token');
    localStorage.removeItem('user_role'); // Clear role
    token = null;
    updateView();
}

async function sendMessage() {
    const inputFn = document.getElementById('message-input');
    const text = inputFn.value;
    if (!text) return;

    // Add user message to UI
    appendMessage(text, 'user', true); // true = save to history
    inputFn.value = '';

    const sessionId = localStorage.getItem('current_session_id');

    const res = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            message: text,
            session_id: sessionId
        })
    });

    if (res.status === 401) {
        logout();
        return;
    }

    const data = await res.json();
    appendMessage(data.response, 'bot', true, data.state, data.risk_level); // Save with state/risk

    // Update status
    const stateEl = document.getElementById('state-display') || document.getElementById('current-state');
    const riskEl = document.getElementById('risk-display') || document.getElementById('risk-level');

    if (stateEl) stateEl.innerText = data.state;
    if (riskEl) riskEl.innerText = data.risk_level;

    // Update emotion tracker
    if (data.state && data.risk_level && typeof updateEmotionDisplay === 'function') {
        updateEmotionDisplay(data.state, data.risk_level);
    }
}

function appendMessage(text, sender, shouldSave = true, state = null, risk_level = null) {
    const area = document.getElementById('messages');
    if (!area) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}-msg`;
    msgDiv.innerText = text;
    area.appendChild(msgDiv);
    area.scrollTop = area.scrollHeight;

    // Save to localStorage
    if (shouldSave) {
        saveChatHistory(text, sender, state, risk_level);
    }
}

function handleKeyPress(e) {
    if (e.key === 'Enter') sendMessage();
}

function showLogin() {
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('register-form').style.display = 'none';
}

function showRegister() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
}

// Init
// New Session Logic
async function startNewSession() {
    // 1. End current session (generate summary)
    // We need the current session ID. 
    // Ideally, we should store it in localStorage or a variable.
    // For now, let's assume the backend finds the last active session for the user 
    // OR we just fire the end request. 
    // Wait, the API expects a session_id. 
    // We should have been storing session_id.

    // Let's check if we store session_id. multimodal_routes returns it on start.
    // app.js doesn't seem to have startSession logic visible in the snippet.
    // It seems sessions are continuous?

    // If we don't have session_id content side, we can't cleanly end it unless we add tracking.
    // Let's try to get it from localStorage if we added it, or just rely on backend to find active?
    // No, backend implementation of end_session requires ID.

    const sessionId = localStorage.getItem('current_session_id');
    if (sessionId) {
        try {
            console.log("Ending session:", sessionId);
            await fetch(`${API_URL}/api/multimodal_session/end`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });
            localStorage.removeItem('current_session_id');
        } catch (e) {
            console.error("Failed to end session:", e);
        }
    }

    // 2. Start new session
    try {
        const res = await fetch(`${API_URL}/api/multimodal_session/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await res.json();
        if (data.session_id) {
            localStorage.setItem('current_session_id', data.session_id);
            console.log("Started new session:", data.session_id);
        }
    } catch (e) {
        console.error("Failed to start new session:", e);
    }

    // 3. Clear UI
    const area = document.getElementById('messages');
    if (area) area.innerHTML = '';

    // Clear history
    clearChatHistory();

    // Reset Emotion Tracker
    if (typeof resetEmotionTracker === 'function') {
        resetEmotionTracker();
    }

    // Reset Status
    updateStatusDisplay("Neutral", "Low");
}

// Expose to window for button onclick
window.startNewSession = startNewSession;

updateView();

// Start a session on load if logged in
if (token && !localStorage.getItem('current_session_id')) {
    startNewSession(); // Auto-start
}
