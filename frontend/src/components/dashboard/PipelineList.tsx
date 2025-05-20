import React, { useState, useEffect } from 'react';
import type { PipelineRun, PipelineResponse as BackendPipelineRun } from '../../types/types';
import api from '../../api/axios';
import PipelineListItem from './PipelineListItem';

const PipelinesList: React.FC = () => {
  const [pipelineRuns, setPipelineRuns] = useState<PipelineRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    setLoading(true);
    setError(null);
    const fetchPipelines = async () => {
      try {
        const response = await api.get<BackendPipelineRun[]>("/api/pipelines");
        setPipelineRuns(
          response.data.map((run) => ({ ...run, logsExpanded: false }))
        );
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchPipelines();
  }, []);

  const togglePipelineLogs = (runId: number) => {
    setPipelineRuns((prevRuns) =>
      prevRuns.map((run) =>
        run.id === runId ? { ...run, logsExpanded: !run.logsExpanded } : run
      )
    );
  };

  const filteredPipelineRuns = pipelineRuns.filter(
    (run) =>
      run.commit_sha?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      run.status.toLowerCase().includes(searchQuery.toLowerCase()) ||
      run.id.toString().includes(searchQuery)
  );

  return (
    <div className="bg-gray-700 p-6 rounded-lg shadow-inner">
      <h2 className="text-2xl font-semibold mb-4 text-indigo-400">
        Pipeline Runs
      </h2>
      <div className="mb-4">
        <input
          type="text"
          className="w-full px-4 py-2 border border-gray-600 rounded-lg bg-gray-800 text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="Search by Commit SHA, Status, or Run ID..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>
      {loading ? (
        <p className="text-center text-gray-400">Loading pipeline runs...</p>
      ) : error ? (
        <p className="text-red-400 text-center">{error}</p>
      ) : filteredPipelineRuns.length === 0 ? (
        <p className="text-center text-gray-400">No pipeline runs found.</p>
      ) : (
        <ul className="space-y-3">
          {filteredPipelineRuns.map((run) => (
            <PipelineListItem
              key={run.id}
              run={run}
              onToggleLogs={togglePipelineLogs}
            />
          ))}
        </ul>
      )}
    </div>
  );
};

export default PipelinesList;