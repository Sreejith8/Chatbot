import React, { useState, useRef, useEffect, useCallback } from 'react';
import { IoSend, IoMic, IoStopCircle } from 'react-icons/io5';
import TrackerPanel from '../tracker/TrackerPanel';
import ModalVideoFeed from './ModalVideoFeed';
import useChat from '../../hooks/useChat';
import useMultimodalSession, { SESSION_STATES } from '../../hooks/useMultimodalSession';

const ChatView = () => {
    const [inputText, setInputText] = useState('');
    const [currentState, setCurrentState] = useState('Neutral');
    const [riskLevel, setRiskLevel] = useState('Low');
    const messagesEndRef = useRef(null);

    // Callback to update global UI state
    const handleStateUpdated = useCallback((state, risk) => {
        setCurrentState(state);
        setRiskLevel(risk);
    }, []);

    // 1. Text Chat Hook
    const { messages, isLoadingHistory, sendTextMessage, injectMessage } = useChat(handleStateUpdated);

    // 2. Multimodal Chat Hook
    const {
        sessionState,
        formattedTimer,
        videoRef,
        isCapturing,
        toggleSession,
        sendTurn
    } = useMultimodalSession(injectMessage, handleStateUpdated);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSendMessage = () => {
        if (!inputText.trim()) return;

        if (sessionState === SESSION_STATES.ACTIVE) {
            // Can't send text while in multimodal mode explicitly unless we modify backend to accept both
            // For now, respect the vanilla JS flow: Send button submits multimodal buffer
            sendTurn();
            setInputText('');
        } else {
            // Flow: Standard Text Chat
            sendTextMessage(inputText);
            setInputText('');
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            handleSendMessage();
        }
    };

    // Style logic for risk badge matching standard CSS
    const getRiskStyle = (risk) => {
        if (risk === 'High') return { background: 'rgba(239, 68, 68, 0.4)' };
        if (risk === 'Medium') return { background: 'rgba(251, 146, 60, 0.4)' };
        return { background: 'rgba(74, 222, 128, 0.2)' };
    };

    // Derived states
    const sessionStartTime = messages.length > 0 ? messages[0].timestamp || Date.now() : Date.now();
    const emotionHistory = messages
        .filter(m => m.state)
        .map(m => ({
            state: m.state,
            risk: m.risk_level,
            timestamp: m.timestamp || Date.now()
        }));

    return (
        <>
            {/* Left: Chat Panel */}
            <div className="chat-panel">
                <div id="messages" className="messages-area">
                    {isLoadingHistory ? (
                        <div style={{ textAlign: 'center', color: '#888', marginTop: '20px' }}>Loading history...</div>
                    ) : (
                        messages.map((msg, idx) => (
                            <div key={idx} className={`message ${msg.sender === 'user' ? 'user-msg' : msg.sender === 'error' ? 'error-msg' : 'bot-msg'}`}>
                                {msg.text}
                            </div>
                        ))
                    )}
                    <div ref={messagesEndRef} />
                </div>

                <div className="input-group">
                    <input
                        type="text"
                        id="message-input"
                        placeholder={sessionState === SESSION_STATES.ACTIVE ? "Speak to send..." : "Type how you feel..."}
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        onKeyPress={handleKeyPress}
                        disabled={sessionState === SESSION_STATES.PROCESSING || isCapturing}
                    />
                    <button
                        className="primary-btn"
                        onClick={sessionState === SESSION_STATES.ACTIVE ? sendTurn : handleSendMessage}
                        disabled={sessionState === SESSION_STATES.PROCESSING}
                    >
                        <IoSend size={20} />
                    </button>
                    <button
                        id="mic-button"
                        className={`primary-btn ${isCapturing ? 'recording' : ''}`}
                        style={{ background: 'linear-gradient(45deg, #FF512F, #DD2476)' }}
                        title="Press to Record (Audio+Video)"
                        onClick={toggleSession}
                    >
                        {isCapturing ? <IoStopCircle size={20} /> : <IoMic size={20} />}
                    </button>
                </div>

                <div id="status-bar">
                    <span>Current State: <b id="state-display">{currentState}</b></span>
                    <span
                        className="risk-badge"
                        id="risk-badge"
                        style={getRiskStyle(riskLevel)}
                    >
                        Risk: <span id="risk-display">{riskLevel}</span>
                    </span>
                    {sessionState === SESSION_STATES.ACTIVE && (
                        <span style={{ color: '#ffab40' }}>Session: {formattedTimer}</span>
                    )}
                </div>
            </div>

            {/* Right: Session Emotion Tracking */}
            <TrackerPanel
                currentState={currentState}
                currentRisk={riskLevel}
                emotionHistory={emotionHistory}
                sessionStartTime={sessionStartTime}
            />

            {/* Overlay for recording feed if needed */}
            <ModalVideoFeed isRecording={isCapturing} videoRef={videoRef} sendTurn={sendTurn} formattedTimer={formattedTimer} />
        </>
    );
};

export default ChatView;
