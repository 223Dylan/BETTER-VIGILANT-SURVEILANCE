# Deployment Guide

This comprehensive guide covers all deployment scenarios for the Shoplifting Detection System, from development to production environments.

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Development Deployment](#development-deployment)
3. [Staging Deployment](#staging-deployment)
4. [Production Deployment](#production-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Cloud Deployment](#cloud-deployment)
7. [Security Configuration](#security-configuration)
8. [Monitoring & Health Checks](#monitoring--health-checks)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)

## Deployment Overview

### Architecture Components

The system consists of several components that need to be deployed:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   AI Services   │
│   (React)       │    │   (FastAPI)     │    │   (ML Model)    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • React 18      │    │ • FastAPI       │    │ • TensorFlow    │
│ • TypeScript    │    │ • Python 3.8+   │    │ • LRCN Model    │
│ • Tailwind CSS │    │ • Celery        │    │ • OpenCV        │
│ • Material-UI   │    │ • WebSockets    │    │ • Preprocessing │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────────┐
         │              Infrastructure                         │
         ├─────────────────┬─────────────────┬─────────────────┤
         │   Database      │   Cache/Queue   │   Monitoring    │
         │   (PostgreSQL)  │   (Redis)       │   (ELK Stack)   │
         └─────────────────┴─────────────────┴─────────────────┘
```

### Deployment Scenarios

1. **Development**: Local development with Docker services
2. **Staging**: Production-like environment for testing
3. **Production**: Full production deployment with HA and security
4. **Cloud**: Managed cloud services (AWS, GCP, Azure)

## Development Deployment

### Quick Development Setup

**Prerequisites:**
- Docker & Docker Compose
- Python 3.8+
- Node.js 18+
- Git

**1. Automated Setup:**
```bash
# Clone repository
git clone https://github.com/your-org/better-vigilant-surveillance.git
cd better-vigilant-surveillance

# Run automated setup
chmod +x scripts/setup_dev.sh && ./scripts/setup_dev.sh
# OR for Windows
scripts\setup_dev.bat
```

**2. Manual Setup:**
```bash
# Setup environment
cp .env.example .env
cp config/config.example.yaml config/config.yaml

# Start infrastructure
docker-compose -f docker-compose.dev.yml up -d

# Setup Python backend
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt

# Setup frontend
npm install

# Initialize database
alembic upgrade head
python scripts/init_system.py
```

**3. Start Services:**
```bash
# Terminal 1: Backend
source .venv/bin/activate
python main.py

# Terminal 2: Frontend
npm start

# Terminal 3: Celery worker (optional)
source .venv/bin/activate
celery -A src.tasks worker --loglevel=info
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs
- Database: localhost:5432
- Kibana: http://localhost:5601

### Development Configuration

**Environment Variables (.env):**
```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/shoplifting_detection

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET=development-secret-key-change-in-production
ENCRYPTION_KEY=development-encryption-key

# Model
MODEL_PATH=models/lrcn_160S_90_90Q.h5

# Monitoring (optional)
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200

# Debug
DEBUG=true
LOG_LEVEL=DEBUG
```

## Staging Deployment

### Staging Environment Setup

Staging should mirror production as closely as possible while remaining accessible for testing.

**1. Infrastructure Setup:**
```bash
# Use production-like Docker setup
cp docker-compose.yml docker-compose.staging.yml

# Update for staging environment
# - Use staging database
# - Enable debug logging
# - Use staging secrets
```

**2. Staging Configuration:**
```bash
# Staging environment variables
DATABASE_URL=postgresql://staging_user:staging_pass@staging-db:5432/staging_db
REDIS_URL=redis://staging-redis:6379/0
JWT_SECRET=staging-secret-key-different-from-prod
ELASTICSEARCH_HOST=staging-elasticsearch
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
```

**3. Deploy to Staging:**
```bash
# Build and deploy
docker-compose -f docker-compose.staging.yml up -d --build

# Initialize database
docker-compose -f docker-compose.staging.yml exec app alembic upgrade head
docker-compose -f docker-compose.staging.yml exec app python scripts/init_system.py

# Verify deployment
curl http://staging-server:8001/api/health
```

### Staging Testing

**1. Automated Testing:**
```bash
# Run full test suite
pytest tests/ --cov=src --cov-report=html

# Integration tests
pytest tests/integration/ -v

# E2E tests
npm run test:e2e
```

**2. Manual Testing:**
- User authentication flows
- Camera management operations
- Alert system functionality
- Real-time video streaming
- Performance under load

## Production Deployment

### Production Requirements

**Hardware Requirements:**
- **CPU**: 8+ cores (16+ recommended)
- **RAM**: 32GB+ (64GB recommended)
- **Storage**: 1TB+ SSD (with backup)
- **Network**: Gigabit Ethernet
- **GPU**: NVIDIA GTX 1080+ (optional, for faster inference)

**Software Requirements:**
- **OS**: Ubuntu 20.04 LTS, CentOS 8, or RHEL 8
- **Docker**: 20.10+
- **Python**: 3.8+
- **PostgreSQL**: 12+
- **Redis**: 6+
- **Nginx**: 1.18+ (reverse proxy)

### Production Infrastructure

**1. Server Architecture:**
```
Internet → Load Balancer → Reverse Proxy → Application Servers
    │            │              │               │
    │            │              │               ├─ Backend API (FastAPI)
    │            │              │               ├─ Frontend (Nginx)
    │            │              │               ├─ Celery Workers
    │            │              │               └─ Model Service
    │            │              │
    │            │              └─ Database Cluster (PostgreSQL)
    │            │
    │            └─ Monitoring Stack (ELK)
    │
    └─ CDN (Static Assets)
```

**2. Production Docker Setup:**

**docker-compose.prod.yml:**
```yaml
version: '3.8'

services:
  app:
    build: .
    restart: unless-stopped
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET=${JWT_SECRET}
      - ENVIRONMENT=production
    depends_on:
      - postgres
      - redis
    networks:
      - app-network
    volumes:
      - ./models:/app/models:ro
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./ssl:/etc/nginx/ssl:ro
      - ./nginx.prod.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - app
    networks:
      - app-network

  worker:
    build: .
    restart: unless-stopped
    command: celery -A src.tasks worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
    networks:
      - app-network
    volumes:
      - ./models:/app/models:ro

  postgres:
    image: postgres:14
    restart: unless-stopped
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - app-network
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - app-network

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.12.1
    restart: unless-stopped
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=${ELASTIC_PASSWORD}
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - app-network

  kibana:
    image: docker.elastic.co/kibana/kibana:8.12.1
    restart: unless-stopped
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - ELASTICSEARCH_USERNAME=elastic
      - ELASTICSEARCH_PASSWORD=${ELASTIC_PASSWORD}
    depends_on:
      - elasticsearch
    networks:
      - app-network
    ports:
      - "5601:5601"

volumes:
  postgres_data:
  redis_data:
  elasticsearch_data:

networks:
  app-network:
    driver: bridge
```

**3. Production Environment Variables:**
```bash
# Database
DATABASE_URL=postgresql://prod_user:secure_password@postgres:5432/prod_db
DB_NAME=prod_db
DB_USER=prod_user
DB_PASSWORD=secure_random_password

# Cache & Queue
REDIS_URL=redis://:redis_password@redis:6379/0
REDIS_PASSWORD=secure_redis_password

# Security
JWT_SECRET=very-secure-random-jwt-secret-key-min-32-chars
ENCRYPTION_KEY=base64-encoded-encryption-key

# Monitoring
ELASTICSEARCH_HOST=elasticsearch
ELASTIC_PASSWORD=secure_elastic_password

# SSL/TLS
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
WORKERS=4
```

### Production Deployment Steps

**1. Pre-deployment:**
```bash
# Create production user
sudo useradd -m -s /bin/bash surveillance
sudo usermod -aG docker surveillance

# Setup directories
sudo mkdir -p /opt/surveillance/{app,data,logs,backups}
sudo chown -R surveillance:surveillance /opt/surveillance

# Setup SSL certificates
sudo mkdir -p /opt/surveillance/ssl
# Copy SSL certificates to /opt/surveillance/ssl/
```

**2. Deploy Application:**
```bash
# Switch to surveillance user
sudo su - surveillance
cd /opt/surveillance/app

# Clone and configure
git clone https://github.com/your-org/better-vigilant-surveillance.git .
cp .env.example .env.prod
# Edit .env.prod with production values

# Build and deploy
docker-compose -f docker-compose.prod.yml up -d --build

# Initialize database
docker-compose -f docker-compose.prod.yml exec app alembic upgrade head
docker-compose -f docker-compose.prod.yml exec app python scripts/init_system.py

# Verify deployment
curl -k https://localhost/api/health
```

**3. SSL/TLS Configuration:**

**nginx.prod.conf:**
```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server app:8001;
    }

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # API proxy
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket proxy
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Frontend
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # Static files
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

## Docker Deployment

### Multi-Stage Docker Build

**Dockerfile:**
```dockerfile
# Build stage for frontend
FROM node:18-alpine AS frontend-build
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY src/ ./src/
COPY public/ ./public/
COPY tsconfig.json ./
RUN npm run build

# Python backend stage
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash surveillance
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=surveillance:surveillance . .
COPY --from=frontend-build --chown=surveillance:surveillance /app/build ./static/

# Switch to app user
USER surveillance

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/api/health || exit 1

# Expose port
EXPOSE 8001

# Start application
CMD ["python", "main.py"]
```

**Frontend Dockerfile (Dockerfile.frontend):**
```dockerfile
FROM node:18-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.prod.conf /etc/nginx/nginx.conf

# Expose ports
EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
```

### Docker Optimization

**1. Multi-stage builds** to reduce image size
**2. Health checks** for container monitoring
**3. Non-root user** for security
**4. Volume mounts** for persistent data
**5. Resource limits** for production stability

```yaml
# Resource limits example
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

## Cloud Deployment

### AWS Deployment

**1. Infrastructure as Code (Terraform):**

**main.tf:**
```hcl
provider "aws" {
  region = var.aws_region
}

# VPC and networking
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "surveillance-vpc"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "surveillance-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# RDS Database
resource "aws_db_instance" "postgres" {
  identifier     = "surveillance-db"
  engine         = "postgres"
  engine_version = "14.9"
  instance_class = "db.t3.medium"

  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_encrypted     = true

  db_name  = "surveillance"
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = false

  tags = {
    Name = "surveillance-db"
  }
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "main" {
  name       = "surveillance-cache-subnet"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "surveillance-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "surveillance-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = false
}
```

**2. ECS Task Definition:**

**task-definition.json:**
```json
{
  "family": "surveillance-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "surveillance-app",
      "image": "your-account.dkr.ecr.region.amazonaws.com/surveillance:latest",
      "portMappings": [
        {
          "containerPort": 8001,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:surveillance/database"
        },
        {
          "name": "JWT_SECRET",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:surveillance/jwt"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/surveillance",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8001/api/health || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

### Google Cloud Platform (GKE)

**1. Kubernetes Deployment:**

**k8s/deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: surveillance-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: surveillance
  template:
    metadata:
      labels:
        app: surveillance
    spec:
      containers:
      - name: app
        image: gcr.io/PROJECT_ID/surveillance:latest
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: surveillance-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: surveillance-secrets
              key: redis-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
```

**k8s/service.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: surveillance-service
spec:
  selector:
    app: surveillance
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8001
  type: LoadBalancer
```

### Azure Container Instances

**azure-deploy.yaml:**
```yaml
apiVersion: '2021-03-01'
location: eastus
name: surveillance-container-group
properties:
  containers:
  - name: surveillance-app
    properties:
      image: your-registry.azurecr.io/surveillance:latest
      resources:
        requests:
          cpu: 1
          memoryInGb: 2
      ports:
      - port: 8001
        protocol: TCP
      environmentVariables:
      - name: 'ENVIRONMENT'
        value: 'production'
      - name: 'DATABASE_URL'
        secureValue: 'postgresql://...'
  osType: Linux
  restartPolicy: Always
  ipAddress:
    type: Public
    ports:
    - protocol: tcp
      port: '80'
    dnsNameLabel: surveillance-app
```

## Security Configuration

### Production Security Checklist

**1. Environment Security:**
```bash
# Secure environment variables
export JWT_SECRET=$(openssl rand -base64 32)
export ENCRYPTION_KEY=$(openssl rand -base64 32)
export DB_PASSWORD=$(openssl rand -base64 24)

# File permissions
chmod 600 .env.prod
chmod 600 ssl/private.key
chmod 644 ssl/certificate.crt

# User security
sudo usermod -s /bin/false surveillance  # Disable shell login
```

**2. Database Security:**
```sql
-- Create dedicated database user
CREATE USER surveillance_app WITH PASSWORD 'secure_random_password';
GRANT CONNECT ON DATABASE surveillance TO surveillance_app;
GRANT USAGE ON SCHEMA public TO surveillance_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO surveillance_app;

-- Enable SSL
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = 'server.crt';
ALTER SYSTEM SET ssl_key_file = 'server.key';
```

**3. Network Security:**
```bash
# Firewall rules
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 5432/tcp   # PostgreSQL (internal only)
sudo ufw deny 6379/tcp   # Redis (internal only)
sudo ufw deny 9200/tcp   # Elasticsearch (internal only)

# Fail2ban for SSH protection
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

**4. SSL/TLS Configuration:**
```bash
# Generate SSL certificate (Let's Encrypt)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# Or use custom certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /opt/surveillance/ssl/key.pem \
  -out /opt/surveillance/ssl/cert.pem
```

### Security Headers

**nginx configuration:**
```nginx
# Security headers
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";
add_header Referrer-Policy "strict-origin-when-cross-origin";

# Hide server information
server_tokens off;
```

## Monitoring & Health Checks

### Application Health Checks

**1. Health Check Endpoint:**
```python
@app.get("/api/health")
async def health_check():
    """Comprehensive health check."""
    try:
        # Database check
        db_status = await check_database_health()

        # Redis check
        redis_status = await check_redis_health()

        # Model check
        model_status = check_model_health()

        # Overall status
        overall_status = "healthy" if all([
            db_status["status"] == "healthy",
            redis_status["status"] == "healthy",
            model_status["status"] == "healthy"
        ]) else "unhealthy"

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": db_status,
                "redis": redis_status,
                "model": model_status
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
```

**2. Docker Health Checks:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/api/health || exit 1
```

**3. External Monitoring:**

**monitoring/prometheus.yml:**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'surveillance-app'
    static_configs:
      - targets: ['app:8001']
    metrics_path: '/api/metrics'
    scrape_interval: 30s

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Log Management

**1. Centralized Logging:**
```yaml
# docker-compose logging
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=surveillance-app"
```

**2. ELK Stack Configuration:**

**logstash/pipeline/surveillance.conf:**
```ruby
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "surveillance-app" {
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:message}" }
    }

    date {
      match => [ "timestamp", "ISO8601" ]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "surveillance-logs-%{+YYYY.MM.dd}"
  }
}
```

## Backup & Recovery

### Database Backup Strategy

**1. Automated Backups:**

**scripts/backup_database.sh:**
```bash
#!/bin/bash

BACKUP_DIR="/opt/surveillance/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="surveillance"
DB_USER="surveillance_app"
DB_HOST="localhost"

# Create backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
    --format=custom \
    --compress=9 \
    --file=$BACKUP_DIR/surveillance_$DATE.dump

# Keep only last 7 days
find $BACKUP_DIR -name "surveillance_*.dump" -mtime +7 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/surveillance_$DATE.dump \
    s3://surveillance-backups/database/
```

**2. Backup Cron Job:**
```bash
# Add to crontab
0 2 * * * /opt/surveillance/scripts/backup_database.sh
```

**3. Recovery Process:**
```bash
# Stop application
docker-compose down

# Restore database
pg_restore -h localhost -U surveillance_app -d surveillance \
    --clean --if-exists \
    /opt/surveillance/backups/surveillance_20240101_020000.dump

# Start application
docker-compose up -d

# Verify restoration
curl http://localhost:8001/api/health
```

### File System Backup

**1. Application Files:**
```bash
# Backup application data
tar -czf surveillance_files_$(date +%Y%m%d).tar.gz \
    /opt/surveillance/uploads \
    /opt/surveillance/logs \
    /opt/surveillance/models \
    /opt/surveillance/.env.prod

# Upload to cloud storage
aws s3 cp surveillance_files_*.tar.gz s3://surveillance-backups/files/
```

**2. Docker Volume Backup:**
```bash
# Backup Docker volumes
docker run --rm -v surveillance_postgres_data:/data -v $(pwd):/backup \
    ubuntu tar czf /backup/postgres_data_backup.tar.gz /data

docker run --rm -v surveillance_redis_data:/data -v $(pwd):/backup \
    ubuntu tar czf /backup/redis_data_backup.tar.gz /data
```

### Disaster Recovery Plan

**1. Recovery Time Objectives (RTO):**
- **Critical Systems**: 15 minutes
- **Full System**: 1 hour
- **Historical Data**: 4 hours

**2. Recovery Point Objectives (RPO):**
- **Configuration**: 24 hours
- **User Data**: 4 hours
- **Logs**: 1 hour

**3. Recovery Procedures:**

**Complete System Recovery:**
```bash
# 1. Provision new infrastructure
terraform apply -var-file="production.tfvars"

# 2. Restore database
pg_restore -h new-db-host -U surveillance_app -d surveillance \
    s3://surveillance-backups/database/latest.dump

# 3. Deploy application
docker-compose -f docker-compose.prod.yml up -d

# 4. Restore application files
aws s3 sync s3://surveillance-backups/files/ /opt/surveillance/

# 5. Update DNS records
# Point domain to new load balancer

# 6. Verify system functionality
./scripts/verify_deployment.sh
```

## Troubleshooting

### Common Deployment Issues

**1. Container Startup Issues:**
```bash
# Check container logs
docker-compose logs app

# Check container health
docker-compose ps

# Debug container
docker-compose exec app bash

# Check resource usage
docker stats
```

**2. Database Connection Issues:**
```bash
# Test database connectivity
docker-compose exec app python -c "
from src.database.base import engine
with engine.connect() as conn:
    result = conn.execute('SELECT 1')
    print('Database connection successful')
"

# Check database logs
docker-compose logs postgres

# Monitor active connections
docker-compose exec postgres psql -U surveillance_app -d surveillance -c "
SELECT count(*) as active_connections
FROM pg_stat_activity
WHERE state = 'active';
"
```

**3. Performance Issues:**
```bash
# Monitor system resources
htop
iotop
nethogs

# Check application metrics
curl http://localhost:8001/api/metrics

# Database performance
docker-compose exec postgres psql -U surveillance_app -d surveillance -c "
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
"
```

**4. SSL/TLS Issues:**
```bash
# Test SSL certificate
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Check certificate expiration
openssl x509 -in /opt/surveillance/ssl/cert.pem -text -noout | grep "Not After"

# Verify nginx configuration
nginx -t
```

### Monitoring Commands

**System Health:**
```bash
# Check all services
docker-compose ps

# System resources
free -h
df -h
uptime

# Network connectivity
netstat -tlnp
ss -tlnp

# Application health
curl -I http://localhost:8001/api/health
```

**Log Analysis:**
```bash
# Application logs
docker-compose logs --tail=100 app

# Error patterns
docker-compose logs app | grep -i error

# Performance logs
docker-compose logs app | grep -E "(slow|timeout|error)"
```

### Emergency Procedures

**1. Emergency Shutdown:**
```bash
# Graceful shutdown
docker-compose down

# Force shutdown if needed
docker-compose kill
```

**2. Emergency Recovery:**
```bash
# Quick recovery from backup
./scripts/emergency_restore.sh

# Rollback to previous version
docker-compose down
git checkout previous-stable-tag
docker-compose up -d --build
```

**3. Scaling Under Load:**
```bash
# Scale workers
docker-compose up -d --scale worker=4

# Scale application (if using Swarm/Kubernetes)
docker service scale surveillance_app=3
```

---

## Additional Resources

- **[Development Workflow Guide](17_DEVELOPMENT_WORKFLOW_GUIDE.md)** - Development and CI/CD processes
- **[API Reference](16_API_REFERENCE.md)** - Complete API documentation
- **[Security Guide](08_AUTHENTICATION_SECURITY.md)** - Security implementation details
- **[Database System](06_DATABASE_SYSTEM.md)** - Database configuration and management

---

**Last Updated**: This deployment guide should be updated when new deployment options or infrastructure changes are implemented.
