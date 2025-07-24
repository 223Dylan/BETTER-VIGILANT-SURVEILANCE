import asyncio
import json
import time
from typing import Dict

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from loguru import logger

from src.websocket_manager import websocket_manager

# Import metrics service with fallback handling
try:
    from src.services.metrics_service import MetricsService
except ImportError:
    # Fallback if aiohttp not available
    from src.services.metrics_service_requests import (
        MetricsServiceRequests as MetricsService,
    )

router = APIRouter()

# Shared stats will be injected from main.py
shared_stats = None

# Initialize metrics service for real-time updates
metrics_service = MetricsService()


def initialize_shared_data(stats):
    """Initialize shared data from main process."""
    global shared_stats
    shared_stats = stats


@router.get("/ws/debug/connections")
async def debug_connections():
    """Debug endpoint to check current WebSocket connections."""
    import os

    return {
        "websocket_manager_id": id(websocket_manager),
        "process_pid": os.getpid(),
        "camera_connections": {
            camera_id: len(connections)
            for camera_id, connections in websocket_manager.camera_connections.items()
        },
        "prediction_connections": {
            camera_id: len(connections)
            for camera_id, connections in websocket_manager.prediction_connections.items()
        },
        "total_camera_connections": len(websocket_manager.camera_connections),
        "total_prediction_connections": len(websocket_manager.prediction_connections),
    }


@router.get("/ws/debug/test-broadcast/{camera_id}")
async def test_broadcast(camera_id: str):
    """Test broadcasting to a specific camera to debug the issue."""
    test_data = {
        "type": "test",
        "message": "Debug test broadcast",
        "timestamp": time.time(),
    }

    try:
        await websocket_manager.broadcast_prediction(camera_id, test_data)
        return {"status": "success", "message": f"Test broadcast sent to {camera_id}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/ws/debug/test-redis/{camera_id}")
async def test_redis_broadcast(camera_id: str):
    """Test Redis-based broadcasting to simulate Celery worker."""
    from src.services.redis_websocket_bridge import redis_websocket_bridge

    test_data = {
        "type": "test_prediction",
        "message": "Redis pub/sub test",
        "confidence": 0.85,
        "timestamp": time.time(),
    }

    try:
        success = redis_websocket_bridge.publish_websocket_event(
            camera_id=camera_id, event_type="prediction", data=test_data
        )

        if success:
            return {
                "status": "success",
                "message": f"Redis test broadcast published for {camera_id}",
            }
        else:
            return {"status": "error", "message": "Failed to publish to Redis"}

    except Exception as e:
        return {"status": "error", "message": str(e)}


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
    """WebSocket endpoint for camera predictions."""
    await websocket.accept()
    await websocket_manager.connect_prediction(camera_id, websocket)

    try:
        while True:
            # Keep connection alive with heartbeat
            try:
                await websocket.send_json(
                    {"type": "heartbeat", "timestamp": time.time()}
                )
            except:
                # WebSocket closed, exit loop
                logger.info(f"WebSocket closed for camera {camera_id} predictions")
                break
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        await websocket_manager.disconnect_prediction(camera_id, websocket)
    except Exception as e:
        logger.error(f"Prediction WebSocket error for camera {camera_id}: {str(e)}")
        await websocket_manager.disconnect_prediction(camera_id, websocket)


