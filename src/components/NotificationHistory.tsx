import React, { useState, useEffect } from 'react';
import {
  BellIcon,
  EnvelopeIcon,
  GlobeAltIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { notificationService, NotificationHistoryItem } from '../services/notification.service';
import { useThemeClasses } from '../contexts/ThemeContext';

interface NotificationHistoryProps {
  limit?: number;
  showFilters?: boolean;
}

const NotificationHistory: React.FC<NotificationHistoryProps> = ({
  limit = 50,
  showFilters = true
}) => {
  const themeClasses = useThemeClasses();
  const [notifications, setNotifications] = useState<NotificationHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    type: 'all',
    status: 'all',
    dateRange: '7d'
  });

  useEffect(() => {
    loadNotificationHistory();
  }, [filters]);

  const loadNotificationHistory = async () => {
    setLoading(true);
    try {
      const data = await notificationService.getNotificationHistory(limit, filters);
      setNotifications(data.notifications || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load notification history');
      // Don't show mock data in production - keep empty state
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  };

  const generateMockNotifications = (): NotificationHistoryItem[] => {
    const types: ('email' | 'push' | 'webhook' | 'alert_broadcast')[] = ['email', 'push', 'webhook', 'alert_broadcast'];
    const statuses: ('pending' | 'sent' | 'delivered' | 'failed' | 'opened' | 'clicked')[] = ['pending', 'sent', 'delivered', 'failed', 'opened', 'clicked'];
    const severities = ['critical', 'high', 'medium', 'low'];

    return Array.from({ length: 20 }, (_, i) => ({
      id: `notification-${i + 1}`,
      user_id: `user-${i + 1}`,
      notification_type: types[Math.floor(Math.random() * types.length)],
      title: `Security Alert - ${severities[Math.floor(Math.random() * severities.length)]} severity`,
      message: `Suspicious activity detected on camera CAM-${Math.floor(Math.random() * 0) + 1}`,
      status: statuses[Math.floor(Math.random() * statuses.length)],
      alert_id: `alert-${i + 1}`,
      channel_data: { severity: severities[Math.floor(Math.random() * severities.length)] },
      retry_count: '0',
      created_at: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString()
    }));
  };

  const getTypeIcon = (notification_type: string) => {
    switch (notification_type) {
      case 'email':
        return <EnvelopeIcon className="h-5 w-5 text-blue-500" />;
      case 'push':
        return <BellIcon className="h-5 w-5 text-green-500" />;
      case 'webhook':
        return <GlobeAltIcon className="h-5 w-5 text-purple-500" />;
      case 'alert_broadcast':
        return <GlobeAltIcon className="h-5 w-5 text-orange-500" />;
      default:
        return <BellIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'sent':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      case 'pending':
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
      default:
        return <XMarkIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-600 bg-red-50';
      case 'high':
        return 'text-orange-600 bg-orange-50';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50';
      case 'low':
        return 'text-green-600 bg-green-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInSeconds = Math.floor((now.getTime() - time.getTime()) / 1000);

    if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  };

  const filteredNotifications = notifications.filter(notification => {
    if (filters.type !== 'all' && notification.notification_type !== filters.type) return false;
    if (filters.status !== 'all' && notification.status !== filters.status) return false;
    return true;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading notification history...</span>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${themeClasses.bg.primary}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <BellIcon className="h-6 w-6 text-blue-600 dark:text-blue-400 mr-3" />
          <h2 className={`text-xl font-semibold ${themeClasses.text.primary}`}>Notification History</h2>
        </div>
        <button
          onClick={loadNotificationHistory}
          className={`inline-flex items-center px-3 py-2 border ${themeClasses.border.primary} rounded-md shadow-sm text-sm font-medium ${themeClasses.text.primary} ${themeClasses.bg.primary} ${themeClasses.hover.bg} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
        >
          Refresh
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm font-medium text-red-800 dark:text-red-200">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      {showFilters && (
        <div className={`${themeClasses.bg.primary} shadow rounded-lg p-4 ${themeClasses.border.primary} border`}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className={`block text-sm font-medium ${themeClasses.text.primary} mb-1`}>Type</label>
              <select
                value={filters.type}
                onChange={(e) => setFilters(prev => ({ ...prev, type: e.target.value }))}
                className={`block w-full px-3 py-2 border ${themeClasses.border.primary} rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${themeClasses.bg.primary} ${themeClasses.text.primary}`}
              >
                <option value="all">All Types</option>
                <option value="email">Email</option>
                <option value="push">Push</option>
                <option value="webhook">Webhook</option>
              </select>
            </div>

            <div>
              <label className={`block text-sm font-medium ${themeClasses.text.primary} mb-1`}>Status</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                className={`block w-full px-3 py-2 border ${themeClasses.border.primary} rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${themeClasses.bg.primary} ${themeClasses.text.primary}`}
              >
                <option value="all">All Status</option>
                <option value="sent">Sent</option>
                <option value="failed">Failed</option>
                <option value="pending">Pending</option>
              </select>
            </div>

            <div>
              <label className={`block text-sm font-medium ${themeClasses.text.primary} mb-1`}>Time Range</label>
              <select
                value={filters.dateRange}
                onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value }))}
                className={`block w-full px-3 py-2 border ${themeClasses.border.primary} rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${themeClasses.bg.primary} ${themeClasses.text.primary}`}
              >
                <option value="1d">Last 24 hours</option>
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Notifications List */}
      <div className={`${themeClasses.bg.primary} shadow rounded-lg overflow-hidden ${themeClasses.border.primary} border`}>
        {filteredNotifications.length === 0 ? (
          <div className="text-center py-12">
            <BellIcon className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" />
            <h3 className={`mt-2 text-sm font-medium ${themeClasses.text.primary}`}>No notifications</h3>
            <p className={`mt-1 text-sm ${themeClasses.text.secondary}`}>
              No notifications found for the selected filters.
            </p>
          </div>
        ) : (
          <div className={`divide-y ${themeClasses.border.primary}`}>
            {filteredNotifications.slice(0, limit).map((notification) => (
              <div key={notification.id} className={`p-4 ${themeClasses.hover.bg}`}>
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    {getTypeIcon(notification.notification_type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <p className={`text-sm font-medium ${themeClasses.text.primary}`}>{notification.title}</p>
                                        {notification.channel_data?.severity && (
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(notification.channel_data.severity)}`}>
                    {notification.channel_data.severity}
                  </span>
                )}
                      </div>
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(notification.status)}
                        <span className={`text-xs ${themeClasses.text.secondary}`}>{formatTimeAgo(notification.created_at)}</span>
                      </div>
                    </div>
                                         <p className={`text-sm ${themeClasses.text.secondary} mt-1`}>{notification.message}</p>
                     {notification.channel_data?.camera_id && (
                       <p className={`text-xs ${themeClasses.text.secondary} mt-1`}>Camera: {notification.channel_data.camera_id}</p>
                     )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Load More */}
      {filteredNotifications.length > limit && (
        <div className="text-center">
          <button className={`inline-flex items-center px-4 py-2 border ${themeClasses.border.primary} rounded-md shadow-sm text-sm font-medium ${themeClasses.text.primary} ${themeClasses.bg.primary} ${themeClasses.hover.bg} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}>
            Load More
          </button>
        </div>
      )}
    </div>
  );
};

export default NotificationHistory;
