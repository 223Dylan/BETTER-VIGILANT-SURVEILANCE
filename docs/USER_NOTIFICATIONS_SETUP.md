# User Notification System Setup Guide

## Overview

The user notification system allows individual users to receive personalized alerts based on their preferences. Users can configure notification channels, alert filters, quiet hours, and other settings.

## Features

- **Multiple Notification Channels**: Email, WebSocket (real-time), and webhook notifications
- **Smart Filtering**: Filter by alert severity, type, and assigned cameras
- **Quiet Hours**: Set specific time ranges to pause notifications
- **Cooldown System**: Prevent notification spam with configurable delays
- **User-Specific Settings**: Each user can configure their own preferences
- **Test Notifications**: Users can test their settings

## Setup Instructions

### 1. Database Migration

Run the database migration to create the notification preferences table:

```bash
# Make sure your database is running
docker-compose up -d postgres

# Run the migration
python -m alembic upgrade head
```

### 2. Environment Configuration

Add SMTP settings to your `.env` file for email notifications:

```bash
# Email notification settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_ADDRESS=alerts@yourcompany.com
SMTP_USE_TLS=true

# Optional: Enable/disable email notifications globally
EMAIL_NOTIFICATIONS_ENABLED=true
```

#### Gmail Setup (Example)

1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
3. Use this app password in your `.env` file

### 3. API Endpoints

The following endpoints are available for managing user notifications:

- `GET /api/users/me/notification-preferences` - Get current user's preferences
- `PUT /api/users/me/notification-preferences` - Update preferences
- `POST /api/users/me/test-notification` - Send test notification
- `GET /api/admin/notification-stats` - System-wide statistics (admin only)

### 4. Frontend Integration

Include the notification settings component in your user settings page:

```tsx
import UserNotificationSettings from '../components/UserNotificationSettings';

// In your user settings page
<UserNotificationSettings onSave={(prefs) => console.log('Saved:', prefs)} />
```

## Configuration Options

### Notification Channels

- **Email**: Sends HTML emails with alert details
- **Push**: Real-time browser notifications via WebSocket
- **Webhook**: POST requests to external URLs (Slack, Discord, etc.)

### Alert Filtering

- **Severities**: critical, high, medium, low
- **Types**: shoplifting, suspicious_activity, object_detection, motion, system_alert
- **Assigned Cameras**: Limit notifications to specific cameras (empty = all cameras)

### Timing Controls

- **Cooldown**: Minimum minutes between notifications (1-1440)
- **Quiet Hours**: Time range to pause notifications (supports overnight ranges)

## Database Schema

```sql
CREATE TABLE user_notification_preferences (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR UNIQUE REFERENCES users(id),
    email_enabled BOOLEAN DEFAULT true,
    push_enabled BOOLEAN DEFAULT true,
    webhook_enabled BOOLEAN DEFAULT false,
    webhook_url VARCHAR(500),
    alert_severities JSON DEFAULT '["critical", "high", "medium"]',
    alert_types JSON DEFAULT '["shoplifting", "suspicious_activity", "system_alert"]',
    assigned_cameras JSON DEFAULT '[]',
    cooldown_minutes INTEGER DEFAULT 5,
    quiet_hours_enabled BOOLEAN DEFAULT false,
    quiet_hours_start VARCHAR(5) DEFAULT '22:00',
    quiet_hours_end VARCHAR(5) DEFAULT '08:00',
    custom_filters JSON DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

## Default Preferences

New users automatically get these default preferences:

```json
{
  "email_enabled": true,
  "push_enabled": true,
  "webhook_enabled": false,
  "alert_severities": ["critical", "high", "medium"],
  "alert_types": ["shoplifting", "suspicious_activity", "system_alert"],
  "assigned_cameras": [],
  "cooldown_minutes": 5,
  "quiet_hours_enabled": false,
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00"
}
```

## Integration with Alert System

The notification system integrates with the existing alert manager:

1. When an alert is created, the alert manager calls the notification service
2. The service filters eligible users based on their preferences
3. Notifications are sent through enabled channels for each user
4. Cooldowns and quiet hours are respected
5. Delivery statistics are tracked

## Webhook Integration Examples

### Slack Webhook

```json
{
  "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
}
```

### Discord Webhook

```json
{
  "webhook_url": "https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK"
}
```

### Custom Webhook

The webhook payload includes:

```json
{
  "type": "security_alert",
  "user": {
    "id": "user-id",
    "username": "username",
    "email": "user@example.com"
  },
  "alert": {
    "alert_id": "alert-id",
    "camera_id": "camera-1",
    "type": "shoplifting",
    "severity": "high",
    "message": "Alert description",
    "confidence": 0.85,
    "timestamp": "2024-01-01T12:00:00Z"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Troubleshooting

### Email Notifications Not Working

1. Check SMTP configuration in `.env`
2. Verify Gmail app password is correct
3. Check server logs for SMTP errors
4. Test with a simple email client first

### WebSocket Notifications Not Received

1. Ensure user is connected to WebSocket
2. Check browser console for WebSocket errors
3. Verify user has push notifications enabled

### No Notifications Received

1. Check user's notification preferences
2. Verify alert matches user's severity/type filters
3. Check if user is in quiet hours
4. Verify cooldown period hasn't blocked notifications

## Monitoring

### Admin Statistics

Administrators can view system-wide notification statistics:

```bash
GET /api/admin/notification-stats?days=7
```

Returns:
- Total notifications sent
- Success/failure rates
- User engagement metrics
- Alert type breakdown

### Logs

Monitor notification delivery in the application logs:

```bash
# Search for notification-related logs
grep "NOTIFICATIONS\|EMAIL\|WEBHOOK" logs/app.log
```

## Performance Considerations

- Email sending is asynchronous to avoid blocking alert processing
- Webhook requests have a 10-second timeout
- Notification history is limited to 1000 recent entries
- Database queries are optimized with proper indexing

## Security

- User notification preferences are isolated per user
- Webhook URLs are validated before sending
- Email content is sanitized
- Admin endpoints require proper permissions
