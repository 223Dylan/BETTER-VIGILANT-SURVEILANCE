import json
import logging
import os
import time
from datetime import datetime

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Configure audit logger (disabled to reduce log noise)
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.ERROR)  # Only log errors, not INFO requests

# Create audit log directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Add file handler for audit logs
audit_handler = logging.FileHandler("logs/audit.log")
audit_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
audit_logger.addHandler(audit_handler)


class AuditLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Get request details
        client_host = request.client.host
        method = request.method
        url = str(request.url)
        headers = dict(request.headers)

        # Remove sensitive information from headers
        if "authorization" in headers:
            headers["authorization"] = "***"
        if "x-api-key" in headers:
            headers["x-api-key"] = "***"

        # Get user role if available
        role = getattr(request.state, "role", "unknown")

        # Log request
        audit_logger.info(
            f"Request: {method} {url} from {client_host} (Role: {role})",
            extra={
                "timestamp": datetime.utcnow().isoformat(),
                "client_host": client_host,
                "method": method,
                "url": url,
                "headers": headers,
                "role": role,
            },
        )

        # Process request
        response = await call_next(request)

        # Calculate request duration
        duration = time.time() - start_time

        # Log response
        audit_logger.info(
            f"Response: {method} {url} - Status: {response.status_code} - Duration: {duration:.2f}s",
            extra={
                "timestamp": datetime.utcnow().isoformat(),
                "client_host": client_host,
                "method": method,
                "url": url,
                "status_code": response.status_code,
                "duration": duration,
                "role": role,
            },
        )

        return response
