import React, { useState, useEffect } from 'react';
import type { ConfigResponse as Config } from '../../types/types';
import api from '../../api/axios';
import ConfigListItem from './ConfigListItem';
import type { AxiosError } from 'axios';

interface ConfigsListProps {
    onEditConfig: (config: Config) => void;
  }
  
  const ConfigsList: React.FC<ConfigsListProps> = ({ onEditConfig }) => {
    const [configs, setConfigs] = useState<Config[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
  
    useEffect(() => {
      setLoading(true);
      setError(null);
      const fetchConfigs = async () => {
        try {
          const response = await api.get<Config[]>("/api/config");
          setConfigs(response.data);
        } catch (err) {
          const error = err as AxiosError<any>;
          console.error(err)
          if (error.response && error.response.data && error.response.data.detail) {
              setError(error.response.data.detail);
          } else if (error.response && error.response.data) {
              setError(error.response.data.toString());
          } else {
              setError('Unexpected error occurred');
          }
      } finally {
          setLoading(false);
        }
      };
      fetchConfigs();
    }, []);
  
    const handleDeleteConfig = (deletedConfigId: number) => {
      setConfigs((prev) => prev.filter((c) => c.id !== deletedConfigId));
    };
  
    const filteredConfigs = configs.filter((config) =>
      config.repo_url.toLowerCase().includes(searchQuery.toLowerCase())
    );
  
    return (
      <div className="bg-gray-700 p-6 rounded-lg shadow-inner">
        <h2 className="text-2xl font-semibold mb-4 text-indigo-400">
          Your Repository Configurations
        </h2>
        <div className="mb-4">
          <input
            type="text"
            className="w-full px-4 py-2 border border-gray-600 rounded-lg bg-gray-800 text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Search configs by URL..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        {loading ? (
          <p className="text-center text-gray-400">Loading configurations...</p>
        ) : error ? (
          <p className="text-red-400 text-center">{error}</p>
        ) : filteredConfigs.length === 0 ? (
          <p className="text-center text-gray-400">No configurations found.</p>
        ) : (
          <ul className="space-y-3">
            {filteredConfigs.map((config) => (
              <ConfigListItem
                key={config.id}
                config={config}
                onEdit={onEditConfig}
                onDelete={handleDeleteConfig}
              />
            ))}
          </ul>
        )}
      </div>
    );
  };
  
  export default ConfigsList;