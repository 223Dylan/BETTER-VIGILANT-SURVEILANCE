import json
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from src.websockets.analytics_websocket_manager import analytics_websocket_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/analytics")
async def analytics_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time analytics updates."""
    await analytics_websocket_manager.connect(websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                await analytics_websocket_manager.handle_message(websocket, message)
            except json.JSONDecodeError:
                await analytics_websocket_manager.send_personal_message(
                    websocket,
                    {
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat(),
                    },
                )

    except WebSocketDisconnect:
        await analytics_websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await analytics_websocket_manager.disconnect(websocket)


@router.websocket("/ws/analytics/{client_id}")
async def analytics_websocket_endpoint_with_id(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time analytics updates with client identification."""
    await analytics_websocket_manager.connect(websocket, client_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                await analytics_websocket_manager.handle_message(websocket, message)
            except json.JSONDecodeError:
                await analytics_websocket_manager.send_personal_message(
                    websocket,
                    {
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat(),
                    },
                )

    except WebSocketDisconnect:
        await analytics_websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await analytics_websocket_manager.disconnect(websocket)


@router.post("/websocket/analytics/start")
async def start_analytics_websocket_broadcasting():
    """Start the analytics WebSocket broadcasting service."""
    await analytics_websocket_manager.start_broadcasting()
    return {"message": "Analytics WebSocket broadcasting started"}


@router.post("/websocket/analytics/stop")
async def stop_analytics_websocket_broadcasting():
    """Stop the analytics WebSocket broadcasting service."""
    await analytics_websocket_manager.stop_broadcasting()
    return {"message": "Analytics WebSocket broadcasting stopped"}


@router.get("/websocket/analytics/status")
async def get_analytics_websocket_status():
    """Get the current status of the analytics WebSocket service."""
    active_connections = len(analytics_websocket_manager.active_connections)
    is_broadcasting = analytics_websocket_manager._running

    return {
        "active_connections": active_connections,
        "broadcasting_active": is_broadcasting,
        "connection_details": [
            {
                "client_id": details.get("client_id", "anonymous"),
                "subscribed_topics": list(details.get("subscribed_topics", [])),
                "connected_at": (
                    details.get("connected_at").isoformat()
                    if details.get("connected_at")
                    else None
                ),
                "last_heartbeat": (
                    details.get("last_heartbeat").isoformat()
                    if details.get("last_heartbeat")
                    else None
                ),
            }
            for details in analytics_websocket_manager.connection_subscriptions.values()
        ],
    }
