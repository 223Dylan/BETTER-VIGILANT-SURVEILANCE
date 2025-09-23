# Advanced Notification System Setup Guide

This guide covers the advanced notification features including templates, scheduling, analytics, and webhook integrations.

## Table of Contents

1. [Overview](#overview)
2. [Database Setup](#database-setup)
3. [Environment Configuration](#environment-configuration)
4. [Advanced Features](#advanced-features)
5. [API Endpoints](#api-endpoints)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

## Overview

The advanced notification system provides enterprise-level features for managing notifications:

- **Notification Templates**: Customizable email, push, and webhook templates
- **Scheduled Notifications**: Automated reports and alerts on schedules
- **Analytics & Reporting**: Detailed metrics and performance tracking
- **Webhook Integrations**: Third-party system integrations
- **Real-time Monitoring**: Live notification tracking and debugging

## Database Setup

### 1. Run Database Migrations

```bash
# Apply the advanced notification features migration
alembic upgrade head
```

This will create the following tables:
- `notification_templates` - Template management
- `notification_schedules` - Scheduled notifications
- `notification_analytics` - Analytics data
- `notification_events` - Event tracking
- `notification_webhooks` - Webhook configurations
- `webhook_delivery_logs` - Webhook delivery tracking

### 2. Verify Database Schema

```sql
-- Check that all tables were created
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE 'notification_%';
```

## Environment Configuration

### 1. Required Environment Variables

Add these to your `.env` file:

```bash
# Advanced Notification Features
ADVANCED_NOTIFICATIONS_ENABLED=true
NOTIFICATION_SCHEDULER_ENABLED=true
NOTIFICATION_ANALYTICS_ENABLED=true
WEBHOOK_INTEGRATIONS_ENABLED=true

# Template Engine
TEMPLATE_ENGINE=jinja2
TEMPLATE_CACHE_ENABLED=true

# Analytics Configuration
ANALYTICS_RETENTION_DAYS=90
ANALYTICS_BATCH_SIZE=1000
ANALYTICS_CLEANUP_INTERVAL=24

# Webhook Configuration
WEBHOOK_MAX_RETRIES=3
WEBHOOK_RETRY_DELAY=60
WEBHOOK_TIMEOUT=30
WEBHOOK_VERIFY_SSL=true

# Scheduler Configuration
SCHEDULER_CHECK_INTERVAL=60
SCHEDULER_MAX_CONCURRENT_JOBS=10
SCHEDULER_TIMEZONE=UTC
```

### 2. Optional Configuration

```bash
# Custom SMTP for templates
TEMPLATE_SMTP_HOST=smtp.gmail.com
TEMPLATE_SMTP_PORT=587
TEMPLATE_SMTP_USERNAME=your-email@gmail.com
TEMPLATE_SMTP_PASSWORD=your-app-password
TEMPLATE_SMTP_FROM_ADDRESS=noreply@yourcompany.com

# Webhook Security
WEBHOOK_SIGNATURE_SECRET=your-webhook-secret
WEBHOOK_RATE_LIMIT=100
WEBHOOK_RATE_LIMIT_WINDOW=3600

# Analytics Storage
ANALYTICS_STORAGE_TYPE=database
ANALYTICS_BACKUP_ENABLED=true
ANALYTICS_BACKUP_SCHEDULE=daily
```

## Advanced Features

### 1. Notification Templates

#### Creating Templates

```python
# Example: Create an email template
template_data = {
    "name": "Security Alert Email",
    "description": "Email template for security alerts",
    "subject": "Security Alert: {alert_type} detected on {camera_id}",
    "body": """
    Security Alert Notification

    Alert Type: {alert_type}
    Severity: {severity}
    Camera: {camera_id}
    Timestamp: {timestamp}
    Location: {location}

    Description: {description}

    Please review this alert immediately.
    """,
    "html_body": """
    <h2>Security Alert Notification</h2>
    <p><strong>Alert Type:</strong> {alert_type}</p>
    <p><strong>Severity:</strong> {severity}</p>
    <p><strong>Camera:</strong> {camera_id}</p>
    <p><strong>Timestamp:</strong> {timestamp}</p>
    <p><strong>Location:</strong> {location}</p>
    <p><strong>Description:</strong> {description}</p>
    <p>Please review this alert immediately.</p>
    """,
    "template_type": "email",
    "variables": {
        "alert_type": "Type of security alert",
        "severity": "Alert severity level",
        "camera_id": "Camera identifier",
        "timestamp": "Alert timestamp",
        "location": "Camera location",
        "description": "Alert description"
    },
    "is_default": True,
    "is_active": True
}
```

#### Using Templates

```python
# Render a template with context
context = {
    "alert_type": "shoplifting",
    "severity": "high",
    "camera_id": "CAM-001",
    "timestamp": "2024-01-01T12:00:00Z",
    "location": "Main Entrance",
    "description": "Suspicious activity detected"
}

rendered = template.render_template(context)
```

### 2. Scheduled Notifications

#### Creating Schedules

```python
# Daily schedule
schedule_data = {
    "name": "Daily Security Report",
    "description": "Daily security report at 9 AM",
    "schedule_type": "daily",
    "schedule_config": {
        "hour": 9,
        "minute": 0
    },
    "timezone": "UTC",
    "template_id": "template-uuid",
    "alert_severities": ["critical", "high"],
    "alert_types": ["shoplifting", "suspicious_activity"],
    "camera_ids": ["CAM-1", "CAM-2"],
    "max_runs": 30
}

# Weekly schedule
weekly_schedule = {
    "name": "Weekly Summary",
    "schedule_type": "weekly",
    "schedule_config": {
        "weekday": 0,  # Monday
        "hour": 8,
        "minute": 0
    },
    "timezone": "America/New_York"
}

# Monthly schedule
monthly_schedule = {
    "name": "Monthly Report",
    "schedule_type": "monthly",
    "schedule_config": {
        "day": 1,  # 1st of month
        "hour": 10,
        "minute": 0
    }
}
```

#### Schedule Types

- **daily**: Run daily at specified time
- **weekly**: Run weekly on specified day and time
- **monthly**: Run monthly on specified day and time
- **custom**: Custom interval-based scheduling

### 3. Analytics and Reporting

#### Analytics Data

The system tracks comprehensive analytics:

```python
# Analytics metrics
analytics_data = {
    "total_sent": 1000,
    "total_failed": 50,
    "total_delivered": 950,
    "total_opened": 800,
    "total_clicked": 200,
    "open_rate": 80.0,
    "click_rate": 20.0,
    "bounce_rate": 5.0,
    "avg_delivery_time": 2.5,
    "avg_open_time": 15.2,
    "avg_click_time": 45.8,
    "channel_breakdown": {
        "email": 600,
        "push": 300,
        "webhook": 100
    }
}
```

#### Event Tracking

```python
# Event types tracked
event_types = [
    "sent",      # Notification sent
    "delivered", # Successfully delivered
    "opened",    # Email opened
    "clicked",   # Link clicked
    "failed"     # Delivery failed
]

# Channel types
channels = [
    "email",     # Email notifications
    "push",      # Push notifications
    "webhook"    # Webhook notifications
]
```

### 4. Webhook Integrations

#### Creating Webhooks

```python
# Basic webhook
webhook_data = {
    "name": "Slack Notifications",
    "description": "Send notifications to Slack",
    "url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "method": "POST",
    "auth_type": "none",
    "content_type": "application/json",
    "alert_severities": ["critical", "high"],
    "alert_types": ["shoplifting", "suspicious_activity"],
    "max_retries": 3,
    "retry_delay": 60,
    "timeout": 30,
    "verify_ssl": True
}

# Authenticated webhook
auth_webhook = {
    "name": "Custom API",
    "url": "https://api.example.com/webhook",
    "method": "POST",
    "auth_type": "bearer",
    "auth_credentials": {
        "token": "your-api-token"
    },
    "headers": {
        "X-Custom-Header": "value"
    },
    "payload_template": {
        "alert": {
            "type": "{alert_type}",
            "severity": "{severity}",
            "camera": "{camera_id}",
            "timestamp": "{timestamp}"
        }
    }
}
```

#### Authentication Types

- **none**: No authentication
- **basic**: HTTP Basic Authentication
- **bearer**: Bearer token authentication
- **custom**: Custom header authentication

## API Endpoints

### Templates

```
GET    /api/advanced/templates              # List templates
POST   /api/advanced/templates              # Create template
GET    /api/advanced/templates/{id}         # Get template
PUT    /api/advanced/templates/{id}         # Update template
DELETE /api/advanced/templates/{id}         # Delete template
```

### Schedules

```
GET    /api/advanced/schedules              # List schedules
POST   /api/advanced/schedules              # Create schedule
GET    /api/advanced/schedules/{id}         # Get schedule
PUT    /api/advanced/schedules/{id}         # Update schedule
DELETE /api/advanced/schedules/{id}         # Delete schedule
GET    /api/advanced/schedules/stats        # Schedule statistics
```

### Analytics

```
GET    /api/advanced/analytics/summary      # Analytics summary
GET    /api/advanced/analytics/hourly       # Hourly breakdown
GET    /api/advanced/analytics/channels     # Channel performance
GET    /api/advanced/analytics/timeline     # Event timeline
```

### Webhooks

```
GET    /api/advanced/webhooks               # List webhooks
POST   /api/advanced/webhooks               # Create webhook
GET    /api/advanced/webhooks/{id}          # Get webhook
PUT    /api/advanced/webhooks/{id}          # Update webhook
DELETE /api/advanced/webhooks/{id}          # Delete webhook
POST   /api/advanced/webhooks/{id}/verify   # Verify webhook
GET    /api/advanced/webhooks/{id}/logs     # Webhook logs
GET    /api/advanced/webhooks/stats         # Webhook statistics
```

## Testing

### 1. Run Advanced Tests

```bash
# Run the comprehensive test suite
python test_advanced_notifications.py
```

### 2. Manual Testing

#### Test Template Creation

```bash
curl -X POST "http://localhost:8000/api/advanced/templates" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Template",
    "subject": "Test Subject",
    "body": "Test Body",
    "template_type": "email"
  }'
```

#### Test Schedule Creation

```bash
curl -X POST "http://localhost:8000/api/advanced/schedules" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Schedule",
    "schedule_type": "daily",
    "schedule_config": {"hour": 9, "minute": 0}
  }'
```

#### Test Webhook Creation

```bash
curl -X POST "http://localhost:8000/api/advanced/webhooks" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Webhook",
    "url": "https://httpbin.org/post",
    "method": "POST"
  }'
```

### 3. WebSocket Testing

```javascript
// Test real-time notifications
const ws = new WebSocket('ws://localhost:8000/ws/notifications');

ws.onopen = () => {
    console.log('Connected to notifications WebSocket');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received notification:', data);
};
```

## Troubleshooting

### Common Issues

#### 1. Database Migration Errors

```bash
# Reset database and reapply migrations
alembic downgrade base
alembic upgrade head
```

#### 2. Template Rendering Issues

- Check template syntax
- Verify all required variables are provided
- Test template with sample data

#### 3. Schedule Not Running

- Check scheduler is enabled
- Verify timezone settings
- Check schedule configuration
- Review logs for errors

#### 4. Webhook Delivery Failures

- Verify webhook URL is accessible
- Check authentication credentials
- Review webhook logs for errors
- Test webhook manually

#### 5. Analytics Not Updating

- Check analytics service is running
- Verify database connections
- Review analytics configuration
- Check data retention settings

### Debug Commands

```bash
# Check service status
python -c "from src.services.notification_template_service import notification_template_service; print('Template service OK')"

# Test database connection
python -c "from src.database.base import get_db; next(get_db()); print('Database OK')"

# Check scheduler
python -c "from src.services.notification_scheduler_service import notification_scheduler_service; print('Scheduler OK')"

# Test webhook service
python -c "from src.services.notification_webhook_service import notification_webhook_service; print('Webhook service OK')"
```

### Log Analysis

```bash
# Check notification logs
tail -f logs/notifications.log

# Check webhook delivery logs
tail -f logs/webhook_delivery.log

# Check scheduler logs
tail -f logs/scheduler.log

# Check analytics logs
tail -f logs/analytics.log
```

### Performance Monitoring

```sql
-- Check notification performance
SELECT
    channel,
    COUNT(*) as total_sent,
    AVG(delivery_time) as avg_delivery_time,
    COUNT(CASE WHEN success = true THEN 1 END) as successful
FROM notification_events
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY channel;

-- Check webhook performance
SELECT
    webhook_id,
    COUNT(*) as total_attempts,
    COUNT(CASE WHEN success = true THEN 1 END) as successful,
    AVG(duration) as avg_duration
FROM webhook_delivery_logs
WHERE request_time > NOW() - INTERVAL '24 hours'
GROUP BY webhook_id;
```

## Support

For additional support:

1. Check the logs for detailed error messages
2. Review the API documentation
3. Test individual components
4. Verify configuration settings
5. Check database connectivity

The advanced notification system provides enterprise-level features for comprehensive notification management and monitoring.
