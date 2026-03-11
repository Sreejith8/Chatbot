import { useState, useCallback, useEffect } from 'react';
import axios from 'axios';

const useChat = (onStateUpdated) => {
    const [messages, setMessages] = useState([]);
    const [isLoadingHistory, setIsLoadingHistory] = useState(true);

    const loadHistory = useCallback(async () => {
        setIsLoadingHistory(true);
        try {
            const token = localStorage.getItem('access_token');
            if (!token) return;

            const res = await axios.get('/api/chat_history', {
                headers: { Authorization: `Bearer ${token}` }
            });

            if (res.data && res.data.messages && res.data.messages.length > 0) {
                setMessages(res.data.messages.map(msg => ({
                    text: msg.text,
                    sender: msg.sender,
                    state: msg.state,
                    risk_level: msg.risk_level,
                    timestamp: msg.timestamp
                })));

                // Update final state from last bot message
                const lastBotMsg = res.data.messages.slice().reverse().find(m => m.sender === 'bot' && m.state);
                if (lastBotMsg && onStateUpdated) {
                    onStateUpdated(lastBotMsg.state, lastBotMsg.risk_level);
                }
            } else {
                // Default greeting if empty
                setMessages([{ text: "Hello! I'm here to listen. How are you feeling today?", sender: 'bot', timestamp: Date.now() }]);
            }
        } catch (error) {
            console.error('[ChatHistory] Failed to load from API:', error);
            setMessages([{ text: "Hello! I'm here to listen. How are you feeling today?", sender: 'bot', timestamp: Date.now() }]);
        } finally {
            setIsLoadingHistory(false);
        }
    }, [onStateUpdated]);

    useEffect(() => {
        loadHistory();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const sendTextMessage = async (text) => {
        if (!text.trim()) return;

        // Optimistic UI update
        const userMsg = { text, sender: 'user' };
        setMessages(prev => [...prev, userMsg]);

        try {
            const token = localStorage.getItem('access_token');
            const res = await axios.post('/api/chat',
                { message: text },
                { headers: token ? { Authorization: `Bearer ${token}` } : {} }
            );

            const result = res.data;
            if (result.response) {
                setMessages(prev => [...prev, {
                    text: result.response,
                    sender: 'bot',
                    state: result.state,
                    risk_level: result.risk_level
                }]);
            }

            if (result.state && result.risk_level && onStateUpdated) {
                onStateUpdated(result.state, result.risk_level);
            }

        } catch (error) {
            console.error('[Chat] Failed to send message:', error);
            setMessages(prev => [...prev, { text: "Network error occurred.", sender: 'error' }]);
        }
    };

    // Helper to allow multimodal session to shove messages in seamlessly
    const injectMessage = useCallback((msgObj) => {
        setMessages(prev => {
            // Replace temporary "Processing..." msg if requested
            if (msgObj.replaceTemporary) {
                return [...prev.filter(m => !m.temporary), msgObj];
            }
            return [...prev, msgObj];
        });
    }, []);

    return {
        messages,
        isLoadingHistory,
        sendTextMessage,
        injectMessage
    };
};

export default useChat;
