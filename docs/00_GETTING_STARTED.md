# Getting Started

Welcome to the Shoplifting Detection System! This guide will help you get up and running quickly.

## Quick Start

### Automated Setup (Recommended)

**For Linux/macOS:**
```bash
git clone <your-repository-url>
cd shoplifting-detection-system
chmod +x scripts/setup_dev.sh
./scripts/setup_dev.sh
```

**For Windows:**
```cmd
git clone <your-repository-url>
cd shoplifting-detection-system
scripts\setup_dev.bat
```

### Manual Setup

1. **Clone and enter the repository:**
   ```bash
   git clone <your-repository-url>
   cd shoplifting-detection-system
   ```

2. **Copy configuration files:**
   ```bash
   cp .env.example .env
   cp config/config.example.yaml config/config.yaml
   cp alembic.example.ini alembic.ini
   ```

3. **Create virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # OR
   .venv\Scripts\activate.bat  # Windows
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Start development services:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

6. **Initialize database:**
   ```bash
   alembic upgrade head
   python scripts/init_sample_data.py
   ```

7. **Start the application:**
   ```bash
   # Start the main application (includes API server)
   python main.py
   
   # In a separate terminal, start frontend (optional)
   npm start
   
   # In another terminal, start Celery worker (optional)
   celery -A src.tasks worker --loglevel=info
   ```

## Prerequisites

### Required Software
- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/downloads)
- **Docker & Docker Compose** - [Download](https://www.docker.com/products/docker-desktop) (recommended for databases)

### Optional Software
- **Node.js 18+** - [Download](https://nodejs.org/) (for frontend development)
- **PostgreSQL 12+** - [Download](https://www.postgresql.org/download/) (if not using Docker)
- **Redis** - [Download](https://redis.io/download/) (if not using Docker)

### System Requirements
- **RAM:** 8GB minimum, 16GB recommended
- **Storage:** 10GB free space minimum
- **CPU:** 4 cores minimum (GPU optional for model inference)
- **OS:** Windows 10+, macOS 10.15+, or Ubuntu 20.04+

## What You Get

After setup, you'll have:

### Default Users (Change passwords for production!)
- **admin / admin123** - System Administrator
- **operator / operator123** - Security Operator  
- **viewer / viewer123** - Security Viewer

### Sample Cameras (Disabled by default)
- **demo-usb-cam-01** - USB Camera example
- **demo-ip-cam-01** - IP Camera example
- **demo-video-file** - Video file example

### Access Points
- **API Documentation:** http://localhost:8001/docs
- **Main Application:** http://localhost:3000 (if frontend running)
- **Database Admin:** http://localhost:8080 (PgAdmin)
- **Redis Admin:** http://localhost:8081 (Redis Commander)
- **Kibana Dashboard:** http://localhost:5601 (System monitoring)

## Next Steps

1. **Configure your environment** - Edit `.env` with your specific settings
2. **Add your AI model** - Place your LRCN model at `models/lrcn_160S_90_90Q.h5`
3. **Add real cameras** - Configure your cameras in `config/config.yaml`
4. **Start detection** - Enable cameras and begin monitoring

## Need Help?

- **Detailed Setup:** See [Installation Guide](10_INSTALLATION_GUIDE.md)
- **Configuration:** See [Configuration Guide](11_CONFIGURATION_GUIDE.md)
- **Camera Setup:** See [Camera Management](04_CAMERA_MANAGEMENT.md)
- **Troubleshooting:** See [Troubleshooting Guide](12_TROUBLESHOOTING_GUIDE.md)

## Security Warning

This system is designed for legitimate security monitoring. Ensure compliance with local privacy laws and regulations when deploying. Change all default passwords before production use! 