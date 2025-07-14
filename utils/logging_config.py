import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

class StructuredLogFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Create base log object
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if they exist
        if hasattr(record, "extra"):
            log_obj.update(record.extra)
            
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)

def setup_logging(
    name: str,
    level: str = "INFO",
    log_file: str = None,
    extra_handlers: list = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    rotation: str = "midnight"
) -> logging.Logger:
    """
    Set up a logger with structured logging and rotation policies.
    
    Args:
        name: Name of the logger
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        extra_handlers: Additional logging handlers to add
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup files to keep
        rotation: When to rotate logs ('midnight', 'size', or None)
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Create handlers
    handlers = []
    
    # Console handler with structured formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredLogFormatter())
    handlers.append(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        if rotation == "midnight":
            # Rotate at midnight
            file_handler = TimedRotatingFileHandler(
                log_file,
                when="midnight",
                interval=1,
                backupCount=backup_count
            )
        elif rotation == "size":
            # Rotate by size
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
        else:
            # No rotation
            file_handler = logging.FileHandler(log_file)
            
        file_handler.setFormatter(StructuredLogFormatter())
        handlers.append(file_handler)
    
    # Add any extra handlers
    if extra_handlers:
        handlers.extend(extra_handlers)
    
    # Remove any existing handlers
    logger.handlers.clear()
    
    # Add all handlers
    for handler in handlers:
        logger.addHandler(handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name) 