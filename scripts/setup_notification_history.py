#!/usr/bin/env python3
"""
Script to set up notification history table and run migrations.
This script should be run after creating the new notification history model.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from alembic import command
from alembic.config import Config
from loguru import logger


def setup_notification_history():
    """Set up the notification history table by running migrations."""
    try:
        logger.info("Setting up notification history table...")

        # Get the project root directory
        project_root = Path(__file__).parent.parent
        alembic_cfg_path = project_root / "alembic.ini"

        if not alembic_cfg_path.exists():
            logger.error(
                "alembic.ini not found. Please ensure you're in the correct directory."
            )
            return False

        # Create Alembic configuration
        alembic_cfg = Config(str(alembic_cfg_path))
        alembic_cfg.set_main_option(
            "script_location", str(project_root / "src" / "database" / "migrations")
        )

        # Run the migration
        logger.info("Running notification history migration...")
        command.upgrade(alembic_cfg, "notification_history_001")

        logger.info("Notification history table setup completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Failed to set up notification history table: {e}")
        return False


def verify_setup():
    """Verify that the notification history table was created successfully."""
    try:
        # Import after migration to avoid circular dependency issues
        from src.database.models.base import get_db

        db = next(get_db())

        # Check if the table exists by running a simple query
        from sqlalchemy import text

        result = db.execute(text("SELECT COUNT(*) FROM notification_history"))
        count = result.scalar()

        logger.info(
            f"Notification history table verified. Current record count: {count}"
        )

        return True

    except Exception as e:
        logger.error(f"Failed to verify notification history table: {e}")
        return False


def main():
    """Main function to set up notification history."""
    logger.info("Starting notification history setup...")

    # Set up the table
    if not setup_notification_history():
        logger.error("Failed to set up notification history table")
        sys.exit(1)

    # Verify the setup
    if not verify_setup():
        logger.error("Failed to verify notification history table setup")
        sys.exit(1)

    logger.info("Notification history setup completed successfully!")
    logger.info("You can now use the notification history API endpoints:")
    logger.info("- GET /api/users/me/notification-history")
    logger.info("- GET /api/users/me/notification-stats")
    logger.info("- GET /api/admin/notification-history")
    logger.info("- GET /api/admin/notification-stats")


if __name__ == "__main__":
    main()
