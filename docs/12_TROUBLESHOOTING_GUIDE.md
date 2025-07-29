# Troubleshooting Guide

This guide helps you diagnose and fix common issues with the Shoplifting Detection System.

## Quick Diagnostics

Run these commands to check system health:

```bash
# Check API health
curl http://localhost:8001/api/health

# Check frontend
curl http://localhost:3000

# Check database connection
python -c "from src.database.base import engine; engine.connect(); print('DB OK')"

# Check Redis connection
redis-cli ping

# Check Elasticsearch
curl http://localhost:9200/_health

# Check logs
tail -f logs/main.log

# Check Docker services
docker-compose ps
```

## Common Issues

### 1. Installation Issues

#### Python Dependencies Failing

**Error:** `pip install` fails with compilation errors

**Solutions:**
```bash
# Update pip and setuptools
pip install --upgrade pip setuptools wheel

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install python3-dev libpq-dev build-essential

# Install system dependencies (macOS)
xcode-select --install
brew install postgresql

# Install system dependencies (Windows)
# Install Visual Studio Build Tools
```

#### Docker Issues

**Error:** `docker-compose` fails to start services

**Solutions:**
```bash
# Check Docker is running
docker --version
docker-compose --version

# Reset Docker volumes
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d

# Check ports aren't in use
netstat -tulpn | grep :5432  # PostgreSQL
netstat -tulpn | grep :6379  # Redis
netstat -tulpn | grep :9200  # Elasticsearch
```

### 2. Frontend Issues

#### React Development Server Won't Start

**Error:** `npm start` fails or frontend not loading

**Solutions:**
```bash
# Check Node.js version (requires 18+)
node --version
npm --version

# Clear npm cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for port conflicts
netstat -tulpn | grep :3000

# Start with specific port
PORT=3001 npm start

# Check for TypeScript errors
npm run build
```

#### Frontend API Connection Issues

**Error:** Frontend can't connect to backend API

**Check:**
1. Backend is running on port 8001
2. CORS configuration allows frontend origin
3. API endpoints returning expected responses

**Solutions:**
```bash
# Verify backend is running
curl http://localhost:8001/api/health

# Check CORS settings in .env
grep CORS_ALLOWED_ORIGINS .env

# Test API endpoints manually
curl http://localhost:8001/api/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Check browser network tab for specific errors
# Look for 401 (auth), 403 (permissions), 500 (server) errors
```

#### Build Failures

**Error:** `npm run build` fails with TypeScript or dependency errors

**Solutions:**
```bash
# Check TypeScript configuration
npx tsc --noEmit

# Update dependencies
npm update

# Clear TypeScript cache
rm -rf node_modules/.cache
npm run build

# Check for specific import errors
npm run lint
```

### 3. Database Issues

#### Connection Refused

**Error:** `psycopg2.OperationalError: could not connect to server`

**Check:**
1. Database service is running
2. Correct DATABASE_URL in .env
3. Firewall/network settings

**Solutions:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Start PostgreSQL container
docker-compose -f docker-compose.dev.yml up -d postgres

# Check DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql://user:password@host:port/database

# Test connection manually
psql -h localhost -U postgres -d shoplifting_detection
```

#### Migration Errors

**Error:** `alembic.util.exc.CommandError: Can't locate revision`

**Solutions:**
```bash
# Check current migration status
alembic current

# Reset to head
alembic upgrade head

# If tables exist, stamp current version
alembic stamp head

# If completely broken, reset database
docker-compose -f docker-compose.dev.yml down -v postgres
docker-compose -f docker-compose.dev.yml up -d postgres
alembic upgrade head
python scripts/init_sample_data.py
```

### 3. Model Issues

#### Model Not Found

**Error:** `FileNotFoundError: [Errno 2] No such file or directory: 'models/lrcn_160S_90_90Q.h5'`

**Solutions:**
1. Place your trained model in the `models/` directory
2. Update MODEL_PATH in .env or config.yaml
3. Ensure model file permissions are correct

```bash
# Check model file exists
ls -la models/
chmod 644 models/lrcn_160S_90_90Q.h5

# Verify model path in config
grep -r "lrcn_160S_90_90Q.h5" .env config/
```

#### Model Loading Errors

**Error:** `ValueError: Error when checking model input`

**Solutions:**
1. Verify model architecture matches expected input shape
2. Check TensorFlow version compatibility
3. Ensure model was saved correctly

```bash
# Check TensorFlow version
python -c "import tensorflow as tf; print(tf.__version__)"

# Verify model structure
python -c "
from tensorflow.keras.models import load_model
model = load_model('models/lrcn_160S_90_90Q.h5')
print(model.summary())
"
```

#### GPU Issues

**Error:** CUDA errors or GPU not detected

