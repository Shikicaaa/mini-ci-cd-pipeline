import React from 'react';
import api from '../../api/axios';

const ConfigForm: React.FC = () => {
    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      const form = e.target as HTMLFormElement;
      const formData = new FormData(form);
      const useSsh = formData.get("use_ssh_deploy") === "on";

      const configPayload = {
        repo_url: formData.get("repo_url") as string,
        main_branch: formData.get("main_branch") as string,
        SSH_for_deploy: useSsh,
        SSH_host: useSsh ? (formData.get("ssh_host") as string) || null : null,
        SSH_port: useSsh ? Number(formData.get("ssh_port")) || 22 : null,
        SSH_username: useSsh ? (formData.get("ssh_user") as string) || null : null,
        SSH_key_path: useSsh ? (formData.get("ssh_private_key_path") as string) || null : null,
        // SSH_key_passphrase: null,
        // docker_username: null,
      };
      try {
        await api.post("/api/config", configPayload);
        alert('Configuration submitted successfully!');
        form.reset();
      } catch (err: any) {
        alert(
          `Error: ${
            err.response?.data?.detail ||
            err.message ||
            "Failed to submit config"
          }`
        );
      }
    }
    return (
        <div className="bg-gray-700 p-6 rounded-lg shadow-inner">
          <h2 className="text-2xl font-semibold mb-4 text-indigo-400">
            Configure Repository
          </h2>
          <form onSubmit={handleSubmit}>
            {/* Repo URL Main Branch */}
            <div className="mb-4">
              <label
                htmlFor="repo_url"
                className="block text-gray-300 font-medium mb-2"
              >
                Repository URL
              </label>
              <input
                id="repo_url"
                type="url"
                name="repo_url"
                className="w-full px-4 py-2 border border-gray-600 rounded-lg bg-gray-800 text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="https://github.com/user/repo.git"
                required
              />
            </div>
            <div className="mb-6">
              <label
                htmlFor="main_branch"
                className="block text-gray-300 font-medium mb-2"
              >
                Main Branch
              </label>
              <input
                id="main_branch"
                type="text"
                name="main_branch"
                defaultValue="main"
                className="w-full px-4 py-2 border border-gray-600 rounded-lg bg-gray-800 text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="main"
                required
              />
            </div>
    
            {/* SSH Deploy */}
            <div className="mb-4 border border-gray-600 p-4 rounded-lg">
              <label className="flex items-center space-x-2 mb-3">
                <input
                  type="checkbox"
                  name="use_ssh_deploy"
                  className="form-checkbox h-5 w-5 text-indigo-600 bg-gray-800 border-gray-600 rounded focus:ring-indigo-500"
                />
                <span className="text-gray-300">
                  Use SSH for Deployment
                </span>
              </label>
              <div className="space-y-3">
                <div>
                  <label
                    htmlFor="ssh_host"
                    className="block text-sm text-gray-400"
                  >
                    SSH Host
                  </label>
                  <input
                    id="ssh_host"
                    type="text"
                    name="ssh_host"
                    className="w-full mt-1 px-3 py-2 border border-gray-600 rounded-md bg-gray-800 text-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    placeholder="e.g., yourserver.com or IP"
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label
                      htmlFor="ssh_port"
                      className="block text-sm text-gray-400"
                    >
                      SSH Port
                    </label>
                    <input
                      id="ssh_port"
                      type="number"
                      name="ssh_port"
                      defaultValue="22"
                      className="w-full mt-1 px-3 py-2 border border-gray-600 rounded-md bg-gray-800 text-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label
                      htmlFor="ssh_user"
                      className="block text-sm text-gray-400"
                    >
                      SSH User
                    </label>
                    <input
                      id="ssh_user"
                      type="text"
                      name="ssh_user"
                      className="w-full mt-1 px-3 py-2 border border-gray-600 rounded-md bg-gray-800 text-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      placeholder="e.g., cicd_user"
                    />
                  </div>
                </div>
                <div>
                  <label
                    htmlFor="ssh_private_key_path"
                    className="block text-sm text-gray-400"
                  >
                    SSH Private Key Path (on CI/CD server)
                  </label>
                  <input
                    id="ssh_private_key_path"
                    type="text"
                    name="ssh_private_key_path"
                    className="w-full mt-1 px-3 py-2 border border-gray-600 rounded-md bg-gray-800 text-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    placeholder="e.g., /home/user/.ssh/id_rsa_cicd"
                  />
                </div>
              </div>
            </div>
    
            <button
              type="submit"
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-500 focus:outline-none focus:ring-2 focus:ring-green-400 focus:ring-opacity-50"
            >
              SUBMIT CONFIGURATION
            </button>
          </form>
        </div>
      );
    };
    export default ConfigForm;