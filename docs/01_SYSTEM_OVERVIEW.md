# System Overview

## Shoplifting Detection System

A comprehensive real-time video surveillance system that uses Long-term Recurrent Convolutional Networks (LRCN) to detect potential shoplifting activities in retail environments.

## Architecture

The system follows a microservices architecture with the following components:

### Core Components

1. **Camera Management System** - Handles multiple camera feeds (USB/IP cameras)
2. **Frame Processing Pipeline** - Preprocesses video frames for model input
3. **LRCN Model** - Deep learning model for behavior analysis
4. **Alert System** - Real-time notification and alert management
5. **Database System** - PostgreSQL with SQLAlchemy ORM
6. **API Server** - FastAPI-based REST API
7. **Web Dashboard** - React/TypeScript frontend
8. **Monitoring Stack** - ELK (Elasticsearch, Logstash, Kibana)
9. **Task Queue** - Celery for async processing

### Technology Stack

**Backend:**
- Python 3.8+
- FastAPI
- PostgreSQL
- SQLAlchemy & Alembic
- Celery
- TensorFlow 2.16+
- OpenCV

**Frontend:**
- React 18.2.0
- TypeScript 4.9.5
- Material-UI 7.1.1
- Tailwind CSS 3.3.5
- React Router v6
- Axios

**Infrastructure:**
- Docker & Docker Compose
- Elasticsearch, Logstash, Kibana
- Redis (Celery broker & caching)
- Nginx (reverse proxy)

**Security:**
- JWT Authentication with token blacklisting
- AES Encryption
- Request Rate Limiting
- CORS Protection
- Security Headers Middleware

## Data Flow

1. **Video Capture** - Cameras capture video frames
2. **Frame Processing** - Frames are preprocessed (grayscale, resize, normalize)
3. **Sequence Building** - 160 consecutive frames form a sequence
4. **Model Prediction** - LRCN model analyzes behavior patterns
5. **Alert Generation** - Suspicious activity triggers alerts
6. **Database Storage** - Events and metadata stored in PostgreSQL
7. **Real-time Monitoring** - Kibana dashboards show system metrics
8. **User Interface** - React dashboard displays cameras and alerts

## Key Features

- **Multi-camera Support** - Monitor multiple camera feeds simultaneously
- **Real-time Detection** - Sub-second response time for threat detection
- **Configurable Sensitivity** - Adjustable detection thresholds per camera
- **Alert Management** - Comprehensive alert lifecycle management
- **Performance Monitoring** - Real-time system health and performance metrics
- **User Management** - Role-based access control
- **Video Streaming** - HLS and MJPEG streaming protocols
- **API Integration** - RESTful API for third-party integrations

## Deployment Options

- **Docker Compose** - Single-machine deployment
- **Kubernetes** - Scalable container orchestration
- **Standalone** - Direct Python installation

## System Requirements

**Minimum:**
- 8GB RAM
- 4 CPU cores
- 100GB storage
- Ubuntu 20.04+ or Windows 10+

**Recommended:**
- 16GB RAM
- 8 CPU cores
- 500GB SSD storage
- GPU (NVIDIA GTX 1060 or better)
- Ubuntu 22.04 LTS
