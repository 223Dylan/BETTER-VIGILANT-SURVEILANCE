from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import os

# Default limits (can be overridden by environment variables)
DEFAULT_MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
DEFAULT_MAX_HEADER_SIZE = 8 * 1024  # 8KB


class RequestLimitsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.max_content_length = int(
            os.getenv("MAX_CONTENT_LENGTH", DEFAULT_MAX_CONTENT_LENGTH)
        )
        self.max_header_size = int(
            os.getenv("MAX_HEADER_SIZE", DEFAULT_MAX_HEADER_SIZE)
        )

    async def dispatch(self, request: Request, call_next):
        # Check header size
        header_size = sum(len(k) + len(v) for k, v in request.headers.items())
        if header_size > self.max_header_size:
            raise HTTPException(
                status_code=431, detail="Request header fields too large"
            )

        # Check content length if present
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                content_length = int(content_length)
                if content_length > self.max_content_length:
                    raise HTTPException(
                        status_code=413, detail="Request entity too large"
                    )
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid content length")

        return await call_next(request)
