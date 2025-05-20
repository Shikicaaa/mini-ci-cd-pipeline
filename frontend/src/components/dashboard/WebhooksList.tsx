import React, { useEffect, useState } from "react";
import type { Webhook } from "../../types/types";
import api from "../../api/axios";
import WebhookListItem from "./WebhookListItem";
import WebhookPlatformSelector from "./WebhookPlatformSelector";


const WebhooksList: React.FC = () => {
    const [webhooks, setWebhooks] = useState<Webhook[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [webhookConfigOpen, setWebhookConfigOpen] = useState(false);
    const [selectedPlatform, setSelectedPlatform] = useState("github");
    const [generated, setGenerated] = useState<{ url: string; secret: string } | null>(null);
    const [showSecret, setShowSecret] = useState(false);
    const [confirming, setConfirming] = useState(false);
    const [selectedRepoId, setSelectedRepoId] = useState<number | null>(null);
    const [availableRepos, setAvailableRepos] = useState<{ id: number; repo_url: string }[]>([]);
    const handleDelete = async (id: number) => {
    const confirmDelete = window.confirm("Are you sure you want to delete this webhook?");
        if (!confirmDelete) return;

        try {
            await api.delete(`/api/webhook/${id}`);
            setWebhooks((prev) => prev.filter((wh) => wh.id !== id));
        } catch (err) {
            console.error(err);
        }
    };

    useEffect(() => {
        const fetchRepos = async () => {
            try {
                const response = await api.get("/api/config");
                setAvailableRepos(response.data);
                if (response.data.length > 0) {
                    setSelectedRepoId(response.data[0].id);
                }
                console.log(response.data)
            } catch (err) {
                console.error("Failed to fetch repos:", err);
            }
        };
        fetchRepos();
    }, []);

    useEffect(() => {
        setLoading(true);
        setError(null);
        const fetchWebhooks = async () => {
            try {
                const response = await api.get<Webhook[]>("/api/webhooks");
                setWebhooks(response.data.map((webhook) => ({ ...webhook })));
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchWebhooks();
    }, []);

    const handleGenerate = async () => {
        if(!selectedRepoId){
            alert("Please select a repository first!");
            return;
        }
        try {
            const response = await api.get("/api/webhook/generate", {params: {
                repo_id: selectedRepoId
            }});
            setGenerated(response.data);
            setShowSecret(true);
        } catch (err) {
            console.error(err);
        }
    };

    const handleConfirm = async () => {
        if (!generated) return;
        try {
            setConfirming(true);
            await api.post("/api/webhook/confirm", {
                url: generated.url,
                secret: generated.secret,
                repo_id: selectedRepoId,
            });
            setShowSecret(false);
            alert("Webhook saved to database.");
        } catch (err) {
            console.error(err);
        } finally {
            setConfirming(false);
        }
    };

    const filteredWebhooks = webhooks.filter((webhook) => {
        const urlMatch = webhook.repo_url?.toLowerCase().includes(searchQuery.toLowerCase());
        const idMatch = webhook.id?.toString().includes(searchQuery.toLowerCase());
        return urlMatch || idMatch;
    });

    const renderWebhookInstructions = () => {
        switch (selectedPlatform) {
            case "github":
                return <p className="text-gray-300">Go to your repository settings.
                Under the "Code and automation" section you will find "webhooks".
                 Once you are here you will enter "generated payload_url" under Payload URL and select content type as "application/json".
                 As of now you don't have any secret key, this is used for webhook identity verification. 
                 You will need to generate one here, it will be shown to you only once make sure to save it somewhere safe!</p>;
            case "gitlab":
                return <p className="text-gray-300">Go to your repository and hover over settings. 
                You will see "Webhooks" section. Click the "Add new webhook" button. Once clicked you will enter "generated payload_url" under URL and you can add the name and description of the webhook.
                As of now you don't have any secret key, this is used for webhook identity verification. 
                You will need to generate one here, it will be shown to you only once make sure to save it somewhere safe!</p>;
            case "bitbucket":
                return <p className="text-gray-300">Go to your repository and click on repository settings on the left side.
                On the settings page select webhooks. Click "add webhook" button for the repository. On the webhook page enter a title with description, enter the URL.
                As of now you don't have any secret key, this is used for webhook identity verification. 
                You will need to generate one here, it will be shown to you only once make sure to save it somewhere safe!
                After that set your webhook to be active and skip certificate verification</p>;
            default:
                return null;
        }
    };

    return (
        <div className="bg-gray-700 p-6 rounded-lg shadow-inner">
            <h2 className="text-2xl font-semibold mb-4 text-indigo-400">
                Webhooks
            </h2>

            <div className="mb-4">
                <div className="flex items-center gap-4 mb-4">
                    <button
                        className="px-4 py-2 bg-green-400 rounded-lg hover:bg-indigo-500"
                        type="button"
                        onClick={() => setWebhookConfigOpen(!webhookConfigOpen)}
                    >
                        How to set webhook?
                    </button>

                    <button
                        className="px-4 py-2 bg-blue-500 rounded-lg hover:bg-blue-600 text-white"
                        type="button"
                        onClick={handleGenerate}
                    >
                        Generate URL and secret
                    </button>
                </div>

                {webhookConfigOpen && (
                    <div className="mb-4 bg-gray-800 p-4 rounded-lg border border-indigo-500">
                        <WebhookPlatformSelector
                            selectedPlatform={selectedPlatform}
                            onChange={setSelectedPlatform}
                        />
                        {availableRepos.length > 0 && (
                        <div className="mb-4">
                            <label className="block text-sm text-gray-300 mb-1">Select Repository:</label>
                            <select
                                className="w-full bg-gray-800 text-white border border-gray-600 rounded px-3 py-2"
                                value={selectedRepoId ?? ""}
                                onChange={(e) => setSelectedRepoId(Number(e.target.value))}
                            >
                                {availableRepos.map((repo) => (
                                    <option key={repo.id} value={repo.id}>
                                        {repo.repo_url}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}
                        {generated && (
                            <div className="mt-4 bg-gray-900 p-4 rounded-lg border border-gray-700">
                                <p className="text-gray-300 mb-2">
                                    <strong>Generated Webhook URL:</strong> {generated.url}
                                </p>

                                {showSecret ? (
                                <div className="overflow-x-auto whitespace-nowrap max-w-full bg-gray-800 p-2 rounded border border-green-500 mb-2">
                                    <p className="text-green-400 text-sm font-mono animate-marquee">
                                        <strong className="mr-2">Secret (shown once):</strong> {generated.secret}
                                    </p>
                                </div>
                                ) : (
                                    <p className="text-red-500 italic mb-2">
                                        Secret can no longer be shown.
                                    </p>
                                )}

                                <button
                                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded"
                                    onClick={handleConfirm}
                                    disabled={confirming}
                                >
                                    {confirming ? "Confirming..." : "Confirm and Save"}
                                </button>
                            </div>
                        )}
                        <div className="mt-2">{renderWebhookInstructions()}</div>
                    </div>
                )}

                <input
                    type="text"
                    className="w-full px-4 py-2 border border-gray-600 rounded-lg bg-gray-800 text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="Search by webhook url or webhook id"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
            </div>

            {loading ? (
                <p className="text-center text-gray-400">Loading webhooks...</p>
            ) : error ? (
                <p className="text-red-400 text-center">{error}</p>
            ) : filteredWebhooks.length === 0 ? (
                <p className="text-center text-gray-400">No webhooks found!</p>
            ) : (
                <ul className="space-y-3">
                    {filteredWebhooks.map((webhook) => (
                        <WebhookListItem
                            key={webhook.id}
                            webhook={webhook}
                            repo_url={webhook.repo_url}
                            onDelete={handleDelete}
                        />
                    ))}
                </ul>
            )}
        </div>
    );
};

export default WebhooksList;
