import React, { useState, useEffect, useRef } from 'react';
import {
  BellIcon,
  XMarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

interface Notification {
  id: string;
  type: 'alert' | 'system' | 'info';
  title: string;
  message: string;
  timestamp: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  camera_id?: string;
  alert_id?: string;
}

interface RealTimeNotificationDisplayProps {
  maxNotifications?: number;
  autoDismiss?: boolean;
  dismissDelay?: number;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
}

const RealTimeNotificationDisplay: React.FC<RealTimeNotificationDisplayProps> = ({
  maxNotifications = 5,
  autoDismiss = true,
  dismissDelay = 5000,
  position = 'top-right'
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const dismissTimeouts = useRef<Map<string, NodeJS.Timeout>>(new Map());

  useEffect(() => {
    setupWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      // Clear all timeouts
      dismissTimeouts.current.forEach(timeout => clearTimeout(timeout));
    };
  }, []);

  const setupWebSocket = () => {
    try {
      // Try to connect to the WebSocket endpoint
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/notifications`;

      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('Real-time notifications WebSocket connected');
        setIsConnected(true);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleNewNotification(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      wsRef.current.onclose = () => {
        console.log('Real-time notifications WebSocket disconnected');
        setIsConnected(false);
        // Try to reconnect after 5 seconds
        setTimeout(setupWebSocket, 5000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };
    } catch (error) {
      console.error('Failed to setup WebSocket:', error);
      setIsConnected(false);
    }
  };

  const handleNewNotification = (data: any) => {
    if (data.type === 'user_notification' || data.type === 'alert') {
      const notification: Notification = {
        id: data.id || `notification-${Date.now()}`,
        type: data.notification_type || 'alert',
        title: data.title || 'Security Alert',
        message: data.message || data.body || 'New security event detected',
        timestamp: data.timestamp || new Date().toISOString(),
        severity: data.severity || 'medium',
        camera_id: data.camera_id,
        alert_id: data.alert_id
      };

      addNotification(notification);
    }
  };

  const addNotification = (notification: Notification) => {
    setNotifications(prev => {
      const newNotifications = [notification, ...prev].slice(0, maxNotifications);
      return newNotifications;
    });

    // Auto-dismiss if enabled
    if (autoDismiss) {
      const timeout = setTimeout(() => {
        dismissNotification(notification.id);
      }, dismissDelay);

      dismissTimeouts.current.set(notification.id, timeout);
    }

    // Show browser notification if permission is granted
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(notification.title, {
        body: notification.message,
        icon: '/favicon.ico',
        tag: notification.id
      });
    }
  };

  const dismissNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));

    // Clear timeout if it exists
    const timeout = dismissTimeouts.current.get(id);
    if (timeout) {
      clearTimeout(timeout);
      dismissTimeouts.current.delete(id);
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      case 'high':
        return <ExclamationTriangleIcon className="h-5 w-5 text-orange-500" />;
      case 'medium':
        return <InformationCircleIcon className="h-5 w-5 text-yellow-500" />;
      case 'low':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      default:
        return <InformationCircleIcon className="h-5 w-5 text-blue-500" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'border-red-200 bg-red-50';
      case 'high':
        return 'border-orange-200 bg-orange-50';
      case 'medium':
        return 'border-yellow-200 bg-yellow-50';
      case 'low':
        return 'border-green-200 bg-green-50';
      default:
        return 'border-blue-200 bg-blue-50';
    }
  };

  const getPositionClasses = () => {
    switch (position) {
      case 'top-left':
        return 'top-4 left-4';
      case 'top-right':
        return 'top-4 right-4';
      case 'bottom-left':
        return 'bottom-4 left-4';
      case 'bottom-right':
        return 'bottom-4 right-4';
      default:
        return 'top-4 right-4';
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInSeconds = Math.floor((now.getTime() - time.getTime()) / 1000);

    if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    return `${Math.floor(diffInSeconds / 3600)}h ago`;
  };

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className={`fixed ${getPositionClasses()} z-50 space-y-2 max-w-sm w-full`}>
      {/* Connection Status */}
      {!isConnected && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 shadow-lg">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-yellow-800">
                Real-time notifications disconnected
              </p>
              <p className="text-xs text-yellow-600">
                Attempting to reconnect...
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Notifications */}
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`border rounded-lg p-4 shadow-lg ${getSeverityColor(notification.severity)} transition-all duration-300 ease-in-out`}
        >
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              {getSeverityIcon(notification.severity)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-900">
                  {notification.title}
                </p>
                <button
                  onClick={() => dismissNotification(notification.id)}
                  className="flex-shrink-0 ml-2 text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                {notification.message}
              </p>
              <div className="flex items-center justify-between mt-2">
                <div className="flex items-center space-x-2">
                  {notification.camera_id && (
                    <span className="text-xs text-gray-500">
                      Camera: {notification.camera_id}
                    </span>
                  )}
                  <span className="text-xs text-gray-500">
                    {formatTimeAgo(notification.timestamp)}
                  </span>
                </div>
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                  notification.severity === 'critical' ? 'text-red-800 bg-red-100' :
                  notification.severity === 'high' ? 'text-orange-800 bg-orange-100' :
                  notification.severity === 'medium' ? 'text-yellow-800 bg-yellow-100' :
                  notification.severity === 'low' ? 'text-green-800 bg-green-100' :
                  'text-blue-800 bg-blue-100'
                }`}>
                  {notification.severity}
                </span>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default RealTimeNotificationDisplay;
