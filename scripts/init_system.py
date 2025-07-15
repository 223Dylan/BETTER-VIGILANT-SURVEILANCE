#!/usr/bin/env python3
"""
Shoplifting Detection System - Complete Initialization Script

This script performs a complete system initialization:
- Checks dependencies
- Initializes database
- Creates admin user
- Sets up sample camera
- Verifies model availability
- Tests system components

Usage:
    python scripts/init_system.py [--force] [--no-model-check]
    
Arguments:
    --force          Force reinitialize even if already set up
    --no-model-check Skip model file verification
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_step(step, description):
    """Print a formatted step."""
    print(f"\nStep {step}: {description}")
    print("-" * 40)

def print_success(message):
    """Print success message."""
    print(f"SUCCESS: {message}")

def print_warning(message):
    """Print warning message."""
    print(f"WARNING: {message}")

def print_error(message):
    """Print error message."""
    print(f"ERROR: {message}")

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print_error(f"Python 3.8+ required, found {sys.version}")
        return False
    print_success(f"Python version: {sys.version}")
    return True

def check_dependencies():
    """Check if required packages are installed."""
    required_packages = [
        'tensorflow', 'opencv-python', 'fastapi', 'sqlalchemy', 
        'psycopg2-binary', 'redis', 'alembic', 'loguru'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print_success(f"Package {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print_error(f"Package {package} is missing")
    
    if missing_packages:
        print_warning("Install missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_docker_services():
    """Check if Docker services are running."""
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if result.returncode != 0:
            print_warning("Docker is not running or not accessible")
            return False
        
        # Check for required containers
        containers = result.stdout
        services = {
            'postgres': 'shoplifting_postgres' in containers or 'postgres' in containers,
            'redis': 'shoplifting_redis' in containers or 'redis' in containers,
        }
        
        all_running = True
        for service, running in services.items():
            if running:
                print_success(f"{service.title()} container is running")
            else:
                print_warning(f"{service.title()} container is not running")
                all_running = False
        
        if not all_running:
            print_warning("Start infrastructure services with:")
            print("docker-compose -f docker-compose.dev.yml up -d")
        
        return all_running
        
    except FileNotFoundError:
        print_warning("Docker is not installed or not in PATH")
        return False

def wait_for_database():
    """Wait for database to be ready."""
    print("Waiting for database connection...")
    max_attempts = 30
    
    for attempt in range(max_attempts):
        try:
            from src.database.models.base import engine
            connection = engine.connect()
            connection.close()
            print_success("Database connection established")
            return True
        except Exception as e:
            if attempt < max_attempts - 1:
                print(f"  Attempt {attempt + 1}/{max_attempts}: {e}")
                time.sleep(2)
            else:
                print_error(f"Database connection failed after {max_attempts} attempts")
                return False
    
    return False

def initialize_database():
    """Initialize database with migrations."""
    try:
        from src.database.init_db import init_db
        print("Running database initialization...")
        init_db()
        print_success("Database initialized successfully")
        return True
    except Exception as e:
        print_error(f"Database initialization failed: {e}")
        return False

def create_admin_user():
    """Create admin user."""
    try:
        from scripts.create_admin import create_admin_user
        print("Creating admin user...")
        success = create_admin_user("admin", "admin123", "admin@localhost")
        return success
    except Exception as e:
        print_error(f"Admin user creation failed: {e}")
        return False

def setup_sample_camera():
    """Set up a sample camera configuration."""
    try:
        from src.services.camera_db_service import CameraDatabaseService
        
        service = CameraDatabaseService()
        
        # Check if local webcam already exists
        cameras = service.get_all_cameras()
        if any(cam.id == 'local-webcam' for cam in cameras):
            print_success("Sample camera already exists")
            return True
        
        # Create sample camera
        camera_data = {
            'id': 'local-webcam',
            'name': 'Local Webcam',
            'description': 'Default local webcam for testing',
            'source': '0',
            'source_type': 'webcam',
            'enabled': True,
            'fps': 30,
            'resolution_width': 640,
            'resolution_height': 480,
            'detection_enabled': True,
            'detection_sensitivity': 0.5,
            'status': 'idle'
        }
        
        service.create_camera(camera_data)
        print_success("Sample camera created: local-webcam")
        return True
        
    except Exception as e:
        print_error(f"Sample camera setup failed: {e}")
        return False

def check_model_file():
    """Check if the required model file exists."""
    model_path = Path(PROJECT_ROOT) / "models" / "lrcn_160S_90_90Q.h5"
    
    if model_path.exists():
        print_success(f"Model file found: {model_path}")
        
        # Try to load the model
        try:
            import tensorflow as tf
            model = tf.keras.models.load_model(str(model_path))
            print_success("Model loads successfully")
            return True
        except Exception as e:
            print_error(f"Model file exists but cannot be loaded: {e}")
            return False
    else:
        print_warning(f"Model file not found: {model_path}")
        print_warning("See models/README.md for instructions on obtaining the model")
        return False

def verify_configuration():
    """Verify configuration files exist."""
    config_files = {
        '.env': 'Environment variables',
        'config/config.yaml': 'Main configuration',
        'alembic.ini': 'Database migration configuration'
    }
    
    all_exist = True
    for file_path, description in config_files.items():
        full_path = Path(PROJECT_ROOT) / file_path
        if full_path.exists():
            print_success(f"{description}: {file_path}")
        else:
            print_warning(f"{description} missing: {file_path}")
            all_exist = False
    
    return all_exist

def test_api_server():
    """Test if the API server can be imported."""
    try:
        import api_server
        print_success("API server imports successfully")
        return True
    except Exception as e:
        print_error(f"API server import failed: {e}")
        return False

def main():
    """Main initialization process."""
    force = '--force' in sys.argv
    no_model_check = '--no-model-check' in sys.argv
    
    print_header("SHOPLIFTING DETECTION SYSTEM - INITIALIZATION")
    
    # Step 1: Environment Check
    print_step(1, "Environment Check")
    if not check_python_version():
        sys.exit(1)
    
    if not check_dependencies():
        print_error("Install missing dependencies first")
        sys.exit(1)
    
    # Step 2: Configuration Check
    print_step(2, "Configuration Check")
    verify_configuration()
    
    # Step 3: Infrastructure Check
    print_step(3, "Infrastructure Services")
    if not check_docker_services():
        print_error("Start Docker services first")
        sys.exit(1)
    
    # Step 4: Database Setup
    print_step(4, "Database Setup")
    if not wait_for_database():
        sys.exit(1)
    
    if not initialize_database():
        sys.exit(1)
    
    # Step 5: Admin User
    print_step(5, "Admin User Creation")
    if not create_admin_user():
        sys.exit(1)
    
    # Step 6: Sample Camera
    print_step(6, "Sample Camera Setup")
    if not setup_sample_camera():
        print_warning("Could not set up sample camera, but continuing...")
    
    # Step 7: Model Check
    if not no_model_check:
        print_step(7, "Model Verification")
        if not check_model_file():
            print_warning("Model file not available - some features will not work")
    
    # Step 8: API Test
    print_step(8, "API Server Test")
    if not test_api_server():
        print_warning("API server has issues - check dependencies")
    
    # Final Summary
    print_header("INITIALIZATION COMPLETE")
    print_success("System initialization completed successfully!")
    print("\nNext Steps:")
    print("1. Start the application: python main.py")
    print("2. Access the web interface: http://localhost:8001")
    print("3. Login with: admin / admin123")
    print("4. Change the default password")
    
    if not no_model_check and not check_model_file():
        print("\nImportant: Model file is missing")
        print("   See models/README.md for setup instructions")
    
    print("\nUseful URLs:")
    print("   Web Interface: http://localhost:8001")
    print("   API Docs: http://localhost:8001/docs")
    print("   Kibana (logs): http://localhost:5601")
    
if __name__ == "__main__":
    if '--help' in sys.argv or '-h' in sys.argv:
        print(__doc__)
        sys.exit(0)
    
    main() 