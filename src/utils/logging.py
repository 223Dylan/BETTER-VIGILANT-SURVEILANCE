import sys
from loguru import logger


def setup_logging():
    """Configure logging for the application."""
    # Remove default handler
    logger.remove()

    # Add console handler with debug level
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
    )

    # Add file handler for app logs
    logger.add(
        "logs/app.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        enqueue=True,
    )

    # Add file handler for camera logs
    logger.add(
        lambda record: f"logs/camera_{record['extra'].get('camera_id', 'unknown')}.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        filter=lambda record: "camera_id" in record["extra"],
        enqueue=True,
    )

    return logger
