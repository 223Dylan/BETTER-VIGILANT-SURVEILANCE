# Database System

## Overview

The Database System uses PostgreSQL with SQLAlchemy ORM and Alembic for migrations. It provides persistent storage for cameras, users, alerts, frames, and system configuration.

## Architecture

### Components

1. **PostgreSQL Database** - Primary data storage
2. **SQLAlchemy ORM** - Object-relational mapping
3. **Alembic** - Database migration management
4. **Database Models** - Entity definitions
5. **Connection Management** - Connection pooling and sessions
6. **Migration System** - Version control for schema changes

### Database Schema

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│      cameras        │    │        users        │    │       alerts        │
├─────────────────────┤    ├─────────────────────┤    ├─────────────────────┤
│ id (PK)             │    │ id (PK)             │    │ id (PK)             │
│ name                │    │ username (UQ)       │    │ camera_id (FK)      │
│ description         │    │ email (UQ)          │    │ type                │
│ enabled             │    │ password_hash       │    │ severity            │
│ source              │    │ role                │    │ status              │
│ source_type         │    │ permissions (JSON)  │    │ confidence          │
│ fps                 │    │ is_active           │    │ message             │
│ resolution_width    │    │ is_verified         │    │ source              │
│ resolution_height   │    │ created_at          │    │ detection_data (JSON)│
│ brightness          │    │ updated_at          │    │ timestamp           │
│ detection_enabled   │    │ last_login_at       │    │ created_at          │
│ detection_sensitivity│   │ last_activity_at    │    │ updated_at          │
│ recording_enabled   │    └─────────────────────┘    │ acknowledged_by     │
│ location            │                               │ acknowledged_at     │
│ zone                │                               │ resolved_by         │
│ advanced_settings (JSON)                          │ resolved_at         │
│ created_at          │                               │ notes               │
│ updated_at          │                               └─────────────────────┘
│ last_online         │
│ status              │    ┌─────────────────────┐
│ error_message       │    │       frames        │
│ uptime_hours        │    ├─────────────────────┤
└─────────────────────┘    │ id (PK)             │
                          │ timestamp           │
                          │ sequence_number     │
                          │ frame_data (BLOB)   │
                          │ frame_metadata (JSON)│
                          │ created_at          │
                          │ processed_at        │
                          └─────────────────────┘

Relationships:
- alerts.camera_id → cameras.id (Many-to-One)
- frames.camera_id → cameras.id (Many-to-One) [conceptual]
```

## Database Models

### Camera Model

**Source:** `src/database/models/camera.py`

```python
class Camera(Base):
    """Camera configuration and status model."""
    __tablename__ = "cameras"

    # Primary identification
    id = Column(String, primary_key=True)  # e.g., "local-webcam", "ip-cam-001"
    name = Column(String(255), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True, nullable=False)

    # Connection details
    source = Column(String(255), nullable=False)  # URL, device index, etc.
    source_type = Column(String(50), nullable=False, default="webcam")  # webcam, rtsp, file

    # Video settings
    fps = Column(Integer, default=15, nullable=False)
    resolution_width = Column(Integer, default=640)
    resolution_height = Column(Integer, default=480)
    brightness = Column(Float, default=1.0, nullable=False)  # 0.0 to 2.0

    # Processing settings
    detection_enabled = Column(Boolean, default=True, nullable=False)
    detection_sensitivity = Column(Float, default=0.5)  # Threshold for ML predictions
    recording_enabled = Column(Boolean, default=False, nullable=False)

    # Location and metadata
    location = Column(String(255))
    zone = Column(String(100))  # e.g., "entrance", "checkout", "aisle-1"
    advanced_settings = Column(JSON, default={})  # Custom configuration per camera

    # Status tracking
    status = Column(String(50), default="stopped")  # stopped, starting, active, error
    error_message = Column(Text)
    uptime_hours = Column(Float, default=0.0)
    last_online = Column(DateTime(timezone=True))

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "source": self.source,
            "source_type": self.source_type,
            "fps": self.fps,
            "resolution": {
                "width": self.resolution_width,
                "height": self.resolution_height,
            },
            "brightness": self.brightness,
            "detection_enabled": self.detection_enabled,
            "detection_sensitivity": self.detection_sensitivity,
            "recording_enabled": self.recording_enabled,
            "location": self.location,
            "zone": self.zone,
            "advanced_settings": self.advanced_settings or {},
            "status": self.status,
            "error_message": self.error_message,
            "uptime_hours": self.uptime_hours,
            "last_online": self.last_online.isoformat() if self.last_online else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
