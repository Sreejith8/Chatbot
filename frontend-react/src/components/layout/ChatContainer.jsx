import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { IoPerson, IoLogOutOutline, IoChatbubbleEllipsesOutline, IoPieChartOutline } from 'react-icons/io5';
import ChatView from '../chat/ChatView';
import AnalyticsView from '../analytics/AnalyticsView';

const ChatContainer = ({ user, onLogout }) => {
    const [currentView, setCurrentView] = useState('chat');

    // Check if user is admin
    const isAdmin = localStorage.getItem('user_role') === 'Admin';

    return (
        <div id="chat-container" className="container">
            {/* Top Header */}
            <div className="app-header" style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '25px',
                paddingBottom: '15px',
                borderBottom: '1px solid var(--border)',
                flexShrink: 0,
                minHeight: '60px'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div className="avatar-circle" style={{
                        width: '36px',
                        height: '36px',
                        background: 'linear-gradient(135deg, var(--primary), #7c4dff)',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontSize: '1.2rem',
                        boxShadow: '0 2px 8px rgba(83, 109, 254, 0.4)'
                    }}>
                        <IoPerson />
                    </div>
                    <div>
                        <h2 style={{ margin: 0, fontSize: '1.1rem', textAlign: 'left', lineHeight: 1.2 }}>
                            Hi, <span id="user-display">{user?.username || 'User'}</span>
                        </h2>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Online</span>
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    {isAdmin && (
                        <Link
                            to="/admin"
                            id="admin-link"
                            style={{
                                color: 'var(--text)',
                                textDecoration: 'none',
                                fontSize: '0.8rem',
                                border: '1px solid var(--border)',
                                padding: '5px 12px',
                                borderRadius: '20px',
                                background: 'rgba(255,255,255,0.05)',
                                transition: 'all 0.2s'
                            }}
                        >
                            Dashboard
                        </Link>
                    )}
                    <button
                        onClick={onLogout}
                        className="icon-btn"
                        title="Logout"
                        style={{ border: 'none', color: 'var(--text-secondary)', background: 'transparent', cursor: 'pointer' }}
                    >
                        <IoLogOutOutline size={24} />
                    </button>
                </div>
            </div>

            {/* Explicit Spacer to prevent upward overlap */}
            <div style={{ height: '30px', width: '100%', flexShrink: 0, display: currentView !== 'chat' ? 'none' : 'block' }}></div>

            {/* Views */}
            <div id="chat-view" className={`app-view ${currentView !== 'chat' ? 'hidden' : ''}`}>
                <ChatView />
            </div>

            <div id="analytics-view" className={`app-view ${currentView !== 'analytics' ? 'hidden' : ''}`} style={{ padding: '20px', overflowY: 'auto' }}>
                <AnalyticsView />
            </div>

            {/* Bottom Floating Nav */}
            <div className="bottom-floating-nav">
                <button
                    id="btn-view-chat"
                    className={`nav-fab ${currentView === 'chat' ? 'active' : ''}`}
                    onClick={() => setCurrentView('chat')}
                >
                    <IoChatbubbleEllipsesOutline size={20} />
                    <span>Chat</span>
                </button>
                <div className="nav-divider"></div>
                <button
                    id="btn-view-analytics"
                    className={`nav-fab ${currentView === 'analytics' ? 'active' : ''}`}
                    onClick={() => setCurrentView('analytics')}
                >
                    <IoPieChartOutline size={20} />
                    <span>Analysis</span>
                </button>
            </div>
        </div>
    );
};

export default ChatContainer;
