import React from 'react';
import api from '../../api/axios';

const DockerSettingsForm: React.FC = () => {
    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      const form = e.target as HTMLFormElement;
      const formData = new FormData(form);
      const docker_username = formData.get("docker_username") as string;
      const specific_repo = (formData.get("specific_repo") as string) || undefined;
  
      try {
        await api.post("/api/docker", {
          docker_username,
          specific_repo,
        });
        alert('Docker settings submitted successfully!');
        form.reset();
      } catch (err) {
        console.error(err);
      }
    };
    return (
        <div className="bg-gray-700 p-6 rounded-lg shadow-inner">
          <h2 className="text-2xl font-semibold mb-4 text-indigo-400">
            Docker Settings
          </h2>
          <p className="text-gray-300 mb-4">
            You can configure Docker Hub username, image naming conventions, etc.
          </p>
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label
                htmlFor="docker_username"
                className="block text-gray-300 font-medium mb-2"
              >
                Docker Username
              </label>
              <input
                id="docker_username"
                type="text"
                name="docker_username"
                className="w-full px-4 py-2 border border-gray-600 rounded-lg bg-gray-800 text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Username"
                required
              />
            </div>
            <div className="mb-6">
              <label
                htmlFor="specific_repo"
                className="block text-gray-300 font-medium mb-2"
              >
                Specific Repository (Optional: if Docker username applies only to one repo)
              </label>
              <input
                id="specific_repo"
                type="text"
                name="specific_repo"
                className="w-full px-4 py-2 border border-gray-600 rounded-lg bg-gray-800 text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="https://github.com/user/repo.git"
              />
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
    
    export default DockerSettingsForm;