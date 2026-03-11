import React, { useState, useEffect } from 'react';
import NeonEmotionRing, { STATE_COLORS } from './NeonEmotionRing';
import EmotionTimeline from './EmotionTimeline';

const TrackerPanel = ({ currentState, currentRisk, emotionHistory = [], sessionStartTime }) => {
    const [durationStr, setDurationStr] = useState('0m');
    const [stateChanges, setStateChanges] = useState(0);
    const [dominantState, setDominantState] = useState('-');

    // Update Session duration
    useEffect(() => {
        if (!sessionStartTime) return;

        const updateDuration = () => {
            const now = new Date();
            const durationMs = now - new Date(sessionStartTime);
            const minutes = Math.floor(durationMs / 60000);

            if (minutes < 60) {
                setDurationStr(`${minutes}m`);
            } else {
                setDurationStr(`${Math.floor(minutes / 60)}h ${minutes % 60}m`);
            }
        };

        // Run immediately and then every minute
        updateDuration();
        const interval = setInterval(updateDuration, 60000);
        return () => clearInterval(interval);
    }, [sessionStartTime]);

    // Update stats from history
    useEffect(() => {
        if (emotionHistory.length === 0) {
            setStateChanges(0);
            setDominantState('Normal');
            return;
        }

        let changes = 0;
        for (let i = 1; i < emotionHistory.length; i++) {
            if (emotionHistory[i].state !== emotionHistory[i - 1].state) changes++;
        }
        setStateChanges(changes);

        const counts = {};
        emotionHistory.forEach(entry => {
            counts[entry.state] = (counts[entry.state] || 0) + 1;
        });

        let dom = 'Normal';
        let maxCount = 0;
        for (const [state, count] of Object.entries(counts)) {
            if (count > maxCount) {
                maxCount = count;
                dom = state;
            }
        }
        setDominantState(dom);
    }, [emotionHistory]);

    return (
        <div className="emotion-panel">
            <h3 style={{ color: 'white', textAlign: 'center', marginTop: 0 }}>Live Tracker</h3>

            <div className="emotion-meter-container">
                <NeonEmotionRing currentState={currentState} currentRisk={currentRisk} />
            </div>

            {/* Session Graph */}
            <div className="emotion-timeline-container" style={{ margin: '15px 0' }}>
                <h4 style={{ color: 'white', fontSize: '0.85rem', marginBottom: '5px' }}>Session Graph</h4>
                <div style={{ width: '100%', height: '150px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', overflow: 'hidden' }}>
                    <EmotionTimeline emotionHistory={emotionHistory} />
                </div>
            </div>

            {/* Stats */}
            <div className="session-stats">
                <div className="stat-item">
                    <span className="stat-label">Duration:</span>
                    <span id="session-duration">{durationStr}</span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">Changes:</span>
                    <span id="state-changes">{stateChanges}</span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">Dominant:</span>
                    <span id="dominant-state" style={{ fontWeight: 'bold', color: STATE_COLORS[dominantState] || 'white' }}>{dominantState}</span>
                </div>
            </div>
        </div>
    );
};

export default TrackerPanel;
