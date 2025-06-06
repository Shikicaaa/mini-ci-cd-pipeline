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
        console.log("--> addNotification: Called with data:", data); // A
        const newNotification: UIMessage = {
            ...data,
            id: crypto.randomUUID(),
        };
        setNotifications((prev) => {
            console.log("--> addNotification: Current notifications BEFORE update:", prev); // B
            const updatedNotifications = [...prev, newNotification];
            console.log("--> addNotification: Notifications AFTER update:", updatedNotifications); // C
            return updatedNotifications;
        });
    }, []);

    const { user_id } = useAuth();
    useEffect(() => {
        if (!user_id) {
            console.warn("--- useEffect: User ID is not available, skipping SSE connection.");
            return;
        }
        console.info("--- useEffect: Connecting to SSE for user:", user_id);
        const eventSource = new EventSource(`${import.meta.env.VITE_SSE_URL}/user/${user_id}`);

        eventSource.onopen = () => {
            console.log("--- SSE Event: Connection opened!"); // D
        };

        eventSource.onmessage = (event) => {
            console.log("--- SSE Event: onmessage TRIGGERED!"); // E - KRITIČAN LOG!
            try {
                console.log("--- SSE Event: Received RAW event object:", event); // F
                console.log("--- SSE Event: Received RAW data (event.data):", event.data); // G
                const data = JSON.parse(event.data);
                console.log("--- SSE Event: Parsed data (object):", data); // H
                addNotification(data);
            } catch (err) {
                console.error("--- SSE Event: ERROR parsing SSE message:", err, "Raw data:", event.data); // I
            }
        };

        eventSource.onerror = (error) => {
            console.error("--- SSE Event: An ERROR occurred with SSE:", error); // J
            eventSource.close();
        };

        return () => {
            console.log("--- useEffect: Cleaning up - Closing SSE connection for user:", user_id); // K
            eventSource.close();
        };
    }, [user_id, addNotification]);

    const removeNotificationCallback = useCallback((idToRemove: string) => {
        console.log("--- removeNotification: Attempting to remove ID:", idToRemove); // L
        setNotifications((prev) =>
            prev.map((n) =>
                n.id === idToRemove ? { ...n, isLeaving: true } : n
            )
        );

        setTimeout(() => {
            setNotifications((prev) => {
                const filtered = prev.filter((n) => n.id !== idToRemove);
                console.log("--- removeNotification: Notifications AFTER filter:", filtered); // M
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