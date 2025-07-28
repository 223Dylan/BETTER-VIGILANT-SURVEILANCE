# Development Workflow Guide

This guide outlines the complete development workflow for the Shoplifting Detection System, from initial setup to production deployment.

## Table of Contents

1. [New Developer Onboarding](#new-developer-onboarding)
2. [Development Environment](#development-environment)
3. [Git Workflow & Branching Strategy](#git-workflow--branching-strategy)
4. [Code Quality Standards](#code-quality-standards)
5. [Testing Procedures](#testing-procedures)
6. [Code Review Process](#code-review-process)
7. [CI/CD Pipeline](#cicd-pipeline)
8. [Release Process](#release-process)
9. [Database Migrations](#database-migrations)
10. [Security Guidelines](#security-guidelines)
11. [Troubleshooting](#troubleshooting)
12. [Best Practices](#best-practices)

## New Developer Onboarding

### Prerequisites

Before starting development, ensure you have the following installed:

#### Required Software
- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Git** - [Download](https://git-scm.com/)
- **Docker & Docker Compose** - [Download](https://www.docker.com/products/docker-desktop)

#### Recommended Tools
- **Visual Studio Code** - [Download](https://code.visualstudio.com/)
- **DBeaver** or **pgAdmin** - Database management
- **Postman** or **Insomnia** - API testing
- **Git client** - GitKraken, SourceTree, or command line

#### VS Code Extensions (Recommended)
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.mypy-type-checker",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode-remote.remote-containers",
    "ms-azuretools.vscode-docker"
  ]
}
```

### Initial Setup

#### 1. Clone Repository
```bash
git clone https://github.com/your-org/better-vigilant-surveillance.git
cd better-vigilant-surveillance
```

#### 2. Automated Setup (Recommended)
```bash
# Linux/macOS
chmod +x scripts/setup_dev.sh
./scripts/setup_dev.sh

# Windows
scripts\setup_dev.bat
```

#### 3. Manual Setup (Alternative)
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate     # Windows

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install

# Copy configuration files
cp .env.example .env
cp config/config.example.yaml config/config.yaml
cp alembic.example.ini alembic.ini

# Generate RSA keys for development
mkdir -p keys
openssl genpkey -algorithm RSA -out keys/private_key.pem -pkcs8
openssl rsa -pubout -in keys/private_key.pem -out keys/public_key.pem

# Create necessary directories
mkdir -p logs uploads temp_frames output data models
```

#### 4. Start Infrastructure Services
```bash
# Start database, Redis, Elasticsearch, etc.
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to start (30-60 seconds)
docker-compose -f docker-compose.dev.yml logs

# Initialize database
alembic upgrade head
python scripts/init_system.py
```

#### 5. Start Development Servers
```bash
# Terminal 1: Backend API
source .venv/bin/activate
python main.py

# Terminal 2: Frontend (in new terminal)
npm start

# Terminal 3: Celery worker (optional)
source .venv/bin/activate
celery -A src.tasks worker --loglevel=info
```

#### 6. Verify Setup
- **Backend API**: http://localhost:8001/docs
- **Frontend**: http://localhost:3000
- **Database**: http://localhost:8080 (Adminer)
- **Elasticsearch**: http://localhost:9200
- **Kibana**: http://localhost:5601

**Default Login**: `admin` / `admin123`

## Development Environment

### Project Structure Overview
```
better-vigilant-surveillance/
├── src/                          # Python backend source
│   ├── components/              # React components
│   ├── pages/                   # React pages
│   ├── services/                # API services
│   ├── routers/                 # FastAPI routers
│   ├── database/                # Database models & migrations
│   ├── middleware/              # Security middleware
│   └── utils/                   # Utility functions
├── docs/                        # Documentation
├── scripts/                     # Development scripts
├── tests/                       # Test files
├── config/                      # Configuration files
├── .github/workflows/           # CI/CD workflows
└── docker-compose.dev.yml       # Development infrastructure
```

### Environment Variables

#### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/shoplifting_detection

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key

# Model
MODEL_PATH=models/lrcn_160S_90_90Q.h5

# Monitoring (optional)
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200

# Alerts (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL_RECIPIENTS=admin@example.com
```

#### Frontend (package.json)
```json
{
  "proxy": "http://localhost:8001"
}
```

### Development Scripts

#### Backend Commands
```bash
# Activate virtual environment
source .venv/bin/activate

# Start API server
python main.py

# Run database migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Run tests
pytest tests/ -v

# Code formatting
black src/
isort src/

# Type checking
mypy src/

# Security scanning
bandit -r src/
```

#### Frontend Commands
```bash
# Start development server
npm start

# Build for production
npm run build

# Run linter
npm run lint
npm run lint:fix

# Type checking
npx tsc --noEmit

# Test build locally
npm run build && npx serve -s build
```

#### Docker Commands
```bash
# Start all development services
docker-compose -f docker-compose.dev.yml up -d

# Stop all services
docker-compose -f docker-compose.dev.yml down

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Rebuild services
docker-compose -f docker-compose.dev.yml up -d --build

# Clean up
docker-compose -f docker-compose.dev.yml down -v
docker system prune -f
```

## Git Workflow & Branching Strategy

### Branching Model

We use **Git Flow** with the following branch structure:

```
main                    # Production-ready code
├── develop            # Integration branch for features
├── feature/*          # Feature development
├── release/*          # Release preparation
├── hotfix/*           # Critical production fixes
└── docs/*             # Documentation updates
```

### Branch Naming Conventions

```bash
# Features
feature/camera-management
feature/alert-system-v2
feature/user-authentication

# Bug fixes
bugfix/video-stream-issue
bugfix/database-connection

# Releases
release/v1.2.0
release/v1.2.1

# Hotfixes
hotfix/security-patch
hotfix/critical-bug-fix

# Documentation
docs/api-reference
docs/deployment-guide
```

### Development Workflow

#### 1. Starting New Feature
```bash
# Update develop branch
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/new-feature-name

# Make changes and commit
git add .
git commit -m "feat: add new feature description"

# Push branch
git push -u origin feature/new-feature-name
```

#### 2. Commit Message Convention

We follow **Conventional Commits** specification:

```bash
# Format
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]

# Types
feat:     # New feature
fix:      # Bug fix
docs:     # Documentation changes
style:    # Code style changes (formatting, etc.)
refactor: # Code refactoring
perf:     # Performance improvements
test:     # Adding or updating tests
chore:    # Build process or auxiliary tool changes
ci:       # CI/CD changes

# Examples
feat(camera): add brightness control slider
fix(auth): resolve token expiration issue
docs(api): update endpoint documentation
refactor(alerts): improve error handling
test(camera): add unit tests for video processing
```

#### 3. Pull Request Process
```bash
# Before creating PR
git checkout feature/your-feature
git rebase develop                    # Rebase onto latest develop
git push --force-with-lease origin feature/your-feature

# Create Pull Request on GitHub with:
# - Clear title and description
# - Link to related issues
# - Screenshots/demos if applicable
# - Checklist completed
```

#### 4. Code Review Checklist
```markdown
## PR Checklist

### Code Quality
- [ ] Code follows style guidelines
- [ ] No console.log or debug statements
- [ ] Error handling implemented
- [ ] Performance considerations addressed

### Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] No breaking changes (or documented)

### Documentation
- [ ] Code comments added where needed
- [ ] API documentation updated
- [ ] README updated if needed

### Security
- [ ] No sensitive data in code
- [ ] Input validation implemented
- [ ] SQL injection protection
- [ ] XSS protection considerations
```

## Code Quality Standards

### Pre-commit Hooks

We use pre-commit hooks to ensure code quality before commits:

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Hooks will run automatically on commit
git commit -m "your message"

# Manual run on all files
pre-commit run --all-files
```

#### Configured Hooks (.pre-commit-config.yaml)
- **Black**: Python code formatting
- **isort**: Import sorting
- **MyPy**: Type checking
- **Trailing whitespace**: Remove trailing spaces
- **YAML validation**: Check YAML syntax
- **Large files**: Prevent large file commits

### Python Code Standards

#### Formatting (Black)
```python
# Configuration in pyproject.toml
[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']

# Usage
black src/
black --check src/  # Check without modifying
```

#### Import Sorting (isort)
```python
# Configuration in pyproject.toml
[tool.isort]
profile = "black"
line_length = 88
src_paths = ["src", "scripts", "tests", "utils"]

# Usage
isort src/
isort --check-only src/  # Check without modifying
```

#### Type Checking (MyPy)
```python
# Configuration in mypy.ini
# Lenient settings for existing codebase
# Stricter for new modules

# Usage
mypy src/
```

#### Code Style Guidelines
```python
# Function documentation
def process_camera_frame(
    camera_id: str,
    frame: np.ndarray,
    config: CameraConfig
) -> ProcessingResult:
    """
    Process a single camera frame for detection.

    Args:
        camera_id: Unique camera identifier
        frame: Input video frame
        config: Camera configuration settings

    Returns:
        ProcessingResult containing detection data

    Raises:
        ProcessingError: If frame processing fails
    """
    # Implementation here
    pass

# Class documentation
class CameraManager:
    """
    Manages multiple camera connections and processing.

    Attributes:
        active_cameras: Dict of currently active cameras
        processing_queue: Queue for frame processing tasks
    """

    def __init__(self, config: SystemConfig) -> None:
        self.config = config
        self.active_cameras: Dict[str, Camera] = {}
```

### TypeScript/React Standards

#### ESLint Configuration (.eslintrc.json)
```json
{
  "extends": ["react-app", "react-app/jest"],
  "rules": {
    "react/react-in-jsx-scope": "off",
    "react/prop-types": "off",
    "@typescript-eslint/explicit-module-boundary-types": "off",
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/no-unused-vars": ["warn", { "argsIgnorePattern": "^_" }]
  }
}
```

#### Component Guidelines
```typescript
// Props interface
interface CameraCardProps {
  camera: Camera;
  onStart: (id: string) => void;
  onStop: (id: string) => void;
  compact?: boolean;
}

// Component with proper typing
const CameraCard: React.FC<CameraCardProps> = ({
  camera,
  onStart,
  onStop,
  compact = false
}) => {
  const [loading, setLoading] = useState(false);

  const handleStart = useCallback(() => {
    setLoading(true);
    onStart(camera.id);
    setLoading(false);
  }, [camera.id, onStart]);

  return (
    <div className="camera-card">
      {/* Component JSX */}
    </div>
  );
};

export default CameraCard;
```

## Testing Procedures

### Test Structure
```
tests/
├── unit/                    # Unit tests
│   ├── test_camera_manager.py
│   ├── test_alert_system.py
│   └── test_auth.py
├── integration/             # Integration tests
│   ├── test_api_endpoints.py
│   ├── test_database.py
│   └── test_websockets.py
├── e2e/                     # End-to-end tests
│   └── test_user_flows.py
├── fixtures/                # Test data and fixtures
└── conftest.py             # Pytest configuration
```

### Testing Commands

#### Python Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test types
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest -m "not slow"       # Skip slow tests

# Run specific test
pytest tests/unit/test_camera_manager.py::test_camera_creation

# Debug mode
pytest -s -vv tests/unit/test_camera_manager.py
```

#### Frontend Tests
```bash
# Run Jest tests
npm test

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch

# Update snapshots
npm test -- --updateSnapshot
```

### Writing Tests

#### Python Unit Test Example
```python
import pytest
from unittest.mock import Mock, patch
from src.camera_manager import CameraManager
from src.utils.config import Config

class TestCameraManager:
    """Test suite for CameraManager class."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config({
            'cameras': {
                'default_fps': 30,
                'buffer_size': 10
            }
        })

    @pytest.fixture
    def camera_manager(self, config):
        """Create CameraManager instance."""
        return CameraManager(config)

    def test_camera_creation(self, camera_manager):
        """Test camera creation with valid configuration."""
        camera_config = {
            'id': 'test-camera',
            'source': '0',
            'source_type': 'webcam'
        }

        result = camera_manager.add_camera(camera_config)

        assert result is True
        assert 'test-camera' in camera_manager.cameras
        assert camera_manager.cameras['test-camera'].id == 'test-camera'

    def test_camera_start_failure(self, camera_manager):
        """Test camera start failure handling."""
        with patch('cv2.VideoCapture') as mock_cap:
            mock_cap.return_value.isOpened.return_value = False

            result = camera_manager.start_camera('nonexistent-camera')

            assert result is False

    @pytest.mark.integration
    def test_database_integration(self, camera_manager, db_session):
        """Test camera manager database integration."""
        # Integration test implementation
        pass
```

#### Frontend Test Example
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CameraCard } from '../CameraCard';
import { Camera } from '../../types';

const mockCamera: Camera = {
  id: 'test-camera',
  name: 'Test Camera',
  status: 'active',
  source: 'rtsp://example.com/stream',
  source_type: 'rtsp'
};

describe('CameraCard', () => {
  const mockOnStart = jest.fn();
  const mockOnStop = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders camera information correctly', () => {
    render(
      <CameraCard
        camera={mockCamera}
        onStart={mockOnStart}
        onStop={mockOnStop}
      />
    );

    expect(screen.getByText('Test Camera')).toBeInTheDocument();
    expect(screen.getByText('active')).toBeInTheDocument();
  });

  it('calls onStart when start button is clicked', async () => {
    render(
      <CameraCard
        camera={mockCamera}
        onStart={mockOnStart}
        onStop={mockOnStop}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /start/i }));

    await waitFor(() => {
      expect(mockOnStart).toHaveBeenCalledWith('test-camera');
    });
  });
});
```

### Test Data Management

#### Database Fixtures
```python
# conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models.base import Base

@pytest.fixture(scope="session")
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///./test.db")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(test_db):
    """Create database session for tests."""
    Session = sessionmaker(bind=test_db)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def sample_camera():
    """Create sample camera for tests."""
    return {
        'id': 'test-camera-001',
        'name': 'Test Camera',
        'source': 'rtsp://test.example.com/stream',
        'source_type': 'rtsp',
        'fps': 30,
        'detection_enabled': True
    }
```

## Code Review Process

### PR Review Guidelines

#### For Authors
1. **Self-review** your code before requesting review
2. **Provide context** in PR description
3. **Link related issues** using "Fixes #123" syntax
4. **Include screenshots** for UI changes
5. **Update documentation** if needed
6. **Write meaningful commit messages**

#### For Reviewers
1. **Be constructive** and respectful
2. **Focus on code quality**, not personal preferences
3. **Check for security issues**
4. **Verify tests** are adequate
5. **Consider performance** implications
6. **Suggest improvements** rather than just pointing out problems

### Review Checklist

#### Functionality
- [ ] Code meets requirements
- [ ] Edge cases handled
- [ ] Error handling implemented
- [ ] Performance considerations

#### Code Quality
- [ ] Follows coding standards
- [ ] No code duplication
- [ ] Clear variable names
- [ ] Adequate comments

#### Security
- [ ] Input validation
- [ ] No sensitive data exposure
- [ ] SQL injection protection
- [ ] Authentication/authorization

#### Testing
- [ ] Unit tests added
- [ ] Tests cover edge cases
- [ ] Integration tests if needed
- [ ] Manual testing performed

## CI/CD Pipeline

### GitHub Actions Workflows

#### 1. CI/CD Pipeline (.github/workflows/ci-cd.yml)
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ master, main ]
  pull_request:
    branches: [ master, main ]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

#### 2. Code Quality (.github/workflows/code-quality.yml)
- **Security scanning** with Bandit and Safety
- **Code quality** with Pylint
- **Frontend checks** with TypeScript and ESLint
- **Dependency analysis** with Depcheck
- **SonarCloud integration**

### Pipeline Stages

#### 1. **Code Quality Gate**
- Python formatting (Black, isort)
- TypeScript compilation
- Linting (flake8, ESLint)
- Type checking (MyPy)
- Security scanning (Bandit, Safety)

#### 2. **Testing**
- Unit tests (pytest, Jest)
- Integration tests
- Coverage reporting
- Test result publishing

#### 3. **Build**
- Docker image building
- Frontend production build
- Artifact creation

#### 4. **Deployment**
- Development environment
- Staging environment
- Production deployment (manual approval)

### Local CI Simulation

```bash
# Run full CI pipeline locally
scripts/run_ci_locally.sh

# Individual checks
black --check src/                    # Formatting
isort --check-only src/               # Import sorting
flake8 src/                          # Linting
mypy src/                            # Type checking
bandit -r src/                       # Security
pytest tests/ --cov=src              # Testing
npm run lint                         # Frontend linting
npx tsc --noEmit                     # TypeScript check
```

## Release Process

### Version Management

We use **Semantic Versioning** (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Example: `v1.2.3`

### Release Workflow

#### 1. Prepare Release
```bash
# Create release branch
git checkout develop
git pull origin develop
git checkout -b release/v1.2.0

# Update version numbers
# - package.json
# - pyproject.toml
# - config files

# Update CHANGELOG.md
# - Add new version section
# - List all changes

# Commit version changes
git add .
git commit -m "chore: prepare release v1.2.0"
```

#### 2. Release Testing
```bash
# Run full test suite
pytest tests/
npm test

# Build and test containers
docker-compose -f docker-compose.dev.yml up -d --build
# Manual testing...

# Performance testing
# Security testing
```

#### 3. Merge and Tag
```bash
# Merge to main
git checkout main
git merge --no-ff release/v1.2.0
git tag -a v1.2.0 -m "Release version 1.2.0"

# Merge back to develop
git checkout develop
git merge --no-ff release/v1.2.0

# Push everything
git push origin main develop --tags
```

#### 4. Deploy
```bash
# Automated deployment via GitHub Actions
# or manual deployment:

# Build production images
docker build -t surveillance-system:v1.2.0 .

# Deploy to production
kubectl apply -f k8s/production/
# or
docker-compose -f docker-compose.prod.yml up -d
```

### Hotfix Process

```bash
# Critical production bug
git checkout main
git checkout -b hotfix/security-patch

# Make minimal fix
# Update version (patch increment)
# Update CHANGELOG

git commit -m "fix: critical security patch"

# Merge to main and develop
git checkout main
git merge --no-ff hotfix/security-patch
git tag -a v1.2.1 -m "Hotfix version 1.2.1"

git checkout develop
git merge --no-ff hotfix/security-patch

git push origin main develop --tags
```

## Database Migrations

### Alembic Workflow

#### 1. Creating Migrations
```bash
# Activate virtual environment
source .venv/bin/activate

# Create new migration
alembic revision --autogenerate -m "Add new table for feature"

# Review generated migration file
# Edit if necessary

# Apply migration
alembic upgrade head
```

#### 2. Migration Best Practices

```python
# Example migration file
"""Add camera brightness column

Revision ID: abc123def456
Revises: def456ghi789
Create Date: 2023-01-01 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123def456'
down_revision = 'def456ghi789'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add brightness column to cameras table."""
    op.add_column('cameras',
                  sa.Column('brightness', sa.Float(), nullable=True))

    # Set default value for existing records
    op.execute("UPDATE cameras SET brightness = 1.0 WHERE brightness IS NULL")

def downgrade() -> None:
    """Remove brightness column from cameras table."""
    op.drop_column('cameras', 'brightness')
```

#### 3. Migration Commands
```bash
# Check current revision
alembic current

# Show migration history
alembic history

# Upgrade to specific revision
alembic upgrade abc123def456

# Downgrade one revision
alembic downgrade -1

# Show SQL without executing
alembic upgrade head --sql
```

### Database Development Guidelines

#### 1. **Schema Changes**
- Always create migrations for schema changes
- Test migrations on copy of production data
- Include both upgrade and downgrade functions
- Document breaking changes

#### 2. **Data Migrations**
- Separate data migrations from schema migrations
- Use transactions for consistency
- Handle large datasets efficiently
- Provide rollback procedures

## Security Guidelines

### Secure Development Practices

#### 1. **Input Validation**
```python
from pydantic import BaseModel, validator

class CameraCreateRequest(BaseModel):
    name: str
    source: str
    source_type: str

    @validator('name')
    def validate_name(cls, v):
        if len(v) < 1 or len(v) > 255:
            raise ValueError('Name must be 1-255 characters')
        return v

    @validator('source_type')
    def validate_source_type(cls, v):
        if v not in ['webcam', 'rtsp', 'file']:
            raise ValueError('Invalid source type')
        return v
```

#### 2. **Authentication & Authorization**
```python
from fastapi import Depends, HTTPException
from src.auth.jwt_auth import jwt_auth

def require_admin(current_user: User = Depends(jwt_auth)) -> User:
    """Require admin role for endpoint access."""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@router.post("/admin-only-endpoint")
async def admin_endpoint(current_user: User = Depends(require_admin)):
    # Admin-only functionality
    pass
```

#### 3. **Data Protection**
```python
import hashlib
from cryptography.fernet import Fernet

def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def encrypt_sensitive_data(data: str, key: bytes) -> str:
    """Encrypt sensitive data."""
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()
```

### Security Checklist

#### Code Review Security
- [ ] No hardcoded secrets or passwords
- [ ] Input validation implemented
- [ ] SQL injection protection
- [ ] XSS protection
- [ ] CSRF protection
- [ ] Authentication required
- [ ] Authorization checked
- [ ] Sensitive data encrypted

#### Deployment Security
- [ ] Environment variables for secrets
- [ ] HTTPS/TLS configuration
- [ ] Database connection encryption
- [ ] Regular security updates
- [ ] Access logs enabled
- [ ] Rate limiting configured

### Security Tools

#### 1. **Bandit** (Python Security)
```bash
# Run security scan
bandit -r src/

# Generate report
bandit -r src/ -f json -o security-report.json
```

#### 2. **Safety** (Dependency Vulnerabilities)
```bash
# Check for known vulnerabilities
safety check

# Generate report
safety check --json --output safety-report.json
```

#### 3. **npm audit** (Node.js Security)
```bash
# Check for vulnerabilities
npm audit

# Fix automatically
npm audit fix
```

## Troubleshooting

### Common Development Issues

#### 1. **Database Connection Issues**
```bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.dev.yml ps postgres

# Check connection
psql postgresql://postgres:postgres@localhost:5432/shoplifting_detection

# Reset database
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d postgres
alembic upgrade head
```

#### 2. **Frontend Build Issues**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npx tsc --noEmit
```

#### 3. **Python Environment Issues**
```bash
# Recreate virtual environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

#### 4. **Docker Issues**
```bash
# Clean Docker system
docker system prune -f

# Rebuild containers
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d --build

# Check logs
docker-compose -f docker-compose.dev.yml logs -f postgres
```

#### 5. **Model Loading Issues**
```bash
# Check model file exists
ls -la models/lrcn_160S_90_90Q.h5

# Check model path in config
grep MODEL_PATH .env config/config.yaml

# Create placeholder model for development
touch models/lrcn_160S_90_90Q.h5
```

### Performance Issues

#### 1. **Slow API Responses**
```bash
# Check database performance
docker exec -it postgres_container psql -U postgres -c "SELECT * FROM pg_stat_activity;"

# Monitor resource usage
docker stats

# Profile Python code
python -m cProfile -o profile.stats main.py
```

#### 2. **Memory Issues**
```bash
# Monitor memory usage
free -h
docker stats

# Check for memory leaks
pip install memory-profiler
python -m memory_profiler your_script.py
```

### Debugging Tools

#### 1. **Python Debugging**
```python
# Use built-in debugger
import pdb; pdb.set_trace()

# Use logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

#### 2. **Frontend Debugging**
```typescript
// Browser DevTools
console.log('Debug info:', data);
console.table(arrayData);

// React DevTools
// Install React DevTools browser extension

// Network debugging
// Use browser Network tab or proxy tools
```

## Best Practices

### Code Organization

#### 1. **File Naming**
```
# Python files
snake_case.py
test_snake_case.py

# TypeScript/React files
PascalCase.tsx        # Components
camelCase.ts          # Services, utilities
snake_case.test.ts    # Test files
```

#### 2. **Directory Structure**
```
src/
├── components/           # Reusable UI components
│   ├── common/          # Shared components
│   ├── alerts/          # Feature-specific components
│   └── camera/
├── pages/               # Page-level components
├── services/            # API and business logic
├── utils/               # Utility functions
├── types/               # TypeScript type definitions
└── hooks/               # Custom React hooks
```

### Performance Optimization

#### 1. **Python Backend**
```python
# Use async/await for I/O operations
async def process_video_stream(camera_id: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(stream_url) as response:
            # Process stream

# Cache expensive operations
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(data: str) -> str:
    # Expensive operation
    return result
```

#### 2. **React Frontend**
```typescript
// Use React.memo for expensive components
const ExpensiveComponent = React.memo(({ data }) => {
  return <div>{/* Expensive rendering */}</div>;
});

// Use useCallback for event handlers
const handleClick = useCallback((id: string) => {
  // Handle click
}, [dependency]);

// Use useMemo for expensive calculations
const expensiveValue = useMemo(() => {
  return expensiveCalculation(data);
}, [data]);
```

### Documentation

#### 1. **Code Comments**
```python
def process_frame(frame: np.ndarray, config: dict) -> dict:
    """
    Process video frame for object detection.

    Args:
        frame: Input video frame (height, width, channels)
        config: Processing configuration containing:
            - threshold: Detection confidence threshold (0.0-1.0)
            - model_path: Path to the LRCN model file

    Returns:
        dict: Detection results containing:
            - confidence: Detection confidence score
            - is_shoplifting: Boolean detection result
            - bounding_boxes: List of detected object boxes

    Raises:
        ProcessingError: If frame processing fails
        ModelLoadError: If model cannot be loaded
    """
```

#### 2. **API Documentation**
```python
from fastapi import FastAPI
from pydantic import BaseModel

class CameraResponse(BaseModel):
    """Camera information response model."""

    id: str
    name: str
    status: str

    class Config:
        schema_extra = {
            "example": {
                "id": "camera-001",
                "name": "Store Entrance",
                "status": "active"
            }
        }

@app.get("/cameras/{camera_id}", response_model=CameraResponse)
async def get_camera(camera_id: str) -> CameraResponse:
    """
    Get camera information by ID.

    - **camera_id**: Unique camera identifier

    Returns camera status and configuration details.
    """
```

### Error Handling

#### 1. **Python Error Handling**
```python
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

async def risky_operation():
    try:
        # Risky operation
        result = await external_api_call()
        return result
    except ConnectionError as e:
        logger.error(f"Connection failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="External service unavailable"
        )
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid request data"
        )
    except Exception as e:
        logger.exception("Unexpected error occurred")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
```

#### 2. **React Error Handling**
```typescript
// Error boundary component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // Log to error reporting service
  }

  render() {
    if (this.state.hasError) {
      return <div>Something went wrong.</div>;
    }
    return this.props.children;
  }
}

// API error handling
const fetchCameras = async () => {
  try {
    const response = await apiService.getCameras();
    setCameras(response.data);
  } catch (error) {
    console.error('Failed to fetch cameras:', error);
    setError('Failed to load cameras. Please try again.');
  }
};
```

### Security Best Practices

#### 1. **Environment Variables**
```bash
# .env file
DATABASE_URL=postgresql://user:pass@localhost:5432/db
JWT_SECRET_KEY=your-super-secret-key-min-32-chars
API_ENCRYPTION_KEY=your-encryption-key

# Never commit secrets to git
echo ".env" >> .gitignore
```

#### 2. **Input Sanitization**
```python
import html
import re

def sanitize_input(user_input: str) -> str:
    """Sanitize user input to prevent XSS."""
    # HTML escape
    sanitized = html.escape(user_input)

    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', sanitized)

    return sanitized.strip()
```

### Monitoring and Logging

#### 1. **Structured Logging**
```python
import structlog

logger = structlog.get_logger(__name__)

async def process_detection(camera_id: str, frame_data: bytes):
    logger.info(
        "Processing detection",
        camera_id=camera_id,
        frame_size=len(frame_data),
        timestamp=time.time()
    )

    try:
        result = await detect_objects(frame_data)
        logger.info(
            "Detection complete",
            camera_id=camera_id,
            confidence=result.confidence,
            detection_count=len(result.objects)
        )
    except Exception as e:
        logger.error(
            "Detection failed",
            camera_id=camera_id,
            error=str(e),
            exc_info=True
        )
```

#### 2. **Performance Monitoring**
```python
import time
from functools import wraps

def monitor_performance(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(
                f"{func.__name__} completed",
                duration_ms=duration * 1000,
                success=True
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"{func.__name__} failed",
                duration_ms=duration * 1000,
                error=str(e),
                success=False
            )
            raise
    return wrapper

@monitor_performance
async def expensive_operation():
    # Implementation
    pass
```

---

## Additional Resources

- **[Frontend Architecture Guide](15_FRONTEND_ARCHITECTURE_GUIDE.md)** - React/TypeScript development
- **[API Reference](16_API_REFERENCE.md)** - Complete API documentation
- **[System Overview](01_SYSTEM_OVERVIEW.md)** - Architecture understanding
- **[Troubleshooting Guide](12_TROUBLESHOOTING_GUIDE.md)** - Common issues and solutions

---

**Last Updated**: This workflow guide should be updated as development processes evolve and new tools are introduced.
