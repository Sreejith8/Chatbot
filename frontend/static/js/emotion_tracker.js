/**
 * Emotion Tracker - Real-time emotion visualization
 * Provides circular emotion meter, timeline chart, and session statistics
 */

// State color mapping
const STATE_COLORS = {
    'Normal': '#4ade80',      // Green
    'Sadness': '#60a5fa',     // Blue
    'Anxiety': '#fbbf24',     // Yellow
    'Stress': '#fb923c',      // Orange
    'Depression': '#a78bfa',  // Purple
    'Bipolar': '#ec4899',     // Pink
    'ADHD': '#22d3ee'         // Cyan
};

const RISK_COLORS = {
    'Low': '#4ade80',
    'Medium': '#fb923c',
    'High': '#ef4444'
};

// Session data
let emotionHistory = [];
let sessionStartTime = null;
let emotionMeter = null;
let emotionTimeline = null;
let sessionDurationInterval = null;

/**
 * Circular Emotion Meter
 */
class EmotionMeter {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error('[EmotionMeter] Canvas not found:', canvasId);
            return;
        }
        this.ctx = this.canvas.getContext('2d');
        this.currentState = 'Normal';
        this.currentRisk = 'Low';
        this.animationProgress = 0;
        this.targetColor = STATE_COLORS['Normal'];
        this.currentColor = STATE_COLORS['Normal'];

        // Set canvas size based on container
        this.resizeCanvas();
        this.render();

        // Add resize listener
        window.addEventListener('resize', () => this.resizeCanvas());
    }

    resizeCanvas() {
        const container = this.canvas.parentElement;
        const size = Math.min(container.offsetWidth * 0.8, 200);
        this.canvas.width = size;
        this.canvas.height = size;
        this.render();
    }

    update(state, risk) {
        this.currentState = state || 'Normal';
        this.currentRisk = risk || 'Low';
        this.targetColor = this.getStateColor(state, risk);
        this.animate();
    }

    getStateColor(state, risk) {
        // High risk overrides state color
        if (risk === 'High') {
            return RISK_COLORS['High'];
        }
        return STATE_COLORS[state] || STATE_COLORS['Normal'];
    }

    animate() {
        this.animationProgress = 0;
        const startColor = this.currentColor;
        const endColor = this.targetColor;

        const step = () => {
            this.animationProgress += 0.05;
            if (this.animationProgress >= 1) {
                this.currentColor = endColor;
                this.render();
                return;
            }

            // Interpolate color
            this.currentColor = this.interpolateColor(startColor, endColor, this.animationProgress);
            this.render();
            requestAnimationFrame(step);
        };

        requestAnimationFrame(step);
    }

    interpolateColor(color1, color2, factor) {
        const c1 = this.hexToRgb(color1);
        const c2 = this.hexToRgb(color2);

        const r = Math.round(c1.r + (c2.r - c1.r) * factor);
        const g = Math.round(c1.g + (c2.g - c1.g) * factor);
        const b = Math.round(c1.b + (c2.b - c1.b) * factor);

        return `rgb(${r}, ${g}, ${b})`;
    }

    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : { r: 0, g: 0, b: 0 };
    }

    render() {
        if (!this.ctx) return;

        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const radius = Math.min(this.canvas.width, this.canvas.height) * 0.35;

        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw outer ring (background)
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        this.ctx.lineWidth = 15;
        this.ctx.stroke();

        // Draw colored arc (emotion indicator)
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius, -Math.PI / 2, Math.PI * 1.5);
        this.ctx.strokeStyle = this.currentColor;
        this.ctx.lineWidth = 15;
        this.ctx.lineCap = 'round';
        this.ctx.stroke();

        // Draw inner circle
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius - 20, 0, 2 * Math.PI);
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
        this.ctx.fill();

        // Add glow effect
        this.ctx.shadowBlur = 20;
        this.ctx.shadowColor = this.currentColor;
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius, -Math.PI / 2, Math.PI * 1.5);
        this.ctx.strokeStyle = this.currentColor;
        this.ctx.lineWidth = 15;
        this.ctx.stroke();
        this.ctx.shadowBlur = 0;
    }
}

/**
 * Emotion Timeline Chart
 */
