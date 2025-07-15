import os
import subprocess
import sys

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy_utils import create_database, database_exists

from src.database.models.base import DATABASE_URL, Base


def init_db():
    """Initialize the database using Alembic migrations."""
    try:
        # Create database if it doesn't exist
        if not database_exists(DATABASE_URL):
            logger.info(f"Creating database: {DATABASE_URL}")
            create_database(DATABASE_URL)
            logger.info("Database created successfully")
        else:
            logger.info("Database already exists")

        # Run Alembic migrations to create/update tables
        logger.info("Running Alembic migrations...")

        # Get the project root directory (where alembic.ini is located)
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        # Run alembic upgrade head
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.info("Database migrations completed successfully")
            logger.info(result.stdout)
        else:
            logger.error(f"Migration failed: {result.stderr}")
            raise Exception(f"Alembic migration failed: {result.stderr}")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def create_tables_fallback():
    """Fallback method to create tables directly (for development/testing)."""
    try:
        logger.warning("Using fallback method to create tables directly")
        engine = create_engine(DATABASE_URL)

        # Import all models to ensure they're registered
        from src.database.models.alert import Alert
        from src.database.models.camera import Camera
        from src.database.models.frame import Frame
        from src.database.models.user import User

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully using fallback method")

    except Exception as e:
        logger.error(f"Error in fallback table creation: {e}")
        raise


if __name__ == "__main__":
    try:
        init_db()
    except Exception as e:
        logger.warning(f"Migration failed, trying fallback: {e}")
        create_tables_fallback()
