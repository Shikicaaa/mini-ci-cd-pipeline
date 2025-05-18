import React from "react";

interface WebhookPlatformSelectorProps {
  selectedPlatform: string;
  onChange: (value: string) => void;
}

const WebhookPlatformSelector: React.FC<WebhookPlatformSelectorProps> = ({
  selectedPlatform,
  onChange,
}) => {
  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-300 mb-2">
        Select Platform:
      </label>
      <select
        value={selectedPlatform}
        onChange={(e) => onChange(e.target.value)}
        className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600"
      >
        <option value="github">GitHub</option>
        <option value="gitlab">GitLab</option>
        <option value="bitbucket">Bitbucket</option>
      </select>
    </div>
  );
};

export default WebhookPlatformSelector;
