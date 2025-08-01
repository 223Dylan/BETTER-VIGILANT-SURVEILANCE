import React from 'react';
import { ArrowPathIcon } from '@heroicons/react/24/outline';
import { useThemeClasses } from '../../contexts/ThemeContext';

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
  const themeClasses = useThemeClasses();

  return (
    <div className={`mb-6 ${themeClasses.card} p-4 rounded-lg shadow border`}>
      <div className="flex flex-wrap gap-4 items-center">
        {/* View Selector */}
        <div className={`flex ${themeClasses.bg.tertiary} rounded-lg p-1`}>
          <button
            onClick={() => onViewChange('active')}
            className={`px-4 py-2 rounded-md transition-colors ${
              view === 'active' ? `${themeClasses.bg.primary} shadow text-blue-600` : themeClasses.text.secondary
            }`}
          >
            Active ({activeCount})
          </button>
          <button
            onClick={() => onViewChange('all')}
            className={`px-4 py-2 rounded-md transition-colors ${
              view === 'all' ? `${themeClasses.bg.primary} shadow text-blue-600` : themeClasses.text.secondary
            }`}
          >
            All Alerts
          </button>
          <button
            onClick={() => onViewChange('stats')}
            className={`px-4 py-2 rounded-md transition-colors ${
              view === 'stats' ? `${themeClasses.bg.primary} shadow text-blue-600` : themeClasses.text.secondary
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
            className={`border ${themeClasses.border.primary} rounded-md px-3 py-2 ${themeClasses.bg.primary} ${themeClasses.text.primary}`}
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
            className={`border ${themeClasses.border.primary} rounded-md px-3 py-2 ${themeClasses.bg.primary} ${themeClasses.text.primary}`}
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