@router.websocket("/ws/metrics")
async def metrics_ws(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics updates."""
    await websocket.accept()
    logger.info("[WEBSOCKET] Metrics WebSocket connected")

    try:
        while True:
            # Get comprehensive metrics summary
            try:
                metrics_summary = await metrics_service.get_metrics_summary()

                # Send metrics update
                try:
                    await websocket.send_json(
                        {
                            "type": "metrics_update",
                            "timestamp": time.time(),
                            "data": metrics_summary,
                        }
                    )
                except:
                    # WebSocket closed, exit loop
                    logger.info("WebSocket closed during metrics update, exiting loop")
                    break

                # Wait 5 seconds before next update
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error fetching metrics for WebSocket: {e}")
                # Only try to send error if WebSocket is still open
                try:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "timestamp": time.time(),
                            "message": "Failed to fetch metrics",
                        }
                    )
                except:
                    # WebSocket is closed, break out of the loop
                    logger.info(
                        "WebSocket closed during error handling, exiting metrics loop"
                    )
                    break
                await asyncio.sleep(10)  # Wait longer on error

    except WebSocketDisconnect:
        logger.info("[WEBSOCKET] Metrics WebSocket disconnected")
    except Exception as e:
        logger.error(f"Metrics WebSocket error: {str(e)}")


@router.websocket("/ws/metrics/camera/{camera_id}")
async def camera_metrics_ws(websocket: WebSocket, camera_id: str):
    """WebSocket endpoint for real-time camera-specific metrics."""
    await websocket.accept()
    logger.info(f"[WEBSOCKET] Camera metrics WebSocket connected for {camera_id}")

    try:
        while True:
            try:
                # Get camera-specific performance data
                performance = await metrics_service.get_camera_performance(
                    camera_id, "5m"
                )

                # Get recent detections for this camera
                recent_detections = await metrics_service.get_detection_metrics(
                    time_range="5m", camera_id=camera_id
                )

                # Send camera metrics update safely
                success = await _safe_websocket_send(
                    websocket,
                    {
                        "type": "camera_metrics_update",
                        "camera_id": camera_id,
                        "timestamp": time.time(),
                        "performance": performance,
                        "recent_detections": recent_detections[:5],  # Last 5 detections
                    },
                )

                # If send failed, connection is likely closed
                if not success:
                    logger.debug(
                        f"[WEBSOCKET] Failed to send camera metrics for {camera_id}, connection likely closed"
                    )
                    break

                await asyncio.sleep(
                    3
                )  # Update every 3 seconds for camera-specific data

            except Exception as e:
                logger.error(
                    f"Error fetching camera {camera_id} metrics for WebSocket: {e}"
                )

                # Try to send error message, but don't fail if WebSocket is closed
                error_sent = await _safe_websocket_send(
                    websocket,
                    {
                        "type": "error",
                        "camera_id": camera_id,
                        "timestamp": time.time(),
                        "message": f"Failed to fetch metrics for camera {camera_id}",
                    },
                )

                if not error_sent:
                    logger.debug(
                        f"[WEBSOCKET] Failed to send error message for camera {camera_id}, connection likely closed"
                    )
                    break

                await asyncio.sleep(10)

    except WebSocketDisconnect:
        logger.info(
            f"[WEBSOCKET] Camera metrics WebSocket disconnected for {camera_id}"
        )
    except Exception as e:
        logger.error(f"Camera metrics WebSocket error for {camera_id}: {str(e)}")


async def _safe_websocket_send(websocket: WebSocket, data: dict) -> bool:
    """Safely send data through WebSocket with connection state checking."""
    try:
        await websocket.send_json(data)
        return True
    except Exception as e:
        logger.debug(f"WebSocket send failed: {e}")
        return False


@router.websocket("/ws/alerts")
async def alerts_ws(websocket: WebSocket):
    """WebSocket endpoint for real-time alert notifications."""
    await websocket.accept()
    logger.info("[WEBSOCKET] Alerts WebSocket connected")

    try:
        while True:
            try:
                # Get recent alerts (last 10 minutes)
                recent_alerts = await metrics_service.get_recent_alerts(limit=20)

                # Filter for very recent alerts (last 5 minutes)
                current_time = time.time()
                five_minutes_ago = current_time - (5 * 60)

                new_alerts = []
                for alert in recent_alerts:
                    alert_time = alert.get("timestamp")
                    if alert_time:
                        # Parse timestamp and check if within last 5 minutes
                        try:
                            from datetime import datetime

                            parsed_time = datetime.fromisoformat(
                                alert_time.replace("Z", "+00:00")
                            )
                            if parsed_time.timestamp() > five_minutes_ago:
                                new_alerts.append(alert)
                        except:
                            continue

                # Send alerts update safely
                success = await _safe_websocket_send(
                    websocket,
                    {
                        "type": "alerts_update",
                        "timestamp": current_time,
                        "new_alerts": new_alerts,
                        "total_recent": len(recent_alerts),
                    },
                )

                # If send failed, connection is likely closed
                if not success:
                    logger.debug(
                        "[WEBSOCKET] Failed to send alerts update, connection likely closed"
                    )
                    break

                await asyncio.sleep(30)  # Check for new alerts every 30 seconds

            except Exception as e:
                logger.error(f"Error fetching alerts for WebSocket: {e}")

                # Try to send error message, but don't fail if WebSocket is closed
                error_sent = await _safe_websocket_send(
                    websocket,
                    {
                        "type": "error",
                        "timestamp": time.time(),
                        "message": "Failed to fetch alerts",
                    },
                )

                if not error_sent:
                    logger.debug(
                        "[WEBSOCKET] Failed to send error message, connection likely closed"
                    )
                    break

                await asyncio.sleep(60)

    except WebSocketDisconnect:
        logger.info("[WEBSOCKET] Alerts WebSocket disconnected")
    except Exception as e:
        logger.error(f"Alerts WebSocket error: {str(e)}")
