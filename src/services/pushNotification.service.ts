import { notificationService } from './notification.service';

export interface PushSubscriptionData {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
}

export interface PushNotificationPayload {
  title: string;
  message: string;
  alert_id?: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  camera_id?: string;
  alert_type?: string;
  confidence?: number;
  timestamp?: string;
  data?: any;
}

class PushNotificationService {
  private swRegistration: ServiceWorkerRegistration | null = null;
  private isSupported: boolean = false;
  private isSubscribed: boolean = false;

  constructor() {
    this.checkSupport();
  }

  /**
   * Check if push notifications are supported
   */
  private checkSupport(): void {
    this.isSupported = 'serviceWorker' in navigator && 'PushManager' in window;
    console.log('[PushService] Push notifications supported:', this.isSupported);
  }

  /**
   * Initialize the push notification service
   */
  async initialize(): Promise<boolean> {
    if (!this.isSupported) {
      console.warn('[PushService] Push notifications not supported');
      return false;
    }

    try {
      // Register service worker
      this.swRegistration = await navigator.serviceWorker.register('/service-worker.js');
      console.log('[PushService] Service Worker registered:', this.swRegistration);

      // Check if already subscribed
      this.isSubscribed = await this.checkSubscription();

      // Listen for service worker updates
      this.swRegistration.addEventListener('updatefound', () => {
        const newWorker = this.swRegistration!.installing;
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New service worker available
              this.showUpdateNotification();
            }
          });
        }
      });

      return true;
    } catch (error) {
      console.error('[PushService] Failed to initialize:', error);
      return false;
    }
  }

  /**
   * Request notification permission from user
   */
  async requestPermission(): Promise<NotificationPermission> {
    if (!this.isSupported) {
      throw new Error('Push notifications not supported');
    }

    try {
      const permission = await Notification.requestPermission();
      console.log('[PushService] Permission result:', permission);
      return permission;
    } catch (error) {
      console.error('[PushService] Permission request failed:', error);
      throw error;
    }
  }

  /**
   * Check current notification permission
   */
  getPermissionStatus(): NotificationPermission {
    return Notification.permission;
  }

  /**
   * Subscribe to push notifications
   */
  async subscribe(): Promise<PushSubscriptionData | null> {
    if (!this.isSupported || !this.swRegistration) {
      throw new Error('Push notifications not supported or not initialized');
    }

    if (this.getPermissionStatus() !== 'granted') {
      throw new Error('Notification permission not granted');
    }

    try {
      // Get push subscription
      const subscription = await this.swRegistration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(this.getVapidPublicKey())
      });

      this.isSubscribed = true;
      console.log('[PushService] Subscribed to push notifications:', subscription);

      // Send subscription to backend
      await this.sendSubscriptionToBackend(subscription);

      return {
        endpoint: subscription.endpoint,
        keys: {
          p256dh: this.arrayBufferToBase64(subscription.getKey('p256dh')!),
          auth: this.arrayBufferToBase64(subscription.getKey('auth')!)
        }
      };
    } catch (error) {
      console.error('[PushService] Subscription failed:', error);
      this.isSubscribed = false;
      throw error;
    }
  }

  /**
   * Unsubscribe from push notifications
   */
  async unsubscribe(): Promise<boolean> {
    if (!this.swRegistration) {
      return false;
    }

    try {
      const subscription = await this.swRegistration.pushManager.getSubscription();
      if (subscription) {
        await subscription.unsubscribe();
        this.isSubscribed = false;
        console.log('[PushService] Unsubscribed from push notifications');

        // Remove subscription from backend
        await this.removeSubscriptionFromBackend();
        return true;
      }
      return false;
    } catch (error) {
      console.error('[PushService] Unsubscribe failed:', error);
      return false;
    }
  }

  /**
   * Check if currently subscribed
   */
  async checkSubscription(): Promise<boolean> {
    if (!this.swRegistration) {
      return false;
    }

    try {
      const subscription = await this.swRegistration.pushManager.getSubscription();
      this.isSubscribed = !!subscription;
      return this.isSubscribed;
    } catch (error) {
      console.error('[PushService] Check subscription failed:', error);
      this.isSubscribed = false;
      return false;
    }
  }

  /**
   * Send test notification
   */
  async sendTestNotification(): Promise<void> {
    if (!this.swRegistration) {
      throw new Error('Service worker not registered');
    }

    const testPayload: PushNotificationPayload = {
      title: 'Test Notification',
      message: 'This is a test push notification from your surveillance system',
      severity: 'medium',
      timestamp: new Date().toISOString()
    };

    await this.swRegistration.showNotification(testPayload.title, {
      body: testPayload.message,
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      tag: 'test-notification',
      data: testPayload
    });
  }

  /**
   * Show notification manually (for testing)
   */
  async showNotification(payload: PushNotificationPayload): Promise<void> {
    if (!this.swRegistration) {
      throw new Error('Service worker not registered');
    }

    const options: NotificationOptions = {
      body: payload.message,
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      tag: payload.alert_id || 'security-alert',
      data: payload,
      requireInteraction: payload.severity === 'critical',
      actions: [
        {
          action: 'view',
          title: 'View Details',
          icon: '/favicon.ico'
        },
        {
          action: 'dismiss',
          title: 'Dismiss',
          icon: '/favicon.ico'
        }
      ],
      vibrate: [200, 100, 200],
      silent: false
    };

    await this.swRegistration.showNotification(payload.title, options);
  }

  /**
   * Send subscription data to backend
   */
  private async sendSubscriptionToBackend(subscription: PushSubscription): Promise<void> {
    try {
      const response = await fetch('/api/users/me/push-subscription', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}`
        },
        body: JSON.stringify({
          endpoint: subscription.endpoint,
          keys: {
            p256dh: this.arrayBufferToBase64(subscription.getKey('p256dh')!),
            auth: this.arrayBufferToBase64(subscription.getKey('auth')!)
          }
        })
      });

      if (!response.ok) {
        throw new Error('Failed to send subscription to backend');
      }

      console.log('[PushService] Subscription sent to backend');
    } catch (error) {
      console.error('[PushService] Failed to send subscription to backend:', error);
      throw error;
    }
  }

  /**
   * Remove subscription from backend
   */
  private async removeSubscriptionFromBackend(): Promise<void> {
    try {
      const response = await fetch('/api/users/me/push-subscription', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to remove subscription from backend');
      }

      console.log('[PushService] Subscription removed from backend');
    } catch (error) {
      console.error('[PushService] Failed to remove subscription from backend:', error);
      throw error;
    }
  }

  /**
   * Get VAPID public key (you'll need to set this)
   */
  private getVapidPublicKey(): string {
    // This should come from your environment variables or backend
    // For now, return a placeholder - you'll need to generate VAPID keys
    return process.env.REACT_APP_VAPID_PUBLIC_KEY || 'YOUR_VAPID_PUBLIC_KEY_HERE';
  }

  /**
   * Convert VAPID key from base64 to Uint8Array
   */
  private urlBase64ToUint8Array(base64String: string): Uint8Array {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  /**
   * Convert ArrayBuffer to base64
   */
  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }

  /**
   * Get auth token from storage
   */
  private getAuthToken(): string {
    // This should get the token from your auth service
    // For now, return empty string - you'll need to implement this
    return localStorage.getItem('authToken') || '';
  }

  /**
   * Show update notification when new service worker is available
   */
  private showUpdateNotification(): void {
    if (this.swRegistration) {
      this.swRegistration.showNotification('App Update Available', {
        body: 'A new version is available. Click to update.',
        icon: '/favicon.ico',
        tag: 'update-notification',
        requireInteraction: true,
        actions: [
          {
            action: 'update',
            title: 'Update Now',
            icon: '/favicon.ico'
          }
        ]
      });
    }
  }

  /**
   * Get service worker registration
   */
  getServiceWorkerRegistration(): ServiceWorkerRegistration | null {
    return this.swRegistration;
  }

  /**
   * Check if push notifications are supported
   */
  isPushSupported(): boolean {
    return this.isSupported;
  }

  /**
   * Check if currently subscribed
   */
  getSubscriptionStatus(): boolean {
    return this.isSubscribed;
  }
}

// Export singleton instance
export const pushNotificationService = new PushNotificationService();
export default pushNotificationService;
