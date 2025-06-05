import { useEffect } from "react";

interface NotificationProps {
    id: string;
    message: {
        config_id: string;
        pipeline_id: string;
        status: string;
    };
    isLeaving?: boolean;
    onClose: (id: string) => void;
}

const statusColors: Record<string, string> = {
    success: "#4BB543",
    fail: "#FF3443",
    unknown: "#FFD000",
};

export default function Notification({ id, message, isLeaving, onClose }: NotificationProps) {
    useEffect(() => {
        if (!isLeaving) {
            const timer = setTimeout(() => {
                onClose(id);
            }, 2000);
            return () => clearTimeout(timer);
        }
    }, [id, isLeaving, onClose]);

    let borderColor;
    const lowerStatus = message.status.toLowerCase();
    if (lowerStatus.includes("success")) {
        borderColor = statusColors.success;
    } else if (lowerStatus.includes("fail")) {
        borderColor = statusColors.fail;
    } else {
        borderColor = statusColors.unknown;
    }

    const animationClass = isLeaving ? "animate-slideOutRight" : "animate-slideInRight";

    return (
        <div
            className={`bg-blue-900 text-white p-4 transform transition-all rounded-2xl shadow-lg w-full max-w-sm border-l-4 ${animationClass}`}
            style={{ borderLeftColor: borderColor }}
        >
            <div className="font-bold text-lg capitalize">{message.status || "Info"}</div>
            <div className="text-sm mt-1">Config ID: {message.config_id}</div>
            <div className="text-sm">Pipeline ID: {message.pipeline_id}</div>
        </div>
    );
}