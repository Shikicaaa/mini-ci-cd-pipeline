import React from 'react';
import type { Webhook } from '../../types/types';

interface WebhookListItemProps {
    webhook: Webhook;
    repo_url: string;
    onDelete: (id: number) => void;
}

const WebhookListItem: React.FC<WebhookListItemProps> = ({ webhook, repo_url, onDelete }) => {
    return (
        <li className="bg-gray-800 p-4 rounded-lg shadow-md">
            <div className="flex justify-between items-start">
                <div>
                    <h3 className="text-lg font-medium text-indigo-400">Webhook ID: {webhook.id}</h3>
                    <p className="text-sm text-gray-400">Config ID: {webhook.repo_id}</p>
                    <p className="text-sm text-gray-400">Repo URL: {repo_url}</p>
                </div>
                <button
                    onClick={() => onDelete(webhook.id)}
                    className="ml-4 bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded h-fit"
                >
                    Delete
                </button>
            </div>
        </li>
    );
};

export default WebhookListItem;
