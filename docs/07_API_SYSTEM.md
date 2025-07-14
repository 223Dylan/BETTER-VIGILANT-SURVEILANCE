# API System

## Overview

The API System provides a comprehensive RESTful interface built with FastAPI, offering endpoints for camera management, alert handling, user authentication, and system monitoring.

## Architecture

### Components

1. **FastAPI Application** - Main API server
2. **Router Modules** - Organized endpoint groups
3. **Middleware Stack** - Security and monitoring
4. **Authentication System** - JWT-based auth
5. **WebSocket Support** - Real-time communication
6. **API Documentation** - Auto-generated OpenAPI docs

### API Structure

```
/api/v1/
├── /auth          - Authentication endpoints
├── /cameras       - Camera management
├── /alerts        - Alert operations  
├── /users         - User management
├── /frames        - Frame data access
├── /stream        - Video streaming
├── /ws            - WebSocket connections
└── /health        - System health checks
```

## Main Application

### FastAPI Setup

**Source:** `api_server.py`

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Router imports
from src.routers import auth, cameras, alerts, users, ws
from src.middleware.security import SecurityHeadersMiddleware
from src.middleware.request_limits import RateLimitMiddleware
from src.database.base import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup
    print("Starting API server...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Shutdown
    print("Shutting down API server...")

# Create FastAPI app
app = FastAPI(
    title="Shoplifting Detection API",
    description="Real-time video surveillance with AI-powered shoplifting detection",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware stack
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(cameras.router, prefix="/api/v1/cameras", tags=["Cameras"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(ws.router, prefix="/api/v1/ws", tags=["WebSocket"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Shoplifting Detection API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
```

## Authentication System

### JWT Authentication

**Source:** `src/routers/auth.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

router = APIRouter()

# JWT configuration
SECRET_KEY = "your-secret-key-here"  # Use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TokenData:
    username: str = None

@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT token."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }

@router.post("/refresh")
async def refresh_token(
    current_user: User = Depends(get_current_user)
):
    """Refresh JWT token."""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
```

## Camera Management API

### Camera Endpoints

**Source:** `src/routers/cameras.py`

```python
@router.get("/", response_model=List[CameraResponse])
async def get_cameras(
    enabled_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all cameras."""
    query = db.query(Camera)
    if enabled_only:
        query = query.filter(Camera.enabled == True)
    
    cameras = query.all()
    return cameras

@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific camera."""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera

@router.post("/", response_model=CameraResponse)
async def create_camera(
    camera: CameraCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new camera."""
    # Check if camera ID already exists
    existing = db.query(Camera).filter(Camera.id == camera.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Camera ID already exists")
    
    db_camera = Camera(
        id=camera.id,
        name=camera.name,
        description=camera.description,
        source=camera.source,
        source_type=camera.source_type,
        fps=camera.fps,
        resolution_width=camera.resolution_width,
        resolution_height=camera.resolution_height,
        enabled=camera.enabled,
        detection_enabled=camera.detection_enabled,
        detection_sensitivity=camera.detection_sensitivity,
        location=camera.location,
        zone=camera.zone
    )
    
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    
    return db_camera

@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: str,
    camera_update: CameraUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update camera configuration."""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    # Update fields
    update_data = camera_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(camera, field, value)
    
    camera.updated_at = datetime.utcnow()
    db.commit()
    
    return camera

@router.delete("/{camera_id}")
async def delete_camera(
    camera_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete camera."""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    db.delete(camera)
    db.commit()
    
    return {"message": "Camera deleted successfully"}

@router.post("/{camera_id}/control")
async def control_camera(
    camera_id: str,
    action: CameraAction,
    current_user: User = Depends(get_current_user)
):
    """Control camera (start/stop/restart)."""
    # Import camera manager
    from src.camera_manager import camera_manager
    
    if not camera_manager:
        raise HTTPException(status_code=503, detail="Camera manager not available")
    
    if action.action == "start":
        result = camera_manager.start_camera(camera_id)
    elif action.action == "stop":
        result = camera_manager.stop_camera(camera_id)
    elif action.action == "restart":
        camera_manager.stop_camera(camera_id)
        result = camera_manager.start_camera(camera_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    return {"success": result, "action": action.action}

@router.get("/{camera_id}/status")
async def get_camera_status(
    camera_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get camera status and statistics."""
    from src.camera_manager import camera_manager
    
    if not camera_manager:
        raise HTTPException(status_code=503, detail="Camera manager not available")
    
    status = camera_manager.get_camera_status(camera_id)
    stats = camera_manager.get_stats(camera_id)
    
    return {
        "camera_id": camera_id,
        "status": status,
        "statistics": stats,
        "timestamp": datetime.utcnow().isoformat()
    }
```

## Alert Management API

### Alert Endpoints

**Source:** `src/routers/alerts.py`

```python
@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, regex="^(active|acknowledged|resolved|dismissed)$"),
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    camera_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get alerts with filtering and pagination."""
    query = db.query(Alert)
    
    # Apply filters
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    if camera_id:
        query = query.filter(Alert.camera_id == camera_id)
    if start_date:
        query = query.filter(Alert.timestamp >= start_date)
    if end_date:
        query = query.filter(Alert.timestamp <= end_date)
    
    # Order by timestamp (newest first)
    query = query.order_by(Alert.timestamp.desc())
    
    # Apply pagination
    alerts = query.offset(skip).limit(limit).all()
    
    return alerts

@router.get("/stats/summary")
async def get_alert_statistics(
    period: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    camera_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get alert statistics summary."""
    # Calculate time range
    now = datetime.utcnow()
    period_map = {
        "1h": timedelta(hours=1),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30)
    }
    
    start_time = now - period_map[period]
    
    query = db.query(Alert).filter(Alert.timestamp >= start_time)
    if camera_id:
        query = query.filter(Alert.camera_id == camera_id)
    
    alerts = query.all()
    
    # Calculate statistics
    stats = {
        "total_alerts": len(alerts),
        "period": period,
        "start_time": start_time.isoformat(),
        "end_time": now.isoformat(),
        "by_severity": {
            "low": len([a for a in alerts if a.severity == "low"]),
            "medium": len([a for a in alerts if a.severity == "medium"]),
            "high": len([a for a in alerts if a.severity == "high"]),
            "critical": len([a for a in alerts if a.severity == "critical"])
        },
        "by_status": {
            "active": len([a for a in alerts if a.status == "active"]),
            "acknowledged": len([a for a in alerts if a.status == "acknowledged"]),
            "resolved": len([a for a in alerts if a.status == "resolved"]),
            "dismissed": len([a for a in alerts if a.status == "dismissed"])
        },
        "avg_confidence": sum(a.confidence for a in alerts) / len(alerts) if alerts else 0
    }
    
    return stats

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Acknowledge an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if alert.status != "active":
        raise HTTPException(status_code=400, detail="Alert is not active")
    
    alert.status = "acknowledged"
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    alert.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Broadcast update via WebSocket
    await broadcast_alert_update(alert)
    
    return {"message": "Alert acknowledged successfully"}

@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolution: AlertResolution,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resolve an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = "resolved"
    alert.resolved_by = current_user.id
    alert.resolved_at = datetime.utcnow()
    alert.updated_at = datetime.utcnow()
    
    if resolution.notes:
        alert.notes = resolution.notes
    
    db.commit()
    
    # Broadcast update via WebSocket
    await broadcast_alert_update(alert)
    
    return {"message": "Alert resolved successfully"}
```

## WebSocket Communication

### WebSocket Manager

**Source:** `src/routers/ws.py`

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove stale connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time communication."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Handle incoming messages
            try:
                message = json.loads(data)
                await handle_websocket_message(message, websocket)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def handle_websocket_message(message: dict, websocket: WebSocket):
    """Handle incoming WebSocket messages."""
    message_type = message.get("type")
    
    if message_type == "ping":
        await websocket.send_text(json.dumps({
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    elif message_type == "subscribe":
        # Handle subscription to specific events
        channels = message.get("channels", [])
        await websocket.send_text(json.dumps({
            "type": "subscribed",
            "channels": channels
        }))
    
    else:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }))

async def broadcast_alert_update(alert):
    """Broadcast alert update to all connected clients."""
    message = {
        "type": "alert_update",
        "data": {
            "id": alert.id,
            "camera_id": alert.camera_id,
            "status": alert.status,
            "severity": alert.severity,
            "timestamp": alert.timestamp.isoformat()
        }
    }
    
    await manager.broadcast(json.dumps(message))

async def broadcast_camera_status(camera_id: str, status: str):
    """Broadcast camera status update."""
    message = {
        "type": "camera_status",
        "data": {
            "camera_id": camera_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    
    await manager.broadcast(json.dumps(message))
```

## API Models and Schemas

### Pydantic Models

**Source:** `src/api/schemas.py`

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime

# Camera schemas
class CameraBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source: str = Field(..., min_length=1)
    source_type: str = Field(default="webcam")
    fps: int = Field(default=15, ge=1, le=60)
    resolution_width: int = Field(default=640, ge=320)
    resolution_height: int = Field(default=480, ge=240)
    enabled: bool = True
    detection_enabled: bool = True
    detection_sensitivity: float = Field(default=0.5, ge=0.0, le=1.0)
    location: Optional[str] = None
    zone: Optional[str] = None

class CameraCreate(CameraBase):
    id: str = Field(..., min_length=1, max_length=50)

class CameraUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    fps: Optional[int] = Field(None, ge=1, le=60)
    brightness: Optional[float] = Field(None, ge=0.1, le=2.0)
    enabled: Optional[bool] = None
    detection_enabled: Optional[bool] = None
    detection_sensitivity: Optional[float] = Field(None, ge=0.0, le=1.0)

class CameraResponse(CameraBase):
    id: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Alert schemas
class AlertBase(BaseModel):
    camera_id: str
    type: str
    severity: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    message: str

class AlertCreate(AlertBase):
    detection_data: Optional[Dict[str, Any]] = {}

class AlertResolution(BaseModel):
    notes: Optional[str] = None

class AlertDismissal(BaseModel):
    reason: Optional[str] = None

class AlertResponse(AlertBase):
    id: str
    status: str
    timestamp: datetime
    created_at: datetime
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    notes: Optional[str]
    
    class Config:
        from_attributes = True

# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    full_name: Optional[str] = None
    role: str = Field(default="user")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

# Control schemas
class CameraAction(BaseModel):
    action: str = Field(..., regex="^(start|stop|restart)$")

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    database: Optional[str] = None
    cache: Optional[str] = None
```

## Error Handling

### Custom Exception Handlers

```python
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_error",
                "status_code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path)
            }
        }
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "validation_error",
                "status_code": 422,
                "message": "Validation failed",
                "details": exc.errors()
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_error",
                "status_code": 500,
                "message": "An unexpected error occurred"
            }
        }
    )
```

## API Testing

### Test Examples

```python
import requests
import pytest

BASE_URL = "http://localhost:8001/api/v1"

def test_authentication():
    """Test user authentication."""
    # Login
    response = requests.post(f"{BASE_URL}/auth/token", data={
        "username": "admin",
        "password": "admin123"
    })
    
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    
    return token_data["access_token"]

def test_camera_management():
    """Test camera CRUD operations."""
    token = test_authentication()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create camera
    camera_data = {
        "id": "test-camera",
        "name": "Test Camera",
        "source": "0",
        "source_type": "webcam"
    }
    
    response = requests.post(f"{BASE_URL}/cameras", 
                           json=camera_data, 
                           headers=headers)
    assert response.status_code == 200
    
    # Get camera
    response = requests.get(f"{BASE_URL}/cameras/test-camera", 
                          headers=headers)
    assert response.status_code == 200
    
    # Update camera
    update_data = {"name": "Updated Camera"}
    response = requests.put(f"{BASE_URL}/cameras/test-camera", 
                          json=update_data, 
                          headers=headers)
    assert response.status_code == 200
    
    # Delete camera
    response = requests.delete(f"{BASE_URL}/cameras/test-camera", 
                             headers=headers)
    assert response.status_code == 200

def test_alert_operations():
    """Test alert management."""
    token = test_authentication()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get alerts
    response = requests.get(f"{BASE_URL}/alerts", headers=headers)
    assert response.status_code == 200
    
    # Get alert statistics
    response = requests.get(f"{BASE_URL}/alerts/stats/summary", 
                          headers=headers)
    assert response.status_code == 200
    assert "total_alerts" in response.json()
```

## Best Practices

1. **Security**
   - Use strong JWT secrets
   - Implement rate limiting
   - Validate all inputs
   - Use HTTPS in production

2. **Performance**
   - Use async/await properly
   - Implement pagination
   - Cache frequently accessed data
   - Monitor response times

3. **Documentation**
   - Use descriptive endpoint names
   - Provide clear error messages
   - Document all parameters
   - Include usage examples

4. **Monitoring**
   - Log all requests
   - Track performance metrics
   - Monitor error rates
   - Set up health checks 