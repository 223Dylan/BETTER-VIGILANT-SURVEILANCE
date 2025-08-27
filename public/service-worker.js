// Service Worker for Better Vigilant Surveillance System
const CACHE_NAME = 'surveillance-v1';
const NOTIFICATION_ICON = '/favicon.ico';

// Install event - cache essential resources
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll([
        '/',
        '/static/js/bundle.js',
        '/static/css/main.css',
        '/favicon.ico'
      ]);
    })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Push event - handle incoming push notifications
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push received:', event);

  if (event.data) {
    try {
      const notificationData = event.data.json();
      const options = {
        body: notificationData.message || 'Security alert detected',
        icon: NOTIFICATION_ICON,
        badge: NOTIFICATION_ICON,
        tag: notificationData.alert_id || 'security-alert',
        data: notificationData,
        requireInteraction: notificationData.severity === 'critical',
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
        vibrate: [200, 100, 200], // Vibration pattern for mobile
        silent: false
      };

      // Set different colors based on severity
      if (notificationData.severity === 'critical') {
        options.icon = '/favicon.ico'; // You can add different icons for different severities
        options.requireInteraction = true;
      }

      event.waitUntil(
        self.registration.showNotification(
          notificationData.title || 'Security Alert',
          options
        )
      );
    } catch (error) {
      console.error('[Service Worker] Error parsing push data:', error);
      // Fallback notification
      event.waitUntil(
        self.registration.showNotification('Security Alert', {
          body: 'A security alert has been detected',
          icon: NOTIFICATION_ICON,
          tag: 'security-alert'
        })
      );
    }
  }
});

// Notification click event - handle user interaction
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notification clicked:', event);

  event.notification.close();

  if (event.action === 'dismiss') {
    // User dismissed the notification
    return;
  }

  // Default action or 'view' action - open the app
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // Check if app is already open
      for (const client of clientList) {
        if (client.url.includes('/notifications') && 'focus' in client) {
          client.focus();
          return;
        }
      }

      // If app is open but not on notifications page, navigate there
      for (const client of clientList) {
        if (client.url.includes(window.location.origin) && 'navigate' in client) {
          client.navigate('/notifications');
          client.focus();
          return;
        }
      }

      // If app is not open, open it
      if (clients.openWindow) {
        clients.openWindow('/notifications');
      }
    })
  );
});

// Background sync for offline notifications
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] Background sync:', event);

  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

async function doBackgroundSync() {
  try {
    // Check for any pending notifications that need to be sent
    const pendingNotifications = await getPendingNotifications();

    for (const notification of pendingNotifications) {
      await sendNotification(notification);
    }
  } catch (error) {
    console.error('[Service Worker] Background sync failed:', error);
  }
}

async function getPendingNotifications() {
  // This would typically check IndexedDB or other storage
  // For now, return empty array
  return [];
}

async function sendNotification(notification) {
  // Implementation for sending pending notifications
  // This would typically make API calls to your backend
  console.log('[Service Worker] Sending pending notification:', notification);
}

// Message event - handle messages from main thread
self.addEventListener('message', (event) => {
  console.log('[Service Worker] Message received:', event);

  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Fetch event - serve cached resources when offline
self.addEventListener('fetch', (event) => {
  // Only handle GET requests
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request).then((response) => {
      // Return cached version or fetch from network
      return response || fetch(event.request);
    }).catch(() => {
      // If both cache and network fail, return offline page
      if (event.request.destination === 'document') {
        return caches.match('/');
      }
    })
  );
});