```

#### Camera Status Values
- **stopped**: Camera is not active
- **starting**: Camera is initializing
- **active**: Camera is running and processing frames
- **error**: Camera encountered an error

#### Source Types
- **webcam**: Local USB/built-in camera (source = device index)
- **rtsp**: RTSP network stream (source = rtsp://...)
- **file**: Video file input (source = file path)

### User Model

**Source:** `src/database/models/user.py`

```python
class User(Base):
    """User authentication and authorization model."""
    __tablename__ = "users"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)

    # Authentication
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Authorization
    role = Column(String(20), nullable=False, default="user")
    permissions = Column(JSON, default=dict)

    # Activity tracking
    last_login_at = Column(DateTime(timezone=True))
    last_activity_at = Column(DateTime(timezone=True))

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "permissions": self.permissions or {},
            "is_active": self.is_active,
            "is_verified": self.is_verified,
        }

    def has_permission(self, permission_key):
        """Check if user has specific permission."""
        if self.role == "admin":
            return True
        return (
            self.permissions.get(permission_key, False) if self.permissions else False
        )
```

#### User Roles
- **admin**: Full system access, can manage users and system settings
- **user**: Standard access, can view cameras and manage alerts
- **viewer**: Read-only access, can only view cameras and alerts

#### Permissions System
The permissions field stores a JSON object with granular permissions:

```json
{
  "canViewCameras": true,
  "canControlCameras": false,
  "canViewAlerts": true,
  "canManageAlerts": true,
  "canViewAnalytics": false,
  "canManageUsers": false,
  "canManageSystem": false,
  "canExportData": false
}
```

### Alert Model

**Source:** `src/database/models/alert.py`

```python
class Alert(Base):
    """Security alert and incident model."""
    __tablename__ = "alerts"

    # Primary identification
    id = Column(String, primary_key=True)  # UUID string
    camera_id = Column(String(255), nullable=False, index=True)

    # Classification
    type = Column(String(100), nullable=False, index=True)  # shoplifting, suspicious_activity
    severity = Column(String(50), nullable=False, index=True)  # low, medium, high, critical
    status = Column(String(50), nullable=False, default="active", index=True)  # active, acknowledged, resolved, dismissed

    # Detection data
    confidence = Column(Float, nullable=False)
    message = Column(Text, nullable=False)
    source = Column(String(100), default="detection", nullable=False)
    detection_data = Column(JSON, default={})  # Additional detection metadata

    # Timestamps
    timestamp = Column(DateTime(timezone=True), nullable=False)  # When detection occurred
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Lifecycle management
    acknowledged_by = Column(String(255), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(255), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index("idx_alert_camera_timestamp", "camera_id", "timestamp"),
        Index("idx_alert_severity_status", "severity", "status"),
        Index("idx_alert_type_timestamp", "type", "timestamp"),
        Index("idx_alert_timestamp_desc", "timestamp"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "camera_id": self.camera_id,
            "type": self.type,
            "severity": self.severity,
            "status": self.status,
            "confidence": self.confidence,
            "message": self.message,
            "source": self.source,
            "detection_data": self.detection_data or {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": (
                self.acknowledged_at.isoformat() if self.acknowledged_at else None
            ),
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "notes": self.notes,
        }
```

#### Alert Types
- **shoplifting_detection**: Primary detection from LRCN model
- **suspicious_activity**: Other suspicious behaviors
- **system_alert**: System-generated alerts

#### Alert Severity Levels
- **low**: Minor incidents requiring attention
- **medium**: Moderate incidents requiring review
- **high**: Serious incidents requiring immediate attention
- **critical**: Critical incidents requiring immediate response

#### Alert Status Lifecycle
- **active**: New alert requiring attention
- **acknowledged**: Alert has been seen by an operator
- **resolved**: Alert has been investigated and closed
- **dismissed**: Alert was marked as false positive

#### Detection Data Structure
The `detection_data` JSON field contains additional metadata:

```json
{
  "sequence_stats": {
    "mean": 0.82,
    "std": 0.15,
    "frames": 160
  },
  "model_version": "1.0.0",
  "processing_time_ms": 120.5,
  "frame_path": "/path/to/frame.jpg"
}
```

### Frame Model

**Source:** `src/database/models/frame.py`

```python
class Frame(Base):
    """Video frame storage and metadata model."""
    __tablename__ = "frames"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)

    # Temporal data
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    sequence_number = Column(Integer, index=True)

    # Frame data
    frame_data = Column(LargeBinary)  # Compressed frame
    frame_metadata = Column(JSON)    # Processing metadata

    # Processing status
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index('idx_frame_timestamp_seq', 'timestamp', 'sequence_number'),
    )
