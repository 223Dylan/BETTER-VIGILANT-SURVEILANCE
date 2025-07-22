import React, { useEffect, useState, useRef } from 'react';
import { metricsService, Alert } from '../services/metrics.service';

interface AlertsNotificationPanelProps {
  limit?: number;
  realTime?: boolean;
  onAlertClick?: (alert: Alert) => void;
}

const AlertsNotificationPanel: React.FC<AlertsNotificationPanelProps> = ({
  limit = 20,
  realTime = false,
  onAlertClick
}) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [newAlertsCount, setNewAlertsCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const lastAlertTime = useRef<number>(0);

  useEffect(() => {
    loadAlerts();

    if (realTime) {
      setupWebSocket();
    } else {
      const interval = setInterval(loadAlerts, 60000); // Check every minute
      return () => clearInterval(interval);
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [limit, realTime]);

  const loadAlerts = async () => {
    try {
      const alertsData = await metricsService.getRecentAlerts(limit);
      setAlerts(alertsData);
      setLoading(false);
      setError(null);

      // Update last alert time
      if (alertsData.length > 0) {
        const latest = new Date(alertsData[0].timestamp).getTime();
        if (latest > lastAlertTime.current) {
          lastAlertTime.current = latest;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load alerts');
      setLoading(false);
    }
  };

  const setupWebSocket = () => {
    try {
      wsRef.current = metricsService.createAlertsWebSocket();

      wsRef.current.onopen = () => {
        console.log('Alerts WebSocket connected');
        setError(null);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = metricsService.parseWebSocketMessage(event);

          if (message?.type === 'alerts_update') {
            const { new_alerts, total_recent } = message;

            if (new_alerts && new_alerts.length > 0) {
              // Add new alerts to the beginning of the list
              setAlerts(prev => {
                const combined = [...new_alerts, ...prev];
                return combined.slice(0, limit); // Keep only the latest alerts
              });

              // Count truly new alerts (after last known alert)
              const newCount = new_alerts.filter((alert: Alert) => {
                const alertTime = new Date(alert.timestamp).getTime();
                return alertTime > lastAlertTime.current;
              }).length;

              if (newCount > 0) {
                setNewAlertsCount(prev => prev + newCount);
                // Update last alert time
                const latestTime = Math.max(...new_alerts.map((a: Alert) => new Date(a.timestamp).getTime()));
                lastAlertTime.current = Math.max(lastAlertTime.current, latestTime);

                // Play notification sound or show browser notification
                if ('Notification' in window && Notification.permission === 'granted') {
                  new Notification(`${newCount} new security alert${newCount > 1 ? 's' : ''}`, {
                    body: `Latest: ${new_alerts[0].label} detected on ${new_alerts[0].camera_id}`,
                    icon: '/favicon.ico'
                  });
                }
              }
            }
          }
        } catch (err) {
          console.error('Error parsing alerts WebSocket message:', err);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('Alerts WebSocket error:', error);
        setError('WebSocket connection error');
      };

      wsRef.current.onclose = () => {
        console.log('Alerts WebSocket disconnected');
        if (realTime) {
          setTimeout(() => setupWebSocket(), 5000);
        }
      };
    } catch (err) {
      console.error('Failed to setup alerts WebSocket:', err);
      setError('Failed to establish real-time connection');
    }
  };

  const clearNewAlertsCount = () => {
    setNewAlertsCount(0);
  };

  const getSeverityColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'critical':
        return 'bg-red-500 text-white';
      case 'high':
        return 'bg-red-400 text-white';
      case 'medium':
        return 'bg-yellow-500 text-white';
      case 'low':
        return 'bg-blue-500 text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  const getSeverityIcon = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'critical':
        return '!';
      case 'high':
        return '!';
      case 'medium':
        return '▲';
      case 'low':
        return 'i';
      default:
        return '•';
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date().getTime();
    const alertTime = new Date(timestamp).getTime();
    const diffMinutes = Math.floor((now - alertTime) / (1000 * 60));

    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;

    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  const requestNotificationPermission = async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      await Notification.requestPermission();
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">
            Recent Alerts
            {newAlertsCount > 0 && (
              <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 animate-pulse">
                {newAlertsCount} new
              </span>
            )}
          </h3>
          <div className="flex items-center space-x-2">
            {realTime && (
              <span className="flex items-center text-sm text-green-600">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></span>
                Live
              </span>
            )}
            {newAlertsCount > 0 && (
              <button
                onClick={clearNewAlertsCount}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Clear
              </button>
            )}
            <button
              onClick={requestNotificationPermission}
              className="text-sm text-blue-600 hover:text-blue-800"
              title="Enable browser notifications"
            >
              [BELL]
            </button>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="max-h-96 overflow-y-auto">
        {error && (
          <div className="p-4 bg-red-50 border-l-4 border-red-400">
            <p className="text-red-700 text-sm">{error}</p>
            <button
              onClick={loadAlerts}
              className="mt-2 text-red-600 hover:text-red-800 text-sm underline"
            >
              Retry
            </button>
          </div>
        )}

        {alerts.length === 0 && !loading && !error && (
          <div className="p-6 text-center text-gray-500">
            <div className="text-4xl mb-2 text-green-600">OK</div>
            <p>No recent alerts</p>
            <p className="text-sm mt-1">System is running smoothly</p>
          </div>
        )}

        {alerts.map((alert, index) => (
          <div
            key={`${alert.timestamp}-${index}`}
            className={`p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors ${
              index < newAlertsCount ? 'bg-red-50 border-l-4 border-l-red-400' : ''
            }`}
            onClick={() => onAlertClick?.(alert)}
          >
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className="text-xl">
                  {getSeverityIcon(alert.level)}
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {alert.label}
                  </p>
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(alert.level)}`}>
                      {alert.level}
                    </span>
                    <span className="text-xs text-gray-500">
                      {formatTimeAgo(alert.timestamp)}
                    </span>
                  </div>
                </div>
                <div className="mt-1 flex items-center justify-between">
                  <p className="text-sm text-gray-600">
                    Camera: <span className="font-medium">{alert.camera_id}</span>
                  </p>
                  <p className="text-sm text-gray-500">
                    Confidence: {metricsService.formatPercentage(alert.confidence * 100)}
                  </p>
                </div>
                {alert.type !== 'detection' && (
                  <p className="text-xs text-gray-500 mt-1">
                    Type: {alert.type}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      {alerts.length > 0 && (
        <div className="px-6 py-3 bg-gray-50 text-center">
          <p className="text-xs text-gray-500">
            Showing last {Math.min(alerts.length, limit)} alerts
          </p>
        </div>
      )}
    </div>
  );
};

export default AlertsNotificationPanel;
