import React, { useState, useEffect } from 'react';
import {
  BellIcon,
  Cog6ToothIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { notificationService } from '../services/notification.service';
import { useThemeClasses } from '../contexts/ThemeContext';

interface NotificationPreferences {
  id?: string;
  user_id?: string;
  email_enabled: boolean;
  push_enabled: boolean;
  webhook_enabled: boolean;
  webhook_url?: string;
  alert_severities: string[];
  alert_types: string[];
  assigned_cameras: string[];
  cooldown_minutes: number;
  quiet_hours_enabled: boolean;
  quiet_hours_start: string;
  quiet_hours_end: string;
  custom_filters: Record<string, any>;
}

interface UserNotificationSettingsProps {
  onSave?: (preferences: NotificationPreferences) => void;
}

const SEVERITY_OPTIONS = [
  { value: 'critical', label: 'Critical', color: 'text-red-600' },
  { value: 'high', label: 'High', color: 'text-orange-600' },
  { value: 'medium', label: 'Medium', color: 'text-yellow-600' },
  { value: 'low', label: 'Low', color: 'text-green-600' }
];

const ALERT_TYPE_OPTIONS = [
  { value: 'shoplifting', label: 'Shoplifting' },
  { value: 'suspicious_activity', label: 'Suspicious Activity' },
  { value: 'object_detection', label: 'Object Detection' },
  { value: 'motion', label: 'Motion Detection' },
  { value: 'system_alert', label: 'System Alert' }
];

const UserNotificationSettings: React.FC<UserNotificationSettingsProps> = ({ onSave }) => {
  const themeClasses = useThemeClasses();
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    email_enabled: true,
    push_enabled: true,
    webhook_enabled: false,
    alert_severities: ['critical', 'high', 'medium'],
    alert_types: ['shoplifting', 'suspicious_activity', 'system_alert'],
    assigned_cameras: [],
    cooldown_minutes: 5,
    quiet_hours_enabled: false,
    quiet_hours_start: '22:00',
    quiet_hours_end: '08:00',
    custom_filters: {}
  });

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    setLoading(true);
    try {
      const data = await notificationService.getNotificationPreferences();
        setPreferences(data);
    } catch (error) {
      console.error('Failed to load preferences:', error);
      setMessage({ type: 'error', text: 'Failed to load notification preferences' });
    } finally {
      setLoading(false);
    }
  };

  const savePreferences = async () => {
    setSaving(true);
    try {
      const data = await notificationService.updateNotificationPreferences(preferences);
        setPreferences(data);
        setMessage({ type: 'success', text: 'Notification preferences saved successfully!' });
        onSave?.(data);
    } catch (error) {
      console.error('Failed to save preferences:', error);
      setMessage({ type: 'error', text: 'Failed to save preferences' });
    } finally {
      setSaving(false);
    }
  };

  const testNotification = async () => {
    try {
      const data = await notificationService.sendTestNotification();
      if (data.success) {
        setMessage({ type: 'success', text: 'Test notification sent! Check your email and browser notifications.' });
      } else {
        setMessage({ type: 'error', text: data.message || 'Failed to send test notification' });
      }
    } catch (error) {
      console.error('Failed to send test notification:', error);
      setMessage({ type: 'error', text: 'Failed to send test notification' });
    }
  };

  const updatePreference = (key: keyof NotificationPreferences, value: any) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
  };

  const toggleSeverity = (severity: string) => {
    const newSeverities = preferences.alert_severities.includes(severity)
      ? preferences.alert_severities.filter(s => s !== severity)
      : [...preferences.alert_severities, severity];
    updatePreference('alert_severities', newSeverities);
  };

  const toggleAlertType = (alertType: string) => {
    const newTypes = preferences.alert_types.includes(alertType)
      ? preferences.alert_types.filter(t => t !== alertType)
      : [...preferences.alert_types, alertType];
    updatePreference('alert_types', newTypes);
  };

  const dismissMessage = () => {
    setMessage(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading notification settings...</span>
      </div>
    );
  }

  return (
    <div className={`max-w-4xl mx-auto p-6 space-y-6 ${themeClasses.bg.primary}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <BellIcon className="h-8 w-8 text-blue-600 dark:text-blue-400 mr-3" />
          <h2 className={`text-2xl font-bold ${themeClasses.text.primary}`}>Notification Settings</h2>
        </div>
        <button
          onClick={testNotification}
          className={`inline-flex items-center px-4 py-2 border ${themeClasses.border.primary} rounded-md shadow-sm text-sm font-medium ${themeClasses.text.primary} ${themeClasses.bg.primary} ${themeClasses.hover.bg} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
        >
          <Cog6ToothIcon className="h-4 w-4 mr-2" />
          Send Test
        </button>
      </div>

      {/* Status Message */}
      {message && (
        <div className={`rounded-md p-4 ${message.type === 'success' ? 'bg-green-50 dark:bg-green-900/20' : 'bg-red-50 dark:bg-red-900/20'}`}>
          <div className="flex">
            <div className="flex-shrink-0">
              {message.type === 'success' ? (
                <CheckCircleIcon className="h-5 w-5 text-green-400" />
              ) : (
                <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
              )}
            </div>
            <div className="ml-3 flex-1">
              <p className={`text-sm font-medium ${message.type === 'success' ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'}`}>
                {message.text}
              </p>
            </div>
            <div className="ml-auto pl-3">
              <button
                onClick={dismissMessage}
                className={`inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                  message.type === 'success'
                    ? 'text-green-500 hover:bg-green-100 dark:hover:bg-green-800 focus:ring-green-600'
                    : 'text-red-500 hover:bg-red-100 dark:hover:bg-red-800 focus:ring-red-600'
                }`}
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Notification Channels */}
        <div className={`${themeClasses.bg.primary} shadow rounded-lg p-6 ${themeClasses.border.primary} border`}>
          <h3 className={`text-lg font-semibold ${themeClasses.text.primary} mb-4`}>Notification Channels</h3>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                  <label className={`text-sm font-medium ${themeClasses.text.primary}`}>Email Notifications</label>
                  <p className={`text-xs ${themeClasses.text.secondary}`}>Receive alerts via email</p>
              </div>
              <button
                type="button"
                className={`${
                  preferences.email_enabled ? 'bg-blue-600' : 'bg-gray-200'
                } relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
                onClick={() => updatePreference('email_enabled', !preferences.email_enabled)}
              >
                <span
                  className={`${
                    preferences.email_enabled ? 'translate-x-5' : 'translate-x-0'
                  } pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                  <label className={`text-sm font-medium ${themeClasses.text.primary}`}>Push Notifications</label>
                  <p className={`text-xs ${themeClasses.text.secondary}`}>Real-time browser notifications</p>
              </div>
              <button
                type="button"
                className={`${
                  preferences.push_enabled ? 'bg-blue-600' : 'bg-gray-200'
                } relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
                onClick={() => updatePreference('push_enabled', !preferences.push_enabled)}
              >
                <span
                  className={`${
                    preferences.push_enabled ? 'translate-x-5' : 'translate-x-0'
                  } pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                  <label className={`text-sm font-medium ${themeClasses.text.primary}`}>Webhook Notifications</label>
                  <p className={`text-xs ${themeClasses.text.secondary}`}>Send alerts to external systems</p>
              </div>
              <button
                type="button"
                className={`${
                  preferences.webhook_enabled ? 'bg-blue-600' : 'bg-gray-200'
                } relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
                onClick={() => updatePreference('webhook_enabled', !preferences.webhook_enabled)}
              >
                <span
                  className={`${
                    preferences.webhook_enabled ? 'translate-x-5' : 'translate-x-0'
                  } pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200`}
                />
              </button>
            </div>

            {preferences.webhook_enabled && (
              <div className="mt-4">
                <label className={`block text-sm font-medium ${themeClasses.text.primary} mb-1`}>Webhook URL</label>
                <input
                  type="url"
                  value={preferences.webhook_url || ''}
                  onChange={(e) => updatePreference('webhook_url', e.target.value)}
                  placeholder="https://hooks.slack.com/services/..."
                  className={`block w-full px-3 py-2 border ${themeClasses.border.primary} rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${themeClasses.bg.primary} ${themeClasses.text.primary}`}
                />
              </div>
            )}
          </div>
        </div>

        {/* Alert Filters */}
        <div className={`${themeClasses.bg.primary} shadow rounded-lg p-6 ${themeClasses.border.primary} border`}>
          <h3 className={`text-lg font-semibold ${themeClasses.text.primary} mb-4`}>Alert Filters</h3>

          <div className="space-y-4">
            <div>
              <label className={`block text-sm font-medium ${themeClasses.text.primary} mb-2`}>Alert Severities</label>
              <div className="space-y-2">
                {SEVERITY_OPTIONS.map((option) => (
                  <label key={option.value} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={preferences.alert_severities.includes(option.value)}
                      onChange={() => toggleSeverity(option.value)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600 rounded"
                    />
                    <span className={`ml-2 text-sm ${option.color}`}>{option.label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className={`block text-sm font-medium ${themeClasses.text.primary} mb-2`}>Alert Types</label>
              <div className="space-y-2">
                {ALERT_TYPE_OPTIONS.map((option) => (
                  <label key={option.value} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={preferences.alert_types.includes(option.value)}
                      onChange={() => toggleAlertType(option.value)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600 rounded"
                    />
                    <span className={`ml-2 text-sm ${themeClasses.text.primary}`}>{option.label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className={`block text-sm font-medium ${themeClasses.text.primary} mb-1`}>Cooldown (minutes)</label>
              <input
                type="number"
                min="1"
                max="1440"
                value={preferences.cooldown_minutes}
                onChange={(e) => updatePreference('cooldown_minutes', parseInt(e.target.value) || 5)}
                className={`block w-full px-3 py-2 border ${themeClasses.border.primary} rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${themeClasses.bg.primary} ${themeClasses.text.primary}`}
              />
              <p className={`text-xs ${themeClasses.text.secondary} mt-1`}>Minimum time between notifications</p>
            </div>
          </div>
        </div>

        {/* Quiet Hours */}
        <div className={`${themeClasses.bg.primary} shadow rounded-lg p-6 ${themeClasses.border.primary} border`}>
          <h3 className={`text-lg font-semibold ${themeClasses.text.primary} mb-4`}>Quiet Hours</h3>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className={`text-sm font-medium ${themeClasses.text.primary}`}>Enable Quiet Hours</label>
                <p className={`text-xs ${themeClasses.text.secondary}`}>Pause notifications during specified hours</p>
              </div>
              <button
                type="button"
                className={`${
                  preferences.quiet_hours_enabled ? 'bg-blue-600' : 'bg-gray-200'
                } relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
                onClick={() => updatePreference('quiet_hours_enabled', !preferences.quiet_hours_enabled)}
              >
                <span
                  className={`${
                    preferences.quiet_hours_enabled ? 'translate-x-5' : 'translate-x-0'
                  } pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200`}
                />
              </button>
            </div>

            {preferences.quiet_hours_enabled && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={`block text-sm font-medium ${themeClasses.text.primary} mb-1`}>Start Time</label>
                  <input
                    type="time"
                    value={preferences.quiet_hours_start}
                    onChange={(e) => updatePreference('quiet_hours_start', e.target.value)}
                    className={`block w-full px-3 py-2 border ${themeClasses.border.primary} rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${themeClasses.bg.primary} ${themeClasses.text.primary}`}
                  />
                </div>
                <div>
                  <label className={`block text-sm font-medium ${themeClasses.text.primary} mb-1`}>End Time</label>
                  <input
                    type="time"
                    value={preferences.quiet_hours_end}
                    onChange={(e) => updatePreference('quiet_hours_end', e.target.value)}
                    className={`block w-full px-3 py-2 border ${themeClasses.border.primary} rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${themeClasses.bg.primary} ${themeClasses.text.primary}`}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={savePreferences}
          disabled={saving}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? (
            <>
              <div className="animate-spin -ml-1 mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
              Saving...
            </>
          ) : (
            'Save Preferences'
          )}
        </button>
      </div>
    </div>
  );
};

export default UserNotificationSettings;
