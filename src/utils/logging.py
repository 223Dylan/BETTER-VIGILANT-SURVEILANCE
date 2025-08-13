import os
import sys

from loguru import logger


def setup_logging():
    """Configure logging for the application using environment variables.

    Respects the following .env vars:
      - LOG_LEVEL (e.g. DEBUG, INFO, WARNING)
      - LOG_FORMAT ("json" or "text")
      - LOG_FILE_PATH (e.g. logs/main.log)
      - LOG_MAX_SIZE (megabytes, for rotation)
      - LOG_BACKUP_COUNT (number of rotated files to keep)
    """
    # Read configuration from environment
    level = os.getenv("LOG_LEVEL", "WARNING").upper()
    log_format = os.getenv("LOG_FORMAT", "text").lower()
    log_file_path = os.getenv("LOG_FILE_PATH", "logs/app.log")
    max_size_mb = int(os.getenv("LOG_MAX_SIZE", "10"))
    backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    serialize = log_format == "json"

    # Remove default handler(s)
    logger.remove()

    # Console handler
    console_kwargs = {
        "sink": sys.stdout,
        "level": level,
        "serialize": serialize,
        "enqueue": True,
    }
    if not serialize:
        console_kwargs["format"] = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:"
            "<cyan>{line}</cyan> - <level>{message}</level>"
        )
    logger.add(**console_kwargs)

    # File handler for app logs
    file_kwargs = {
        "sink": log_file_path,
        "level": level,
        "rotation": f"{max_size_mb} MB",
        "retention": backup_count,
        "serialize": serialize,
        "enqueue": True,
    }
    if not serialize:
        file_kwargs["format"] = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
            "{name}:{function}:{line} - {message}"
        )
    logger.add(**file_kwargs)

    # File handler for per-camera logs (only if not JSON for readability)
    # For per-camera sink (callable sink), rotation/retention are not supported
    per_camera_kwargs = {
        "sink": lambda record: f"logs/camera_{record['extra'].get('camera_id', 'unknown')}.log",
        "level": level,
        "filter": lambda record: "camera_id" in record["extra"],
        "serialize": serialize,
        "enqueue": True,
    }
    if not serialize:
        per_camera_kwargs["format"] = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
            "{name}:{function}:{line} - {message}"
        )
    logger.add(**per_camera_kwargs)

    return logger
