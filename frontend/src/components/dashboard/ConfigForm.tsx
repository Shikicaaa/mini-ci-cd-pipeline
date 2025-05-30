import React, { useState } from "react";
import api from "../../api/axios";

const ConfigForm: React.FC = () => {
  const [selectedProvider, setSelectedProvider] = useState("github");
  const handleProviderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const provider = e.target.value + "";
    const getProviderFromUrl = (url: string): string => {
      const keywordsToDetect = ["github", "gitlab", "bitbucket", "gitea"];
      const lowerUrl = String(url).toLowerCase();
      for (const keyword of keywordsToDetect) {
      if (lowerUrl.includes(keyword)) {
        return keyword;
      }
      }
      return "other";
    };
    const validProvders = getProviderFromUrl(provider);
    setSelectedProvider(validProvders);
  };
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const formData = new FormData(form);
    const useSsh = formData.get("use_ssh_deploy") === "on";
    const useSshForClone = formData.get("use_ssh_for_clone") === "on";
    console.log(formData.values());
    const configPayload = {
      repo_url: formData.get("repo_url") as string,
      main_branch: formData.get("main_branch") as string,
      platform: selectedProvider.toLowerCase(),
      installation_id: null,
      use_ssh_for_clone: useSshForClone,
      git_ssh_private_key_encrypted: useSshForClone ? (formData.get("git_ssh_private_key") as string) || null : null,
      git_ssh_key_passphrase_encrypted: useSshForClone ? (formData.get("git_ssh_key_passphrase") as string) || null : null,
      git_ssh_host_key: useSshForClone ? (formData.get("git_ssh_host_key") as string) || null : null,
      SSH_for_deploy: useSsh,
      SSH_host: useSsh ? (formData.get("ssh_host") as string) || null : null,
      SSH_port: useSsh ? Number(formData.get("ssh_port")) || 22 : null,
      SSH_username: useSsh
        ? (formData.get("ssh_user") as string) || null
        : null,
      SSH_key_path: useSsh
        ? (formData.get("ssh_private_key_path") as string) || null
        : null,
      git_ssh_private_key:
        (formData.get("git_ssh_private_key") as string) || null,
      git_ssh_key_passphrase:
        (formData.get("git_ssh_key_passphrase") as string) || null,
    };
    console.log("Config Payload:", configPayload);
    try {
      await api.post("/api/config", configPayload);
      console.log(formData);
      alert("Configuration submitted successfully!");
      form.reset();
    } catch (err) {
      console.error(err);
    }
  };
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
            onChange={handleProviderChange}
            className="w-full px-4 py-2 border border-gray-600 rounded-lg bg-gray-800 text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="https://github.com/user/repo.git"
            required
          />
        </div>
        <div className="mb-4">
          <label
            htmlFor="git_provider"
            className="block text-gray-300 font-medium mb-2"
          >
            Git Provider
          </label>
          <select
            id="git_provider"
            name="git_provider"
            value={selectedProvider}
            className="w-full px-4 py-2 border border-gray-600 rounded-lg bg-gray-800 text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="github">GitHub</option>
            <option value="gitlab">GitLab</option>
            <option value="bitbucket">Bitbucket</option>
            <option value="gitea">Gitea</option>
            <option value="other">Other (Generic)</option>
          </select>
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
        {/* SSH Clone Section */}
        <div className="mb-4 border border-gray-600 p-4 rounded-lg">
          <label className="flex items-center space-x-2 mb-3">
            <input
              type="checkbox"
              name="use_ssh_for_clone"
              id="use_ssh_for_clone"
              className="form-checkbox h-5 w-5 text-indigo-600 bg-gray-800 border-gray-600 rounded focus:ring-indigo-500"
            />
            <span className="text-gray-300">
              Use SSH for Cloning Repository
            </span>
          </label>
          <div className="space-y-3">
            <div>
              <label
                htmlFor="git_ssh_private_key"
                className="block text-sm text-gray-400"
              >
                Git SSH Private Key
              </label>
              <textarea
                id="git_ssh_private_key"
                name="git_ssh_private_key"
                rows={5}
                className="w-full mt-1 px-3 py-2 border border-gray-600 rounded-md bg-gray-800 text-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                placeholder="Paste your SSH private key for cloning here (e.g., -----BEGIN OPENSSH PRIVATE KEY-----...)"
              />
            </div>
            <div>
              <label
                htmlFor="git_ssh_key_passphrase"
                className="block text-sm text-gray-400"
              >
                Git SSH Key Passphrase
              </label>
              <input
                id="git_ssh_key_passphrase"
                type="password"
                name="git_ssh_key_passphrase"
                className="w-full mt-1 px-3 py-2 border border-gray-600 rounded-md bg-gray-800 text-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                placeholder="Enter passphrase for the SSH key (if any)"
              />
            </div>
            <div>
              <label
                htmlFor="git_ssh_host_key"
                className="block text-sm text-gray-400"
              >
                Git SSH Host Key (e.g., from `ssh-keyscan your-git-host.com`)
              </label>
              <textarea
                id="git_ssh_host_key"
                name="git_ssh_host_key"
                rows={3}
                className="w-full mt-1 px-3 py-2 border border-gray-600 rounded-md bg-gray-800 text-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                placeholder="e.g., github.com ssh-rsa AAAA..."
              />
            </div>
          </div>
        </div>
        {/* SSH Deploy */}
        <div className="mb-4 border border-gray-600 p-4 rounded-lg">
          <label className="flex items-center space-x-2 mb-3">
            <input
              type="checkbox"
              name="use_ssh_deploy"
              className="form-checkbox h-5 w-5 text-indigo-600 bg-gray-800 border-gray-600 rounded focus:ring-indigo-500"
            />
            <span className="text-gray-300">Use SSH for Deployment</span>
          </label>
          <div className="space-y-3">
            <div>
              <label htmlFor="ssh_host" className="block text-sm text-gray-400">
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
