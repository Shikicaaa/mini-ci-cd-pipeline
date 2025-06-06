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

    const addNotification = useCallback((data: Omit<UIMessage, 'id' | 'isLeaving'>) => {
        const newNotification: UIMessage = {
            ...data,
            id: crypto.randomUUID(),
        };
        setNotifications((prev) => [...prev, newNotification]);
    }, []);

    const { user_id } = useAuth();
    useEffect(() => {
        if (!user_id) {
            console.warn("User ID is not available, skipping SSE connection.");
            return;
        }
        console.info("Connecting to SSE for user:", user_id);
        const eventSource = new EventSource(`${import.meta.env.VITE_SSE_URL}/user/${user_id}`);
        eventSource.onmessage = (event) => {
            try {
                console.log("Received SSE:", event.data);
                const data = JSON.parse(event.data);
                addNotification(data);
            } catch (err) {
                console.error("Error while parsing SSE message:", err);
            }
        };

        eventSource.onerror = (error) => {
            console.error("SSE Error:", error);
            eventSource.close();
        };

        return () => {
            eventSource.close();
        };
    }, [user_id, addNotification]);

    const removeNotificationCallback = useCallback((idToRemove: string) => {
        setNotifications((prev) =>
            prev.map((n) =>
                n.id === idToRemove ? { ...n, isLeaving: true } : n
            )
        );

        setTimeout(() => {
            setNotifications((prev) => prev.filter((n) => n.id !== idToRemove));
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
