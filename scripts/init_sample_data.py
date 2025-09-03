#!/usr/bin/env python3
"""
Initialize the database with sample data for development and testing.
This script creates sample users, cameras, and configuration data.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.auth.jwt_auth import JWTAuth
from src.database.models.alert import Alert
from src.database.models.base import Base, SessionLocal, engine
from src.database.models.camera import Camera
from src.database.models.user import User


def create_sample_users(db):
    """Create sample users for development."""
    print("Creating sample users...")

    users_data = [
        {
            "id": str(uuid.uuid4()),
            "username": "admin",
            "email": "admin@example.com",
            "password": "admin123",
            "full_name": "System Administrator",
            "role": "admin",
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "username": "operator",
            "email": "operator@example.com",
            "password": "operator123",
            "full_name": "Security Operator",
            "role": "operator",
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "username": "viewer",
            "email": "viewer@example.com",
            "password": "viewer123",
            "full_name": "Security Viewer",
            "role": "viewer",
            "is_active": True,
        },
    ]

    for user_data in users_data:
        # Check if user already exists
        existing_user = (
            db.query(User).filter(User.username == user_data["username"]).first()
        )
        if existing_user:
            print(f"User {user_data['username']} already exists, skipping...")
            continue

        # Hash password
        # For simplicity, store password as plain text (in production, use proper hashing)
        password_hash = user_data["password"]

        # Create user
        user = User(
            id=user_data["id"],
            username=user_data["username"],
            email=user_data["email"],
            password_hash=password_hash,
            role=user_data["role"],
            is_active=user_data["is_active"],
        )

        db.add(user)
        print(f"Created user: {user_data['username']} ({user_data['role']})")

    db.commit()
    print("Sample users created successfully!")


def create_sample_cameras(db):
    """Create sample cameras for development."""
    print("Creating sample cameras...")

    cameras_data = [
        {
            "id": "demo-usb-cam-01",
            "name": "Demo USB Camera",
            "description": "Sample USB camera for testing",
            "source": "0",
            "source_type": "usb",
            "fps": 15,
            "resolution_width": 640,
            "resolution_height": 480,
            "enabled": False,  # Disabled by default to avoid errors
            "detection_enabled": True,
            "detection_sensitivity": 0.6,
            "location": "Demo Location",
            "zone": "demo",
            "status": "stopped",
        },
        {
            "id": "demo-ip-cam-01",
            "name": "Demo IP Camera",
            "description": "Sample IP camera configuration",
            "source": "rtsp://demo:demo@demo.camera.com:554/stream",
            "source_type": "rtsp",
            "fps": 30,
            "resolution_width": 1920,
            "resolution_height": 1080,
            "enabled": False,  # Disabled by default
            "detection_enabled": True,
            "detection_sensitivity": 0.7,
            "location": "Demo Entrance",
            "zone": "entrance",
            "status": "stopped",
        },
        {
            "id": "demo-video-file",
            "name": "Demo Video File",
            "description": "Sample video file for testing",
            "source": "uploads/videos/sample_video.mp4",
            "source_type": "file",
            "fps": 25,
            "resolution_width": 1280,
            "resolution_height": 720,
            "enabled": False,
            "detection_enabled": True,
            "detection_sensitivity": 0.5,
            "location": "Demo Store",
            "zone": "store",
            "status": "stopped",
        },
    ]

    for camera_data in cameras_data:
        # Check if camera already exists
        existing_camera = (
            db.query(Camera).filter(Camera.id == camera_data["id"]).first()
        )
        if existing_camera:
            print(f"Camera {camera_data['id']} already exists, skipping...")
            continue

        # Create camera
        camera = Camera(**camera_data)
        db.add(camera)
        print(f"Created camera: {camera_data['name']} ({camera_data['source_type']})")

    db.commit()
    print("Sample cameras created successfully!")


def create_sample_alerts(db):
    """Create sample alerts for development."""
    print("Creating sample alerts...")

    # Get sample camera
    camera = db.query(Camera).first()
    if not camera:
        print("No cameras found, skipping alert creation...")
        return

    alerts_data = [
        {
            "id": str(uuid.uuid4()),
            "camera_id": camera.id,
            "type": "shoplifting",
            "severity": "high",
            "status": "active",
            "confidence": 0.85,
            "message": f"High-confidence shoplifting detected on camera {camera.name}",
            "timestamp": datetime.utcnow() - timedelta(minutes=30),
            "detection_data": {
                "frames_analyzed": 160,
                "sequence_number": 1,
                "processing_time_ms": 245.7,
            },
        },
        {
            "id": str(uuid.uuid4()),
            "camera_id": camera.id,
            "type": "suspicious_activity",
            "severity": "medium",
            "status": "acknowledged",
            "confidence": 0.67,
            "message": f"Suspicious activity detected on camera {camera.name}",
            "timestamp": datetime.utcnow() - timedelta(hours=2),
            "detection_data": {
                "frames_analyzed": 160,
                "sequence_number": 2,
                "processing_time_ms": 198.3,
            },
        },
        {
            "id": str(uuid.uuid4()),
            "camera_id": camera.id,
            "type": "shoplifting",
            "severity": "critical",
            "status": "resolved",
            "confidence": 0.92,
            "message": f"Critical shoplifting event on camera {camera.name}",
            "timestamp": datetime.utcnow() - timedelta(hours=24),
            "resolved_at": datetime.utcnow() - timedelta(hours=23),
            "notes": "False positive - customer was adjusting clothing",
            "detection_data": {
                "frames_analyzed": 160,
                "sequence_number": 3,
                "processing_time_ms": 312.1,
            },
        },
    ]

    for alert_data in alerts_data:
        alert = Alert(**alert_data)
        db.add(alert)
        print(f"Created alert: {alert_data['type']} - {alert_data['severity']}")

    db.commit()
    print("Sample alerts created successfully!")


def main():
    """Main initialization function."""
    print("=" * 70)
    print("SHOPLIFTING DETECTION SYSTEM - DATABASE INITIALIZATION")
    print("=" * 70)
    print()

    try:
        # Create database tables
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
        print()

        # Create database session
        db = SessionLocal()

        try:
            # Create sample data
            create_sample_users(db)
            print()
            create_sample_cameras(db)
            print()
            create_sample_alerts(db)
            print()

            print("=" * 70)
            print("DATABASE INITIALIZATION COMPLETED SUCCESSFULLY!")
            print("=" * 70)
            print()
            print("Sample users created:")
            print("- admin / admin123 (Administrator)")
            print("- operator / operator123 (Security Operator)")
            print("- viewer / viewer123 (Security Viewer)")
            print()
            print("Sample cameras created (disabled by default):")
            print("- demo-usb-cam-01: USB Camera demo")
            print("- demo-ip-cam-01: IP Camera demo")
            print("- demo-video-file: Video file demo")
            print()
            print("Sample alerts created for testing the alert system.")
            print()
            print("You can now start the API server:")
            print("  python api_server.py")
            print()
            print("Access the API documentation at:")
            print("  http://localhost:8001/docs")

        finally:
            db.close()

    except Exception as e:
        print(f"Error during initialization: {e}")
        print("Please check your database configuration and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
