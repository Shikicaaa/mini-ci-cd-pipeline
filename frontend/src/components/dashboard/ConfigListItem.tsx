import React from 'react';
import type { ConfigResponse as Config } from '../../types/types'; 
import api from '../../api/axios';

interface ConfigListItemProps {
    config: Config;
    onEdit: (config: Config) => void;
    onDelete: (configId: number) => void;
  }

const ConfigListItem: React.FC<ConfigListItemProps> = ({ config, onEdit, onDelete }) => {
  const handleDelete = async () => {
    if (
      window.confirm(
        `Are you sure you want to delete config for ${config.repo_url}?`
      )
    ) {
      try {
        await api.delete(`/api/config/${config.id}`);
        onDelete(config.id);
      } catch (err) {
        console.error(err);
      }
    }
  };

  return (
    <li className="bg-gray-800 p-4 rounded-lg shadow-md hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start">
        <div
          onClick={() => onEdit(config)}
          className="cursor-pointer flex-grow"
        >
          <h3 className="text-lg font-medium text-indigo-400 hover:underline break-all">
            {config.repo_url}
          </h3>
          <p className="text-sm text-gray-400">
            Branch: <span className="font-semibold">{config.main_branch}</span>
          </p>
          <p className="text-sm text-gray-400">
            SSH Clone: {config.use_ssh_for_clone ? "Enabled" : "Disabled"}
          </p>
          {config.use_ssh_for_clone && (
            <p className="text-xs text-gray-500">
              Host Key: {config.git_ssh_host_key || "Not set"}
            </p>
          )}
          <p className="text-sm text-gray-400">
            SSH Deploy: {config.SSH_for_deploy ? "Enabled" : "Disabled"}
          </p>
          {config.SSH_for_deploy && (
            <>
              <p className="text-xs text-gray-500">
                Host: {config.SSH_host || "Not set"}
              </p>
              <p className="text-xs text-gray-500">
                User: {config.SSH_username || "Not set"}
              </p>
            </>
          )}
        </div>
        <div className="flex-shrink-0 ml-4 space-x-2">
          <button
            className="bg-blue-600 text-white text-xs px-3 py-1 rounded-md hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-400"
            onClick={() => onEdit(config)}
          >
            Edit
          </button>
          <button
            className="bg-red-600 text-white text-xs px-3 py-1 rounded-md hover:bg-red-500 focus:outline-none focus:ring-2 focus:ring-red-400"
            onClick={handleDelete}
          >
            Delete
          </button>
        </div>
      </div>
    </li>
  );
};

export default ConfigListItem;