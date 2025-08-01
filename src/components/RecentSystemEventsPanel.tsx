import React, { useState, useEffect } from 'react';
import { ClockIcon, ExclamationTriangleIcon, CheckCircleIcon, InformationCircleIcon } from '@heroicons/react/24/outline';
import { useThemeClasses } from '../contexts/ThemeContext';
import { apiService } from '../services/api.service';

interface SystemEvent {
  id: string;
  timestamp: string;
  action: string;
  username: string;
  user_role: string;
  success: boolean;
  severity: string;
  resource_type?: string;
  error_message?: string;
}

interface RecentSystemEventsPanelProps {
  limit?: number;
  refreshInterval?: number; // in milliseconds
}

const RecentSystemEventsPanel: React.FC<RecentSystemEventsPanelProps> = ({
  limit = 10,
  refreshInterval = 30000 // 30 seconds
}) => {
  const [events, setEvents] = useState<SystemEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const themeClasses = useThemeClasses();

  useEffect(() => {
    loadEvents();

    const interval = setInterval(loadEvents, refreshInterval);
    return () => clearInterval(interval);
  }, [limit, refreshInterval]);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const data = await apiService.get<any>(`/api/audit/recent-events?limit=${limit}&hours=24`);
      setEvents(data.logs || []);
      setError(data.sample_data ? 'Using sample data' : null);
    } catch (err) {
      // Silently handle errors and use sample data
      setError('Using sample data');
      // Provide sample data for demonstration
      setEvents([
        {
          id: '1',
          timestamp: new Date().toISOString(),
          action: 'USER_LOGIN',
          username: 'admin',
          user_role: 'admin',
          success: true,
          severity: 'low',
          resource_type: 'authentication'
        },
        {
          id: '2',
          timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
          action: 'CAMERA_ACCESS',
          username: 'operator',
          user_role: 'operator',
          success: true,
          severity: 'low',
          resource_type: 'camera'
        },
        {
          id: '3',
          timestamp: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
          action: 'PERMISSION_DENIED',
          username: 'user',
          user_role: 'user',
          success: false,
          severity: 'medium',
          resource_type: 'alert',
          error_message: 'Insufficient permissions'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityIcon = (severity: string, success: boolean) => {
    if (!success) {
      return <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />;
    }

    switch (severity.toLowerCase()) {
      case 'critical':
        return <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />;
      case 'high':
        return <ExclamationTriangleIcon className="h-4 w-4 text-orange-500" />;
      case 'medium':
        return <InformationCircleIcon className="h-4 w-4 text-yellow-500" />;
      default:
        return <CheckCircleIcon className="h-4 w-4 text-green-500" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  const formatAction = (action: string) => {
    return action.replace(/_/g, ' ').toLowerCase()
      .replace(/\b\w/g, l => l.toUpperCase());
  };

  if (loading) {
    return (
      <div className={`${themeClasses.bg.primary} rounded-lg shadow ${themeClasses.border.primary} border p-6`}>
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${themeClasses.bg.primary} rounded-lg shadow ${themeClasses.border.primary} border p-6`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <ClockIcon className={`h-5 w-5 mr-2 ${themeClasses.text.primary}`} />
          <h3 className={`text-lg font-medium ${themeClasses.text.primary}`}>Recent System Events</h3>
        </div>
        {error && (
          <span className="text-xs text-red-500 bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded">
            Sample Data
          </span>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded">
          Error: {error}
        </div>
      )}

      {/* Events List */}
      <div className="space-y-3">
        {events.length === 0 ? (
          <div className={`text-center py-8 ${themeClasses.text.secondary}`}>
            <ClockIcon className="w-8 h-8 mx-auto mb-2" />
            <p className="text-sm">No recent system events</p>
          </div>
        ) : (
          events.map((event) => (
            <div
              key={event.id}
              className={`flex items-start space-x-3 p-3 rounded-lg border ${
                event.success
                  ? 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800'
                  : 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-800'
              }`}
            >
              <div className="flex-shrink-0 mt-1">
                {getSeverityIcon(event.severity, event.success)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className={`text-sm font-medium ${themeClasses.text.primary}`}>
                    {formatAction(event.action)}
                  </p>
                  <span className={`text-xs ${themeClasses.text.secondary}`}>
                    {formatTimestamp(event.timestamp)}
                  </span>
                </div>
                <div className="flex items-center space-x-2 mt-1">
                  <span className={`text-xs ${themeClasses.text.secondary}`}>
                    {event.username} ({event.user_role})
                  </span>
                  {event.resource_type && (
                    <span className={`text-xs px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-800 ${themeClasses.text.secondary}`}>
                      {event.resource_type}
                    </span>
                  )}
                </div>
                {event.error_message && (
                  <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                    {event.error_message}
                  </p>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex justify-between items-center">
          <span className={`text-xs ${themeClasses.text.secondary}`}>
            Showing {events.length} recent events
          </span>
          <button
            onClick={loadEvents}
            className={`text-xs ${themeClasses.text.primary} hover:underline`}
          >
            Refresh
          </button>
        </div>
      </div>
    </div>
  );
};

export default RecentSystemEventsPanel;
