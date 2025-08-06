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
  type: 'email' | 'push' | 'webhook';
  title: string;
  message: string;
  timestamp: string;
  status: 'sent' | 'failed' | 'pending';
  alert_id?: string;
  camera_id?: string;
  severity?: string;
}

export interface NotificationStats {
  total_sent: number;
  total_failed: number;
  email_sent: number;
  push_sent: number;
  webhook_sent: number;
  last_24h: number;
  last_7d: number;
  last_30d: number;
}

class NotificationService {
  private baseUrl = '/api';

  async getNotificationPreferences(): Promise<NotificationPreferences> {
    try {
      const response = await fetch(`${this.baseUrl}/users/me/notification-preferences`, {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
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
          'Authorization': `Bearer ${authService.getToken()}`
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
          'Authorization': `Bearer ${authService.getToken()}`
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

      const response = await fetch(`${this.baseUrl}/users/me/notification-history?${params}`, {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch notification history');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching notification history:', error);
      // Return empty array for demo
      return { notifications: [] };
    }
  }

  async getNotificationStats(): Promise<NotificationStats> {
    try {
      const response = await fetch(`${this.baseUrl}/users/me/notification-stats`, {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
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
        total_sent: 0,
        total_failed: 0,
        email_sent: 0,
        push_sent: 0,
        webhook_sent: 0,
        last_24h: 0,
        last_7d: 0,
        last_30d: 0
      };
    }
  }

  // WebSocket connection for real-time notifications
  createNotificationWebSocket(): WebSocket | null {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/notifications`;

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
