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
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   cameras   │    │    users    │    │   alerts    │    │   frames    │
├─────────────┤    ├─────────────┤    ├─────────────┤    ├─────────────┤
│ id (PK)     │    │ id (PK)     │    │ id (PK)     │    │ id (PK)     │
│ name        │    │ username    │    │ camera_id   │    │ timestamp   │
│ source      │    │ email       │    │ type        │    │ sequence_no │
│ fps         │    │ role        │    │ severity    │    │ frame_data  │
│ enabled     │    │ created_at  │    │ confidence  │    │ metadata    │
│ ...         │    │ ...         │    │ ...         │    │ ...         │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## Database Models

### Camera Model

**Source:** `src/database/models/camera.py`

```python
class Camera(Base):
    """Camera configuration and status model."""
    __tablename__ = "cameras"
    
    # Primary identification
    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True, nullable=False)
    
    # Connection details
    source = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False, default="webcam")
    
    # Video settings
    fps = Column(Integer, default=15, nullable=False)
    resolution_width = Column(Integer, default=640)
    resolution_height = Column(Integer, default=480)
    brightness = Column(Float, default=1.0, nullable=False)
    
    # Processing settings
    detection_enabled = Column(Boolean, default=True, nullable=False)
    detection_sensitivity = Column(Float, default=0.5)
    recording_enabled = Column(Boolean, default=False, nullable=False)
    
    # Location and metadata
    location = Column(String(255))
    zone = Column(String(100))
    advanced_settings = Column(JSON, default={})
    
    # Status tracking
    status = Column(String(50), default="stopped")
    error_message = Column(Text)
    last_online = Column(DateTime(timezone=True))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### User Model

**Source:** `src/database/models/user.py`

```python
class User(Base):
    """User authentication and authorization model."""
    __tablename__ = "users"
    
    # Primary identification
    id = Column(String, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    
    # Authentication
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Authorization
    role = Column(String(50), default="user", nullable=False)
    permissions = Column(JSON, default={})
    
    # Profile information
    full_name = Column(String(100))
    last_login = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0)
    
    # Security settings
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### Alert Model

**Source:** `src/database/models/alert.py`

```python
class Alert(Base):
    """Security alert and incident model."""
    __tablename__ = "alerts"
    
    # Primary identification
    id = Column(String, primary_key=True)
    camera_id = Column(String(255), nullable=False, index=True)
    
    # Classification
    type = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="active", index=True)
    
    # Detection data
    confidence = Column(Float, nullable=False)
    message = Column(Text, nullable=False)
    source = Column(String(100), default="detection", nullable=False)
    detection_data = Column(JSON, default={})
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), nullable=False)
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
        Index('idx_alert_camera_timestamp', 'camera_id', 'timestamp'),
        Index('idx_alert_status_severity', 'status', 'severity'),
        Index('idx_alert_type_timestamp', 'type', 'timestamp'),
    )
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

## Database Services

### Camera Service

```python
class CameraService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_camera(self, camera_id: str) -> Optional[Camera]:
        """Get camera by ID."""
        return self.db.query(Camera).filter(Camera.id == camera_id).first()
    
    def get_cameras(self, enabled_only: bool = False) -> List[Camera]:
        """Get all cameras."""
        query = self.db.query(Camera)
        if enabled_only:
            query = query.filter(Camera.enabled == True)
        return query.all()
    
    def create_camera(self, camera_data: dict) -> Camera:
        """Create new camera."""
        camera = Camera(**camera_data)
        self.db.add(camera)
        self.db.commit()
        self.db.refresh(camera)
        return camera
    
    def update_camera(self, camera_id: str, updates: dict) -> Optional[Camera]:
        """Update camera configuration."""
        camera = self.get_camera(camera_id)
        if not camera:
            return None
        
        for field, value in updates.items():
            if hasattr(camera, field):
                setattr(camera, field, value)
        
        camera.updated_at = datetime.utcnow()
        self.db.commit()
        return camera
    
    def delete_camera(self, camera_id: str) -> bool:
        """Delete camera."""
        camera = self.get_camera(camera_id)
        if not camera:
            return False
        
        self.db.delete(camera)
        self.db.commit()
        return True
```

### User Service

```python
class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: dict) -> User:
        """Create new user."""
        # Hash password
        password_hash = self._hash_password(user_data['password'])
        
        user = User(
            id=str(uuid.uuid4()),
            username=user_data['username'],
            email=user_data['email'],
            password_hash=password_hash,
            full_name=user_data.get('full_name'),
            role=user_data.get('role', 'user')
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials."""
        user = self.db.query(User).filter(
            User.username == username,
            User.is_active == True
        ).first()
        
        if not user or not self._verify_password(password, user.password_hash):
            if user:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                self.db.commit()
            return None
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        user.login_count += 1
        self.db.commit()
        
        return user
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _verify_password(self, password: str, hash: str) -> bool:
        """Verify password against hash."""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hash.encode('utf-8'))
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