**Solutions:**
```bash
# Check CUDA installation
nvidia-smi

# Check TensorFlow GPU support
python -c "
import tensorflow as tf
print('GPUs:', tf.config.list_physical_devices('GPU'))
"

# Install TensorFlow GPU (if needed)
pip uninstall tensorflow
pip install tensorflow-gpu

# Disable GPU if causing issues
# In .env: USE_GPU=false
```

### 4. Camera Issues

#### Camera Not Detected

**Error:** `cv2.error: OpenCV: can't open camera`

**Solutions:**
```bash
# Check camera permissions (Linux)
sudo usermod -a -G video $USER
# Logout and login again

# Test camera manually
python -c "
import cv2
cap = cv2.VideoCapture(0)
print('Camera opened:', cap.isOpened())
cap.release()
"

# Check available cameras (Linux)
ls /dev/video*

# Check camera in use by other application
lsof /dev/video0
```

#### RTSP Stream Issues

**Error:** Cannot connect to IP camera

**Solutions:**
1. Verify RTSP URL format
2. Check network connectivity
3. Test with VLC or similar

```bash
# Test RTSP stream with FFmpeg
ffmpeg -i "rtsp://username:password@ip:port/stream" -t 10 output.mp4

# Test network connectivity
ping camera_ip
telnet camera_ip 554

# Check firewall settings
# Ensure ports 554 (RTSP) and 6970-6999 (RTP) are open
```

#### Frame Processing Errors

**Error:** Frames not being processed or poor quality

**Solutions:**
1. Check camera FPS settings
2. Adjust processing parameters
3. Monitor system resources

```bash
# Check camera configuration
cat config/config.yaml | grep -A 10 cameras

# Monitor processing performance
top -p $(pgrep -f api_server.py)

# Check frame processing logs
grep "frame" logs/main.log | tail -20
```

### 5. API Issues

#### Server Won't Start

**Error:** `OSError: [Errno 98] Address already in use`

**Solutions:**
```bash
# Check what's using the port
netstat -tulpn | grep :8001
lsof -i :8001

# Kill process using the port
sudo kill -9 $(lsof -t -i:8001)

# Change port in configuration
# In .env: API_PORT=8002
```

#### High Memory Usage

**Error:** Server becomes unresponsive or crashes

**Solutions:**
```bash
# Monitor memory usage
free -h
ps aux | grep python | head -10

# Reduce memory usage in config
# In config.yaml:
processing:
  processing_threads: 2
  max_queue_size: 20

# Restart with memory limits
python -X dev main.py
```

#### Authentication Issues

**Error:** `401 Unauthorized` or JWT errors

**Solutions:**
```bash
# Check JWT secret configuration
grep JWT_SECRET .env

# Generate new JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Test authentication
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Clear browser cache/cookies
# Or use incognito/private browsing mode
```

### 6. Redis Issues

#### Connection Failed

**Error:** `redis.exceptions.ConnectionError`

**Solutions:**
```bash
# Check Redis is running
docker ps | grep redis
redis-cli ping

# Start Redis container
docker-compose -f docker-compose.dev.yml up -d redis

# Check Redis configuration
grep REDIS .env

# Test Redis connection
python -c "
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
print(r.ping())
"
```

### 7. Elasticsearch/Logstash Issues

#### Elasticsearch Not Starting

**Error:** Elasticsearch fails to start or is unreachable

**Solutions:**
```bash
# Check Elasticsearch status
curl http://localhost:9200/_cluster/health

# Check Docker logs
docker logs $(docker ps -q -f name=elasticsearch)

# Increase memory limit (if needed)
# Add to docker-compose.dev.yml:
environment:
  - "ES_JAVA_OPTS=-Xms512m -Xmx512m"

# Reset Elasticsearch data
docker-compose -f docker-compose.dev.yml down -v elasticsearch
docker-compose -f docker-compose.dev.yml up -d elasticsearch
```

#### Logstash Configuration Errors

**Error:** Logstash fails to process logs

**Solutions:**
```bash
# Check Logstash logs
docker logs $(docker ps -q -f name=logstash)

# Validate Logstash configuration
docker exec -it $(docker ps -q -f name=logstash) \
  bin/logstash --config.test_and_exit

# Check Logstash pipeline
curl -X GET "localhost:9600/_node/pipelines"
```

### 8. Frontend Issues

#### Frontend Won't Start

**Error:** React development server fails

**Solutions:**
```bash
# Check Node.js version
node --version
npm --version

# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Start with verbose logging
npm run dev --verbose
```

#### API Connection Issues

**Error:** Frontend can't connect to API

