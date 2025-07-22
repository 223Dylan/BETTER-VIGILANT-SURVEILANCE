# Database System Documentation

## Overview

This project uses **PostgreSQL** with **SQLAlchemy** ORM and **Alembic** for database migrations. The database system has been completely refactored to use proper migration management.

## Database Models

### Core Models

1. **`Frame`** (`models/frame.py`)
   - Stores captured frame data
   - Binary frame storage with metadata
   - Sequence tracking

2. **`Camera`** (`models/camera.py`)
   - Camera configuration and settings
   - Status tracking (stopped, starting, active, error)
   - Video settings (resolution, FPS, detection sensitivity)

3. **`User`** (`models/user.py`)
   - User authentication and authorization
   - Role-based permissions (admin/user)
   - Activity tracking

4. **`Alert`** (`models/alert.py`)
   - Security alert persistence
   - Detection data and confidence scores
   - Alert lifecycle management (active → acknowledged → resolved)

## Migration System

### Alembic Migrations

The project uses **Alembic** for professional database versioning:

```bash
# Check migration status
alembic current

# View migration history
alembic history --verbose

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Generate new migration
alembic revision --autogenerate -m "Description"
```

### Migration History

1. **`4ed1393c0e75`** - Initial migration (frames table)
2. **`455924c09f24`** - Add cameras, users, and alerts tables

## Database Management

### Quick Setup

```bash
# Initialize database with migrations
python src/database/init_db.py

# Or use the management script
python scripts/database_management.py init
```

### Management Script

Use `scripts/database_management.py` for common operations:

```bash
# Initialize database
python scripts/database_management.py init

# Run migrations
python scripts/database_management.py migrate

# Check status
python scripts/database_management.py status

# Rollback last migration
python scripts/database_management.py rollback

# Create admin user
python scripts/database_management.py create-user

# Reset database (DANGEROUS)
python scripts/database_management.py reset --force
```

## Configuration

### Environment Variables

Set these in your `.env` file:

```env
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=frames_db

# Connection pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
```

### Connection Pooling

The database uses SQLAlchemy connection pooling for optimal performance:
- Pool size: 20 connections
- Max overflow: 10 additional connections
- Pool timeout: 30 seconds
- Pool recycle: 30 minutes

## Database Schema

### Tables Created

1. **`frames`** - Video frame storage
2. **`cameras`** - Camera configurations
3. **`users`** - User management
4. **`alerts`** - Security alerts

### Indexes

Performance indexes are automatically created:
- Alert queries by camera, severity, status, timestamp
- User lookups by username and email
- Frame sequence and timestamp queries

## Development Workflow

### Adding New Models

1. Create model in `src/database/models/`
2. Import in `migrations/env.py`
3. Generate migration:
   ```bash
   alembic revision --autogenerate -m "Add new model"
   ```
4. Review and apply:
   ```bash
   alembic upgrade head
   ```

### Schema Changes

1. Modify existing model
2. Generate migration:
   ```bash
   alembic revision --autogenerate -m "Update model"
   ```
3. Review generated migration carefully
4. Apply migration:
   ```bash
   alembic upgrade head
   ```

## Troubleshooting

### Common Issues

**Migration Conflicts:**
```bash
# If tables already exist, stamp current state
alembic stamp head
```

**Database Connection Issues:**
- Check PostgreSQL is running
- Verify environment variables
- Check database exists

**Migration Failures:**
- Review migration files for errors
- Use rollback if needed: `alembic downgrade -1`
- Check database permissions

### Legacy System Migration

If upgrading from the old `init_db.py` direct table creation:

1. The system automatically detects existing tables
2. Uses `alembic stamp head` to sync migration state
3. Falls back to direct creation if migrations fail

## Best Practices

1. **Always backup** before running migrations in production
2. **Review generated migrations** before applying
3. **Test migrations** in development first
4. **Use transactions** for complex data migrations
5. **Document schema changes** in migration messages

## Files Structure

```
src/database/
├── models/
│   ├── base.py          # Database configuration
│   ├── frame.py         # Frame model
│   ├── camera.py        # Camera model
│   ├── user.py          # User model
│   └── alert.py         # Alert model
├── migrations/
│   ├── env.py           # Alembic environment
│   ├── script.py.mako   # Migration template
│   └── versions/        # Migration files
├── init_db.py           # Database initialization
└── README.md            # This file

scripts/
└── database_management.py  # Management utilities
```

## Production Deployment

1. Set production environment variables
2. Run migrations: `alembic upgrade head`
3. Create admin user: `python scripts/database_management.py create-user`
4. Monitor connection pool usage
5. Set up regular backups

---

**Note:** The old custom migration scripts (`add_alerts_table.py`) are deprecated and should not be used. All schema changes now go through Alembic.
