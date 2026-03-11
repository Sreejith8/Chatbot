import React, { useState, useEffect } from 'react';
import { IoBulbOutline } from 'react-icons/io5';
import axios from 'axios';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';
import { Doughnut, Bar, Line } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

const AnalyticsView = () => {
    const [analyticsData, setAnalyticsData] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchAnalytics = async () => {
            try {
                const token = localStorage.getItem('access_token');
                if (!token) {
                    setError('Authentication required');
                    setIsLoading(false);
                    return;
                }

                const res = await axios.get('/api/user_analytics', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                setAnalyticsData(res.data);
                setIsLoading(false);
            } catch (err) {
                console.error("Failed to load analytics:", err);
                setError('Failed to load insights. Please try again later.');
                setIsLoading(false);
            }
        };

        fetchAnalytics();
    }, []);

    if (isLoading) {
        return <div style={{ padding: '20px', textAlign: 'center', color: '#888' }}>Loading your insights...</div>;
    }

    if (error) {
        return <div style={{ padding: '20px', textAlign: 'center', color: '#ef4444' }}>{error}</div>;
    }

    if (!analyticsData) return null;

    // 1. State Distribution Data
    const stateLabels = Object.keys(analyticsData.state_distribution || {});
    const stateValues = Object.values(analyticsData.state_distribution || {});

    // We already have a centralized STATE_COLORS in NeonEmotionRing, but we can redefine the required ones here or use the same
    const stateColors = stateLabels.map(label => {
        const colorMap = {
            'Normal': '#4ade80',
            'Sadness': '#60a5fa',
            'Anxiety': '#fbbf24',
            'Stress': '#fb923c',
            'Depression': '#a78bfa',
            'Bipolar': '#ec4899',
            'ADHD': '#22d3ee',
            'Happy': '#fde047',
            'Angry': '#dc2626',
            'Fear': '#9333ea'
        };
        return colorMap[label] || '#9e9e9e'; // Default gray
    });

    const stateChartData = {
        labels: stateLabels,
        datasets: [{
            data: stateValues,
            backgroundColor: stateColors,
            borderWidth: 1
        }]
    };

    // 2. Risk Profile Data
    const riskLabels = Object.keys(analyticsData.risk_distribution || {});
    const riskValues = Object.values(analyticsData.risk_distribution || {});

    const riskColors = riskLabels.map(label => {
        if (label === 'High') return '#f44336';
        if (label === 'Medium') return '#ff9800';
        return '#4caf50'; // Low
    });

    const riskChartData = {
        labels: riskLabels,
        datasets: [{
            label: 'Session Count',
            data: riskValues,
            backgroundColor: riskColors,
            borderRadius: 5
        }]
    };

    // 3. Timeline Data
    const timelineLabels = (analyticsData.timeline || []).map(item => item.date);
    const riskMap = { 'Low': 0, 'Medium': 1, 'High': 2 };
    const timelineData = (analyticsData.timeline || []).map(item => riskMap[item.risk] || 0);

    const timelineChartData = {
        labels: timelineLabels,
        datasets: [{
            label: 'Risk Level Trend',
            data: timelineData,
            borderColor: '#673ab7',
            backgroundColor: 'rgba(103, 58, 183, 0.1)',
            fill: true,
            tension: 0.4
        }]
    };

    const timelineOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                ticks: {
                    callback: function (value) {
                        return ['Low', 'Medium', 'High'][value] || '';
                    },
                    stepSize: 1
                },
                min: 0,
                max: 2.5
            }
        },
        plugins: {
            tooltip: {
                callbacks: {
                    label: function (context) {
                        return ['Low Risk', 'Medium Risk', 'High Risk'][context.raw] || 'Unknown';
                    }
                }
            }
        }
    };

    return (
        <div>
            <div className="analytics-header">
                <h2>Mental Health Insights</h2>
                <p style={{ color: '#aaa', fontSize: '0.9em' }}>Analysis based on your conversation history.</p>
            </div>

            {/* 1. Descriptive Summary */}
            <div className="summary-card"
                style={{
                    background: '#1e293b',
                    padding: '15px',
                    borderRadius: '10px',
                    marginBottom: '20px',
                    borderLeft: '5px solid #3b82f6',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.5)'
                }}
            >
                <h4 style={{ marginTop: 0, color: '#60a5fa', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <IoBulbOutline size={20} /> AI Summary
                </h4>
                <p id="analytics-summary-text" style={{ color: '#e2e8f0', lineHeight: 1.6, fontSize: '0.95em' }}>
                    {analyticsData.summary || "Not enough data to generate a summary yet."}
                </p>
            </div>

            {/* 2. Charts Grid */}
            <div className="charts-grid"
                style={{
                    display: 'grid',
                    gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)',
                    gap: '20px',
                    marginBottom: '20px'
                }}
            >
                <div className="chart-card"
                    style={{
                        background: '#1e293b',
                        padding: '15px',
                        borderRadius: '10px',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.5)'
                    }}
                >
                    <h4 style={{ textAlign: 'center', color: '#e2e8f0', marginTop: 0, marginBottom: '15px' }}>Emotional State Distribution</h4>
                    <div style={{ height: '200px', position: 'relative', display: 'flex', justifyContent: 'center' }}>
                        {stateValues.length > 0 && stateValues.some(v => v > 0) ? (
                            <Doughnut data={stateChartData} options={{ responsive: true, maintainAspectRatio: false }} />
                        ) : (
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b' }}>No emotion data available yet.</div>
                        )}
                    </div>
                </div>
                <div className="chart-card"
                    style={{
                        background: '#1e293b',
                        padding: '15px',
                        borderRadius: '10px',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.5)'
                    }}
                >
                    <h4 style={{ textAlign: 'center', color: '#e2e8f0', marginTop: 0, marginBottom: '15px' }}>Risk Profile</h4>
                    <div style={{ height: '200px', position: 'relative' }}>
                        {riskValues.length > 0 && riskValues.some(v => v > 0) ? (
                            <Bar data={riskChartData} options={{ responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }} />
                        ) : (
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b' }}>No risk data available yet.</div>
                        )}
                    </div>
                </div>
            </div>

            {/* 3. Timeline */}
            <div className="chart-card full-width"
                style={{
                    background: '#1e293b',
                    padding: '15px',
                    borderRadius: '10px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.5)'
                }}
            >
                <h4 style={{ textAlign: 'center', color: '#e2e8f0', marginTop: 0, marginBottom: '15px' }}>Mood Timeline (Last 20 Interactions)</h4>
                <div style={{ height: '250px', position: 'relative' }}>
                    {timelineLabels.length > 0 ? (
                        <Line data={timelineChartData} options={timelineOptions} />
                    ) : (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b' }}>No timeline data available yet.</div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AnalyticsView;
