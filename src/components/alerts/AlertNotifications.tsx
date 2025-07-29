import React, { useState, useEffect } from 'react';
import { XMarkIcon, ExclamationTriangleIcon, ShieldExclamationIcon } from '@heroicons/react/24/outline';
import { Alert } from '../../types';
import { getSeverityColor } from './AlertUtils';

interface AlertNotificationsProps {
  websocketUrl?: string;
  maxNotifications?: number;
  autoHideDelay?: number;
}

interface NotificationAlert extends Alert {
  notificationId: string;
  showTime: number;
}

const AlertNotifications: React.FC<AlertNotificationsProps> = ({
  websocketUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//localhost:8001/ws/alerts`,
  maxNotifications = 5,
  autoHideDelay = 8000,
}) => {
  const [notifications, setNotifications] = useState<NotificationAlert[]>([]);

  useEffect(() => {
    const ws = new WebSocket(websocketUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'alert_created' && data.alert) {
          const newNotification: NotificationAlert = {
            ...data.alert,
            notificationId: `${data.alert.id}-${Date.now()}`,
            showTime: Date.now(),
          };

          setNotifications(prev => {
            const updated = [newNotification, ...prev].slice(0, maxNotifications);
            return updated;
          });
        }
      } catch (error) {
        console.error('Error parsing notification:', error);
      }
    };

    return () => {
      ws.close();
    };
  }, [websocketUrl, maxNotifications]);

  // Auto-hide notifications after delay
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      setNotifications(prev =>
        prev.filter(notification => now - notification.showTime < autoHideDelay)
      );
    }, 1000);

    return () => clearInterval(interval);
  }, [autoHideDelay]);

  const hideNotification = (notificationId: string) => {
    setNotifications(prev =>
      prev.filter(notification => notification.notificationId !== notificationId)
    );
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
      case 'high':
        return <ShieldExclamationIcon className="h-5 w-5 text-red-500" />;
      case 'medium':
      case 'low':
      default:
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
    }
  };

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
      {notifications.map((notification) => (
        <div
          key={notification.notificationId}
          className="bg-white shadow-lg rounded-lg border border-gray-200 p-4 transform transition-all duration-300 ease-in-out"
        >
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0">
              {getSeverityIcon(notification.severity)}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${getSeverityColor(notification.severity)}`}>
                  {notification.severity.toUpperCase()}
                </span>
                <span className="text-xs text-gray-500 font-mono">
                  {notification.cameraId}
                </span>
              </div>

              <p className="text-sm font-medium text-gray-900 mb-1">
                {notification.type.replace('_', ' ').toUpperCase()} DETECTED
              </p>

              <p className="text-xs text-gray-600 line-clamp-2">
                {notification.message}
              </p>

              <div className="text-xs text-gray-500 mt-1">
                Confidence: {Math.round(notification.confidence * 100)}%
              </div>
            </div>

            <button
              onClick={() => hideNotification(notification.notificationId)}
              className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          </div>

          {/* Progress bar for auto-hide */}
          <div className="mt-3 w-full bg-gray-200 rounded-full h-1">
            <div
              className="bg-blue-500 h-1 rounded-full transition-all duration-1000 ease-linear"
              style={{
                width: `${Math.max(0, 100 - ((Date.now() - notification.showTime) / autoHideDelay) * 100)}%`
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};

export default AlertNotifications;
