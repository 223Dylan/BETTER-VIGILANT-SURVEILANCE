# Installation Guide

This guide provides detailed installation instructions for different deployment scenarios.

## Quick Installation Methods

### Method 1: Development Setup (Recommended)

**Best for**: Development, testing, and local deployment

This method runs infrastructure services (database, Redis, etc.) in Docker while running the Python application locally for easy development.

1. **Start infrastructure services:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. **Setup Python environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # OR
   .venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

3. **Initialize the system:**
   ```bash
   python scripts/init_system.py
   ```

4. **Start the application:**
   ```bash
   python main.py
   ```

### Method 2: Full Docker Setup

**Best for**: Production deployment, isolated environments

This method runs everything in Docker containers.

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Initialize database (one-time):**
   ```bash
   docker-compose exec app python scripts/init_system.py
   ```

### Method 3: Manual Local Setup

**Best for**: Custom configurations, specific requirements

For users who prefer to install all dependencies manually.

## Detailed Installation Steps

### Prerequisites

#### Required Software
- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/downloads)
- **Docker & Docker Compose** - [Download](https://www.docker.com/products/docker-desktop)

#### System Requirements
- **RAM:** 8GB minimum, 16GB recommended
- **Storage:** 10GB free space minimum
- **CPU:** 4 cores minimum (GPU optional for model inference)
- **OS:** Windows 10+, macOS 10.15+, or Ubuntu 20.04+

### Step-by-Step Development Setup

#### 1. Clone Repository
```bash
git clone <your-repository-url>
cd shoplifting-detection-system
```

#### 2. Configuration Files
```bash
# Copy example configurations
cp .env.example .env
cp config/config.example.yaml config/config.yaml
cp alembic.example.ini alembic.ini

# Edit .env file for your environment
# The defaults should work for development
```

#### 3. Infrastructure Services
```bash
# Start PostgreSQL, Redis, Elasticsearch, etc.
docker-compose -f docker-compose.dev.yml up -d

# Verify services are running
docker-compose -f docker-compose.dev.yml ps
```

Services started:
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Elasticsearch**: localhost:9200
- **Kibana**: localhost:5601

#### 4. Python Environment
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

#### 5. System Initialization
```bash
# Run comprehensive setup
python scripts/init_system.py

# Or run steps manually:
# python -c "from src.database.init_db import init_db; init_db()"
# python scripts/create_admin.py
```

This creates:
- Database tables and schema
- Admin user: `admin` / `admin123`
- Sample camera configuration

#### 6. Model Setup

**Critical**: The AI model file is required but not included in the repository.

See [models/README.md](../models/README.md) for:
- Model download instructions
- Training your own model
- Alternative model options

#### 7. Start Application
```bash
python main.py
```

Access points:
- **Web Interface**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

### Manual Local Installation

If you prefer to install services locally instead of Docker:

#### 1. Install PostgreSQL
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS (with Homebrew)
brew install postgresql

# Windows
# Download from: https://www.postgresql.org/download/windows/
```

Create database:
```sql
sudo -u postgres createdb shoplifting_detection
sudo -u postgres createuser --interactive --pwprompt shoplifting_user
```

#### 2. Install Redis
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS (with Homebrew)  
brew install redis

# Windows
# Download from: https://github.com/tporadowski/redis/releases
```

#### 3. Install Elasticsearch (Optional)
```bash
# Download and install from:
# https://www.elastic.co/downloads/elasticsearch

# Start service
sudo systemctl start elasticsearch
```

#### 4. Update Configuration
```bash
# Update .env file with your local service URLs
DATABASE_URL=postgresql://shoplifting_user:password@localhost:5432/shoplifting_detection
REDIS_URL=redis://localhost:6379/0
ELASTICSEARCH_URL=http://localhost:9200
```

### Production Deployment

#### Environment Variables
```bash
# Security (CHANGE THESE!)
SECRET_KEY=your-super-secure-secret-key-at-least-32-chars
ENCRYPTION_KEY=your-encryption-key
JWT_SECRET_KEY=your-jwt-secret

# Database (Production settings)
DATABASE_URL=postgresql://user:pass@prod-db:5432/shoplifting_detection
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Redis
REDIS_URL=redis://prod-redis:6379/0

# API Settings
API_HOST=0.0.0.0
API_PORT=8001
CORS_ALLOWED_ORIGINS=https://your-domain.com

# Logging
LOG_LEVEL=WARNING
```

#### Docker Compose for Production
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    build: .
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    ports:
      - "8001:8001"
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: shoplifting_detection
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:latest
    restart: unless-stopped

volumes:
  postgres_data:
```

## Troubleshooting

### Common Installation Issues

#### Docker Issues
```bash
# Permission denied
sudo docker-compose up -d

# Port conflicts
docker-compose -f docker-compose.dev.yml down
# Edit docker-compose.dev.yml to change ports
```

#### Database Issues
```bash
# Connection refused
docker-compose -f docker-compose.dev.yml logs postgres

# Wrong database name
# Check all configs use 'shoplifting_detection'
grep -r "frames_db" .  # Should return nothing
```

#### Python Issues
```bash
# Module not found
pip install -r requirements.txt

# Import errors
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### Model Issues
```bash
# Model file missing
ls -la models/lrcn_160S_90_90Q.h5

# Model loading errors
python -c "import tensorflow as tf; print(tf.__version__)"
```

### Performance Optimization

#### Development
```yaml
# docker-compose.dev.yml - Minimal services
services:
  postgres:
    # ... postgres config only
  redis:
    # ... redis config only
  # Comment out elasticsearch, kibana, logstash for faster startup
```

#### Production
```bash
# Enable model caching
USE_GPU=true
MODEL_CACHING=true

# Database connection pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Redis optimizations
REDIS_CACHE_TTL=3600
```

### Security Checklist

- [ ] Change all default passwords
- [ ] Update SECRET_KEY and encryption keys
- [ ] Configure HTTPS/SSL certificates
- [ ] Set up firewall rules
- [ ] Enable database SSL
- [ ] Configure Redis authentication
- [ ] Set up log monitoring
- [ ] Regular security updates

### Monitoring Setup

#### Log Aggregation (Optional)
```bash
# Start ELK stack
docker-compose -f docker-compose.dev.yml up -d elasticsearch kibana logstash

# Access Kibana
open http://localhost:5601
```

#### Health Checks
```bash
# API health
curl http://localhost:8001/health

# Database health
docker-compose -f docker-compose.dev.yml exec postgres pg_isready

# Redis health
docker-compose -f docker-compose.dev.yml exec redis redis-cli ping
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | postgres://... | PostgreSQL connection string |
| `REDIS_URL` | redis://localhost:6379/0 | Redis connection string |
| `SECRET_KEY` | (required) | JWT signing key |
| `API_HOST` | 0.0.0.0 | API server host |
| `API_PORT` | 8001 | API server port |
| `LOG_LEVEL` | INFO | Logging level |
| `USE_GPU` | false | Enable GPU for model inference |

### Docker Services

#### Core Services (Always Required)
- **postgres**: Database
- **redis**: Message broker and cache

#### Optional Services  
- **elasticsearch**: Log storage and search
- **kibana**: Log visualization
- **logstash**: Log processing

#### Application Services
- **app**: Main Python application
- **worker**: Celery background tasks

## Upgrade Guide

### Backup Before Upgrade
```bash
# Database backup
docker-compose -f docker-compose.dev.yml exec postgres pg_dump -U postgres shoplifting_detection > backup.sql

# Configuration backup
cp .env .env.backup
cp config/config.yaml config/config.yaml.backup
```

### Update Process
```bash
# Pull latest code
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Run migrations
python scripts/init_system.py --force

# Restart services
docker-compose -f docker-compose.dev.yml restart
python main.py
```

## Support

### Getting Help
1. Check [Troubleshooting Guide](12_TROUBLESHOOTING_GUIDE.md)
2. Review logs: `docker-compose -f docker-compose.dev.yml logs`
3. Run diagnostics: `python scripts/init_system.py --force`
4. Search existing GitHub issues
5. Create new issue with logs and system info

### Useful Commands
```bash
# System status
python scripts/init_system.py --force

# Service logs
docker-compose -f docker-compose.dev.yml logs --tail=50

# Database access
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres shoplifting_detection

# Reset everything
docker-compose -f docker-compose.dev.yml down -v
python scripts/init_system.py
``` 