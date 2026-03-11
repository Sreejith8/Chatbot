import { useState, useRef, useCallback, useEffect } from 'react';
import axios from 'axios';
import useMediaCapture from './useMediaCapture';

export const SESSION_STATES = {
    IDLE: 'idle',
    ACTIVE: 'active',
    PROCESSING: 'processing'
};

const useMultimodalSession = (onMessageReceived, onStateUpdated) => {
    const { isCapturing, startContinuousCapture, captureCurrentBuffer, endSession } = useMediaCapture();

    const [sessionState, setSessionState] = useState(SESSION_STATES.IDLE);
    const [sessionId, setSessionId] = useState(null);
    const [sessionSeconds, setSessionSeconds] = useState(0);

    const timerIntervalRef = useRef(null);
    const videoRef = useRef(null);

    // Format timer
    const formattedTimer = `${Math.floor(sessionSeconds / 60).toString().padStart(2, '0')}:${(sessionSeconds % 60).toString().padStart(2, '0')}`;

    // Timer effect
    useEffect(() => {
        if (sessionState === SESSION_STATES.ACTIVE) {
            timerIntervalRef.current = setInterval(() => {
                setSessionSeconds(prev => prev + 1);
            }, 1000);
        } else {
            clearInterval(timerIntervalRef.current);
        }
        return () => clearInterval(timerIntervalRef.current);
    }, [sessionState]);

    const startBackendSession = async () => {
        try {
            const token = localStorage.getItem('access_token');
            const res = await axios.post('/api/multimodal_session/start', {}, {
                headers: token ? { Authorization: `Bearer ${token}` } : {}
            });
            return res.data.session_id;
        } catch (err) {
            console.error('[Session] Failed to create backend session:', err);
            return null; // Fallback to standalone
        }
    };

    const toggleSession = async () => {
        if (sessionState === SESSION_STATES.IDLE) {
            // Start
            const started = await startContinuousCapture(videoRef.current);
            if (started) {
                const newSessionId = await startBackendSession();
                setSessionId(newSessionId);
                setSessionState(SESSION_STATES.ACTIVE);
                setSessionSeconds(0);
                onMessageReceived({ text: "Live session started. Speak and click 'Send' when ready.", sender: 'bot' });
            }
        } else if (sessionState === SESSION_STATES.ACTIVE) {
            // Stop
            await finalizeSession();
        }
    };

    const finalizeSession = async () => {
        if (sessionId) {
            try {
                const token = localStorage.getItem('access_token');
                await axios.post('/api/multimodal_session/end',
                    { session_id: sessionId },
                    { headers: token ? { Authorization: `Bearer ${token}` } : {} }
                );
            } catch (err) {
                console.error('[Session] Failed to end backend session:', err);
            }
        }

        endSession();
        setSessionId(null);
        setSessionState(SESSION_STATES.IDLE);
        setSessionSeconds(0);
        onMessageReceived({ text: "Session ended.", sender: 'bot' });
    };

    const sendTurn = async () => {
        if (sessionState !== SESSION_STATES.ACTIVE) return;

        setSessionState(SESSION_STATES.PROCESSING);

        const data = await captureCurrentBuffer();
        if (!data || !data.audioBlob || data.audioBlob.size === 0) {
            onMessageReceived({ text: "No audio detected. Please speak and try again.", sender: 'error' });
            setSessionState(SESSION_STATES.ACTIVE);
            return;
        }

        onMessageReceived({ text: "Processing...", sender: 'user', temporary: true });

        const formData = new FormData();
        formData.append('audio', data.audioBlob, 'input.webm');
        for (let i = 0; i < data.videoFrames.length; i++) {
            formData.append('frames', data.videoFrames[i], `frame_${i}.jpg`);
        }
        if (sessionId) formData.append('session_id', sessionId);

        formData.append('metadata', JSON.stringify({
            timestamp: new Date().toISOString(),
            session_mode: 'continuous'
        }));

        try {
            const token = localStorage.getItem('access_token');
            const res = await axios.post('/api/multimodal_input', formData, {
                headers: token ? {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data'
                } : { 'Content-Type': 'multipart/form-data' }
            });

            const result = res.data;
            if (result.response) {
                onMessageReceived({ text: result.response, sender: 'bot', replaceTemporary: true });
            }
            if (result.state && result.risk_level) {
                onStateUpdated(result.state, result.risk_level);
            }
            setSessionState(SESSION_STATES.ACTIVE);
        } catch (err) {
            console.error("Upload failed:", err);
            onMessageReceived({ text: "Error processing input. Please try again.", sender: 'error', replaceTemporary: true });
            setSessionState(SESSION_STATES.ACTIVE);
        }
    };

    return {
        sessionState,
        formattedTimer,
        videoRef,
        isCapturing,
        toggleSession,
        sendTurn
    };
};

export default useMultimodalSession;
