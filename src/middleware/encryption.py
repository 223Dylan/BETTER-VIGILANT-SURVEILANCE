from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.security.encryption import encryption_manager
import json
from typing import Callable
import time

class EncryptionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # List of paths that require encryption
        self.encrypted_paths = {
            '/api/cameras/{camera_id}/prediction',
            '/api/cameras/{camera_id}/frame',
            '/api/cameras/details'
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if the path requires encryption
        path = request.url.path
        if not any(path.startswith(p.replace('{camera_id}', '')) for p in self.encrypted_paths):
            return await call_next(request)

        # Process request
        try:
            # Get request body if present
            body = None
            if request.method in ['POST', 'PUT', 'PATCH']:
                body = await request.body()
                if body:
                    try:
                        # Try to decrypt if encrypted
                        decrypted = encryption_manager.decrypt_data(body.decode())
                        # Replace request body with decrypted data
                        request._body = json.dumps(decrypted).encode()
                    except:
                        # If decryption fails, assume it's not encrypted
                        pass

            # Get response
            response = await call_next(request)

            # Encrypt response if it's JSON
            if response.headers.get('content-type') == 'application/json':
                try:
                    body = await response.body()
                    data = json.loads(body)
                    encrypted = encryption_manager.encrypt_data(data)
                    return Response(
                        content=encrypted,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type='application/json'
                    )
                except:
                    # If encryption fails, return original response
                    return response

            return response

        except Exception as e:
            # Log the error and return a 500 response
            print(f"Encryption middleware error: {str(e)}")
            return Response(
                content=json.dumps({"error": "Internal server error"}),
                status_code=500,
                media_type='application/json'
            )

class RequestSigningMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # List of paths that require request signing
        self.signed_paths = {
            '/api/cameras/{camera_id}/enable',
            '/api/cameras/{camera_id}/disable',
            '/api/cameras/{camera_id}/control'
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if the path requires signing
        path = request.url.path
        if not any(path.startswith(p.replace('{camera_id}', '')) for p in self.signed_paths):
            return await call_next(request)

        # Verify request signature
        signature = request.headers.get('X-Request-Signature')
        if not signature:
            return Response(
                content=json.dumps({"error": "Missing request signature"}),
                status_code=401,
                media_type='application/json'
            )

        try:
            # Get request body
            body = await request.body()
            if not body:
                return Response(
                    content=json.dumps({"error": "Empty request body"}),
                    status_code=400,
                    media_type='application/json'
                )

            # Parse request data
            data = json.loads(body)

            # Verify signature
            if not encryption_manager.verify_signature(data, signature):
                return Response(
                    content=json.dumps({"error": "Invalid request signature"}),
                    status_code=401,
                    media_type='application/json'
                )

            # Check timestamp to prevent replay attacks
            timestamp = data.get('timestamp')
            if not timestamp:
                return Response(
                    content=json.dumps({"error": "Missing timestamp"}),
                    status_code=400,
                    media_type='application/json'
                )

            # Allow 5-minute window for request timing
            request_time = time.time()
            timestamp_time = time.mktime(time.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f"))
            if abs(request_time - timestamp_time) > 300:
                return Response(
                    content=json.dumps({"error": "Request expired"}),
                    status_code=401,
                    media_type='application/json'
                )

            return await call_next(request)

        except Exception as e:
            print(f"Request signing middleware error: {str(e)}")
            return Response(
                content=json.dumps({"error": "Internal server error"}),
                status_code=500,
                media_type='application/json'
            ) 