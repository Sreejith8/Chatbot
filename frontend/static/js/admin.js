const API_URL = 'http://127.0.0.1:5001'; // Ensure port matches config

document.addEventListener('DOMContentLoaded', () => {
    checkAdminAuth();
    loadDashboard();
});

function checkAdminAuth() {
    const token = localStorage.getItem('access_token');
    const role = localStorage.getItem('user_role'); // We'll set this in app.js on login

    // Simple client-side check, real security is on API
    if (!token) {
        window.location.href = '/';
        return;
    }

    // We can also verify with /auth/me if needed, but API calls will fail 403 anyway
}

function logoutAdmin() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
    localStorage.removeItem('user_role');
    window.location.href = '/';
}

function showSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.main-content').forEach(el => el.style.display = 'none');
    document.getElementById(sectionId + '-section').style.display = 'block';

    // Update active nav
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    // Find nav item (approximate)
    // ... logic to highlight sidebar ...

    if (sectionId === 'users') loadUsers();
    if (sectionId === 'sessions') loadSessions();
}

async function loadDashboard() {
    const token = localStorage.getItem('access_token');
    try {
        const res = await fetch(`${API_URL}/admin/stats`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.status === 403) {
            alert("Access Denied: Admins Only");
            window.location.href = '/';
            return;
        }

        const data = await res.json();

        document.getElementById('stats-total-users').innerText = data.total_users;
        document.getElementById('stats-total-sessions').innerText = data.total_sessions;
        document.getElementById('stats-total-messages').innerText = data.total_messages || '-';
        document.getElementById('stats-avg-sessions').innerText = data.avg_sessions_per_user || '-';

        const modelsContainer = document.getElementById('models-list');
        modelsContainer.innerHTML = '';
        data.active_models.forEach(model => {
            const badge = document.createElement('span');
            badge.className = 'badge badge-admin';
            badge.innerText = model;
            modelsContainer.appendChild(badge);
        });

        // Render Chart
        // Render Chart
        renderActivityChart(data.daily_activity);

    } catch (e) {
        console.error("Dashboard Load Failed:", e);
    }
}

async function loadUsers() {
    const token = localStorage.getItem('access_token');
    const tbody = document.querySelector('#users-table tbody');
    tbody.innerHTML = '<tr><td colspan="5">Loading...</td></tr>';

    try {
        const res = await fetch(`${API_URL}/admin/users`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const users = await res.json();

        tbody.innerHTML = '';
        users.forEach(u => {
            const row = `
                <tr>
                    <td>${u.id}</td>
                    <td>${u.username}</td>
                    <td><span class="badge ${u.role === 'Admin' ? 'badge-admin' : 'badge-user'}">${u.role}</span></td>
                    <td>${u.joined}</td>
                    <td>${u.sessions}</td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="5">Error loading users</td></tr>';
    }
}

async function loadSessions() {
    const token = localStorage.getItem('access_token');
    const tbody = document.querySelector('#sessions-table tbody');
    tbody.innerHTML = '<tr><td colspan="5">Loading...</td></tr>';

    try {
        const res = await fetch(`${API_URL}/admin/sessions`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const sessions = await res.json();

        tbody.innerHTML = '';
        sessions.forEach(s => {
            const row = `
                <tr>
                    <td>${s.id}</td>
                    <td>${s.user}</td>
                    <td>${s.start}</td>
                    <td>${s.messages}</td>
                    <td>${s.summary}</td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="5">Error loading sessions</td></tr>';
    }
}

function renderActivityChart(activityData) {
    const ctx = document.getElementById('activityChart').getContext('2d');

    const labels = activityData ? activityData.labels : [];
    const dataPoints = activityData ? activityData.values : [];

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Sessions',
                data: dataPoints,
                borderColor: '#536dfe',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#fff' } }
            },
            scales: {
                y: { ticks: { color: '#888' }, grid: { color: 'rgba(255,255,255,0.1)' } },
                x: { ticks: { color: '#888' }, grid: { display: false } }
            }
        }
    });
}
