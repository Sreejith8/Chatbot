import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './styles/index.css'
import axios from 'axios'

// Global Axios Interceptor for 401 Unauthorized (Token Expiration)
axios.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            console.warn("Global Axios Interceptor: JWT Expired. Redirecting to Auth.");
            localStorage.removeItem('access_token');
            localStorage.removeItem('username');
            localStorage.removeItem('user_role');
            window.location.href = '/auth';
        }
        return Promise.reject(error);
    }
);

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <BrowserRouter>
            <App />
        </BrowserRouter>
    </React.StrictMode>,
)
