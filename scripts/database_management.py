#!/usr/bin/env python3
"""
Database Management Script
==========================

This script provides utilities for managing the database with proper Alembic migrations.

Usage:
    python scripts/database_management.py init          # Initialize database
    python scripts/database_management.py migrate       # Run migrations
    python scripts/database_management.py rollback      # Rollback one migration
    python scripts/database_management.py status        # Show migration status
    python scripts/database_management.py reset         # Reset database (DANGEROUS)
    python scripts/database_management.py create-user   # Create admin user
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

from src.database.init_db import create_tables_fallback, init_db


def run_alembic_command(command_args, description):
    """Run an Alembic command with error handling."""
    try:
        logger.info(f"[RUNNING] {description}...")
        result = subprocess.run(
            [sys.executable, "-m", "alembic"] + command_args,
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.info(f"[SUCCESS] {description} completed successfully")
            if result.stdout.strip():
                print(result.stdout)
            return True
        else:
            logger.error(f"[ERROR] {description} failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"[ERROR] Error running {description}: {e}")
        return False


def cmd_init(args):
    """Initialize the database."""
    logger.info("[INIT] Initializing database...")
    try:
        init_db()
        logger.info("[SUCCESS] Database initialization completed!")
    except Exception as e:
        logger.error(f"[ERROR] Database initialization failed: {e}")
        logger.warning("[FALLBACK] Trying fallback method...")
        try:
            create_tables_fallback()
            logger.info("[SUCCESS] Database initialized using fallback method")
        except Exception as fallback_error:
            logger.error(f"[ERROR] Fallback method also failed: {fallback_error}")
            return False
    return True


def cmd_migrate(args):
    """Run database migrations."""
    return run_alembic_command(["upgrade", "head"], "Database migration")


def cmd_rollback(args):
    """Rollback the last migration."""
    return run_alembic_command(["downgrade", "-1"], "Migration rollback")


def cmd_status(args):
    """Show migration status."""
    print("[STATUS] Database Migration Status")
    print("=" * 50)

    # Show current migration
    logger.info("Current migration:")
    run_alembic_command(["current"], "Getting current migration")

    print()

    # Show migration history
    logger.info("Migration history:")
    run_alembic_command(["history", "--verbose"], "Getting migration history")

    return True


def cmd_reset(args):
    """Reset the database (DANGEROUS - drops all tables)."""
    if not args.force:
        print("[WARNING] This will DROP ALL TABLES and recreate them!")
        print("All data will be PERMANENTLY LOST!")
        response = input("Type 'DELETE_ALL_DATA' to confirm: ")
        if response != "DELETE_ALL_DATA":
            logger.info("[CANCELLED] Database reset cancelled")
            return False

    logger.warning("[RESET] Resetting database...")

    # Downgrade to base
    if run_alembic_command(["downgrade", "base"], "Dropping all tables"):
        # Upgrade to head
        return run_alembic_command(["upgrade", "head"], "Recreating all tables")

    return False


def cmd_create_user(args):
    """Create an admin user."""
    try:
        # Import here to avoid circular imports
        import uuid

        from werkzeug.security import generate_password_hash

        from src.database.models.base import get_db
        from src.database.models.user import User

        # Get database session
        db = next(get_db())

        # Create admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@example.com",
            password_hash=generate_password_hash("admin123"),
            role="admin",
            is_active=True,
            is_verified=True,
        )

        # Check if admin already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            logger.warning("[EXISTS] Admin user already exists")
            return True

        db.add(admin_user)
        db.commit()

        logger.info("[SUCCESS] Admin user created successfully")
        logger.info("   Username: admin")
        logger.info("   Password: admin123")
        logger.warning("[WARNING] Please change the default password!")

        return True

    except Exception as e:
        logger.error(f"[ERROR] Failed to create admin user: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Database Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    parser_init = subparsers.add_parser("init", help="Initialize database")

    # Migrate command
    parser_migrate = subparsers.add_parser("migrate", help="Run migrations")

    # Rollback command
    parser_rollback = subparsers.add_parser("rollback", help="Rollback last migration")

    # Status command
    parser_status = subparsers.add_parser("status", help="Show migration status")

    # Reset command
    parser_reset = subparsers.add_parser("reset", help="Reset database (DANGEROUS)")
    parser_reset.add_argument("--force", action="store_true", help="Skip confirmation")

    # Create user command
    parser_user = subparsers.add_parser("create-user", help="Create admin user")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Command mapping
    commands = {
        "init": cmd_init,
        "migrate": cmd_migrate,
        "rollback": cmd_rollback,
        "status": cmd_status,
        "reset": cmd_reset,
        "create-user": cmd_create_user,
    }

    command_func = commands.get(args.command)
    if command_func:
        success = command_func(args)
        sys.exit(0 if success else 1)
    else:
        logger.error(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
