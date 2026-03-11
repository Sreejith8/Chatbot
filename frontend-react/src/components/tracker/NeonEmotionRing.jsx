import React, { useEffect, useRef } from 'react';

const STATE_COLORS = {
    'Normal': '#4ade80',
    'Sadness': '#60a5fa',
    'Anxiety': '#fbbf24',
    'Stress': '#fb923c',
    'Depression': '#a78bfa',
    'Bipolar': '#ec4899',
    'ADHD': '#22d3ee',
    'Happy': '#fde047',   // Adding yellow for Happy
    'Angry': '#dc2626',   // Adding red for Angry
    'Fear': '#9333ea'     // Adding deep purple for Fear
};

const RISK_COLORS = {
    'Low': '#4ade80',
    'Medium': '#fb923c',
    'High': '#ef4444'
};

const hexToRgb = (hex) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : { r: 0, g: 0, b: 0 };
};

const interpolateColor = (color1, color2, factor) => {
    const c1 = hexToRgb(color1);
    const c2 = hexToRgb(color2);
    const r = Math.round(c1.r + (c2.r - c1.r) * factor);
    const g = Math.round(c1.g + (c2.g - c1.g) * factor);
    const b = Math.round(c1.b + (c2.b - c1.b) * factor);
    return `rgb(${r}, ${g}, ${b})`;
};

const getStateColor = (state, risk) => {
    if (risk === 'High') return RISK_COLORS['High'];
    return STATE_COLORS[state] || STATE_COLORS['Normal'];
};

const NeonEmotionRing = ({ currentState, currentRisk }) => {
    const canvasRef = useRef(null);
    const animState = useRef({
        currentColor: STATE_COLORS['Normal'],
        targetColor: STATE_COLORS['Normal'],
        progress: 1,
        animationFrameId: null
    });

    useEffect(() => {
        const targetHex = getStateColor(currentState, currentRisk);
        animState.current.targetColor = targetHex;
        animState.current.progress = 0; // Trigger animation
    }, [currentState, currentRisk]);

    useEffect(() => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        const container = canvas.parentElement;

        const resize = () => {
            const size = Math.min(container.offsetWidth * 0.8, 200);
            canvas.width = size;
            canvas.height = size;
        };

        window.addEventListener('resize', resize);
        resize();

        const render = () => {
            const state = animState.current;

            if (state.progress < 1) {
                state.progress += 0.05;
                state.currentColor = interpolateColor(state.currentColor, state.targetColor, Math.min(state.progress, 1));
                if (state.progress >= 1) {
                    state.currentColor = state.targetColor;
                }
            }

            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            const radius = Math.min(canvas.width, canvas.height) * 0.35;

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Outer ring
            ctx.beginPath();
            ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
            ctx.lineWidth = 15;
            ctx.stroke();

            // Colored Arc
            ctx.beginPath();
            ctx.arc(centerX, centerY, radius, -Math.PI / 2, Math.PI * 1.5);
            ctx.strokeStyle = state.currentColor;
            ctx.lineWidth = 15;
            ctx.lineCap = 'round';
            ctx.stroke();

            // Inner circle
            ctx.beginPath();
            ctx.arc(centerX, centerY, radius - 20, 0, 2 * Math.PI);
            ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
            ctx.fill();

            // Glow
            ctx.shadowBlur = 20;
            ctx.shadowColor = state.currentColor;
            ctx.beginPath();
            ctx.arc(centerX, centerY, radius, -Math.PI / 2, Math.PI * 1.5);
            ctx.strokeStyle = state.currentColor;
            ctx.lineWidth = 15;
            ctx.stroke();
            ctx.shadowBlur = 0;

            state.animationFrameId = requestAnimationFrame(render);
        };

        render();

        return () => {
            window.removeEventListener('resize', resize);
            if (animState.current.animationFrameId) {
                cancelAnimationFrame(animState.current.animationFrameId);
            }
        };
    }, []);

    const textColor = getStateColor(currentState, currentRisk);

    return (
        <div style={{ position: 'relative', width: '100%', display: 'flex', justifyContent: 'center' }}>
            <canvas ref={canvasRef} />
            <div className="current-emotion-label" style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', fontWeight: 'bold' }}>
                <span id="current-emotion-text" style={{ color: textColor }}>{currentState || 'Normal'}</span>
            </div>
        </div>
    );
};

export { STATE_COLORS, RISK_COLORS, getStateColor };
export default NeonEmotionRing;
