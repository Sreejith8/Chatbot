import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { IoGridOutline, IoPeopleOutline, IoChatbubblesOutline, IoArrowBackOutline, IoLogOutOutline, IoPersonCircleOutline } from 'react-icons/io5';
import axios from 'axios';
import '../../styles/admin.css';

import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

const AdminDashboard = ({ onLogout }) => {
    const [activeSection, setActiveSection] = useState('overview');
    const [stats, setStats] = useState(null);
    const [users, setUsers] = useState([]);
    const [sessions, setSessions] = useState([]);
    const navigate = useNavigate();

    const fetchStats = async () => {
        try {
            const token = localStorage.getItem('access_token');
            const res = await axios.get('/admin/stats', { headers: { Authorization: `Bearer ${token}` } });
            setStats(res.data);
        } catch (err) {
            if (err.response?.status === 403) {
                alert("Access Denied: Admins Only");
                navigate('/');
            }
        }
    };

    const fetchUsers = async () => {
        try {
            const token = localStorage.getItem('access_token');
            const res = await axios.get('/admin/users', { headers: { Authorization: `Bearer ${token}` } });
            setUsers(res.data);
        } catch (err) {
            console.error("Failed to load users", err);
        }
    };

    const fetchSessions = async () => {
        try {
            const token = localStorage.getItem('access_token');
            const res = await axios.get('/admin/sessions', { headers: { Authorization: `Bearer ${token}` } });
            setSessions(res.data);
        } catch (err) {
            console.error("Failed to load sessions", err);
        }
    };

    useEffect(() => {
        if (activeSection === 'overview') fetchStats();
        if (activeSection === 'users') fetchUsers();
        if (activeSection === 'sessions') fetchSessions();
    }, [activeSection]);

    // Chart Configuration
    const chartData = {
        labels: stats?.activity_timeline?.labels || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [
            {
                label: 'Interactions',
                data: stats?.activity_timeline?.data || [12, 19, 3, 5, 2, 3, 9],
                borderColor: '#536dfe',
                backgroundColor: 'rgba(83, 109, 254, 0.1)',
                fill: true,
                tension: 0.4
            }
        ]
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: { color: 'rgba(255,255,255,0.05)' },
                ticks: { color: '#888' }
            },
            x: {
                grid: { color: 'rgba(255,255,255,0.05)' },
                ticks: { color: '#888' }
            }
        }
    };

    return (
        <div className="dashboard-container">
            {/* Sidebar */}
            <aside className="sidebar">
                <h2>Mental Health Chatbot</h2>
                <nav>
                    <div className={`nav-link ${activeSection === 'overview' ? 'active' : ''}`} onClick={() => setActiveSection('overview')}>
                        <IoGridOutline /> Overview
                    </div>
                    <div className={`nav-link ${activeSection === 'users' ? 'active' : ''}`} onClick={() => setActiveSection('users')}>
                        <IoPeopleOutline /> Users
                    </div>
                    <div className={`nav-link ${activeSection === 'sessions' ? 'active' : ''}`} onClick={() => setActiveSection('sessions')}>
                        <IoChatbubblesOutline /> Sessions
                    </div>
                    <div className="nav-link" onClick={() => navigate('/')}>
                        <IoArrowBackOutline /> Back to Chat
                    </div>
                    <div className="nav-link logout-btn" onClick={onLogout}>
                        <IoLogOutOutline /> Logout
                    </div>
                </nav>
            </aside>

            {/* Main Content: Overview */}
            {activeSection === 'overview' && (
                <main className="main-content">
                    <header className="header">
                        <h1>Overview</h1>
                        <div className="user-info">
                            <span>Admin</span>
                            <IoPersonCircleOutline size={32} />
                        </div>
                    </header>

                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-label">Total Users</div>
                            <div className="stat-value">{stats?.total_users || '-'}</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-label">Total Sessions</div>
                            <div className="stat-value">{stats?.total_sessions || '-'}</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-label">Total Messages</div>
                            <div className="stat-value">{stats?.total_messages || '-'}</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-label">Avg Sessions/User</div>
                            <div className="stat-value">{stats?.avg_sessions_per_user || '-'}</div>
                        </div>
                    </div>

                    <div className="chart-section glow">
                        <h3>System Activity</h3>
                        <div style={{ height: '300px', width: '100%', maxWidth: '100%', position: 'relative' }}>
                            <Line data={chartData} options={chartOptions} />
                        </div>
                    </div>

                    <div className="chart-section glow">
                        <h3>Active Models</h3>
                        <div id="models-list" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '10px' }}>
                            {stats?.active_models?.map((model, idx) => (
                                <span key={idx} className="badge badge-admin">{model}</span>
                            ))}
                        </div>
                    </div>
                </main>
            )}

            {/* Main Content: Users */}
            {activeSection === 'users' && (
                <main className="main-content">
                    <header className="header">
                        <h1>User Management</h1>
                    </header>
                    <div className="data-table-container">
                        <table id="users-table">
                            <thead>
                                <tr>
                                    <th style={{ width: '10%' }}>ID</th>
                                    <th style={{ width: '30%' }}>Username</th>
                                    <th style={{ width: '20%' }}>Role</th>
                                    <th style={{ width: '20%' }}>Joined Date</th>
                                    <th style={{ width: '20%' }}>Sessions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {users.length > 0 ? users.map((u) => (
                                    <tr key={u.id}>
                                        <td>{u.id}</td>
                                        <td>{u.username}</td>
                                        <td><span className={`badge ${u.role === 'Admin' ? 'badge-admin' : 'badge-user'}`}>{u.role}</span></td>
                                        <td>{u.joined}</td>
                                        <td>{u.sessions}</td>
                                    </tr>
                                )) : <tr><td colSpan="5">No users found or loading...</td></tr>}
                            </tbody>
                        </table>
                    </div>
                </main>
            )}

            {/* Main Content: Sessions */}
            {activeSection === 'sessions' && (
                <main className="main-content">
                    <header className="header">
                        <h1>Recent Sessions</h1>
                    </header>
                    <div className="data-table-container">
                        <table id="sessions-table">
                            <thead>
                                <tr>
                                    <th style={{ width: '10%' }}>ID</th>
                                    <th style={{ width: '20%' }}>User</th>
                                    <th style={{ width: '30%' }}>Start Time</th>
                                    <th style={{ width: '15%' }}>Messages</th>
                                    <th style={{ width: '25%' }}>Summary</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sessions.length > 0 ? sessions.map((s) => (
                                    <tr key={s.id}>
                                        <td>{s.id}</td>
                                        <td>{s.user}</td>
                                        <td>{s.start}</td>
                                        <td>{s.messages}</td>
                                        <td>{s.summary}</td>
                                    </tr>
                                )) : <tr><td colSpan="5">No sessions found or loading...</td></tr>}
                            </tbody>
                        </table>
                    </div>
                </main>
            )}
        </div>
    );
};

export default AdminDashboard;
