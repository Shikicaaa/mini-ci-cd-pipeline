import React from 'react';
import type { PipelineRun } from '../../types/types'; 

interface PipelineListItemProps {
    run: PipelineRun;
    onToggleLogs: (runId: number) => void;
}

const formatDate = (dateString?: string | Date | null) => {
    if (!dateString) return "N/A";
    try {
      return new Date(dateString).toLocaleString();
    } catch (e) {
      console.error(e);
      if (typeof dateString === 'string') return dateString;
      return 'Invalid Date';
    }
};

const getStatusColor = (status: string) => {
    if (status.includes("SUCCESS")) return "text-green-500";
    if (status.includes("FAILED")) return "text-red-500";
    if (status.includes("RUNNING") || status.includes("PENDING")) return "text-blue-500";
    if (status.includes("UNKNOWN")) return "text-yellow-500";
    return "text-gray-500";
  };
  
   const getStatusBgColor = (status: string) => {
      if (status.includes("SUCCESS")) return "bg-green-500";
      if (status.includes("FAILED")) return "bg-red-500";
      if (status.includes("UNKNOWN")) return "bg-yellow-500";
      return "bg-blue-500";
  };
  
  
  const PipelineListItem: React.FC<PipelineListItemProps> = ({ run, onToggleLogs }) => {
    return (
      <li className="bg-gray-800 p-4 rounded-lg shadow-md">
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-lg font-medium text-indigo-400">Run ID: {run.id}</h3>
          <span
            className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(
              run.status
            )} bg-opacity-20 ${getStatusBgColor(run.status)}`}
          >
            {run.status}
          </span>
        </div>
        <p className="text-sm text-gray-400">Config ID: {run.config_id}</p>
        <p className="text-sm text-gray-400">
          Commit: <span className="font-mono">{run.commit_sha?.substring(0, 7) || "N/A"}</span>
        </p>
        <p className="text-sm text-gray-400">
          Triggered: {formatDate(run.trigger_time)}
        </p>
        <p className="text-sm text-gray-400">
          Finished: {formatDate(run.end_time)}
        </p>
  
        {run.status.includes("FAILED") && (
          <p className="text-sm text-red-400 mt-2">
            Failure Reason: {run.status.replace("FAILED_", "").replace("_", " ").toLowerCase()}
          </p>
        )}
        {run.status === "SUCCESS" && (
          <p className="text-sm text-green-400 mt-2">
            Pipeline completed successfully!
          </p>
        )}
        {run.status === "UNKNOWN" && (
           <p className="text-sm text-yellow-400 mt-2">
              Pipeline status is unknown. Please check logs for more details.
           </p>
        )}
  
  
        <div className="mt-3">
          <button
            onClick={() => onToggleLogs(run.id)}
            className="text-sm text-indigo-400 hover:underline focus:outline-none"
          >
            {run.logsExpanded ? "Hide Logs" : "Show Logs"}
          </button>
          {run.logsExpanded && (
            <pre className="mt-2 p-3 bg-gray-900 rounded-md text-xs text-gray-300 whitespace-pre-wrap break-all max-h-60 overflow-y-auto">
              {run.logs || "No logs available."}
            </pre>
          )}
        </div>
      </li>
    );
  };
  
  export default PipelineListItem;
