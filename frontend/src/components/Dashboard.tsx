import { useState, useEffect } from 'react';
import type { ConfigResponse } from '../types/types';
import api from '../api/axios';
import Navbar from './Navbar';

export const Dashboard = () => {
    const [activeTab, setActiveTab] = useState<'repository' | 'docker' | 'configs' | 'pipelines'>('repository');
    const [searchQuery, setSearchQuery] = useState('');
    const [configs, setConfigs] = useState<{ id: number; main_branch: string; repo_url: string; docker_username: string; }[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (activeTab === 'configs') {
            setLoading(true);
            setError(null);
            const fetchConfigs = async () => {
                try {
                    const response = await api.get<ConfigResponse[]>('/api/config');
                    setConfigs(response.data.map((config) => ({
                        id: config.id,
                        main_branch: config.main_branch,
                        repo_url: config.repo_url,
                        docker_username: config.docker_username,
                    })));
                } catch (err: any) {
                    setError(err.message || 'Failed to fetch configs');
                } finally {
                    setLoading(false);
                }
            };

            fetchConfigs();
        }
        if (activeTab === "pipelines"){
            setLoading(true);
            setError(null);
            const fetchPipelines = async () => {
                try {
                    const response = await api.get('/api/pipelines');
                    console.log(response.data);
                } catch (err: any) {
                    setError(err.message || 'Failed to fetch pipelines');
                } finally {
                    setLoading(false);
                }
            };

            fetchPipelines();
        }
    }, [activeTab]);

    const filteredConfigs = configs.filter(config =>
        config.repo_url.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="min-h-screen bg-gray-100">
            <Navbar />
            <div className="container mx-auto mt-8">
                <div className="bg-white shadow-md rounded-lg p-6">
                    <div className="flex space-x-4 mb-6">
                        <button
                            className={`px-4 py-2 rounded ${activeTab === 'repository' ? 'bg-blue-700 text-white' : 'bg-blue-500 text-white hover:bg-blue-700'}`}
                            onClick={() => setActiveTab('repository')}
                        >
                            Configure repository
                        </button>
                        <button
                            className={`px-4 py-2 rounded ${activeTab === 'docker' ? 'bg-blue-700 text-white' : 'bg-blue-500 text-white hover:bg-blue-700'}`}
                            onClick={() => setActiveTab('docker')}
                        >
                            Docker settings
                        </button>
                        <button
                            className={`px-4 py-2 rounded ${activeTab === 'configs' ? 'bg-blue-700 text-white' : 'bg-blue-500 text-white hover:bg-blue-700'}`}
                            onClick={() => setActiveTab('configs')}
                        >
                            Show configs
                        </button>
                    </div>
                    {activeTab === 'repository' && (
                        <div className="bg-gray-100 p-6 rounded-lg">
                            <form
                                onSubmit={async (e) => {
                                    e.preventDefault();
                                    const formData = new FormData(e.target as HTMLFormElement);
                                    const repo_url = formData.get('repo_url') as string;
                                    const main_branch = formData.get('main_branch') as string;

                                    try {
                                        await api.post('/api/config', { repo_url, main_branch });
                                        alert('Repository configuration submitted successfully!');
                                    } catch (err: any) {
                                        setError(err.message || 'Failed to submit repository configuration');
                                    }
                                }}
                            >
                                <div className="mb-4">
                                    <label className="block text-gray-700 font-medium mb-2">
                                        Repository URL
                                    </label>
                                    <input
                                        type="text"
                                        name="repo_url"
                                        className="w-full px-4 py-2 border rounded-lg bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="Enter repository URL"
                                        required
                                    />
                                </div>
                                <div className="mb-4">
                                    <label className="block text-gray-700 font-medium mb-2">
                                        Main Branch
                                    </label>
                                    <input
                                        type="text"
                                        name="main_branch"
                                        className="w-full px-4 py-2 border rounded-lg bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="Enter main branch"
                                        required
                                    />
                                </div>
                                <button
                                    type="submit"
                                    className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-500"
                                >
                                    SUBMIT
                                </button>
                            </form>
                        </div>
                    )}
                    {activeTab === 'docker' && (
                        <div className="bg-gray-100 p-6 rounded-lg">
                            <form
                                onSubmit={async (e) => {
                                    e.preventDefault();
                                    const formData = new FormData(e.target as HTMLFormElement);
                                    const docker_username = formData.get('docker_username') as string;
                                    const specific_repo = formData.get('specific_repo') as string;

                                    try {
                                        await api.post('/api/docker', { docker_username, specific_repo });
                                        alert('Docker settings submitted successfully!');
                                    } catch (err: any) {
                                        setError(err.message || 'Failed to submit Docker settings');
                                    }
                                }}
                            >
                                <div className="mb-4">
                                    <label className="block text-gray-700 font-medium mb-2">
                                        Docker username
                                    </label>
                                    <input
                                        type="text"
                                        name="docker_username"
                                        className="w-full px-4 py-2 border rounded-lg bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="Enter Docker username"
                                        required
                                    />
                                </div>
                                <div className="mb-4">
                                    <label className="block text-gray-700 font-medium mb-2">
                                        Specific Repo
                                    </label>
                                    <input
                                        type="text"
                                        name="specific_repo"
                                        className="w-full px-4 py-2 border rounded-lg bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="Can be empty, if so will fill every repo"
                                    />
                                </div>
                                <button
                                    type="submit"
                                    className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-500"
                                >
                                    SUBMIT
                                </button>
                            </form>
                        </div>
                    )}
                    {activeTab === 'configs' && (
                        <div className="bg-gray-100 p-6 rounded-lg">
                            <div className="mb-4">
                                <input
                                    type="text"
                                    className="w-full px-4 py-2 border rounded-lg bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="Search configs by URL"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                />
                            </div>
                            {loading ? (
                                <p>Loading...</p>
                            ) : error ? (
                                <p className="text-red-500">{error}</p>
                            ) : (
                                <>
                                    <ul className="space-y-2">
                                        {filteredConfigs.slice(0, 5).map(config => (
                                            <li key={config.id} className="bg-white p-4 rounded-lg shadow flex justify-between items-center">
                                                <div>
                                                    <a
                                                        href={config.repo_url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="text-blue-500 hover:underline"
                                                    >
                                                        {config.repo_url}
                                                    </a>
                                                    <p className="text-gray-600">Main Branch: {config.main_branch}</p>
                                                    <p className="text-gray-600">Docker Username: {config.docker_username}</p>
                                                </div>
                                                <button
                                                    className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600"
                                                    onClick={async () => {
                                                        try {
                                                            await api.delete(`/api/config/${config.id}`);
                                                            setConfigs(prevConfigs => prevConfigs.filter(c => c.id !== config.id));
                                                        } catch (err: any) {
                                                            setError(err.message || 'Failed to delete config');
                                                        }
                                                    }}
                                                >
                                                    Delete
                                                </button>
                                            </li>
                                        ))}
                                    </ul>
                                    {filteredConfigs.length > 5 && (
                                        <p className="text-gray-500 mt-4">Showing 5 of {filteredConfigs.length} configs. Refine your search to see more.</p>
                                    )}
                                </>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
