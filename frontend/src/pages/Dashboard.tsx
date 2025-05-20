import { useState } from "react";
import type { ConfigResponse as Config } from "../types/types";
import Navbar from "../components/Navbar";
import TabNavigation from "../components/dashboard/TabNavigation";
import ConfigForm from "../components/dashboard/ConfigForm";
import DockerSettingsForm from "../components/dashboard/DockerSettingsForm";
import ConfigsList from "../components/dashboard/ConfigList";
import PipelinesList from "../components/dashboard/PipelineList";
import EditConfigModal from "../components/dashboard/EditConfigModal";
import WebhooksList from "../components/dashboard/WebhooksList";

type TabName = "repository" | "docker" | "configs" | "webhooks" | "pipelines";

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState<TabName>("repository");
  const [editingConfig, setEditingConfig] = useState<Config | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  const handleEditConfig = (config: Config) => {
    setEditingConfig(config);
    setIsEditModalOpen(true);
  };

  const handleCloseEditModal = () => {
    setIsEditModalOpen(false);
    setEditingConfig(null);
  };

  const handleSaveConfig = async (updatedConfig: Config) => {
    console.log("Config saved, RERENDER ConfigsList or Refetch if needed", updatedConfig);
    handleCloseEditModal();
  };


  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <Navbar />
      <div className="container mx-auto mt-8 px-4">
        <div className="bg-gray-800 shadow-xl rounded-lg p-6">
          <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />

          {activeTab === "repository" && <ConfigForm />}
          {activeTab === "docker" && <DockerSettingsForm />}
          {activeTab === "configs" && <ConfigsList onEditConfig={handleEditConfig} />}
          {activeTab === "pipelines" && <PipelinesList />}
          {activeTab === "webhooks" && <WebhooksList />}
        </div>
      </div>
      <EditConfigModal
        isOpen={isEditModalOpen}
        onClose={handleCloseEditModal}
        config={editingConfig}
        onSave={handleSaveConfig}
      />
    </div>
  );
};

export default Dashboard;