```

## Database Configuration

### Connection Settings

**Source:** `src/database/base.py`

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/shoplifting_detection"
)

# Engine configuration
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
    echo=False  # Set to True for SQL debugging
)

# Session configuration
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Environment Variables

```bash
# Database connection
DATABASE_URL=postgresql://username:password@host:port/database_name

# Connection pool settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# SSL settings (for production)
DB_SSL_MODE=require
DB_SSL_CERT_PATH=/path/to/cert.pem
```

## Migration System

### Alembic Configuration

**Source:** `alembic.ini`

```ini
[alembic]
script_location = src/database/migrations
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://postgres:password@localhost:5432/shoplifting_detection

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 79
```

### Migration Environment

**Source:** `src/database/migrations/env.py`

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.database.base import Base
from src.database.models import *  # Import all models

# Alembic Config object
config = context.config

# Override database URL from environment
if os.getenv("DATABASE_URL"):
    config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Migration Commands

```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history --verbose

# Check current revision
alembic current

# View SQL for migration
alembic upgrade head --sql
```

### Recent Migrations

#### Current Schema (Latest Migration: 455924c09f24)

**Migration:** `455924c09f24_add_cameras_users_and_alerts_tables.py`

This migration establishes the core database schema with comprehensive tables:

**Tables Created:**
- **cameras**: Complete camera configuration and status tracking
- **users**: User authentication and authorization with role-based permissions
- **alerts**: Alert management with full lifecycle tracking
- **frames**: Frame storage and metadata (optional)

**Key Features:**
- **JSON fields**: `advanced_settings` in cameras, `permissions` in users, `detection_data` in alerts
- **Indexes**: Optimized for common query patterns
- **Timestamps**: Created/updated tracking with timezone support
- **Status tracking**: Comprehensive status fields for monitoring

**Previous Migration:** `4ed1393c0e75_initial_migration.py`
- Initial database setup and base configuration

#### Migration Best Practices

1. **Always backup before migrations:**
   ```bash
   pg_dump shoplifting_detection > backup_before_migration.sql
   ```

2. **Test migrations on development first:**
   ```bash
   # Apply migration to dev environment
   alembic upgrade head

   # Verify data integrity
   python scripts/verify_migration.py
   ```

3. **Use descriptive migration messages:**
   ```bash
   alembic revision --autogenerate -m "Add brightness column to cameras table"
   ```

4. **Review generated migrations before applying:**
   ```bash
   # Always review the generated migration file
   cat src/database/migrations/versions/abc123_migration_name.py
   ```

## Database Services

### Camera Database Service

**Source:** `src/services/camera_db_service.py`

```python
class CameraDatabaseService:
    """Service for managing camera configurations in database."""

    def __init__(self):
        # Uses fresh sessions for each operation
        pass

    def get_session(self) -> Session:
        """Get a new database session for each operation."""
        return next(get_db())

    def get_all_cameras(self) -> List[Camera]:
        """Get all cameras from database."""
        session = self.get_session()
        try:
            cameras = session.query(Camera).all()
            logger.info(f"Retrieved {len(cameras)} cameras from database")
            return cameras
        except Exception as e:
            logger.error(f"Error retrieving cameras: {e}")
            return []
        finally:
            session.close()

    def get_camera_by_id(self, camera_id: str) -> Optional[Camera]:
        """Get camera by ID."""
        session = self.get_session()
        try:
            camera = session.query(Camera).filter(Camera.id == camera_id).first()
            return camera
        except Exception as e:
            logger.error(f"Error retrieving camera {camera_id}: {e}")
            return None
        finally:
            session.close()

    def create_camera(self, camera: Camera) -> bool:
        """Create new camera in database."""
        session = self.get_session()
        try:
            session.add(camera)
            session.commit()
            logger.info(f"Created camera: {camera.id}")
            return True
        except Exception as e:
            logger.error(f"Error creating camera: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def update_camera(self, camera_id: str, updates: Dict[str, Any]) -> bool:
        """Update camera configuration."""
        session = self.get_session()
        try:
            camera = session.query(Camera).filter(Camera.id == camera_id).first()
            if not camera:
                return False

            for field, value in updates.items():
                if hasattr(camera, field):
                    setattr(camera, field, value)

            camera.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Updated camera {camera_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating camera {camera_id}: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def delete_camera(self, camera_id: str) -> bool:
        """Delete camera from database."""
        session = self.get_session()
        try:
            camera = session.query(Camera).filter(Camera.id == camera_id).first()
            if not camera:
                return False

            session.delete(camera)
            session.commit()
            logger.info(f"Deleted camera: {camera_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting camera {camera_id}: {e}")
            session.rollback()
            return False
        finally:
            session.close()

# Global service instance
camera_db_service = CameraDatabaseService()
```

### Alert Manager Service

**Source:** `src/services/alert_manager.py`

The Alert Manager handles real-time alert processing, storage, and lifecycle management.

```python
class AlertManager:
    """Manages alert creation, processing, and lifecycle."""

    def __init__(self):
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)

    def process_prediction(self, prediction_data: dict) -> Optional[str]:
        """Process ML prediction and create alert if necessary."""
        try:
            confidence = prediction_data.get("confidence", 0)
            camera_id = prediction_data.get("camera_id")

            # Determine if alert should be created based on thresholds
            if confidence >= 0.8:
                severity = "critical"
            elif confidence >= 0.6:
                severity = "high"
            elif confidence >= 0.4:
                severity = "medium"
            else:
                return None  # Below threshold

            # Create alert
            alert_id = str(uuid.uuid4())
            alert = {
                "id": alert_id,
                "camera_id": camera_id,
                "type": "shoplifting_detection",
                "severity": severity,
                "status": "active",
                "confidence": confidence,
                "message": f"Shoplifting behavior detected with {confidence:.1%} confidence",
                "timestamp": datetime.utcnow().isoformat(),
                "detection_data": prediction_data.get("sequence_stats", {})
            }

            # Store in memory and database
            self.active_alerts[alert_id] = alert
            self._save_alert_to_database(alert)

            logger.info(f"Created alert {alert_id} for camera {camera_id}")
            return alert_id

        except Exception as e:
            logger.error(f"Error processing prediction: {e}")
            return None

    def acknowledge_alert(self, alert_id: str, user_id: str, notes: str = None) -> bool:
        """Acknowledge an active alert."""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert["status"] = "acknowledged"
                alert["acknowledged_by"] = user_id
                alert["acknowledged_at"] = datetime.utcnow().isoformat()
                if notes:
                    alert["notes"] = notes

                self._update_alert_in_database(alert)
                return True
            return False
        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {e}")
            return False

    def resolve_alert(self, alert_id: str, user_id: str, notes: str = None) -> bool:
        """Resolve an alert and move to history."""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert["status"] = "resolved"
                alert["resolved_by"] = user_id
                alert["resolved_at"] = datetime.utcnow().isoformat()
                if notes:
                    alert["notes"] = notes

                # Move to history
                self.alert_history.append(alert)
                del self.active_alerts[alert_id]

                self._update_alert_in_database(alert)
                return True
            return False
        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {e}")
            return False

# Global alert manager instance
alert_manager = AlertManager()
```

### User Management

User management is handled through FastAPI routers with database integration:

**Source:** `src/routers/users.py`

```python
def get_current_user(token_data: dict = Depends(jwt_auth), db: Session = Depends(get_db)) -> User:
    """Get current user from JWT token."""
    username = token_data.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

@router.post("/users/", response_model=UserResponse)
async def create_user(user_data: CreateUserRequest, db: Session = Depends(get_db)):
    """Create a new user."""
    # Check for existing user
    existing_user = db.query(User).filter(
        or_(User.username == user_data.username, User.email == user_data.email)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        permissions=user_data.permissions or get_default_permissions(user_data.role),
        is_active=True,
        is_verified=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return user_to_response(new_user)
```

## Database Initialization

### Initialization Script

**Source:** `src/database/init_db.py`

```python
import logging
from sqlalchemy import create_engine
from src.database.base import Base, DATABASE_URL
from src.database.models import *
from src.services.user_service import UserService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database with tables and default data."""
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)

        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        # Create default admin user
        create_default_admin()

        logger.info("Database initialization completed")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def create_default_admin():
    """Create default admin user."""
    from src.database.base import SessionLocal

    db = SessionLocal()
    try:
        user_service = UserService(db)

        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            logger.info("Admin user already exists")
            return

        # Create admin user
        admin_data = {
            "username": "admin",
            "email": "admin@example.com",
            "password": "admin123",  # Change in production
            "full_name": "System Administrator",
            "role": "admin"
        }

        admin = user_service.create_user(admin_data)
        logger.info(f"Created admin user: {admin.username}")

    finally:
        db.close()

if __name__ == "__main__":
    init_database()
```

## Performance Optimization

### Indexing Strategy

```python
# Important indexes for performance
CREATE INDEX CONCURRENTLY idx_alert_camera_timestamp ON alerts(camera_id, timestamp DESC);
CREATE INDEX CONCURRENTLY idx_alert_status_severity ON alerts(status, severity);
CREATE INDEX CONCURRENTLY idx_camera_enabled_status ON cameras(enabled, status);
CREATE INDEX CONCURRENTLY idx_frame_timestamp ON frames(timestamp DESC);
CREATE INDEX CONCURRENTLY idx_user_username ON users(username);
CREATE INDEX CONCURRENTLY idx_user_email ON users(email);
```

### Query Optimization

```python
# Efficient alert queries with proper indexing
def get_recent_alerts(camera_id: str, hours: int = 24):
    """Get recent alerts with optimized query."""
    start_time = datetime.utcnow() - timedelta(hours=hours)

    return db.query(Alert)\
        .filter(
            Alert.camera_id == camera_id,
            Alert.timestamp >= start_time
        )\
        .order_by(Alert.timestamp.desc())\
        .limit(100)\
        .all()

# Use pagination for large datasets
def get_alerts_paginated(page: int = 1, size: int = 50):
    """Get paginated alerts."""
    offset = (page - 1) * size

    return db.query(Alert)\
        .order_by(Alert.timestamp.desc())\
        .offset(offset)\
        .limit(size)\
        .all()
```

### Connection Pool Configuration

```python
# Optimized connection pool settings
engine = create_engine(
    DATABASE_URL,
    pool_size=20,           # Base connections
    max_overflow=30,        # Additional connections
    pool_timeout=30,        # Connection timeout
    pool_recycle=3600,      # Recycle connections hourly
    pool_pre_ping=True,     # Validate connections
    echo=False              # Disable SQL logging in production
)
```

## Backup and Recovery

### Backup Strategy

```bash
#!/bin/bash
# Database backup script

DB_NAME="shoplifting_detection"
DB_USER="postgres"
DB_HOST="localhost"
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
    --format=custom \
    --compress=9 \
    --file=$BACKUP_DIR/backup_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
```

### Recovery Process

```bash
# Restore from backup
pg_restore -h localhost -U postgres -d shoplifting_detection \
    --clean --if-exists \
    /backups/backup_20240101_120000.sql

# Verify data integrity
psql -h localhost -U postgres -d shoplifting_detection \
    -c "SELECT COUNT(*) FROM cameras; SELECT COUNT(*) FROM alerts;"
```

## Monitoring and Maintenance

### Health Checks

```python
def check_database_health():
    """Check database connectivity and performance."""
    try:
        from src.database.base import engine

        # Test connection
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")

        # Check table sizes
        table_stats = get_table_statistics()

        return {
            "status": "healthy",
            "connection": "ok",
            "tables": table_stats
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

def get_table_statistics():
    """Get table row counts and sizes."""
    from src.database.base import SessionLocal

    db = SessionLocal()
    try:
        stats = {}

        # Count rows in each table
        stats['cameras'] = db.query(Camera).count()
        stats['users'] = db.query(User).count()
        stats['alerts'] = db.query(Alert).count()
        stats['frames'] = db.query(Frame).count()

        return stats

    finally:
        db.close()
```

## Best Practices

1. **Connection Management**
   - Use connection pooling
   - Close sessions properly
   - Handle connection failures gracefully

2. **Migration Management**
   - Always backup before migrations
   - Test migrations on staging first
   - Use descriptive migration names

3. **Performance**
   - Add appropriate indexes
   - Use pagination for large datasets
   - Monitor query performance

4. **Security**
   - Use environment variables for credentials
   - Enable SSL for production
   - Implement proper user permissions
