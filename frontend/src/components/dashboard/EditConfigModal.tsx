import React, { useEffect, useState } from "react";
import api from "../../api/axios";
import type { Config } from "../../types/types";
import type { BackendPayload } from "../../types/types";
import type { FormDataShape } from "../../types/types";
import type { AxiosError } from "axios";


interface EditConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  config: Config | null;
  onSave: (updatedConfig: Config) => void;
}

interface ValidationError {
  loc: string[];
  msg: string;
  [key: string]: unknown;
}

const EditConfigModal: React.FC<EditConfigModalProps> = ({
    isOpen,
    onClose,
    config,
    onSave,
  }) => {
    const [formData, setFormData] = useState<FormDataShape>({});
  
    useEffect(() => {
      if (config) {
        setFormData({
          repo_url: config.repo_url,
          main_branch: config.main_branch,
          SSH_host: config.SSH_host || "",
          SSH_port: config.SSH_port ? parseInt(String(config.SSH_port), 10) : 22,
          SSH_username: config.SSH_username || "",
          SSH_key_path: config.SSH_key_path || "",
          docker_username: config.docker_username || "",
          // SSH_key_passphrase: config.SSH_key_passphrase || ''
        });
      }
    }, [config]);
  
    if (!isOpen || !config) return null;
  
    const handleChange = (
      e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
    ) => {
      const { name, value, type } = e.target;
      if (type === "checkbox") {
        const checkbox = e.target as HTMLInputElement;
        setFormData((prev) => ({ ...prev, [name]: checkbox.checked }));
      } else if (name === "SSH_port") {
        setFormData((prev) => ({
          ...prev,
          [name]: value ? parseInt(value, 10) : null,
        }));
      } else {
        setFormData((prev) => ({ ...prev, [name]: value }));
      }
    };
  
    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
  
      if (!formData.repo_url || !formData.main_branch) {
        alert("Repository URL and Main Branch are required.");
        return;
      }
  
      const payload: BackendPayload = {
        repo_url: formData.repo_url,
        main_branch: formData.main_branch,
        SSH_for_deploy: !!formData.SSH_for_deploy,
        docker_username: formData.docker_username || null,
        use_ssh_for_clone: !!formData.use_ssh_for_clone,
        // SSH_key_passphrase: formData.SSH_key_passphrase || null,
      };
  
      if (formData.SSH_for_deploy) {
        payload.SSH_host = formData.SSH_host || null;
        payload.SSH_port =
          formData.SSH_port !== undefined && formData.SSH_port !== null
            ? Number(formData.SSH_port)
            : 22;
        payload.SSH_username = formData.SSH_username || null;
        payload.SSH_key_path = formData.SSH_key_path || null;
      } else {
        payload.SSH_host = null;
        payload.SSH_port = null;
        payload.SSH_username = null;
        payload.SSH_key_path = null;
      }
  
      try {
        const response = await api.put<Config>(
          `/api/config/${config.id}`,
          payload
        );
        await onSave(response.data);
        onClose();
      } catch (err) {
        let errorMessage = "Failed to update config";
        const error = err as AxiosError;
        if (error.response && error.response.data) {
          if (
            error.response.data &&
            Array.isArray(error.response.data)
          ) {
            errorMessage = error.response.data
              .map((d: ValidationError) => {
                const field = d.loc && d.loc.length > 1 ? d.loc[1] : "error";
                return `${field} - ${d.msg}`;
              })
              .join("; ");
          } else if (typeof error.response.data === "string") {
            errorMessage = error.response.data;
          } else {
            try {
              errorMessage = JSON.stringify(error.response.data);
            } catch {
              //nesto
            }
          }
        } else if (error.message) {
          errorMessage = error.message;
        }
        alert(`Error updating config: ${errorMessage}`);
        console.error("Update error details:", error.response?.data || err);
      }
    };
  
    return (
      <div className="fixed inset-0 backdrop-blur-sm bg-black/30 flex items-center justify-center z-50 p-4">
        <div className="bg-gray-800 p-6 rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
          <h2 className="text-2xl font-semibold mb-6 text-indigo-400">
            Edit Repository Configuration (ID: {config.id})
          </h2>
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label
                htmlFor="edit_repo_url"
                className="block text-gray-300 font-medium mb-1"
              >
                Repository URL
              </label>
              <input
                id="edit_repo_url"
                type="url"
                name="repo_url"
                value={formData.repo_url || ""}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-600 rounded-lg bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>
            <div className="mb-6">
              <label
                htmlFor="edit_main_branch"
                className="block text-gray-300 font-medium mb-1"
              >
                Main Branch
              </label>
              <input
                id="edit_main_branch"
                type="text"
                name="main_branch"
                value={formData.main_branch || ""}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-600 rounded-lg bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>
            <div className="mb-6 border border-gray-700 p-4 rounded-lg">
              <label className="flex items-center space-x-2 mb-3 cursor-pointer">
              <input
                type="checkbox"
                name="use_ssh_for_clone"
                checked={!!formData.use_ssh_for_clone}
                onChange={handleChange}
                className="form-checkbox h-5 w-5 text-indigo-600 bg-gray-800 border-gray-600 rounded focus:ring-indigo-500"
              />
              <span className="text-gray-300">Use SSH for clone</span>
              </label>
              {formData.use_ssh_for_clone && (
              <div className="space-y-3 mt-2">
                {/* SSH Private Key Path for cloning */}
                <div>
                <label
                  htmlFor="clone_ssh_key_path"
                  className="block text-sm text-gray-400"
                >
                  SSH Private Key (for cloning)
                </label>
                <div className="flex items-center space-x-2">
                  <input
                  id="clone_ssh_key_path"
                  type="text"
                  name="git_ssh_private_key"
                  value={formData.git_ssh_private_key || ""}
                  onChange={handleChange}
                  className="w-full mt-1 px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  placeholder="-----BEGIN OPENSSH PRIVATE KEY-----..."
                  />
                  <button
                  type="button"
                  onClick={() => {
                    setFormData((prev) => ({
                    ...prev,
                    git_ssh_private_key: "",
                    git_ssh_passphrase: "",
                    git_ssh_host_key: "",
                    }));
                  }}
                  className="mt-1 px-3 py-2 border border-red-600 text-red-500 rounded-md hover:bg-red-500 hover:text-white focus:outline-none focus:ring-1 focus:ring-red-400"
                  title="Clear Key Path and Passphrase"
                  >
                  Clear
                  </button>
                </div>
                </div>

                {/* SSH Key Passphrase for cloning */}
                
                <div>
                <label
                  htmlFor="clone_ssh_key_passphrase"
                  className="block text-sm text-gray-400"
                >
                  SSH Key Passphrase (optional, for cloning key)
                </label>
                <input
                  id="clone_ssh_key_passphrase"
                  type="password"
                  name="git_ssh_passphrase"
                  value={formData.git_ssh_passphrase || ""}
                  onChange={handleChange}
                  className="w-full mt-1 px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  placeholder="Enter passphrase if key is encrypted"
                />
                </div>
                <div>
                <label
                  htmlFor="ssh_host_key"
                  className="block text-sm text-gray-400"
                >
                  SSH Host key
                </label>
                <input
                  id="git_ssh_host_key"
                  type="text"
                  name="git_ssh_host_key"
                  value={formData.git_ssh_host_key || ""}
                  onChange={handleChange}
                  className="w-full mt-1 px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  placeholder="(e.g., from `ssh-keyscan your-git-host.com`)"
                />
                </div>
              </div>
              )}
            </div>
            <div className="mb-6 border border-gray-700 p-4 rounded-lg">
              <label className="flex items-center space-x-2 mb-3 cursor-pointer">
                <input
                  type="checkbox"
                  name="SSH_for_deploy"
                  checked={!!formData.SSH_for_deploy}
                  onChange={handleChange}
                  className="form-checkbox h-5 w-5 text-indigo-600 bg-gray-800 border-gray-600 rounded focus:ring-indigo-500"
                />
                <span className="text-gray-300">Use SSH for Deployment</span>
              </label>
              {formData.SSH_for_deploy && (
                <div className="space-y-3 mt-2">
                  <div>
                    <label
                      htmlFor="edit_ssh_host"
                      className="block text-sm text-gray-400"
                    >
                      SSH Host
                    </label>
                    <input
                      id="edit_ssh_host"
                      type="text"
                      name="SSH_host"
                      value={formData.SSH_host || ""}
                      onChange={handleChange}
                      className="w-full mt-1 px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      placeholder="e.g., yourserver.com or IP"
                    />
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label
                        htmlFor="edit_ssh_port"
                        className="block text-sm text-gray-400"
                      >
                        SSH Port
                      </label>
                      <input
                        id="edit_ssh_port"
                        type="number"
                        name="SSH_port"
                        value={
                          formData.SSH_port === null ||
                          formData.SSH_port === undefined
                            ? ""
                            : formData.SSH_port
                        }
                        onChange={handleChange}
                        className="w-full mt-1 px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label
                        htmlFor="edit_ssh_user"
                        className="block text-sm text-gray-400"
                      >
                        SSH User
                      </label>
                      <input
                        id="edit_ssh_user"
                        type="text"
                        name="SSH_username"
                        value={formData.SSH_username || ""}
                        onChange={handleChange}
                        className="w-full mt-1 px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        placeholder="e.g., cicd_user"
                      />
                    </div>
                  </div>
                  <div>
                    <label
                      htmlFor="edit_ssh_private_key_path"
                      className="block text-sm text-gray-400"
                    >
                      SSH Private Key Path (on CI/CD server)
                    </label>
                    <input
                      id="edit_ssh_private_key_path"
                      type="text"
                      name="SSH_key_path"
                      value={formData.SSH_key_path || ""}
                      onChange={handleChange}
                      className="w-full mt-1 px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      placeholder="e.g., /home/user/.ssh/id_rsa_cicd"
                    />
                  </div>
                </div>
              )}
            </div>
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-lg text-gray-300 bg-gray-600 hover:bg-gray-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-500"
              >
                Save Changes
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

export default EditConfigModal;