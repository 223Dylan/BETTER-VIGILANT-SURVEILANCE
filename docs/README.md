# Documentation Index

Welcome to the Shoplifting Detection System documentation! This guide helps you navigate through all available documentation.

## Quick Start

**New to the system?** Start here:

1. **[Getting Started](00_GETTING_STARTED.md)** - Quick setup and first steps
2. **[Installation Guide](10_INSTALLATION_GUIDE.md)** - Detailed installation instructions
3. **[Configuration Guide](11_CONFIGURATION_GUIDE.md)** - Complete configuration reference

## Core Documentation

### System Architecture & Implementation

| Document | Description | For Who |
|----------|-------------|----------|
| **[System Overview](01_SYSTEM_OVERVIEW.md)** | Architecture, tech stack, data flow | Developers, Architects |
| **[Frame Processing](02_FRAME_PROCESSING.md)** | Video pipeline and preprocessing | ML Engineers, Developers |
| **[LRCN Model](03_LRCN_MODEL.md)** | AI model implementation | Data Scientists, ML Engineers |
| **[Database System](06_DATABASE_SYSTEM.md)** | PostgreSQL schema and optimization | Database Admins, Developers |

### Feature Documentation

| Document | Description | For Who |
|----------|-------------|----------|
| **[Camera Management](04_CAMERA_MANAGEMENT.md)** | Multi-camera setup and streaming | System Admins, Operators |
| **[Alert System](05_ALERT_SYSTEM.md)** | Alert lifecycle and notifications | Security Teams, Operators |
| **[API System](07_API_SYSTEM.md)** | FastAPI endpoints and WebSocket | Frontend Developers, Integrators |
| **[Authentication & Security](08_AUTHENTICATION_SECURITY.md)** | JWT auth, RBAC, encryption | Security Engineers, Admins |
| **[Monitoring & Analytics](09_MONITORING_ANALYTICS.md)** | ELK stack and metrics | DevOps Engineers, Admins |

### Setup & Configuration

| Document | Description | For Who |
|----------|-------------|----------|
| **[Getting Started](00_GETTING_STARTED.md)** | Quick setup guide | Everyone |
| **[Installation Guide](10_INSTALLATION_GUIDE.md)** | Detailed installation | System Admins, DevOps |
| **[Configuration Guide](11_CONFIGURATION_GUIDE.md)** | Complete configuration reference | System Admins, Developers |
| **[Troubleshooting Guide](12_TROUBLESHOOTING_GUIDE.md)** | Common issues and solutions | Support Teams, Developers |

### Specialized Documentation

| Document | Description | For Who |
|----------|-------------|----------|
| **[Frontend Architecture Guide](15_FRONTEND_ARCHITECTURE_GUIDE.md)** | React/TypeScript frontend architecture | Frontend Developers, Architects |
| **[API Reference](16_API_REFERENCE.md)** | Complete API documentation and examples | Developers, Integrators |
| **[Alert Database Setup](ALERT_DATABASE_SETUP.md)** | Alert system database configuration | Database Admins |
| **[Alert System Guide](ALERT_SYSTEM_GUIDE.md)** | Advanced alert configuration | Security Operators |
| **[Detection Metrics Guide](DETECTION_METRICS_GUIDE.md)** | Performance metrics and monitoring | Data Analysts, DevOps |

## Quick Navigation by Role

### For **System Administrators**
1. [Getting Started](00_GETTING_STARTED.md) → [Installation Guide](10_INSTALLATION_GUIDE.md) → [Configuration Guide](11_CONFIGURATION_GUIDE.md)
2. [Database System](06_DATABASE_SYSTEM.md) for database setup
3. [Authentication & Security](08_AUTHENTICATION_SECURITY.md) for security configuration
4. [Troubleshooting Guide](12_TROUBLESHOOTING_GUIDE.md) for issue resolution

### For **Security Operators**
1. [Getting Started](00_GETTING_STARTED.md) → [Camera Management](04_CAMERA_MANAGEMENT.md)
2. [Alert System](05_ALERT_SYSTEM.md) for alert configuration
3. [Monitoring & Analytics](09_MONITORING_ANALYTICS.md) for system monitoring

### For **Developers**
1. [System Overview](01_SYSTEM_OVERVIEW.md) for architecture understanding
2. [Frontend Architecture Guide](15_FRONTEND_ARCHITECTURE_GUIDE.md) for React/TypeScript frontend
3. [API Reference](16_API_REFERENCE.md) for complete API documentation
4. [API System](07_API_SYSTEM.md) for API integration details
5. [Authentication & Security](08_AUTHENTICATION_SECURITY.md) for auth implementation
6. [Database System](06_DATABASE_SYSTEM.md) for data layer

### For **ML Engineers/Data Scientists**
1. [LRCN Model](03_LRCN_MODEL.md) for model implementation
2. [Frame Processing](02_FRAME_PROCESSING.md) for preprocessing pipeline
3. [Detection Metrics Guide](DETECTION_METRICS_GUIDE.md) for performance analysis

### For **DevOps Engineers**
1. [Installation Guide](10_INSTALLATION_GUIDE.md) for deployment
2. [Monitoring & Analytics](09_MONITORING_ANALYTICS.md) for observability
3. [Configuration Guide](11_CONFIGURATION_GUIDE.md) for environment setup
4. [Troubleshooting Guide](12_TROUBLESHOOTING_GUIDE.md) for operations

## Configuration Quick Reference

### Essential Files
- **`.env`** - Environment variables and secrets
- **`config/config.yaml`** - Main system configuration
- **`docker-compose.dev.yml`** - Development infrastructure
- **`alembic.ini`** - Database migration settings

### Key Directories
- **`docs/`** - All documentation (you are here!)
- **`src/`** - Main application source code
- **`models/`** - AI model files
- **`scripts/`** - Setup and utility scripts
- **`config/`** - Configuration files
- **`kibana/`** - Kibana dashboards and templates

## Need Help?

### Quick Troubleshooting
1. **Installation issues?** → [Troubleshooting Guide](12_TROUBLESHOOTING_GUIDE.md)
2. **Configuration problems?** → [Configuration Guide](11_CONFIGURATION_GUIDE.md)
3. **Camera not working?** → [Camera Management](04_CAMERA_MANAGEMENT.md)
4. **Database errors?** → [Database System](06_DATABASE_SYSTEM.md)

### Common Questions
- **How to add a new camera?** → [Camera Management](04_CAMERA_MANAGEMENT.md)
- **How to configure alerts?** → [Alert System](05_ALERT_SYSTEM.md)
- **How to monitor performance?** → [Monitoring & Analytics](09_MONITORING_ANALYTICS.md)
- **How to secure the system?** → [Authentication & Security](08_AUTHENTICATION_SECURITY.md)

## Documentation Updates

This documentation is maintained alongside the codebase. When making changes to the system:

1. **Update relevant documentation** if functionality changes
2. **Add new sections** for new features
3. **Keep examples current** with actual code
4. **Test all setup instructions** before committing

## External Resources

- **TensorFlow Documentation** - For LRCN model customization
- **FastAPI Documentation** - For API development
- **PostgreSQL Documentation** - For database optimization
- **Elasticsearch Documentation** - For search and analytics
- **Docker Documentation** - For containerization

---

**Last Updated:** This documentation reflects the current state of the Shoplifting Detection System and should be kept up to date with system changes.
