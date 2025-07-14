import React from 'react';
import { ArrowPathIcon } from '@heroicons/react/24/outline';

interface AlertFiltersProps {
  view: 'active' | 'all' | 'stats';
  onViewChange: (view: 'active' | 'all' | 'stats') => void;
  severityFilter: string[];
  onSeverityFilterChange: (severity: string[]) => void;
  cameraFilter: string;
  onCameraFilterChange: (camera: string) => void;
  onRefresh: () => void;
  activeCount: number;
}

const AlertFilters: React.FC<AlertFiltersProps> = ({
  view,
  onViewChange,
  severityFilter,
  onSeverityFilterChange,
  cameraFilter,
  onCameraFilterChange,
  onRefresh,
  activeCount,
}) => {
  return (
    <div className="mb-6 bg-white p-4 rounded-lg shadow border">
      <div className="flex flex-wrap gap-4 items-center">
        {/* View Selector */}
        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => onViewChange('active')}
            className={`px-4 py-2 rounded-md transition-colors ${
              view === 'active' ? 'bg-white shadow text-blue-600' : 'text-gray-600'
            }`}
          >
            Active ({activeCount})
          </button>
          <button
            onClick={() => onViewChange('all')}
            className={`px-4 py-2 rounded-md transition-colors ${
              view === 'all' ? 'bg-white shadow text-blue-600' : 'text-gray-600'
            }`}
          >
            All Alerts
          </button>
          <button
            onClick={() => onViewChange('stats')}
            className={`px-4 py-2 rounded-md transition-colors ${
              view === 'stats' ? 'bg-white shadow text-blue-600' : 'text-gray-600'
            }`}
          >
            Statistics
          </button>
        </div>

        {/* Filters */}
        <div className="flex gap-4">
          <select
            value={severityFilter.join(',')}
            onChange={(e) => onSeverityFilterChange(e.target.value ? e.target.value.split(',') : [])}
            className="border border-gray-300 rounded-md px-3 py-2"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <input
            type="text"
            placeholder="Filter by camera..."
            value={cameraFilter}
            onChange={(e) => onCameraFilterChange(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2"
          />

          <button
            onClick={onRefresh}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <ArrowPathIcon className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>
    </div>
  );
};

export default AlertFilters; 