class EmotionTimeline {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error('[EmotionTimeline] Canvas not found:', canvasId);
            return;
        }
        this.ctx = this.canvas.getContext('2d');
        this.dataPoints = [];
        this.maxPoints = 50;

        // Set canvas size based on container
        this.resizeCanvas();
        this.render();

        // Add resize listener
        window.addEventListener('resize', () => this.resizeCanvas());
    }

    resizeCanvas() {
        const container = this.canvas.parentElement;
        const width = container.offsetWidth;
        const height = Math.min(150, width * 0.4);
        this.canvas.width = width;
        this.canvas.height = height;
        this.render();
    }

    addDataPoint(state, risk, timestamp) {
        this.dataPoints.push({
            state: state || 'Normal',
            risk: risk || 'Low',
            timestamp: timestamp || new Date(),
            color: this.getPointColor(state, risk)
        });

        // Limit to max points
        if (this.dataPoints.length > this.maxPoints) {
            this.dataPoints.shift();
        }

        this.render();
    }

    getPointColor(state, risk) {
        if (risk === 'High') return RISK_COLORS['High'];
        return STATE_COLORS[state] || STATE_COLORS['Normal'];
    }

    clear() {
        this.dataPoints = [];
        this.render();
    }

    render() {
        if (!this.ctx) return;

        const width = this.canvas.width;
        const height = this.canvas.height;
        const padding = 30;
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding * 2;

        // Clear canvas
        this.ctx.clearRect(0, 0, width, height);

        if (this.dataPoints.length === 0) {
            // Show "No data yet" message
            this.ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
            this.ctx.font = '14px Inter, sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('No emotion data yet', width / 2, height / 2);
            return;
        }

        // Draw axes
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        this.ctx.lineWidth = 1;
        this.ctx.beginPath();
        this.ctx.moveTo(padding, padding);
        this.ctx.lineTo(padding, height - padding);
        this.ctx.lineTo(width - padding, height - padding);
        this.ctx.stroke();

        // Draw data points and connecting lines
        const pointSpacing = chartWidth / Math.max(this.dataPoints.length - 1, 1);

        for (let i = 0; i < this.dataPoints.length; i++) {
            const x = padding + i * pointSpacing;
            const y = padding + chartHeight / 2; // Center vertically for now

            // Draw connecting line
            if (i > 0) {
                const prevX = padding + (i - 1) * pointSpacing;
                const prevY = padding + chartHeight / 2;

                this.ctx.strokeStyle = this.dataPoints[i].color;
                this.ctx.lineWidth = 2;
                this.ctx.beginPath();
                this.ctx.moveTo(prevX, prevY);
                this.ctx.lineTo(x, y);
                this.ctx.stroke();
            }

            // Draw data point
            this.ctx.beginPath();
            this.ctx.arc(x, y, 4, 0, 2 * Math.PI);
            this.ctx.fillStyle = this.dataPoints[i].color;
            this.ctx.fill();

            // Add glow
            this.ctx.shadowBlur = 8;
            this.ctx.shadowColor = this.dataPoints[i].color;
            this.ctx.beginPath();
            this.ctx.arc(x, y, 4, 0, 2 * Math.PI);
            this.ctx.fillStyle = this.dataPoints[i].color;
            this.ctx.fill();
            this.ctx.shadowBlur = 0;
        }

        // Draw time labels (first and last)
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
        this.ctx.font = '10px Inter, sans-serif';
        this.ctx.textAlign = 'left';

        if (this.dataPoints.length > 0) {
            const firstTime = this.formatTime(this.dataPoints[0].timestamp);
            const lastTime = this.formatTime(this.dataPoints[this.dataPoints.length - 1].timestamp);

            this.ctx.fillText(firstTime, padding, height - 10);
            this.ctx.textAlign = 'right';
            this.ctx.fillText(lastTime, width - padding, height - 10);
        }
    }

    formatTime(date) {
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

/**
 * Initialize emotion tracker
 */
function initEmotionTracker() {
    console.log('[EmotionTracker] Initializing...');

    // Reset session data
    emotionHistory = [];
    sessionStartTime = new Date();

    // Initialize visualizations
    emotionMeter = new EmotionMeter('emotion-meter');
    emotionTimeline = new EmotionTimeline('emotion-timeline');

    // Start session duration timer
    updateSessionDuration();
    sessionDurationInterval = setInterval(updateSessionDuration, 60000); // Update every minute

    // Reset statistics
    updateSessionStats();

    console.log('[EmotionTracker] Initialized successfully');
}

/**
 * Update emotion display
 */
function updateEmotionDisplay(state, risk) {
    console.log('[EmotionTracker] Updating:', state, risk);

    // Update meter
    if (emotionMeter) {
        emotionMeter.update(state, risk);
    }

    // Update timeline
    if (emotionTimeline) {
        emotionTimeline.addDataPoint(state, risk, new Date());
    }

    // Add to history
    emotionHistory.push({
        state: state,
        risk: risk,
        timestamp: new Date()
    });

    // Update current emotion label
    const emotionLabel = document.getElementById('current-emotion-text');
    if (emotionLabel) {
        emotionLabel.textContent = state || 'Normal';
        emotionLabel.style.color = STATE_COLORS[state] || STATE_COLORS['Normal'];
    }

    // Update statistics
    updateSessionStats();
}

/**
 * Update session statistics
 */
function updateSessionStats() {
    // Calculate actual state changes (only count when state differs from previous)
    let stateChanges = 0;
    for (let i = 1; i < emotionHistory.length; i++) {
        if (emotionHistory[i].state !== emotionHistory[i - 1].state) {
            stateChanges++;
        }
    }

    const stateChangesEl = document.getElementById('state-changes');
    if (stateChangesEl) {
        stateChangesEl.textContent = stateChanges;
    }

    // Calculate dominant state
    const stateCounts = {};
    emotionHistory.forEach(entry => {
        stateCounts[entry.state] = (stateCounts[entry.state] || 0) + 1;
    });

    let dominantState = 'Normal';
    let maxCount = 0;
    for (const [state, count] of Object.entries(stateCounts)) {
        if (count > maxCount) {
            maxCount = count;
            dominantState = state;
        }
    }

    const dominantStateEl = document.getElementById('dominant-state');
    if (dominantStateEl) {
        dominantStateEl.textContent = dominantState;
        dominantStateEl.style.color = STATE_COLORS[dominantState] || STATE_COLORS['Normal'];
    }
}

/**
 * Update session duration
 */
function updateSessionDuration() {
    if (!sessionStartTime) return;

    const now = new Date();
    const durationMs = now - sessionStartTime;
    const minutes = Math.floor(durationMs / 60000);

    const durationEl = document.getElementById('session-duration');
    if (durationEl) {
        if (minutes < 60) {
            durationEl.textContent = `${minutes}m`;
        } else {
            const hours = Math.floor(minutes / 60);
            const remainingMinutes = minutes % 60;
            durationEl.textContent = `${hours}h ${remainingMinutes}m`;
        }
    }
}

/**
 * Reset emotion tracker
 */
function resetEmotionTracker() {
    console.log('[EmotionTracker] Resetting...');

    // Clear history
    emotionHistory = [];
    sessionStartTime = null;

    // Clear visualizations
    if (emotionTimeline) {
        emotionTimeline.clear();
    }

    if (emotionMeter) {
        emotionMeter.update('Normal', 'Low');
    }

    // Clear interval
    if (sessionDurationInterval) {
        clearInterval(sessionDurationInterval);
        sessionDurationInterval = null;
    }

    // Reset statistics
    const stateChangesEl = document.getElementById('state-changes');
    const dominantStateEl = document.getElementById('dominant-state');
    const durationEl = document.getElementById('session-duration');

    if (stateChangesEl) stateChangesEl.textContent = '0';
    if (dominantStateEl) {
        dominantStateEl.textContent = 'Normal';
        dominantStateEl.style.color = STATE_COLORS['Normal'];
    }
    if (durationEl) durationEl.textContent = '0m';

    const emotionLabel = document.getElementById('current-emotion-text');
    if (emotionLabel) {
        emotionLabel.textContent = 'Normal';
        emotionLabel.style.color = STATE_COLORS['Normal'];
    }
}

// Export functions for global access
window.initEmotionTracker = initEmotionTracker;
window.updateEmotionDisplay = updateEmotionDisplay;
window.resetEmotionTracker = resetEmotionTracker;

/**
 * Hydrate emotion history from existing messages
 * @param {Array} historyData - Array of objects {state, risk, timestamp}
 */
window.hydrateEmotionHistory = function (historyData) {
    if (!historyData || !Array.isArray(historyData)) return;

    // Clear current
    emotionHistory = [];
    if (emotionTimeline) emotionTimeline.clear();

    // Add points chronologically
    historyData.forEach(item => {
        if (!item.state) return;

        const timestamp = item.timestamp ? new Date(item.timestamp) : new Date();

        emotionHistory.push({
            state: item.state,
            risk: item.risk_level || 'Low',
            timestamp: timestamp
        });

        if (emotionTimeline) {
            emotionTimeline.addDataPoint(item.state, item.risk_level, timestamp);
        }
    });

    // Update last known state on meter
    if (emotionHistory.length > 0) {
        const last = emotionHistory[emotionHistory.length - 1];
        if (emotionMeter) emotionMeter.update(last.state, last.risk);

        const emotionLabel = document.getElementById('current-emotion-text');
        if (emotionLabel) {
            emotionLabel.textContent = last.state;
            emotionLabel.style.color = STATE_COLORS[last.state] || STATE_COLORS['Normal'];
        }
    }

    updateSessionStats();
    console.log(`[EmotionTracker] Hydrated with ${emotionHistory.length} points`);
};
