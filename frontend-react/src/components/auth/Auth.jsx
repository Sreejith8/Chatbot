import React, { useState } from 'react';
import axios from 'axios';

const Auth = ({ onLogin }) => {
    const [isLoginView, setIsLoginView] = useState(true);

    // Form State
    const [loginUser, setLoginUser] = useState('');
    const [loginPass, setLoginPass] = useState('');

    const [regUser, setRegUser] = useState('');
    const [regPass, setRegPass] = useState('');

    const handleLogin = async () => {
        try {
            const res = await axios.post('/auth/login', {
                username: loginUser,
                password: loginPass
            });

            // Store role (match vanilla logic)
            if (res.data.is_admin) {
                localStorage.setItem('user_role', 'Admin');
            } else {
                localStorage.setItem('user_role', 'User');
            }

            onLogin(res.data.access_token, loginUser);
        } catch (error) {
            alert(error.response?.data?.msg || 'Login failed');
        }
    };

    const handleRegister = async () => {
        try {
            const res = await axios.post('/auth/register', {
                username: regUser,
                password: regPass
            });
            alert(res.data.msg);
            setIsLoginView(true); // Switch to login after successful registration
        } catch (error) {
            alert(error.response?.data?.msg || 'Registration failed');
        }
    };

    return (
        <div id="auth-container" className="container">
            <h1>Mental Health Chatbot</h1>

            <div className="tabs">
                <button
                    id="tab-login"
                    className={isLoginView ? 'active' : ''}
                    onClick={() => setIsLoginView(true)}
                >
                    Login
                </button>
                <button
                    id="tab-register"
                    className={!isLoginView ? 'active' : ''}
                    onClick={() => setIsLoginView(false)}
                >
                    Register
                </button>
            </div>

            {isLoginView ? (
                <div id="login-form">
                    <input
                        type="text"
                        id="login-username"
                        placeholder="Username"
                        value={loginUser}
                        onChange={(e) => setLoginUser(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                    />
                    <input
                        type="password"
                        id="login-password"
                        placeholder="Password"
                        value={loginPass}
                        onChange={(e) => setLoginPass(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                    />
                    <button className="primary-btn" onClick={handleLogin}>Login</button>
                </div>
            ) : (
                <div id="register-form">
                    <input
                        type="text"
                        id="reg-username"
                        placeholder="Choose Username"
                        value={regUser}
                        onChange={(e) => setRegUser(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleRegister()}
                    />
                    <input
                        type="password"
                        id="reg-password"
                        placeholder="Choose Password"
                        value={regPass}
                        onChange={(e) => setRegPass(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleRegister()}
                    />
                    <button className="primary-btn" onClick={handleRegister}>Create Account</button>
                </div>
            )}
        </div>
    );
};

export default Auth;
