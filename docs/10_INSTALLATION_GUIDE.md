# Installation Guide

This guide provides detailed installation instructions for different deployment scenarios.

## Installation Methods

### Method 1: Docker Development Environment (Recommended)

This method sets up all services (database, Redis, ELK stack) using Docker while running the Python application locally for development.

1. **Start infrastructure services:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. **Setup Python environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Initialize database:**
   ```bash
   alembic upgrade head
   python scripts/init_sample_data.py
   ```

4. **Start the application:**
   ```bash
   python main.py
   ```

### Method 2: Full Manual Setup

For users who prefer to install all dependencies manually.

1. **Install PostgreSQL:**
   - Create database: `createdb shoplifting_detection`
   - Update `DATABASE_URL` in `.env`

2. **Install Redis:**
   - Start Redis server on port 6379
   - Update `REDIS_URL` in `.env`

3. **Install ELK Stack (optional):**
   - Elasticsearch on port 9200
   - Logstash on port 5000
   - Kibana on port 5601

4. **Follow Python setup from Method 1**

### Method 3: Full Docker Setup

Run everything in containers (useful for production-like environment).

1. **Build and start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Access the application:**
   - API: http://localhost:8001
   - Frontend: http://localhost:3000 (if enabled)

## Configuration Files Setup

### Environment Variables (.env)

Copy and customize the environment file:
```bash
cp .env.example .env
```

Edit `.env` with your specific settings:

```bash
# Database
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/shoplifting_detection

# Security (CHANGE THESE!)
JWT_SECRET_KEY=your-super-secret-jwt-key-here
ENCRYPTION_PASSWORD=your-encryption-password
ENCRYPTION_SALT=your-encryption-salt

# Model Configuration
MODEL_PATH=models/lrcn_160S_90_90Q.h5
USE_GPU=false

# API Settings
API_PORT=8001
API_DEBUG=true
```

### Main Configuration (config/config.yaml)

Copy and customize the main configuration:
```bash
cp config/config.example.yaml config/config.yaml
```

Key settings to configure:

```yaml
# Model settings
model:
  path: "models/lrcn_160S_90_90Q.h5"
  use_gpu: false

# Detection thresholds
processing:
  probability_thresholds:
    low: 0.3
    medium: 0.6
    high: 0.8

# Camera configuration (add your cameras here)
cameras:
  # example_cameras:
  #   usb_camera_1:
  #     name: "Front Door Camera"
  #     source: 0
  #     enabled: true
```

### Database Migration Configuration

Copy the Alembic configuration:
```bash
cp alembic.example.ini alembic.ini
```

## Model Setup

The system requires an LRCN model file. You need to:

1. **Obtain or train an LRCN model** for shoplifting detection
2. **Place the model file** at `models/lrcn_160S_90_90Q.h5`
3. **Or update the path** in your configuration

> **Note:** The repository includes a placeholder model file. Replace it with your actual trained model.

## Directory Structure

The installation will create the following directories:

```
shoplifting-detection-system/
├── logs/                     # Application logs
├── uploads/                  # File uploads
│   └── videos/              # Video files
├── temp_frames/             # Temporary frame storage
├── output/                  # Processing output
├── keys/                    # Encryption keys (auto-generated)
├── data/                    # Data files
└── models/                  # AI model files
```

## Running the Application

### Development Mode

1. **Activate virtual environment:**
   ```bash
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate.bat  # Windows
   ```

2. **Start infrastructure (if using Docker):**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

3. **Start the application:**
   ```bash
   python main.py
   ```

4. **Start Celery worker (in another terminal):**
   ```bash
   source .venv/bin/activate
   celery -A src.tasks worker --loglevel=info
   ```

5. **Start frontend (if available):**
   ```bash
   npm run dev
   ```

### Production Mode

For production deployment, use the main docker-compose file:

```bash
docker-compose up -d
```

## Verification

### Check Services