**Solutions:**
```bash
# Check API URL configuration
grep REACT_APP_API_URL .env

# Test API from browser
# Open: http://localhost:8001/docs

# Check CORS configuration
grep CORS .env

# Test API connectivity
curl http://localhost:8001/health
```

### 9. Performance Issues

#### High CPU Usage

**Symptoms:** System becomes slow, high CPU usage

**Solutions:**
1. Reduce processing threads
2. Lower camera FPS
3. Enable frame skipping
4. Optimize model inference

```bash
# Monitor CPU usage
top -p $(pgrep -f api_server.py)

# Reduce processing load
# In config.yaml:
processing:
  processing_threads: 2
  skip_frames: 2  # Process every 3rd frame

cameras:
  defaults:
    fps: 10  # Reduce from 30
```

#### High Memory Usage

**Symptoms:** System becomes unresponsive, out of memory errors

**Solutions:**
```bash
# Monitor memory usage
free -h
ps aux --sort=-%mem | head -10

# Reduce memory usage
# In config.yaml:
processing:
  max_queue_size: 20
  frame_buffer:
    max_size: 50

# Restart services
sudo systemctl restart docker
docker-compose -f docker-compose.dev.yml restart
```

#### Slow Detection

**Symptoms:** Long delays in detection results

**Solutions:**
1. Enable GPU if available
2. Reduce model sequence length
3. Optimize preprocessing
4. Increase processing threads

```bash
# Enable GPU (if available)
# In .env: USE_GPU=true

# Check GPU utilization
nvidia-smi

# Optimize preprocessing
# In config.yaml:
preprocessing:
  background_removal: false
  gaussian_blur: false
```

## Log Analysis

### Common Log Patterns

**Database connection issues:**
```bash
grep -i "database\|connection\|psycopg2" logs/main.log
```

**Camera issues:**
```bash
grep -i "camera\|cv2\|opencv" logs/main.log
```

**Model issues:**
```bash
grep -i "model\|tensorflow\|prediction" logs/main.log
```

**Memory issues:**
```bash
grep -i "memory\|oom\|killed" logs/main.log
```

### Log Levels

Adjust log level for debugging:

```bash
# In .env
LOG_LEVEL=DEBUG

# Restart application
python main.py
```

## System Monitoring

### Health Checks

Create monitoring script:

```bash
#!/bin/bash
# health_check.sh

echo "=== System Health Check ==="

# API Health
echo -n "API: "
curl -s http://localhost:8001/health && echo "OK" || echo "FAILED"

# Database
echo -n "Database: "
docker exec $(docker ps -q -f name=postgres) pg_isready && echo "OK" || echo "FAILED"

# Redis
echo -n "Redis: "
redis-cli ping && echo "OK" || echo "FAILED"

# Elasticsearch
echo -n "Elasticsearch: "
curl -s http://localhost:9200/_cluster/health | grep -q green && echo "OK" || echo "FAILED"

# Memory usage
echo "Memory usage:"
free -h | grep Mem
```

### Performance Monitoring

```bash
# CPU and memory usage
top -b -n 1 | grep python

# Disk usage
df -h

# Network connections
netstat -tulpn | grep python

# Docker container stats
docker stats --no-stream
```

## Getting Help

### Enable Debug Mode

```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG

# In config.yaml
api:
  debug: true

logging:
  level: "DEBUG"
```

### Collect Diagnostic Information

```bash
#!/bin/bash
# collect_diagnostics.sh

echo "=== System Information ===" > diagnostics.txt
uname -a >> diagnostics.txt
python --version >> diagnostics.txt
docker --version >> diagnostics.txt

echo -e "\n=== Environment Variables ===" >> diagnostics.txt
env | grep -E "(DATABASE|REDIS|API|MODEL)" >> diagnostics.txt

echo -e "\n=== Docker Services ===" >> diagnostics.txt
docker ps >> diagnostics.txt

echo -e "\n=== Recent Logs ===" >> diagnostics.txt
tail -100 logs/main.log >> diagnostics.txt

echo "Diagnostics collected in diagnostics.txt"
```

### Common Solutions Summary

1. **Restart services**: Often fixes temporary issues
2. **Check logs**: First step in diagnosing problems
3. **Verify configuration**: Ensure all settings are correct
4. **Test components individually**: Isolate the failing component
5. **Monitor resources**: Check CPU, memory, and disk usage
6. **Update dependencies**: Ensure all packages are up to date

### When to Seek Additional Help

If you've tried the solutions above and still have issues:

1. **Collect diagnostic information** using the script above
2. **Document the exact error message** and steps to reproduce
3. **Check system logs** for additional error details
4. **Verify system requirements** are met
5. **Consider environmental factors** (network, permissions, etc.)

For hardware-specific issues (cameras, GPUs), consult the manufacturer's documentation and ensure proper drivers are installed.
