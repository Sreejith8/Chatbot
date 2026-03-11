import React from 'react';
import { IoSend } from 'react-icons/io5';

const ModalVideoFeed = ({ isRecording, videoRef, sendTurn, formattedTimer }) => {
    return (
        <div className="multimodal-ui-container" style={{ display: isRecording ? 'block' : 'none' }}>
            <div className="video-preview-modal" id="video-modal" style={{ display: 'block' }}>
                <video
                    id="multimodal-video"
                    autoPlay
                    muted
                    playsInline
                    ref={videoRef}
                    style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scaleX(-1)' }}
                ></video>
                <div
                    className="multimodal-overlay"
                    style={{
                        position: 'absolute',
                        top: 0, left: 0, right: 0, bottom: 0,
                        border: '3px solid #ff5252',
                        pointerEvents: 'none',
                        boxShadow: 'inset 0 0 20px rgba(255, 82, 82, 0.5)'
                    }}
                >
                    <div style={{
                        position: 'absolute',
                        top: '10px',
                        left: '10px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                    }}>
                        <div style={{
                            width: '10px', height: '10px',
                            background: '#ff5252',
                            borderRadius: '50%',
                            animation: 'pulse 1.5s infinite'
                        }}></div>
                        <span style={{
                            color: 'white',
                            fontSize: '12px',
                            fontWeight: 'bold',
                            textShadow: '0 1px 3px rgba(0,0,0,0.8)'
                        }}>RECORDING</span>
                    </div>
                </div>

                <div
                    className="multimodal-controls-group"
                    style={{
                        position: 'absolute',
                        bottom: '15px',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        display: 'flex',
                        gap: '10px',
                        background: 'rgba(0,0,0,0.6)',
                        padding: '8px 15px',
                        borderRadius: '30px',
                        backdropFilter: 'blur(4px)',
                        pointerEvents: 'auto'
                    }}
                >
                    <button className="multimodal-send-btn" onClick={sendTurn}>
                        <IoSend size={16} /> Send
                    </button>
                    <div className="recording-timer" style={{ color: 'white', fontWeight: 'bold' }}>
                        {formattedTimer || "00:00"}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ModalVideoFeed;