1. **API Health:**
   ```bash
   curl http://localhost:8001/health
   ```

2. **Database Connection:**
   ```bash
   # Test from within virtual environment
   python -c "from src.database.base import engine; print('Database OK')"
   ```

3. **Redis Connection:**
   ```bash
   redis-cli ping
   ```

4. **Elasticsearch:**
   ```bash
   curl http://localhost:9200
   ```

### Access Points

Once running, you can access:

- **API Documentation:** http://localhost:8001/docs
- **API Alternative Docs:** http://localhost:8001/redoc
- **Main Application:** http://localhost:3000 (if frontend is running)
- **Database Admin:** http://localhost:8080 (PgAdmin, if using Docker)
- **Redis Admin:** http://localhost:8081 (Redis Commander, if using Docker)
- **Kibana Dashboard:** http://localhost:5601 (if using ELK stack)

## Default Credentials

**Database Admin (PgAdmin):**
- Email: admin@example.com
- Password: admin123

**Application Admin User:**
- Username: admin
- Password: admin123

> **Important:** Change these default credentials before production use!

## Platform-Specific Instructions

### Windows

- Use `python` instead of `python3`
- Use backslashes in paths: `scripts\setup_dev.bat`
- Install Visual C++ Build Tools if compilation errors occur
- Consider using Windows Subsystem for Linux (WSL) for better compatibility

### macOS

- Install Xcode Command Line Tools: `xcode-select --install`
- Use Homebrew for additional dependencies: `brew install postgresql`
- May need to install OpenSSL: `brew install openssl`

### Linux (Ubuntu/Debian)

- Install system dependencies:
  ```bash
  sudo apt-get update
  sudo apt-get install python3-dev postgresql-dev build-essential
  ```
- Ensure Docker permissions: `sudo usermod -aG docker $USER`

## Performance Optimization

### GPU Support

To enable GPU acceleration:

1. **Install CUDA and cuDNN** (NVIDIA GPUs only)
2. **Install TensorFlow GPU:**
   ```bash
   pip install tensorflow-gpu
   ```
3. **Update configuration:**
   ```bash
   USE_GPU=true
   ```

### Memory Management

For systems with limited memory:

```yaml
# In config/config.yaml
performance:
  max_memory_usage_mb: 2048
  processing_threads: 2
  max_concurrent_cameras: 3
```

### Database Optimization

Add indexes for better performance:

```sql
-- Connect to your database and run:
CREATE INDEX idx_alert_camera_timestamp ON alerts(camera_id, timestamp);
CREATE INDEX idx_frame_timestamp ON frames(timestamp);
```

## Security Considerations

Before deploying to production:

1. **Change all default passwords**
2. **Generate secure JWT secrets:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
3. **Enable HTTPS** with proper SSL certificates
4. **Configure firewall** to restrict access to necessary ports only
5. **Regularly update dependencies:**
   ```bash
   pip install -r requirements.txt --upgrade
   ```
6. **Set up proper backup procedures** for database and model files

## Uninstallation

To remove the system:

1. **Stop all services:**
   ```bash
   docker-compose -f docker-compose.dev.yml down -v
   ```

2. **Remove virtual environment:**
   ```bash
   rm -rf .venv
   ```

3. **Remove generated files:**
   ```bash
   rm -rf logs/ uploads/ temp_frames/ output/ keys/
   ```

4. **Remove Docker images (optional):**
   ```bash
   docker system prune -a
   ```

## Next Steps

After installation:

1. **Read the [Configuration Guide](11_CONFIGURATION_GUIDE.md)** to customize your setup
2. **Set up cameras** using the [Camera Management](04_CAMERA_MANAGEMENT.md) guide
3. **Configure alerts** with the [Alert System](05_ALERT_SYSTEM.md) documentation
4. **Monitor system performance** using [Monitoring and Analytics](09_MONITORING_ANALYTICS.md) 