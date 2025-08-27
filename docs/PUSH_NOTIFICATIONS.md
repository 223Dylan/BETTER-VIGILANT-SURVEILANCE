# Push Notifications Implementation

This document describes the implementation of browser push notifications for the Better Vigilant Surveillance system.

## Overview

Push notifications allow the system to send real-time security alerts to users even when the web application is closed. This implementation uses the Web Push API with service workers for reliable delivery.

## Architecture

### Frontend Components

1. **Service Worker** (`public/service-worker.js`)
   - Handles push events and displays notifications
   - Manages notification clicks and actions
   - Provides offline caching

2. **Push Notification Service** (`src/services/pushNotification.service.ts`)
   - Manages service worker registration
   - Handles permission requests
   - Manages push subscriptions
   - Sends test notifications

3. **Push Notification Settings Component** (`src/components/PushNotificationSettings.tsx`)
   - User interface for managing push notification preferences
   - Permission status display
   - Subscription management
   - Test notification functionality

### Backend Components

1. **Push Notification Service** (`src/services/push_notification_service.py`)
   - Manages user subscriptions in database
   - Sends push notifications to subscribed users
   - Handles VAPID key management

2. **Database Model** (`src/database/models/push_subscription.py`)
   - Stores push subscription data
   - Links subscriptions to users
   - Tracks subscription status

3. **API Endpoints** (`src/routers/user_notifications.py`)
   - `POST /api/users/me/push-subscription` - Subscribe to push notifications
   - `DELETE /api/users/me/push-subscription` - Unsubscribe from push notifications
   - `GET /api/users/me/push-subscription` - Get subscription status

## Setup Instructions

### 1. Generate VAPID Keys

VAPID (Voluntary Application Server Identification) keys are required for push notifications:

```bash
# Install required package
pip install pywebpush

# Generate keys
python scripts/generate_vapid_keys.py
```

This will create a `.env.example` file with your keys.

### 2. Configure Environment Variables

Add the generated keys to your environment:

```bash
# Backend (.env file)
VAPID_PUBLIC_KEY=your_public_key_here
VAPID_PRIVATE_KEY=your_private_key_here

# Frontend (.env file)
REACT_APP_VAPID_PUBLIC_KEY=your_public_key_here
```

### 3. Run Database Migration

```bash
# Run the migration to create push_subscriptions table
alembic upgrade head
```

### 4. Install Frontend Dependencies

The implementation uses standard Web APIs, so no additional packages are required.

## Usage

### For Users

1. Navigate to **Notifications** → **Push Settings** tab
2. Click **Grant Permission** to allow browser notifications
3. Click **Subscribe to Push Notifications**
4. Use **Send Test Notification** to verify setup

### For Developers

#### Sending Push Notifications

```python
from src.services.push_notification_service import push_notification_service

# Send to specific users
await push_notification_service.send_push_notification(
    db=db,
    user_ids=["user1", "user2"],
    notification_data={
        "title": "Security Alert",
        "message": "Motion detected on camera 1",
        "severity": "high",
        "camera_id": "camera1"
    }
)

# Send to all subscribers
await push_notification_service.send_push_notification_to_all(
    db=db,
    notification_data={...}
)
```

#### Frontend Integration

```typescript
import { pushNotificationService } from '../services/pushNotification.service';

// Initialize the service
await pushNotificationService.initialize();

// Subscribe to push notifications
await pushNotificationService.subscribe();

// Send test notification
await pushNotificationService.sendTestNotification();
```

## Browser Support

- **Chrome**: 42+ (Full support)
- **Firefox**: 44+ (Full support)
- **Safari**: 16+ (Limited support)
- **Edge**: 17+ (Full support)

## Security Considerations

1. **VAPID Keys**: Keep private key secure, never expose publicly
2. **HTTPS Required**: Push notifications only work over HTTPS (localhost works for development)
3. **User Consent**: Always request permission before subscribing
4. **Subscription Validation**: Verify subscription ownership on backend

## Testing

### Manual Testing

1. Start the application
2. Navigate to Push Settings tab
3. Grant notification permission
4. Subscribe to push notifications
5. Send test notification
6. Verify notification appears in browser

### Automated Testing

```bash
# Test backend service
python -m pytest tests/test_push_notifications.py

# Test frontend components
npm test -- --testPathPattern=PushNotificationSettings
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Check browser notification settings
   - Clear site data and retry
   - Ensure HTTPS in production

2. **Service Worker Not Registered**
   - Check browser console for errors
   - Verify service-worker.js exists in public folder
   - Clear browser cache

3. **VAPID Key Errors**
   - Verify keys are correctly set in environment
   - Check key format (should be base64)
   - Restart backend after key changes

4. **Notifications Not Appearing**
   - Check browser notification settings
   - Verify service worker is active
   - Check console for errors

### Debug Mode

Enable debug logging in the service worker:

```javascript
// In service-worker.js
const DEBUG = true;

if (DEBUG) {
    console.log('[Service Worker] Debug mode enabled');
}
```

## Performance Considerations

1. **Subscription Limits**: Monitor database size for subscriptions
2. **Notification Frequency**: Implement rate limiting for high-volume alerts
3. **Payload Size**: Keep notification data minimal
4. **Service Worker**: Optimize for fast startup and low memory usage

## Future Enhancements

1. **Rich Notifications**: Add images, actions, and custom layouts
2. **Notification Groups**: Group related notifications
3. **Smart Delivery**: Time-based and priority-based delivery
4. **Analytics**: Track notification engagement and delivery rates
5. **Multi-language**: Support for different languages
6. **Custom Sounds**: Personalized notification sounds

## Resources

- [Web Push Protocol](https://tools.ietf.org/html/rfc8030)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)
- [VAPID Specification](https://tools.ietf.org/html/rfc8292)
