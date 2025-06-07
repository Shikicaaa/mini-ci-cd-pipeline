import { useEffect, useState, useCallback } from "react";
import Notification from "./Notification";
import { useAuth } from "../auth/AuthContext";

interface UIMessage {
    id: string;
    config_id: string;
    pipeline_id: string;
    status: string;
    isLeaving?: boolean;
}

export default function NotificationCenter() {
    const [notifications, setNotifications] = useState<UIMessage[]>([]);
    const { user_id } = useAuth();

    const addNotification = useCallback((data: Omit<UIMessage, 'id' | 'isLeaving'>) => {
        // console.log("--> addNotification: Called with data:", data);
        const newNotification: UIMessage = {
            ...data,
            id: crypto.randomUUID(),
        };
        setNotifications((prev) => {
            // console.log("--> addNotification: Current notifications BEFORE update:", prev);
            const updatedNotifications = [...prev, newNotification];
            // console.log("--> addNotification: Notifications AFTER update:", updatedNotifications);
            return updatedNotifications;
        });
    }, []);

    useEffect(() => {
        if (!user_id) {
            // console.warn("--- useEffect: User ID is not available, skipping WebSocket connection.");
            return;
        }

        const wsUrl = `${import.meta.env.VITE_WS_URL}/notifications/${user_id}`.replace("http", "ws");
        // console.info("--- useEffect: Connecting to WebSocket for user:", user_id, "at URL:", wsUrl);

        const websocket = new WebSocket(wsUrl);

        websocket.onopen = () => {
            console.log("--- WebSocket Event: Connection opened!");
        };

        websocket.onmessage = (event) => {
            // console.log("--- WebSocket Event: onmessage TRIGGERED!");
            try {
                // console.log("--- WebSocket Event: Received RAW event object:", event);
                // console.log("--- WebSocket Event: Received RAW data (event.data):", event.data);
                const data = JSON.parse(event.data);
                // console.log("--- WebSocket Event: Parsed data (object):", data);
                addNotification(data);
            } catch (err) {
                console.error("--- WebSocket Event: ERROR parsing WebSocket message:", err, "Raw data:", event.data);
            }
        };

        websocket.onerror = (error) => {
            console.error("--- WebSocket Event: An ERROR occurred with WebSocket:", error);
            websocket.close();
        };

        websocket.onclose = (event) => {
             console.log("--- WebSocket Event: Connection closed!", event);
        };

        return () => {
            // console.log("--- useEffect: Cleaning up - Closing WebSocket connection for user:", user_id);
            websocket.close();
        };
    }, [user_id, addNotification]);

    const removeNotificationCallback = useCallback((idToRemove: string) => {
        // console.log("--- removeNotification: Attempting to remove ID:", idToRemove);
        setNotifications((prev) =>
            prev.map((n) =>
                n.id === idToRemove ? { ...n, isLeaving: true } : n
            )
        );

        setTimeout(() => {
            setNotifications((prev) => {
                const filtered = prev.filter((n) => n.id !== idToRemove);
                console.log("--- removeNotification: Notifications AFTER filter:", filtered);
                return filtered;
            });
        }, 500);
    }, []);

    return (
        <div className="fixed bottom-4 left-4 flex flex-col-reverse gap-3 z-50 w-80">
            {notifications.map((msg) => (
                <Notification
                    key={msg.id}
                    id={msg.id}
                    message={{
                        config_id: msg.config_id,
                        pipeline_id: msg.pipeline_id,
                        status: msg.status,
                    }}
                    isLeaving={!!msg.isLeaving}
                    onClose={removeNotificationCallback}
                />
            ))}
        </div>
    );
}