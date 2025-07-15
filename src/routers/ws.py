import asyncio
import json
import time
from typing import Dict

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from loguru import logger

from src.websocket_manager import websocket_manager

router = APIRouter()

# Shared stats will be injected from main.py
shared_stats = None


def initialize_shared_data(stats):
    """Initialize shared data from main process."""
    global shared_stats
    shared_stats = stats


@router.websocket("/ws/camera/{camera_id}")
async def camera_ws(websocket: WebSocket, camera_id: str):
    """WebSocket endpoint for camera general status."""
    await websocket.accept()
    await websocket_manager.connect_camera(camera_id, websocket)

    try:
        while True:
            # Get camera status from the shared stats
            if shared_stats and camera_id in shared_stats:
                status = shared_stats[camera_id]
                await websocket.send_json(status)
            else:
                await websocket.send_json(
                    {
                        "status": "offline",
                        "error": "Camera not found or not initialized",
                    }
                )
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        await websocket_manager.disconnect_camera(camera_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for camera {camera_id}: {str(e)}")
        await websocket_manager.disconnect_camera(camera_id, websocket)


@router.websocket("/ws/cameras/{camera_id}/prediction")
async def prediction_ws(websocket: WebSocket, camera_id: str):
    """WebSocket endpoint for camera predictions and alerts."""
    logger.info(
        f"[WEBSOCKET] Prediction WebSocket connection attempt for camera {camera_id}"
    )

    try:
        await websocket.accept()
        logger.info(f"[SUCCESS] WebSocket accepted for camera {camera_id}")

        await websocket_manager.connect_prediction(camera_id, websocket)
        logger.info(
            f"[WEBSOCKET] Prediction WebSocket registered in manager for camera {camera_id}"
        )

        # Send initial connection confirmation
        await websocket.send_json(
            {
                "type": "connection",
                "status": "connected",
                "camera_id": camera_id,
                "message": "Connected to prediction feed",
            }
        )
        logger.info(f"[SENT] Sent connection confirmation for camera {camera_id}")

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages (can be used for client-side requests)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                logger.debug(
                    f"[RECEIVED] Received client message for {camera_id}: {data}"
                )

                # Handle client requests (optional)
                try:
                    request = json.loads(data)
                    if request.get("type") == "ping":
                        await websocket.send_json(
                            {"type": "pong", "timestamp": time.time()}
                        )
                        logger.debug(f"[PONG] Sent pong to {camera_id}")
                except json.JSONDecodeError:
                    pass  # Ignore malformed requests

            except asyncio.TimeoutError:
                # Send keep-alive ping
                connection_count = websocket_manager.get_connection_count(camera_id)
                await websocket.send_json(
                    {
                        "type": "keepalive",
                        "timestamp": time.time(),
                        "connections": connection_count,
                    }
                )
                logger.debug(
                    f"[KEEPALIVE] Sent keepalive to {camera_id}, connections: {connection_count}"
                )

    except WebSocketDisconnect:
        logger.info(
            f"[DISCONNECTED] Prediction WebSocket disconnected for camera {camera_id}"
        )
        await websocket_manager.disconnect_prediction(camera_id, websocket)
    except Exception as e:
        logger.error(
            f"[ERROR] Error in prediction WebSocket for camera {camera_id}: {str(e)}"
        )
        await websocket_manager.disconnect_prediction(camera_id, websocket)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
