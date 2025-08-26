import React, { useState, useEffect } from 'react';
import { notificationService, NotificationHistoryItem } from '../services/notification.service';
import { useTheme } from '../contexts/ThemeContext';
import { BellIcon, EnvelopeIcon, GlobeAltIcon, CheckIcon, CheckCircleIcon, XCircleIcon, ClockIcon } from '@heroicons/react/24/outline';

interface NotificationsTabProps {
  onClose: () => void;
}

const NotificationsTab: React.FC<NotificationsTabProps> = ({ onClose }) => {
  const { theme } = useTheme();
  const [notifications, setNotifications] = useState<NotificationHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'unread' | 'read'>('all');

  const themeClasses = {
    bg: {
      primary: theme === 'dark' ? 'bg-gray-800' : 'bg-white',
      secondary: theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50',
      hover: theme === 'dark' ? 'hover:bg-gray-700' : 'hover:bg-gray-100',
    },
    text: {
      primary: theme === 'dark' ? 'text-white' : 'text-gray-900',
      secondary: theme === 'dark' ? 'text-gray-300' : 'text-gray-600',
      muted: theme === 'dark' ? 'text-gray-400' : 'text-gray-500',
    },
    border: {
      primary: theme === 'dark' ? 'border-gray-600' : 'border-gray-200',
      secondary: theme === 'dark' ? 'border-gray-700' : 'border-gray-300',
    },
  };

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const history = await notificationService.getNotificationHistory(100);
      setNotifications(history.notifications);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId: string) => {
    try {
      await notificationService.updateNotificationStatus(notificationId, 'delivered');
      // Update local state
      setNotifications(prev =>
        prev.map(n =>
          n.id === notificationId
            ? { ...n, status: 'delivered' as const }
            : n
        )
      );
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
    }
  };

  const markAllAsRead = async () => {
    try {
      await notificationService.markAllNotificationsAsRead();
      // Update local state
      setNotifications(prev =>
        prev.map(n => ({ ...n, status: 'delivered' as const }))
      );
    } catch (err) {
      console.error('Failed to mark all notifications as read:', err);
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'email':
        return <EnvelopeIcon className="w-5 h-5 text-blue-500" />;
      case 'push':
        return <BellIcon className="w-5 h-5 text-green-500" />;
      case 'webhook':
        return <GlobeAltIcon className="w-5 h-5 text-purple-500" />;
      default:
        return <BellIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'delivered':
      case 'opened':
      case 'clicked':
        return <CheckCircleIcon className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="w-4 h-4 text-red-500" />;
      case 'pending':
        return <ClockIcon className="w-4 h-4 text-yellow-500" />;
      default:
        return <ClockIcon className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'delivered':
        return 'Read';
      case 'opened':
        return 'Opened';
      case 'clicked':
        return 'Clicked';
      case 'failed':
        return 'Failed';
      case 'pending':
        return 'Unread';
      default:
        return status;
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60));

    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  const filteredNotifications = notifications.filter(n => {
    if (filter === 'unread') return n.status === 'pending';
    if (filter === 'read') return n.status !== 'pending';
    return true;
  });

  const unreadCount = notifications.filter(n => n.status === 'pending').length;

  if (loading) {
    return (
      <div className={`fixed inset-0 z-50 ${themeClasses.bg.primary} flex items-center justify-center`}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className={`fixed inset-0 z-50 ${themeClasses.bg.primary} flex flex-col`}>
      {/* Header */}
      <div className={`flex items-center justify-between p-4 border-b ${themeClasses.border.primary}`}>
        <div className="flex items-center space-x-3">
          <BellIcon className="w-6 h-6 text-blue-500" />
          <h2 className={`text-xl font-semibold ${themeClasses.text.primary}`}>
            Notifications ({unreadCount} unread)
          </h2>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={markAllAsRead}
            disabled={unreadCount === 0}
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
              unreadCount === 0
                ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            Mark All Read
          </button>
          <button
            onClick={onClose}
            className={`p-2 rounded-md ${themeClasses.bg.hover} ${themeClasses.text.primary}`}
          >
            <XCircleIcon className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className={`p-4 border-b ${themeClasses.border.primary}`}>
        <div className="flex space-x-2">
          {[
            { key: 'all', label: 'All' },
            { key: 'unread', label: 'Unread' },
            { key: 'read', label: 'Read' }
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setFilter(key as typeof filter)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                filter === key
                  ? 'bg-blue-600 text-white'
                  : `${themeClasses.bg.secondary} ${themeClasses.text.secondary} hover:${themeClasses.bg.hover}`
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Notifications List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {error && (
          <div className={`p-4 rounded-md bg-red-100 border border-red-300 text-red-700`}>
            {error}
          </div>
        )}

        {filteredNotifications.length === 0 ? (
          <div className={`text-center py-8 ${themeClasses.text.secondary}`}>
            <BellIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No notifications found</p>
          </div>
        ) : (
          filteredNotifications.map((notification) => (
            <div
              key={notification.id}
              className={`p-4 rounded-lg border ${themeClasses.border.secondary} ${themeClasses.bg.secondary} transition-all hover:shadow-md`}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-1">
                  {getNotificationIcon(notification.notification_type)}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className={`font-medium ${themeClasses.text.primary} mb-1`}>
                        {notification.title || 'Security Alert'}
                      </h3>
                      <p className={`text-sm ${themeClasses.text.secondary} mb-2`}>
                        {notification.message}
                      </p>

                      {notification.channel_data?.camera_id && (
                        <p className={`text-xs ${themeClasses.text.muted} mb-2`}>
                          Camera: {notification.channel_data.camera_id}
                        </p>
                      )}

                      <div className="flex items-center space-x-3">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          notification.channel_data?.severity === 'critical'
                            ? 'bg-red-100 text-red-800'
                            : notification.channel_data?.severity === 'high'
                            ? 'bg-orange-100 text-orange-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {notification.channel_data?.severity || 'medium'}
                        </span>

                        <div className={`flex items-center space-x-1 text-xs ${themeClasses.text.muted}`}>
                          {getStatusIcon(notification.status)}
                          <span>{getStatusText(notification.status)}</span>
                        </div>

                        <span className={`text-xs ${themeClasses.text.muted}`}>
                          {formatTimeAgo(notification.created_at)}
                        </span>
                      </div>
                    </div>

                                         {notification.status === 'pending' && (
                       <button
                         onClick={() => markAsRead(notification.id)}
                         className={`ml-3 p-2 rounded-md ${themeClasses.bg.hover} ${themeClasses.text.primary} hover:bg-green-100 hover:text-green-700 transition-colors`}
                         title="Mark as read"
                       >
                         <CheckIcon className="w-4 h-4" />
                       </button>
                     )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default NotificationsTab;
