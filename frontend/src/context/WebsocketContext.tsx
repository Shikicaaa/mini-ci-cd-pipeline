import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuth } from '../auth/AuthContext';

interface WebSocketContextType {
    messages: UIMessage[];
    isConnected: boolean;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export const useWebSocket = () => useContext(WebSocketContext);

interface UIMessage {
    id: string;
    config_id: string;
    pipeline_id: string;
    status: string;
    isLeaving?: boolean;
}

export const WebSocketProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
    const [messages, setMessages] = useState<UIMessage[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const {user_id}= useAuth();

    useEffect(() => {
        const baseURL = (import.meta.env.VITE_WS_URL)
        const wsUrl = baseURL + `/notifications/${user_id}`;
        const socket = new WebSocket(wsUrl);

        socket.onopen = () => setIsConnected(true);
        socket.onclose = () => setIsConnected(false);

        socket.onmessage = (event) => {
            const newMessage = JSON.parse(event.data);
            setMessages(prev => [...prev, newMessage]);
        };

        return () => socket.close();
    }, [user_id]);

    const value = { messages, isConnected };

    return (
        <WebSocketContext.Provider value={value}>
            {children}
        </WebSocketContext.Provider>
    );
};