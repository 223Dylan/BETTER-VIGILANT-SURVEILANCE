#!/usr/bin/env python3
"""
Script to migrate camera configurations from YAML to database.
Run this once to move from file-based to database-based configuration.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models.base import init_db
from src.services.camera_db_service import camera_db_service
from loguru import logger

def main():
    """Main migration function."""
    logger.info("Starting camera configuration migration...")
    
    # Initialize database
    init_db()
    
    # Migrate from YAML config
    config_path = "config/config.yaml"
    if os.path.exists(config_path):
        success = camera_db_service.migrate_from_yaml_config(config_path)
        if success:
            logger.info("[SUCCESS] Migration completed successfully!")
            logger.info("You can now use database-based camera management.")
            logger.info("Consider backing up your YAML config and switching to database mode.")
        else:
            logger.error("[ERROR] Migration failed!")
    else:
        logger.warning(f"Config file {config_path} not found!")

if __name__ == "__main__":
    main() 