import asyncio
import json
import time
from typing import Dict, Set

from fastapi import WebSocket
from loguru import logger


class WebSocketManager:
    """Manages WebSocket connections and routes messages to appropriate cameras."""

    def __init__(self):
        # Dictionary to store WebSocket connections per camera
        self.camera_connections: Dict[str, Set[WebSocket]] = {}
        self.prediction_connections: Dict[str, Set[WebSocket]] = {}

    async def connect_camera(self, camera_id: str, websocket: WebSocket):
        """Connect a WebSocket to a camera's general feed."""
        if camera_id not in self.camera_connections:
            self.camera_connections[camera_id] = set()
        self.camera_connections[camera_id].add(websocket)
        logger.info(
            f"[WEBSOCKET] Camera WebSocket connected for {camera_id}. Total connections: {len(self.camera_connections[camera_id])}"
        )

    async def connect_prediction(self, camera_id: str, websocket: WebSocket):
        """Connect a WebSocket to a camera's prediction feed."""
        import os

        if camera_id not in self.prediction_connections:
            self.prediction_connections[camera_id] = set()
        self.prediction_connections[camera_id].add(websocket)
        logger.info(
            f"[WEBSOCKET] Prediction WebSocket ADDED for {camera_id}. Total connections: {len(self.prediction_connections[camera_id])}"
        )
        logger.info(
            f"[DEBUG] WebSocketManager instance ID: {id(self)} | Process PID: {os.getpid()}"
        )
        logger.info(
            f"[INFO] Current prediction connections: {list(self.prediction_connections.keys())}"
        )

    async def disconnect_camera(self, camera_id: str, websocket: WebSocket):
        """Disconnect a WebSocket from a camera's general feed."""
        if camera_id in self.camera_connections:
            self.camera_connections[camera_id].discard(websocket)
            if not self.camera_connections[camera_id]:
                del self.camera_connections[camera_id]
            logger.info(f"[WEBSOCKET] Camera WebSocket disconnected for {camera_id}")

    async def disconnect_prediction(self, camera_id: str, websocket: WebSocket):
        """Disconnect a WebSocket from a camera's prediction feed."""
        if camera_id in self.prediction_connections:
            self.prediction_connections[camera_id].discard(websocket)
            if not self.prediction_connections[camera_id]:
                del self.prediction_connections[camera_id]
            logger.info(f"[WEBSOCKET] Prediction WebSocket REMOVED for {camera_id}")

    async def broadcast_to_camera(self, camera_id: str, message: dict):
        """Broadcast a message to all general WebSocket connections for a camera."""
        if camera_id not in self.camera_connections:
            return

        connections_to_remove = set()
        for websocket in self.camera_connections[camera_id].copy():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to camera {camera_id}: {e}")
                connections_to_remove.add(websocket)

        # Remove failed connections
        for websocket in connections_to_remove:
            self.camera_connections[camera_id].discard(websocket)

    async def broadcast_prediction(self, camera_id: str, prediction_data: dict):
        """Broadcast a prediction to all prediction WebSocket connections for a camera."""
        import os

        logger.info(f"[SEARCH] Looking for prediction connections for {camera_id}")
        logger.info(
            f"[DEBUG] WebSocketManager instance ID: {id(self)} | Process PID: {os.getpid()}"
        )
        logger.info(
            f"[INFO] Available cameras with connections: {list(self.prediction_connections.keys())}"
        )

        if camera_id not in self.prediction_connections:
            logger.warning(
                f"[WARNING] No prediction connections for camera {camera_id}"
            )
            return

        connections = self.prediction_connections[camera_id]
        logger.info(f"[INFO] Found {len(connections)} connections for {camera_id}")

        message = {
            "type": "prediction",
            "camera_id": camera_id,
            "timestamp": time.time(),
            "prediction": prediction_data,
        }

        connections_to_remove = set()
        sent_count = 0

        for websocket in connections.copy():
            try:
                await websocket.send_json(message)
                sent_count += 1
                logger.info(
                    f"[SUCCESS] Sent prediction to connection #{sent_count} for {camera_id}"
                )
            except Exception as e:
                logger.error(f"[ERROR] Error sending prediction to {camera_id}: {e}")
                connections_to_remove.add(websocket)

        # Remove failed connections
        for websocket in connections_to_remove:
            connections.discard(websocket)

        logger.info(
            f"[SENT] Successfully sent prediction to {sent_count} connections for {camera_id}"
        )

    async def broadcast_alert(self, camera_id: str, alert_data: dict):
        """Broadcast an alert to all connected clients for a camera."""
        logger.info(f"[BROADCAST] Broadcasting alert for {camera_id}")

        # Broadcast to both camera and prediction connections
        await self.broadcast_to_camera(camera_id, alert_data)
        await self.broadcast_prediction(camera_id, alert_data)

        logger.info(f"[SENT] Alert broadcasted for {camera_id}")

    async def send_to_user(self, user_id: str, message: dict):
        """Send a notification message to a specific user."""
        logger.info(f"[WEBSOCKET] Attempting to send notification to user {user_id}")

        # Broadcast to all connections since we don't have user-specific connections
        sent_count = 0

        # Broadcast to all camera connections
        for camera_id, connections in self.camera_connections.items():
            for websocket in connections.copy():
                try:
                    await websocket.send_json(
                        {
                            "type": "user_notification",
                            "user_id": user_id,
                            "message": message,
                            "timestamp": time.time(),
                        }
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"[WEBSOCKET] Error sending to user {user_id}: {e}")

        # Broadcast to all prediction connections
        for camera_id, connections in self.prediction_connections.items():
            for websocket in connections.copy():
                try:
                    await websocket.send_json(
                        {
                            "type": "user_notification",
                            "user_id": user_id,
                            "message": message,
                            "timestamp": time.time(),
                        }
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"[WEBSOCKET] Error sending to user {user_id}: {e}")

        logger.info(
            f"[WEBSOCKET] Sent notification to {sent_count} connections for user {user_id}"
        )
        return sent_count > 0

    def get_connection_count(self, camera_id: str) -> dict:
        """Get connection counts for a camera."""
        return {
            "camera_connections": len(self.camera_connections.get(camera_id, set())),
            "prediction_connections": len(
                self.prediction_connections.get(camera_id, set())
            ),
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
