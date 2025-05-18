import React from 'react';

type TabName = "repository" | "docker" | "configs" | "pipelines" | "webhooks";

interface TabNavigationProps {
    activeTab: TabName;
    onTabChange: (tab: TabName) => void;
  }

  const TABS: { id: TabName; label: string }[] = [
    { id: "repository", label: "Configure Repository" },
    { id: "docker", label: "Docker Settings" },
    { id: "configs", label: "Configs" },
    { id: "pipelines", label: "Pipelines" },
    { id: "webhooks", label: "Manage webhooks" },
  ];

  const TabNavigation: React.FC<TabNavigationProps> = ({ activeTab, onTabChange }) => {
    return (
      <div className="flex flex-wrap space-x-0 sm:space-x-4 mb-6">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`px-4 py-2 rounded-md text-sm sm:text-base mb-2 sm:mb-0 w-full sm:w-auto
                        ${
                          activeTab === tab.id
                            ? "bg-indigo-600 text-white shadow-lg"
                            : "bg-gray-700 text-gray-300 hover:bg-indigo-500 hover:text-white"
                        }`}
            onClick={() => onTabChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
    );
  };
  
  export default TabNavigation;