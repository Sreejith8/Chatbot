import React, { useEffect, useRef } from 'react';
import { getStateColor } from './NeonEmotionRing';

const EmotionTimeline = ({ emotionHistory = [] }) => {
    const canvasRef = useRef(null);
    const maxPoints = 50;

    useEffect(() => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        const container = canvas.parentElement;

        const resize = () => {
            const width = container.offsetWidth;
            const height = Math.min(150, width * 0.4);
            canvas.width = width;
            canvas.height = height;
            render();
        };

        window.addEventListener('resize', resize);
        resize();

        function render() {
            const width = canvas.width;
            const height = canvas.height;
            const padding = 30;
            const chartWidth = width - padding * 2;
            const chartHeight = height - padding * 2;

            ctx.clearRect(0, 0, width, height);

            // Limit points array
            const pointsToRender = emotionHistory.slice(-maxPoints);

            if (pointsToRender.length === 0) {
                ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
                ctx.font = '14px Inter, sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('No emotion data yet', width / 2, height / 2);
                return;
            }

            // Draw axes
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(padding, padding);
            ctx.lineTo(padding, height - padding);
            ctx.lineTo(width - padding, height - padding);
            ctx.stroke();

            // Draw data points and connecting lines
            const pointSpacing = chartWidth / Math.max(pointsToRender.length - 1, 1);

            for (let i = 0; i < pointsToRender.length; i++) {
                const item = pointsToRender[i];
                const x = padding + i * pointSpacing;
                const y = padding + chartHeight / 2; // Fixed y-axis for now as in original
                const pointColor = getStateColor(item.state, item.risk);

                // Draw line
                if (i > 0) {
                    const prevX = padding + (i - 1) * pointSpacing;
                    const prevY = padding + chartHeight / 2;

                    ctx.strokeStyle = pointColor;
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(prevX, prevY);
                    ctx.lineTo(x, y);
                    ctx.stroke();
                }

                // Draw point
                ctx.beginPath();
                ctx.arc(x, y, 4, 0, 2 * Math.PI);
                ctx.fillStyle = pointColor;
                ctx.fill();

                // Glow
                ctx.shadowBlur = 8;
                ctx.shadowColor = pointColor;
                ctx.beginPath();
                ctx.arc(x, y, 4, 0, 2 * Math.PI);
                ctx.fillStyle = pointColor;
                ctx.fill();
                ctx.shadowBlur = 0;
            }

            // Draw time labels (first and last)
            ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
            ctx.font = '10px Inter, sans-serif';
            ctx.textAlign = 'left';

            if (pointsToRender.length > 0) {
                const formatTime = (ts) => new Date(ts).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
                const firstTime = formatTime(pointsToRender[0].timestamp);
                const lastTime = formatTime(pointsToRender[pointsToRender.length - 1].timestamp);

                ctx.fillText(firstTime, padding, height - 10);
                ctx.textAlign = 'right';
                ctx.fillText(lastTime, width - padding, height - 10);
            }
        }

        render();

        return () => window.removeEventListener('resize', resize);
    }, [emotionHistory]);

    return (
        <canvas ref={canvasRef} />
    );
};

export default EmotionTimeline;
