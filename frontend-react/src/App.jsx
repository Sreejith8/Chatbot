import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import Auth from './components/auth/Auth';
import ChatContainer from './components/layout/ChatContainer';
import AdminDashboard from './components/admin/AdminDashboard';
import './styles/index.css';

// Simple Auth Hook (will expand later)
export const useAuth = () => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState(null);

    useEffect(() => {
        const token = localStorage.getItem('access_token');
        const username = localStorage.getItem('username');
        if (token && username) {
            setIsAuthenticated(true);
            setUser({ username });
        }
    }, []);

    const login = (token, username) => {
        localStorage.setItem('access_token', token);
        localStorage.setItem('username', username);
        setIsAuthenticated(true);
        setUser({ username });
    };

    const logout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('username');
        setIsAuthenticated(false);
        setUser(null);
    };

    return { isAuthenticated, user, login, logout };
};

const ProtectedRoute = ({ children, isAuthenticated }) => {
    if (!isAuthenticated) {
        return <Navigate to="/auth" />;
    }
    return children;
};

function App() {
    const { isAuthenticated, user, login, logout } = useAuth();
    const navigate = useNavigate();

    // Centralize logout to force redirect
    const handleLogout = () => {
        logout();
        navigate('/auth');
    };

    return (
        <div id="app">
            <Routes>
                <Route
                    path="/auth"
                    element={
                        !isAuthenticated ?
                            <Auth onLogin={login} /> :
                            <Navigate to="/" />
                    }
                />

                <Route
                    path="/"
                    element={
                        <ProtectedRoute isAuthenticated={isAuthenticated}>
                            <ChatContainer user={user} onLogout={handleLogout} />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/admin"
                    element={
                        <ProtectedRoute isAuthenticated={isAuthenticated}>
                            <AdminDashboard onLogout={handleLogout} />
                        </ProtectedRoute>
                    }
                />
            </Routes>
        </div>
    );
}

export default App;
