# API Reference Guide

This comprehensive guide documents all available API endpoints for the Shoplifting Detection System.

## Table of Contents

1. [Base Information](#base-information)
2. [Authentication](#authentication)
3. [Camera Management](#camera-management)
4. [Alert System](#alert-system)
5. [User Management](#user-management)
6. [Metrics & Analytics](#metrics--analytics)
7. [Video Streaming](#video-streaming)
8. [WebSocket Connections](#websocket-connections)
9. [Error Handling](#error-handling)
10. [Security Considerations](#security-considerations)

## Base Information

### Base URL
```
http://localhost:8001
```

### Content Types
- **Request**: `application/json`
- **Response**: `application/json`
- **File Upload**: `multipart/form-data`
- **Video Stream**: `application/octet-stream`

### API Versioning
Current API version: `v1` (prefix: `/api/` where applicable)

### Rate Limiting
- Default: 100 requests per minute per IP
- Authenticated users: 1000 requests per minute
- Video streaming: No rate limit

## Authentication

All authenticated endpoints require a JWT token in the Authorization header.

### Headers
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Authentication Endpoints

#### Login
```http
POST /api/auth/login
```

**Request Body:**
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `500 Internal Server Error`: Server error

#### Refresh Token
```http
POST /api/auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

#### Logout
```http
POST /api/auth/logout
```

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

## Camera Management

All camera endpoints require authentication.

### Get Available Cameras
```http
GET /cameras/available
```

**Response:**
```json
[
  {
    "id": "store-entrance",
    "name": "Store Entrance",
    "description": "Main entrance camera",
    "enabled": true,
    "source": "rtsp://192.168.1.100/stream",
    "source_type": "rtsp",
    "fps": 30,
    "resolution_width": 1920,
    "resolution_height": 1080,
    "detection_enabled": true,
    "detection_sensitivity": 0.6,
    "recording_enabled": false,
    "location": "Entrance",
    "zone": "Zone A",
    "status": "active",
    "created_at": "2023-01-01T00:00:00Z",
    "last_online": "2023-01-01T12:00:00Z"
  }
]
```

### Get Camera Status
```http
GET /cameras/status
```

**Response:**
```json
{
  "store-entrance": {
    "status": "active",
    "fps": 29.5,
    "resolution": "1920x1080",
    "last_frame_time": 1609459200.123,
    "error": null
  },
  "store-aisle-1": {
    "status": "failed",
    "error": "Connection timeout"
  }
}
```

### Create Camera
```http
POST /cameras/
```

**Request Body:**
```json
{
  "id": "new-camera-01",
  "name": "New Camera",
  "description": "Camera description",
  "source": "rtsp://192.168.1.101/stream",
  "source_type": "rtsp",
  "fps": 30,
  "resolution": {
    "width": 1920,
    "height": 1080
  },
  "detection_enabled": true,
  "detection_sensitivity": 0.6,
  "recording_enabled": false,
  "location": "Aisle 1",
  "zone": "Zone B"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Camera created successfully",
  "camera": {
    "id": "new-camera-01",
    "name": "New Camera",
    // ... full camera object
  }
}
```

**Validation Rules:**
- `id`: Required, unique string
- `name`: Required string
- `source`: Required string (URL for RTSP/HTTP, integer for webcam)
- `source_type`: Required, one of: `webcam`, `rtsp`, `file`
- `fps`: Optional integer, default: 15
- `detection_sensitivity`: Optional float (0.0-1.0), default: 0.5

### Start Camera
```http
POST /cameras/{camera_id}/start
```

**Response:**
```json
{
  "status": "success",
  "message": "Camera 'store-entrance' started."
}
```

### Stop Camera
```http
POST /cameras/{camera_id}/stop
```

**Response:**
```json
{
  "status": "success",
  "message": "Camera 'store-entrance' stopped."
}
```

### Update Camera
```http
PUT /cameras/{camera_id}
```

**Request Body:**
```json
{
  "name": "Updated Camera Name",
  "detection_sensitivity": 0.7,
  "brightness": 1.2
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Camera 'store-entrance' updated"
}
```

### Update Camera Brightness
```http
PUT /cameras/{camera_id}/brightness
```

**Request Body:**
```json
{
  "brightness": 1.5
}
```

**Brightness Range:** 0.0 - 2.0 (1.0 = normal)

### Delete Camera
```http
DELETE /cameras/{camera_id}
```

**Response:**
```json
{
  "status": "success",
  "message": "Camera 'store-entrance' deleted"
}
```

### Upload Video File
```http
POST /cameras/upload-video
```

**Content-Type:** `multipart/form-data`

**Form Data:**
- `file`: Video file (.mp4, .avi, .mov, .mkv, .webm, .flv, .wmv)

**Response:**
```json
{
  "status": "success",
  "message": "Video file uploaded successfully",
  "file_path": "uploads/videos/abc123_video.mp4",
  "original_filename": "video.mp4",
  "size_bytes": 15728640
}
```

## Alert System

Alert management endpoints with real-time capabilities.

### Get Active Alerts
```http
GET /alerts/active?severity=critical&camera_id=store-entrance&limit=50
```

**Query Parameters:**
- `severity`: Filter by severity (critical,high,medium,low)
- `camera_id`: Filter by camera ID
- `limit`: Maximum alerts to return (default: 100)

**Response:**
```json
{
  "success": true,
  "message": "Retrieved 5 active alerts",
  "data": {
    "alerts": [
      {
        "id": "alert_001",
        "camera_id": "store-entrance",
        "type": "shoplifting_detection",
        "severity": "high",
        "confidence": 0.87,
        "timestamp": "2023-01-01T12:00:00Z",
        "status": "active",
        "message": "High confidence shoplifting behavior detected",
        "location": "Entrance",
        "zone": "Zone A"
      }
    ],
    "total": 5
  }
}
```

### Get Alert History
```http
GET /alerts/history?limit=100&severity=high&camera_id=store-entrance
```

**Response:**
```json
{
  "success": true,
  "message": "Retrieved 25 historical alerts",
  "data": {
    "alerts": [
      {
        "id": "alert_002",
        "camera_id": "store-entrance",
        "type": "shoplifting_detection",
        "severity": "medium",
        "confidence": 0.65,
        "timestamp": "2023-01-01T11:30:00Z",
        "status": "resolved",
        "resolved_by": "admin",
        "resolved_at": "2023-01-01T11:45:00Z",
        "notes": "False positive - customer looking for item"
      }
    ],
    "total": 25
  }
}
```

### Get Alert Statistics
```http
GET /alerts/stats?days=7
```

**Response:**
```json
{
  "success": true,
  "message": "Retrieved statistics for 7 days",
  "data": {
    "total_alerts": 156,
    "active_alerts": 8,
    "resolved_alerts": 148,
    "by_severity": {
      "critical": 12,
      "high": 45,
      "medium": 78,
      "low": 21
    },
    "by_camera": {
      "store-entrance": 89,
      "store-aisle-1": 34,
      "checkout-area": 33
    },
    "average_resolution_time_minutes": 15.5
  }
}
```

### Search Alerts
```http
POST /alerts/search?limit=100
```

**Request Body:**
```json
{
  "severity": ["high", "critical"],
  "status": ["active", "acknowledged"],
  "type": ["shoplifting_detection"],
  "cameraId": ["store-entrance"],
  "confidenceMin": 0.7,
  "confidenceMax": 1.0,
  "dateRange": {
    "start": "2023-01-01T00:00:00Z",
    "end": "2023-01-07T23:59:59Z"
  }
}
```

### Acknowledge Alert
```http
POST /alerts/{alert_id}/acknowledge
```

**Request Body:**
```json
{
  "userId": "admin",
  "notes": "Investigating this incident"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Alert alert_001 acknowledged successfully",
  "data": {
    "alert_id": "alert_001",
    "acknowledged_by": "admin"
  }
}
```

### Resolve Alert
```http
POST /alerts/{alert_id}/resolve
```

**Request Body:**
```json
{
  "userId": "admin",
  "notes": "False positive - customer behavior"
}
```

### Get Alert Details
```http
GET /alerts/{alert_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Alert alert_001 details retrieved",
  "data": {
    "id": "alert_001",
    "camera_id": "store-entrance",
    "type": "shoplifting_detection",
    "severity": "high",
    "confidence": 0.87,
    "timestamp": "2023-01-01T12:00:00Z",
    "status": "acknowledged",
    "acknowledged_by": "admin",
    "acknowledged_at": "2023-01-01T12:05:00Z",
    "sequence_stats": {
      "mean": 0.82,
      "std": 0.15,
      "frames": 160
    },
    "location": "Entrance",
    "zone": "Zone A"
  }
}
```

### Bulk Acknowledge Alerts
```http
POST /alerts/bulk-acknowledge
```

**Request Body:**
```json
["alert_001", "alert_002", "alert_003"]
```

**Action Body:**
```json
{
  "userId": "admin",
  "notes": "Bulk acknowledgment"
}
```

### Dismiss Alert
```http
DELETE /alerts/{alert_id}
```

**Request Body:**
```json
{
  "userId": "admin",
  "notes": "Not relevant"
}
```

### Bulk Actions (Admin Only)
```http
POST /alerts/bulk-action
```

**Request Body:**
```json
{
  "alert_ids": ["alert_001", "alert_002"],
  "action": "acknowledge",
  "user_id": "admin",
  "notes": "Bulk processing"
}
```

**Actions:** `acknowledge`, `resolve`

### Create Sample Alerts (Testing)
```http
POST /alerts/test/create-sample-alerts
```

Creates test alerts for development and testing purposes.

## User Management

User management endpoints (Admin access required for most operations).

### Get Users
```http
GET /users/?page=1&per_page=10&search=john&role=admin&is_active=true
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (1-100, default: 10)
- `search`: Search in username/email
- `role`: Filter by role
- `is_active`: Filter by active status

**Response:**
```json
{
  "users": [
    {
      "id": "user_001",
      "username": "admin",
      "email": "admin@example.com",
      "first_name": "System",
      "last_name": "Administrator",
      "role": "admin",
      "is_active": true,
      "is_verified": true,
      "permissions": {
        "canViewCameras": true,
        "canControlCameras": true,
        "canViewAlerts": true,
        "canManageAlerts": true,
        "canViewAnalytics": true,
        "canManageUsers": true,
        "canManageSystem": true,
        "canExportData": true
      },
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T12:00:00Z",
      "last_login_at": "2023-01-01T12:00:00Z",
      "last_activity_at": "2023-01-01T12:30:00Z",
      "avatar_url": null
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 10,
  "total_pages": 1
}
```

### Create User
```http
POST /users/
```

**Request Body:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user",
  "permissions": {
    "canViewCameras": true,
    "canViewAlerts": true
  }
}
```

**User Roles:**
- `admin`: Full system access
- `user`: Camera and alert management
- `viewer`: Read-only access

### Get User by ID
```http
GET /users/{user_id}
```

### Update User
```http
PATCH /users/{user_id}
```

**Request Body:**
```json
{
  "username": "updateduser",
  "email": "updated@example.com",
  "first_name": "Updated",
  "last_name": "Name",
  "role": "user",
  "is_active": true,
  "permissions": {
    "canViewCameras": true,
    "canControlCameras": false
  }
}
```

### Delete User
```http
DELETE /users/{user_id}
```

**Response:**
```json
{
  "message": "User deleted successfully"
}
```

### Change User Password
```http
POST /users/{user_id}/change-password
```

**Request Body:**
```json
{
  "new_password": "newSecurePassword123"
}
```

### Reset User Password
```http
POST /users/{user_id}/reset-password
```

**Response:**
```json
{
  "message": "Password reset successfully",
  "temporary_password": "Abc123def456"
}
```

## Metrics & Analytics

Performance and analytics endpoints.

### System Metrics
```http
GET /api/metrics/system?time_range=15m&limit=100
```

**Time Ranges:** `5m`, `15m`, `1h`, `24h`

**Response:**
```json
[
  {
    "timestamp": "2023-01-01T12:00:00Z",
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.1,
    "active_cameras": 3
  }
]
```

### Camera Metrics
```http
GET /api/metrics/cameras
```

**Response:**
```json
[
  {
    "camera_id": "store-entrance",
    "fps_actual": 29.5,
    "fps_target": 30.0,
    "latency_ms": 120.5,
    "status": "active",
    "last_detection": "2023-01-01T12:00:00Z"
  }
]
```

### Camera Performance
```http
GET /api/metrics/cameras/{camera_id}/performance?time_range=1h
```

**Response:**
```json
{
  "camera_id": "store-entrance",
  "time_range": "1h",
  "data_points": [
    {
      "timestamp": "2023-01-01T12:00:00Z",
      "fps": 29.5,
      "latency_ms": 120.5,
      "frame_drops": 0,
      "detection_count": 5
    }
  ],
  "summary": {
    "avg_fps": 29.2,
    "avg_latency_ms": 125.3,
    "total_detections": 45,
    "uptime_percentage": 98.5
  }
}
```

### Detection Metrics
```http
GET /api/metrics/detections?time_range=1h&camera_id=store-entrance&confidence_threshold=0.5
```

**Response:**
```json
[
  {
    "camera_id": "store-entrance",
    "confidence": 0.87,
    "label": "shoplifting",
    "is_shoplifting": true,
    "timestamp": "2023-01-01T12:00:00Z",
    "alert_triggered": true
  }
]
```

### Metrics Summary
```http
GET /api/metrics/summary
```

**Response:**
```json
{
  "system": {
    "timestamp": "2023-01-01T12:00:00Z",
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.1,
    "active_cameras": 3
  },
  "cameras": [
    {
      "camera_id": "store-entrance",
      "fps_actual": 29.5,
      "fps_target": 30.0,
      "latency_ms": 120.5,
      "status": "active"
    }
  ],
  "recent_detections": [
    {
      "camera_id": "store-entrance",
      "confidence": 0.87,
      "timestamp": "2023-01-01T12:00:00Z",
      "alert_triggered": true
    }
  ],
  "total_detections_today": 156,
  "alert_count_today": 23
}
```

### Health Status
```http
GET /api/metrics/health
```

**Response:**
```json
{
  "elasticsearch": {
    "status": "healthy",
    "response_time_ms": 15.2
  },
  "database": {
    "status": "healthy",
    "active_connections": 5
  },
  "redis": {
    "status": "healthy",
    "memory_usage_mb": 12.5
  },
  "overall_status": "healthy"
}
```

### Recent Alerts
```http
GET /api/metrics/alerts/recent?limit=50&severity=high
```

### Analytics Data
```http
GET /api/metrics/analytics?time_range=24h
```

**Response:**
```json
{
  "system_metrics": [],
  "detection_metrics": [],
  "summary": {},
  "health_status": {},
  "recent_alerts": [],
  "time_range": "24h",
  "generated_at": "2023-01-01T12:00:00Z",
  "computed_stats": {
    "total_detections": 342,
    "shoplifting_detections": 45,
    "average_confidence": 72.5,
    "detection_rate": 13.2
  }
}
```

## Video Streaming

Real-time video streaming endpoints using WebSockets and HTTP.

### WebSocket Video Stream
```
ws://localhost:8001/api/video/stream/{camera_id}
```

**Usage Example (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8001/api/video/stream/store-entrance');

ws.onopen = () => {
  console.log('Video stream connected');
};

ws.onmessage = (event) => {
  if (event.data instanceof Blob) {
    // Handle frame data
    const url = URL.createObjectURL(event.data);
    videoElement.src = url;
  } else {
    // Handle JSON messages (errors, status)
    const message = JSON.parse(event.data);
    console.log('Stream message:', message);
  }
};

ws.onerror = (error) => {
  console.error('Stream error:', error);
};

ws.onclose = () => {
  console.log('Stream disconnected');
};
```

### Stream Status
```http
GET /status/{camera_id}
```

**Response:**
```json
{
  "camera_id": "store-entrance",
  "connected": true,
  "buffer_size": 15,
  "frames_sent": 1250,
  "last_frame_time": 1609459200.123,
  "connection_count": 2
}
```

### Connection Status
```http
GET /connection/{camera_id}
```

**Response:**
```json
{
  "camera_id": "store-entrance",
  "websocket_connections": 2,
  "active_streams": 1,
  "last_activity": "2023-01-01T12:00:00Z",
  "stream_health": "good"
}
```

### Stream Debug Information
```http
GET /debug/{camera_id}
```

**Response:**
```json
{
  "camera_id": "store-entrance",
  "timestamp": 1609459200.123,
  "buffer_status": {
    "size": 15,
    "max_size": 30,
    "utilization_percent": 50.0
  },
  "stream_stats": {
    "frames_sent": 1250,
    "bytes_sent": 125000000,
    "average_fps": 29.5
  },
  "connection_status": {
    "active_connections": 2,
    "total_connections": 5
  },
  "stream_manager_running": true,
  "stream_manager_initialized": true
}
```

### Inject Frame (Development)
```http
POST /inject-frame/{camera_id}
```

**Content-Type:** `application/octet-stream`

**Body:** Raw frame data (JPEG bytes)

### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

## WebSocket Connections

Real-time data connections for live updates.

### Camera Status WebSocket
```
ws://localhost:8001/ws/camera/{camera_id}
```

**Messages Received:**
```json
{
  "status": "active",
  "fps": 29.5,
  "resolution": "1920x1080",
  "last_frame_time": 1609459200.123,
  "error": null
}
```

### Prediction WebSocket
```
ws://localhost:8001/ws/cameras/{camera_id}/prediction
```

**Messages Received:**
```json
{
  "type": "prediction",
  "camera_id": "store-entrance",
  "confidence": 0.87,
  "is_shoplifting": true,
  "timestamp": 1609459200.123,
  "sequence_stats": {
    "mean": 0.82,
    "std": 0.15,
    "frames": 160
  }
}
```

### Metrics WebSocket
```
ws://localhost:8001/ws/metrics
```

**Messages Received:**
```json
{
  "type": "metrics_update",
  "timestamp": 1609459200.123,
  "data": {
    "system": {
      "cpu_usage": 45.2,
      "memory_usage": 67.8,
      "active_cameras": 3
    },
    "cameras": [],
    "recent_detections": []
  }
}
```

### Camera Metrics WebSocket
```
ws://localhost:8001/ws/metrics/camera/{camera_id}
```

**Messages Received:**
```json
{
  "type": "camera_metrics_update",
  "camera_id": "store-entrance",
  "timestamp": 1609459200.123,
  "performance": {
    "fps": 29.5,
    "latency_ms": 120.5,
    "detection_count": 5
  },
  "recent_detections": []
}
```

### Alerts WebSocket
```
ws://localhost:8001/ws/alerts
```

**Messages Received:**
```json
{
  "type": "alerts_update",
  "timestamp": 1609459200.123,
  "new_alerts": [
    {
      "id": "alert_001",
      "camera_id": "store-entrance",
      "severity": "high",
      "confidence": 0.87,
      "timestamp": "2023-01-01T12:00:00Z"
    }
  ],
  "total_recent": 5
}
```

## Error Handling

### Standard Error Response Format
```json
{
  "detail": "Error description",
  "status_code": 400,
  "error_type": "validation_error"
}
```

### HTTP Status Codes

#### Success Codes
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `204 No Content`: Request successful, no response body

#### Client Error Codes
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or invalid
- `403 Forbidden`: Access denied (insufficient permissions)
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource already exists
- `422 Unprocessable Entity`: Validation error

#### Server Error Codes
- `500 Internal Server Error`: Unexpected server error
- `502 Bad Gateway`: Upstream service error
- `503 Service Unavailable`: Service temporarily unavailable

### Common Error Examples

#### Authentication Error
```json
{
  "detail": "Could not validate credentials",
  "status_code": 401
}
```

#### Validation Error
```json
{
  "detail": "Missing required field: camera_id",
  "status_code": 400
}
```

#### Permission Error
```json
{
  "detail": "Admin access required",
  "status_code": 403
}
```

#### Resource Not Found
```json
{
  "detail": "Camera 'invalid-id' not found",
  "status_code": 404
}
```

## Security Considerations

### Authentication Requirements
- All endpoints except `/api/auth/login` require valid JWT token
- Tokens expire after 24 hours (configurable)
- Refresh tokens expire after 7 days (configurable)

### Role-Based Access Control

#### Admin Role
- Full access to all endpoints
- User management capabilities
- System configuration access

#### User Role
- Camera management (view, control)
- Alert management (view, acknowledge, resolve)
- Analytics access (read-only)

#### Viewer Role
- Camera viewing (read-only)
- Alert viewing (read-only)
- No management capabilities

### Rate Limiting
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1609459260
```

### Security Headers
All responses include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`

### Input Validation
- All input is validated against schemas
- SQL injection protection via parameterized queries
- XSS protection via input sanitization
- File upload validation (type, size limits)

### WebSocket Security
- WebSocket connections inherit HTTP authentication
- Real-time data is filtered based on user permissions
- Connection limits per user/IP address

---

## Additional Resources

- **OpenAPI Documentation**: Available at `/docs` when running the server
- **Interactive API Explorer**: Available at `/redoc`
- **Frontend Integration**: See [Frontend Architecture Guide](15_FRONTEND_ARCHITECTURE_GUIDE.md)
- **Authentication Setup**: See [Authentication & Security Guide](08_AUTHENTICATION_SECURITY.md)

---

**Last Updated**: This API reference reflects the current state of the system and should be updated when new endpoints are added or existing ones are modified.
