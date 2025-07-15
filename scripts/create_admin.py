#!/usr/bin/env python3
"""
Create admin user for the Shoplifting Detection System.
This script can be run from the project root directory.

Usage:
    python scripts/create_admin.py
    OR
    python -m scripts.create_admin
"""

import os
import sys
import hashlib

# Add project root to Python path to fix import issues
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from src.database.models.user import User
    from src.database.models.base import get_db
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from loguru import logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this script from the project root directory.")
    print("And that all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

def create_admin_user(username="admin", password="admin123", email="admin@localhost"):
    """Create admin user with the specified credentials."""
    
    print("Creating admin user for Shoplifting Detection System...")
    print(f"Username: {username}")
    print(f"Email: {email}")
    
    # Get database session
    try:
        db = next(get_db())
    except Exception as e:
        print(f"Database connection error: {e}")
        print("Make sure PostgreSQL is running and the database exists.")
        print("Run: docker-compose up -d postgres")
        return False

    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == username).first()
        
        if admin_user:
            print(f"Admin user '{username}' already exists")
            
            # Ask if user wants to update password
            response = input("Update password? (y/N): ").lower().strip()
            if response == 'y':
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                admin_user.password_hash = password_hash
                db.commit()
                print("Password updated successfully!")
            return True
        else:
            # Create admin user
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            admin_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role="admin",
                is_active=True,
                is_verified=True,
                permissions={
                    "canViewCameras": True,
                    "canControlCameras": True,
                    "canViewAlerts": True,
                    "canManageAlerts": True,
                    "canViewAnalytics": True,
                    "canManageUsers": True,
                    "canAccessSettings": True,
                    "canManageSystem": True
                }
            )
            
            db.add(admin_user)
            db.commit()
            
            print("Admin user created successfully!")
            print(f"   Username: {username}")
            print(f"   Password: {password}")
            print(f"   Email: {email}")
            print(f"   Role: admin")
            print("\nPlease change the default password after first login!")
            return True
            
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Main function to create admin user."""
    
    # Check for custom credentials from environment or command line
    username = os.getenv('ADMIN_USERNAME', 'admin')
    password = os.getenv('ADMIN_PASSWORD', 'admin123')
    email = os.getenv('ADMIN_EMAIL', 'admin@localhost')
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print(__doc__)
            print("\nEnvironment variables:")
            print("  ADMIN_USERNAME - Admin username (default: admin)")
            print("  ADMIN_PASSWORD - Admin password (default: admin123)")
            print("  ADMIN_EMAIL - Admin email (default: admin@localhost)")
            return
        
        if len(sys.argv) >= 2:
            username = sys.argv[1]
        if len(sys.argv) >= 3:
            password = sys.argv[2]
        if len(sys.argv) >= 4:
            email = sys.argv[3]
    
    success = create_admin_user(username, password, email)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

