import React from 'react';
import { AlertStats as AlertStatsType } from '../../types';
import { getSeverityColor } from './AlertUtils';

interface AlertStatsProps {
  stats: AlertStatsType;
}

const AlertStats: React.FC<AlertStatsProps> = ({ stats }) => {
  return (
    <>
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow border">
          <div className="text-2xl font-bold text-red-600">{stats.totalActive}</div>
          <div className="text-sm text-gray-600">Active Alerts</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border">
          <div className="text-2xl font-bold text-blue-600">{stats.totalToday}</div>
          <div className="text-sm text-gray-600">Today</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border">
          <div className="text-2xl font-bold text-purple-600">{stats.totalWeek}</div>
          <div className="text-sm text-gray-600">This Week</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border">
          <div className="text-2xl font-bold text-green-600">{Math.round(stats.avgConfidence * 100)}%</div>
          <div className="text-sm text-gray-600">Avg Confidence</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border">
          <div className="text-2xl font-bold text-orange-600">{stats.avgResponseTime}m</div>
          <div className="text-sm text-gray-600">Avg Response</div>
        </div>
      </div>

      {/* Detailed Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Severity Breakdown */}
        <div className="bg-white p-6 rounded-lg shadow border">
          <h3 className="text-lg font-semibold mb-4">Alerts by Severity</h3>
          <div className="space-y-2">
            {Object.entries(stats.bySeverity).map(([severity, count]) => (
              <div key={severity} className="flex justify-between items-center">
                <span className={`px-2 py-1 rounded text-sm ${getSeverityColor(severity)}`}>
                  {severity.toUpperCase()}
                </span>
                <span className="font-medium">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Camera Breakdown */}
        <div className="bg-white p-6 rounded-lg shadow border">
          <h3 className="text-lg font-semibold mb-4">Alerts by Camera</h3>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {Object.entries(stats.byCamera).map(([camera, count]) => (
              <div key={camera} className="flex justify-between items-center">
                <span className="text-sm font-mono">{camera}</span>
                <span className="font-medium">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Type Breakdown */}
        <div className="bg-white p-6 rounded-lg shadow border">
          <h3 className="text-lg font-semibold mb-4">Alerts by Type</h3>
          <div className="space-y-2">
            {Object.entries(stats.byType).map(([type, count]) => (
              <div key={type} className="flex justify-between items-center">
                <span className="text-sm">{type.replace('_', ' ')}</span>
                <span className="font-medium">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
};

export default AlertStats; 