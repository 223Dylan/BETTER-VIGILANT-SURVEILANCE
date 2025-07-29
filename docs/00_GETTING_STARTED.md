# Getting Started

Welcome to the Shoplifting Detection System! This guide will help you get up and running quickly.

## Quick Start

### Automated Setup (Recommended)

**For Windows:**
```cmd
git clone <your-repository-url>
cd shoplifting-detection-system
scripts\setup_dev.bat
```

**For Linux/macOS:**
```bash
git clone <your-repository-url>
cd shoplifting-detection-system
chmod +x scripts/setup_dev.sh
./scripts/setup_dev.sh
```

### Manual Setup

#### Step 1: Clone and Configure

1. **Clone the repository:**
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

#### Step 2: Python Environment

1. **Create virtual environment:**
   ```bash
   python3 -m venv .venv

   # Linux/macOS
   source .venv/bin/activate

   # Windows
   .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

#### Step 3: Infrastructure Services

Start the required services using Docker:

```bash
# Development setup (infrastructure only)
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to start (30-60 seconds)
docker-compose -f docker-compose.dev.yml logs
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Elasticsearch (port 9200)
- Kibana (port 5601)

#### Step 4: System Initialization

Run the comprehensive initialization script:

```bash
python scripts/init_system.py
```

This will:
- Check dependencies
- Initialize database
- Create admin user (admin/admin123)
- Set up sample camera
- Verify system components

#### Step 5: Model Setup

**Important**: The system requires an AI model file that's not included in the repository.

See [models/README.md](../models/README.md) for detailed instructions on:
- Downloading the pre-trained model
- Training your own model
- Using alternative models

#### Step 6: Start the Application

```bash
python main.py
```

#### Step 6: Frontend Setup

In a new terminal, set up and start the React frontend:

```bash
# Install Node.js dependencies
npm install

# Start the React development server
npm start
```

The application will be available at:
- **Frontend Web Interface**: http://localhost:3000 (Main user interface)
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs

## First Login

1. Open http://localhost:3000
2. Login with:
   - **Username**: `admin`
   - **Password**: `admin123`
3. **Important**: Change the default password immediately!

## Verification Checklist

After setup, verify these components are working:

- [ ] Frontend loads (http://localhost:3000)
- [ ] Backend API responds (http://localhost:8001/api/health)
- [ ] Can login with admin credentials
- [ ] Database is connected (no connection errors)
- [ ] Camera appears in camera list
- [ ] Docker services are running
- [ ] Model file exists (if doing detection)
- [ ] WebSocket connections working (real-time updates)

## Troubleshooting

### Common Issues

#### Import Errors
```
ModuleNotFoundError: No module named 'src'
```
**Solution**: Make sure you're in the project root directory and virtual environment is activated.

#### Database Connection Failed
```
psycopg2.OperationalError: connection to server ... failed
```
**Solutions**:
1. Start Docker services: `docker-compose -f docker-compose.dev.yml up -d`
2. Wait for PostgreSQL to fully start (check logs)
3. Verify database name matches in all configs

#### Model Not Found
```
FileNotFoundError: Unable to open file models/lrcn_160S_90_90Q.h5
```
**Solution**: See [models/README.md](../models/README.md) for model setup instructions.

#### Camera Initialization Failed
```
Failed to read test frame from camera
```
**Solutions**:
1. Check camera permissions
2. Close other applications using the camera
3. Try different camera index (0, 1, 2)
4. Update camera settings in web interface

#### Admin User Creation Failed
```
Error creating admin user
```
**Solutions**:
1. Ensure database is running and accessible
2. Run database migrations: `python scripts/init_system.py`
3. Check for existing admin user

### Port Conflicts

If you get port conflicts, update these files:

**docker-compose.dev.yml**:
```yaml
ports:
  - "5433:5432"  # Change PostgreSQL port
  - "6380:6379"  # Change Redis port
```

**Update .env accordingly**:
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/shoplifting_detection
REDIS_URL=redis://localhost:6380/0
```

### Windows-Specific Issues

#### PowerShell Execution Policy
```
execution of scripts is disabled on this system
```
**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Virtual Environment Launcher Issues
```
Fatal error in launcher: Unable to create process
```
**Solution**: Recreate virtual environment:
```cmd
rmdir /s .venv
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Performance Issues

#### High CPU/Memory Usage
- Reduce camera resolution in settings
- Lower FPS settings
- Disable unnecessary services (Elasticsearch, Kibana)
- Use `docker-compose down elasticsearch kibana logstash`

#### Slow Frame Processing
- Check camera settings (resolution, FPS)
- Verify model preprocessing pipeline
- Monitor system resources

## Next Steps

After successful setup:

1. **Configure Cameras**: Add your IP cameras or adjust webcam settings
2. **Test Detection**: Upload test videos or use live camera feed
3. **Set Up Alerts**: Configure notification preferences
4. **Review Logs**: Check Kibana dashboard for system monitoring
5. **Production Setup**: See [Installation Guide](10_INSTALLATION_GUIDE.md) for production deployment

## Additional Resources

- [System Overview](01_SYSTEM_OVERVIEW.md)
- [Configuration Guide](11_CONFIGURATION_GUIDE.md)
- [API Documentation](07_API_SYSTEM.md)
- [Troubleshooting Guide](12_TROUBLESHOOTING_GUIDE.md)

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](12_TROUBLESHOOTING_GUIDE.md)
2. Review logs: `docker-compose -f docker-compose.dev.yml logs`
3. Run diagnostics: `python scripts/init_system.py --force`
4. Check GitHub issues or create a new one

## Next Steps

Now that you have the basic system running, explore these guides based on your role:

### **For Developers**
- **[Frontend Architecture Guide](15_FRONTEND_ARCHITECTURE_GUIDE.md)** - Understanding the React/TypeScript frontend
- **[API Reference](16_API_REFERENCE.md)** - Complete API documentation with examples
- **[Development Workflow Guide](17_DEVELOPMENT_WORKFLOW_GUIDE.md)** - Development process, testing, and best practices

### **For DevOps/System Administrators**
- **[Deployment Guide](18_DEPLOYMENT_GUIDE.md)** - Production deployment scenarios and infrastructure
- **[Configuration Guide](11_CONFIGURATION_GUIDE.md)** - Detailed configuration options
- **[Monitoring & Analytics](09_MONITORING_ANALYTICS.md)** - Setting up observability

### **For Security Operators**
- **[Authentication & Security](08_AUTHENTICATION_SECURITY.md)** - Security implementation details
- **[Alert System](05_ALERT_SYSTEM.md)** - Alert management and configuration

### **For System Understanding**
- **[System Overview](01_SYSTEM_OVERVIEW.md)** - Architecture and components
- **[Database System](06_DATABASE_SYSTEM.md)** - Database schema and management
- **[Troubleshooting Guide](12_TROUBLESHOOTING_GUIDE.md)** - Common issues and solutions

## Security Notes

- Change default passwords immediately
- Use environment variables for sensitive data
- Enable HTTPS in production
- Regularly update dependencies
- Review camera access permissions
