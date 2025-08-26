import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { notificationService, NotificationPreferences, NotificationHistoryItem } from '../services/notification.service';

interface NotificationContextType {
  preferences: NotificationPreferences | null;
  unreadCount: number;
  notifications: NotificationHistoryItem[];
  loading: boolean;
  error: string | null;
  updatePreferences: (preferences: NotificationPreferences) => Promise<void>;
  sendTestNotification: () => Promise<void>;
  markAsRead: (notificationId: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  clearAll: () => void;
  requestPermission: () => Promise<boolean>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<NotificationHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPreferences();
    loadNotifications();
    requestNotificationPermission();
  }, []);

  const loadPreferences = async () => {
    try {
      setLoading(true);
      const prefs = await notificationService.getNotificationPreferences();
      setPreferences(prefs);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load notification preferences');
    } finally {
      setLoading(false);
    }
  };

  const loadNotifications = async () => {
    try {
      const history = await notificationService.getNotificationHistory(20);
      setNotifications(history.notifications);

      // Calculate unread count based on status, not time
      const unread = history.notifications.filter(n => n.status === 'pending').length;
      setUnreadCount(unread);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    }
  };

  const updatePreferences = async (newPreferences: NotificationPreferences) => {
    try {
      setLoading(true);
      const updated = await notificationService.updateNotificationPreferences(newPreferences);
      setPreferences(updated);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update preferences');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const sendTestNotification = async () => {
    try {
      setLoading(true);
      await notificationService.sendTestNotification();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send test notification');
      throw err;
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
      // Update unread count
      setUnreadCount(prev => Math.max(0, prev - 1));
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
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all notifications as read:', err);
    }
  };

  const clearAll = () => {
    setNotifications([]);
    setUnreadCount(0);
  };

  const requestNotificationPermission = async (): Promise<boolean> => {
    try {
      const granted = await notificationService.requestNotificationPermission();
      return granted;
    } catch (err) {
      console.error('Failed to request notification permission:', err);
      return false;
    }
  };

  const value: NotificationContextType = {
    preferences,
    unreadCount,
    notifications,
    loading,
    error,
    updatePreferences,
    sendTestNotification,
    markAsRead,
    markAllAsRead,
    clearAll,
    requestPermission: requestNotificationPermission,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotifications = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};
