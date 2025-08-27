import React, { useState, useEffect } from 'react';
import {
  BellIcon,
  BellSlashIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { pushNotificationService } from '../services/pushNotification.service';
import { useThemeClasses } from '../contexts/ThemeContext';

const PushNotificationSettings: React.FC = () => {
  const themeClasses = useThemeClasses();
  const [isSupported, setIsSupported] = useState(false);
  const [permissionStatus, setPermissionStatus] = useState<NotificationPermission>('default');
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    initializePushNotifications();
  }, []);

  const initializePushNotifications = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Check if push notifications are supported
      const supported = pushNotificationService.isPushSupported();
      setIsSupported(supported);

      if (supported) {
        // Initialize the service
        await pushNotificationService.initialize();

        // Check current permission status
        const permission = pushNotificationService.getPermissionStatus();
        setPermissionStatus(permission);

        // Check subscription status
        const subscribed = await pushNotificationService.checkSubscription();
        setIsSubscribed(subscribed);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initialize push notifications');
    } finally {
      setIsLoading(false);
    }
  };

  const requestPermission = async () => {
    try {
      setIsLoading(true);
      setError(null);
      setSuccess(null);

      const permission = await pushNotificationService.requestPermission();
      setPermissionStatus(permission);

      if (permission === 'granted') {
        setSuccess('Notification permission granted! You can now subscribe to push notifications.');
      } else if (permission === 'denied') {
        setError('Notification permission denied. You can enable it in your browser settings.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to request permission');
    } finally {
      setIsLoading(false);
    }
  };

  const subscribeToPush = async () => {
    try {
      setIsLoading(true);
      setError(null);
      setSuccess(null);

      await pushNotificationService.subscribe();
      setIsSubscribed(true);
      setSuccess('Successfully subscribed to push notifications!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to subscribe to push notifications');
    } finally {
      setIsLoading(false);
    }
  };

  const unsubscribeFromPush = async () => {
    try {
      setIsLoading(true);
      setError(null);
      setSuccess(null);

      const success = await pushNotificationService.unsubscribe();
      if (success) {
        setIsSubscribed(false);
        setSuccess('Successfully unsubscribed from push notifications.');
      } else {
        setError('Failed to unsubscribe from push notifications.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to unsubscribe from push notifications');
    } finally {
      setIsLoading(false);
    }
  };

  const sendTestNotification = async () => {
    try {
      setIsLoading(true);
      setError(null);
      setSuccess(null);

      await pushNotificationService.sendTestNotification();
      setSuccess('Test notification sent! Check your browser notifications.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send test notification');
    } finally {
      setIsLoading(false);
    }
  };

  const getPermissionStatusIcon = () => {
    switch (permissionStatus) {
      case 'granted':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'denied':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      case 'default':
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />;
      default:
        return <InformationCircleIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  const getPermissionStatusText = () => {
    switch (permissionStatus) {
      case 'granted':
        return 'Permission Granted';
      case 'denied':
        return 'Permission Denied';
      case 'default':
        return 'Permission Not Set';
      default:
        return 'Unknown Status';
    }
  };

  const getPermissionStatusColor = () => {
    switch (permissionStatus) {
      case 'granted':
        return 'text-green-600';
      case 'denied':
        return 'text-red-600';
      case 'default':
        return 'text-yellow-600';
      default:
        return 'text-gray-600';
    }
  };

  if (isLoading && !isSupported) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!isSupported) {
    return (
      <div className={`p-6 rounded-lg border ${themeClasses.border.secondary} ${themeClasses.bg.primary}`}>
        <div className="flex items-center space-x-3 mb-4">
          <XCircleIcon className="w-8 h-8 text-red-500" />
          <h3 className={`text-lg font-medium ${themeClasses.text.primary}`}>
            Push Notifications Not Supported
          </h3>
        </div>
        <p className={`text-sm ${themeClasses.text.secondary} mb-4`}>
          Your browser doesn't support push notifications. This feature requires a modern browser with service worker support.
        </p>
        <div className="text-xs text-gray-500">
          <p>Supported browsers: Chrome 42+, Firefox 44+, Safari 16+, Edge 17+</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className={`text-lg font-medium ${themeClasses.text.primary}`}>
          Push Notification Settings
        </h3>
        <p className={`text-sm ${themeClasses.text.secondary} mt-1`}>
          Manage your browser push notification preferences for security alerts
        </p>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Permission Status */}
        <div className={`p-4 rounded-lg border ${themeClasses.border.secondary} ${themeClasses.bg.primary}`}>
          <div className="flex items-center space-x-3 mb-3">
            {getPermissionStatusIcon()}
            <span className={`font-medium ${getPermissionStatusColor()}`}>
              {getPermissionStatusText()}
            </span>
          </div>
          <p className={`text-sm ${themeClasses.text.secondary}`}>
            Browser notification permission status
          </p>
        </div>

        {/* Subscription Status */}
        <div className={`p-4 rounded-lg border ${themeClasses.border.secondary} ${themeClasses.bg.primary}`}>
          <div className="flex items-center space-x-3 mb-3">
            {isSubscribed ? (
              <CheckCircleIcon className="w-5 h-5 text-green-500" />
            ) : (
              <BellSlashIcon className="w-5 h-5 text-gray-500" />
            )}
            <span className={`font-medium ${isSubscribed ? 'text-green-600' : 'text-gray-600'}`}>
              {isSubscribed ? 'Subscribed' : 'Not Subscribed'}
            </span>
          </div>
          <p className={`text-sm ${themeClasses.text.secondary}`}>
            Push notification subscription status
          </p>
        </div>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="p-4 rounded-md bg-red-100 border border-red-300 text-red-700">
          {error}
        </div>
      )}

      {success && (
        <div className="p-4 rounded-md bg-green-100 border border-green-300 text-green-700">
          {success}
        </div>
      )}

      {/* Action Buttons */}
      <div className="space-y-4">
        {/* Permission Request */}
        {permissionStatus === 'default' && (
          <div className={`p-4 rounded-lg border ${themeClasses.border.secondary} ${themeClasses.bg.primary}`}>
            <div className="flex items-center space-x-3 mb-3">
              <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />
              <h4 className={`font-medium ${themeClasses.text.primary}`}>
                Enable Notifications
              </h4>
            </div>
            <p className={`text-sm ${themeClasses.text.secondary} mb-4`}>
              To receive push notifications for security alerts, you need to grant notification permission.
            </p>
            <button
              onClick={requestPermission}
              disabled={isLoading}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                isLoading
                  ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isLoading ? 'Requesting...' : 'Grant Permission'}
            </button>
          </div>
        )}

        {/* Subscription Management */}
        {permissionStatus === 'granted' && (
          <div className={`p-4 rounded-lg border ${themeClasses.border.secondary} ${themeClasses.bg.primary}`}>
            <div className="flex items-center space-x-3 mb-3">
              <BellIcon className="w-5 h-5 text-blue-500" />
              <h4 className={`font-medium ${themeClasses.text.primary}`}>
                Push Notification Subscription
              </h4>
            </div>
            <p className={`text-sm ${themeClasses.text.secondary} mb-4`}>
              {isSubscribed
                ? 'You are currently subscribed to push notifications for security alerts.'
                : 'Subscribe to receive real-time push notifications for security alerts.'
              }
            </p>

            <div className="flex space-x-3">
              {!isSubscribed ? (
                <button
                  onClick={subscribeToPush}
                  disabled={isLoading}
                  className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    isLoading
                      ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                      : 'bg-green-600 text-white hover:bg-green-700'
                  }`}
                >
                  {isLoading ? 'Subscribing...' : 'Subscribe to Push Notifications'}
                </button>
              ) : (
                <button
                  onClick={unsubscribeFromPush}
                  disabled={isLoading}
                  className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    isLoading
                      ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                      : 'bg-red-600 text-white hover:bg-red-700'
                  }`}
                >
                  {isLoading ? 'Unsubscribing...' : 'Unsubscribe from Push Notifications'}
                </button>
              )}
            </div>
          </div>
        )}

        {/* Test Notification */}
        {permissionStatus === 'granted' && (
          <div className={`p-4 rounded-lg border ${themeClasses.border.secondary} ${themeClasses.bg.primary}`}>
            <div className="flex items-center space-x-3 mb-3">
              <BellIcon className="w-5 h-5 text-purple-500" />
              <h4 className={`font-medium ${themeClasses.text.primary}`}>
                Test Push Notification
              </h4>
            </div>
            <p className={`text-sm ${themeClasses.text.secondary} mb-4`}>
              Send a test push notification to verify your setup is working correctly.
            </p>
            <button
              onClick={sendTestNotification}
              disabled={isLoading}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                isLoading
                  ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                  : 'bg-purple-600 text-white hover:bg-purple-700'
              }`}
            >
              {isLoading ? 'Sending...' : 'Send Test Notification'}
            </button>
          </div>
        )}

        {/* Permission Denied Help */}
        {permissionStatus === 'denied' && (
          <div className={`p-4 rounded-lg border border-red-200 bg-red-50`}>
            <div className="flex items-center space-x-3 mb-3">
              <XCircleIcon className="w-5 h-5 text-red-500" />
              <h4 className="font-medium text-red-800">
                Permission Denied
              </h4>
            </div>
            <p className="text-sm text-red-700 mb-4">
              Notification permission was denied. To enable push notifications:
            </p>
            <div className="text-sm text-red-700 space-y-2">
              <p>• Click the lock/info icon in your browser's address bar</p>
              <p>• Change "Notifications" to "Allow"</p>
              <p>• Refresh this page and try again</p>
            </div>
          </div>
        )}
      </div>

      {/* Information */}
      <div className={`p-4 rounded-lg border ${themeClasses.border.secondary} ${themeClasses.bg.secondary}`}>
        <div className="flex items-start space-x-3">
          <InformationCircleIcon className="w-5 h-5 text-blue-500 mt-0.5" />
          <div>
            <h4 className={`font-medium ${themeClasses.text.primary} mb-2`}>
              About Push Notifications
            </h4>
            <div className={`text-sm ${themeClasses.text.secondary} space-y-2`}>
              <p>• Push notifications work even when the app is closed</p>
              <p>• Critical security alerts will require your attention</p>
              <p>• Notifications include camera ID, alert type, and severity</p>
              <p>• Click on notifications to view full details</p>
              <p>• You can unsubscribe at any time</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PushNotificationSettings;
