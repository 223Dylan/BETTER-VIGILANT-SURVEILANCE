import { authService } from './auth.service';

export interface NotificationPreferences {
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

export interface NotificationHistoryItem {
  id: string;
  user_id: string;
  alert_id?: string;
  notification_type: 'email' | 'push' | 'webhook' | 'alert_broadcast';
  title?: string;
  message?: string;
  status: 'pending' | 'sent' | 'delivered' | 'failed' | 'opened' | 'clicked';
  sent_at?: string;
  delivered_at?: string;
  opened_at?: string;
  clicked_at?: string;
  channel_data?: Record<string, any>;
  error_message?: string;
  retry_count: string;
  delivery_time?: string;
  processing_time?: string;
  created_at: string;
  updated_at: string;
}

export interface NotificationStats {
  total_notifications: number;
  successful_notifications: number;
  failed_notifications: number;
  success_rate: number;
  status_breakdown: Record<string, number>;
  type_breakdown: Record<string, number>;
  period_days: number;
  generated_at: string;
}

class NotificationService {
  private baseUrl = '/api';

  async getNotificationPreferences(): Promise<NotificationPreferences> {
    try {
      const token = authService.getAuthToken();
      if (!token) {
        console.warn('No authentication token available for notification preferences');
        // Return default preferences instead of throwing error
        return {
          email_enabled: true,
          push_enabled: true,
          webhook_enabled: false,
          webhook_url: undefined,
          alert_severities: ['critical', 'high', 'medium'],
          alert_types: ['shoplifting', 'suspicious_activity', 'system_alert'],
          assigned_cameras: [],
          cooldown_minutes: 5,
          quiet_hours_enabled: false,
          quiet_hours_start: '22:00',
          quiet_hours_end: '08:00',
          custom_filters: {},
        };
      }

      const response = await fetch(`${this.baseUrl}/users/me/notification-preferences`, {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch notification preferences');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching notification preferences:', error);
      // Return default preferences
      return {
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
      };
    }
  }

  async updateNotificationPreferences(preferences: NotificationPreferences): Promise<NotificationPreferences> {
    try {
      const response = await fetch(`${this.baseUrl}/users/me/notification-preferences`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getAuthToken()}`
        },
        body: JSON.stringify(preferences)
      });

      if (!response.ok) {
        throw new Error('Failed to update notification preferences');
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating notification preferences:', error);
      throw error;
    }
  }

  async sendTestNotification(): Promise<{ success: boolean; message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/users/me/test-notification`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getAuthToken()}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to send test notification');
      }

      return await response.json();
    } catch (error) {
      console.error('Error sending test notification:', error);
      throw error;
    }
  }

  async getNotificationHistory(limit: number = 50, filters?: {
    type?: string;
    status?: string;
    dateRange?: string;
  }): Promise<{ notifications: NotificationHistoryItem[] }> {
    try {
      const params = new URLSearchParams();
      params.append('limit', limit.toString());
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.dateRange) params.append('date_range', filters.dateRange);

      const token = authService.getAuthToken();
      if (!token) {
        console.warn('No authentication token available for notification history');
        return { notifications: [] };
      }

      const response = await fetch(`${this.baseUrl}/users/me/notification-history?${params}`, {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch notification history');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching notification history:', error);
      // Return empty array when API fails
      return { notifications: [] };
    }
  }

  async getNotificationStats(): Promise<NotificationStats> {
    try {
      const response = await fetch(`${this.baseUrl}/users/me/notification-stats`, {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${authService.getAuthToken()}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch notification stats');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching notification stats:', error);
      // Return mock stats for demo
      return {
        total_notifications: 0,
        successful_notifications: 0,
        failed_notifications: 0,
        success_rate: 0.0,
        status_breakdown: {},
        type_breakdown: {},
        period_days: 7,
        generated_at: new Date().toISOString()
      };
    }
  }

  // WebSocket connection for real-time notifications
  createNotificationWebSocket(): WebSocket | null {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = process.env.NODE_ENV === 'development' ? 'localhost:8001' : window.location.host;
      const wsUrl = `${protocol}//${wsHost}/ws/alerts`;

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('Notification WebSocket connected');
      };

      ws.onclose = () => {
        console.log('Notification WebSocket disconnected');
      };

      ws.onerror = (error) => {
        console.error('Notification WebSocket error:', error);
      };

      return ws;
    } catch (error) {
      console.error('Failed to create notification WebSocket:', error);
      return null;
    }
  }

  // Browser notification permission request
  async requestNotificationPermission(): Promise<boolean> {
    if (!('Notification' in window)) {
      console.warn('This browser does not support notifications');
      return false;
    }

    if (Notification.permission === 'granted') {
      return true;
    }

    if (Notification.permission === 'denied') {
      console.warn('Notification permission denied');
      return false;
    }

    try {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return false;
    }
  }

  // Update notification status
  async updateNotificationStatus(
    notificationId: string,
    status: string,
    channelData?: Record<string, any>
  ): Promise<{ message: string; notification: any }> {
    try {
      const response = await fetch(`${this.baseUrl}/users/me/notifications/${notificationId}/status`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getAuthToken()}`
        },
        body: JSON.stringify({
          status,
          channel_data: channelData
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update notification status');
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating notification status:', error);
      throw error;
    }
  }

  // Mark all notifications as read
  async markAllNotificationsAsRead(): Promise<{ message: string; updated_count: number }> {
    try {
      const response = await fetch(`${this.baseUrl}/users/me/notifications/mark-all-read`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getAuthToken()}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to mark notifications as read');
      }

      return await response.json();
    } catch (error) {
      console.error('Error marking notifications as read:', error);
      throw error;
    }
  }

  // Show browser notification
  showBrowserNotification(title: string, options?: NotificationOptions): void {
    if (!('Notification' in window) || Notification.permission !== 'granted') {
      return;
    }

    try {
      new Notification(title, {
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        ...options
      });
    } catch (error) {
      console.error('Error showing browser notification:', error);
    }
  }
}

export const notificationService = new NotificationService();
