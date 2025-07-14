import hashlib
from src.database.models.user import User
from src.database.models.base import get_db

# Get database session
db = next(get_db())

try:
    # Check if admin user exists
    admin_user = db.query(User).filter(User.username == "admin").first()
    
    if admin_user:
        print("Admin user already exists")
    else:
        # Create admin user
        password_hash = hashlib.sha256("admin123".encode()).hexdigest()
        
        admin_user = User(
            username="admin",
            email="admin@localhost",
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
                "canManageSystem": True,
                "canExportData": True
            }
        )
        
        db.add(admin_user)
        db.commit()
        print("Admin user created successfully: admin/admin123")
        
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()

