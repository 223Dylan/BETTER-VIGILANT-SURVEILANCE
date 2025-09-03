import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket
from loguru import logger

from src.database.models import (
    AnalyticsAggregates,
    CameraMetrics,
    DetectionMetrics,
    SystemMetrics,
    get_db,
)
from src.services.analytics_aggregation_service import analytics_aggregation_service


class AnalyticsWebSocketManager:
    """Manages WebSocket connections for real-time analytics updates."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_subscriptions: Dict[WebSocket, Dict[str, Any]] = {}
        self._broadcast_task: Optional[asyncio.Task] = None
        self._running = False

    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_subscriptions[websocket] = {
            "client_id": client_id,
            "subscribed_topics": set(),
            "connected_at": datetime.now(),
            "last_heartbeat": datetime.now(),
        }
        logger.info(f"Analytics WebSocket connected: {client_id or 'anonymous'}")

        # Send initial connection confirmation
        await self.send_personal_message(
            websocket,
            {
                "type": "connection_established",
                "message": "Connected to analytics WebSocket",
                "timestamp": datetime.now().isoformat(),
                "available_topics": [
                    "system_metrics",
                    "camera_metrics",
                    "detection_metrics",
                    "analytics_aggregates",
                    "system_status",
                    "alerts_summary",
                ],
            },
        )

    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection."""
        if websocket in self.active_connections:
            client_id = self.connection_subscriptions.get(websocket, {}).get(
                "client_id"
            )
            self.active_connections.remove(websocket)
            if websocket in self.connection_subscriptions:
                del self.connection_subscriptions[websocket]
            logger.info(f"Analytics WebSocket disconnected: {client_id or 'anonymous'}")

    async def subscribe(self, websocket: WebSocket, topics: List[str]):
        """Subscribe to specific analytics topics."""
        if websocket in self.connection_subscriptions:
            self.connection_subscriptions[websocket]["subscribed_topics"].update(topics)
            await self.send_personal_message(
                websocket,
                {
                    "type": "subscription_confirmed",
                    "topics": topics,
                    "message": f"Subscribed to: {', '.join(topics)}",
                    "timestamp": datetime.now().isoformat(),
                },
            )
            logger.info(f"Client subscribed to topics: {topics}")

    async def unsubscribe(self, websocket: WebSocket, topics: List[str]):
        """Unsubscribe from specific analytics topics."""
        if websocket in self.connection_subscriptions:
            self.connection_subscriptions[websocket][
                "subscribed_topics"
            ].difference_update(topics)
            await self.send_personal_message(
                websocket,
                {
                    "type": "unsubscription_confirmed",
                    "topics": topics,
                    "message": f"Unsubscribed from: {', '.join(topics)}",
                    "timestamp": datetime.now().isoformat(),
                },
            )
            logger.info(f"Client unsubscribed from topics: {topics}")

    async def send_personal_message(
        self, websocket: WebSocket, message: Dict[str, Any]
    ):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            await self.disconnect(websocket)

    async def broadcast_to_topic(self, topic: str, message: Dict[str, Any]):
        """Broadcast a message to all connections subscribed to a specific topic."""
        if not self.active_connections:
            return

        disconnected = set()
        for websocket in self.active_connections:
            if websocket in self.connection_subscriptions:
                subscribed_topics = self.connection_subscriptions[websocket][
                    "subscribed_topics"
                ]
                if topic in subscribed_topics:
                    try:
                        await websocket.send_text(json.dumps(message))
                    except Exception as e:
                        logger.error(f"Error broadcasting to topic {topic}: {e}")
                        disconnected.add(websocket)

        # Clean up disconnected connections
        for websocket in disconnected:
            await self.disconnect(websocket)

    async def broadcast_system_metrics(self, system_metrics: SystemMetrics):
        """Broadcast system metrics update."""
        message = {
            "type": "system_metrics_update",
            "topic": "system_metrics",
            "data": {
                "id": str(system_metrics.id),
                "hostname": system_metrics.hostname,
                "cpu_usage_percent": system_metrics.cpu_usage_percent,
                "memory_usage_percent": system_metrics.memory_usage_percent,
                "disk_usage_percent": system_metrics.disk_usage_percent,
                "active_cameras": system_metrics.active_cameras,
                "active_detections": system_metrics.active_detections,
                "active_alerts": system_metrics.active_alerts,
                "timestamp": (
                    system_metrics.timestamp.isoformat()
                    if system_metrics.timestamp
                    else None
                ),
            },
            "timestamp": datetime.now().isoformat(),
        }
        await self.broadcast_to_topic("system_metrics", message)

    async def broadcast_camera_metrics(self, camera_metrics: CameraMetrics):
        """Broadcast camera metrics update."""
        message = {
            "type": "camera_metrics_update",
            "topic": "camera_metrics",
            "data": {
                "id": str(camera_metrics.id),
                "camera_id": camera_metrics.camera_id,
                "connection_status": camera_metrics.connection_status,
                "fps_actual": camera_metrics.fps_actual,
                "fps_target": camera_metrics.fps_target,
                "resolution_width": camera_metrics.resolution_width,
                "resolution_height": camera_metrics.resolution_height,
                "queue_depth": camera_metrics.queue_depth,
                "dropped_frames": camera_metrics.dropped_frames,
                "timestamp": (
                    camera_metrics.timestamp.isoformat()
                    if camera_metrics.timestamp
                    else None
                ),
            },
            "timestamp": datetime.now().isoformat(),
        }
        await self.broadcast_to_topic("camera_metrics", message)

    async def broadcast_detection_metrics(self, detection_metrics: DetectionMetrics):
        """Broadcast detection metrics update."""
        message = {
            "type": "detection_metrics_update",
            "topic": "detection_metrics",
            "data": {
                "id": str(detection_metrics.id),
                "camera_id": detection_metrics.camera_id,
                "model_name": detection_metrics.model_name,
                "prediction_label": detection_metrics.prediction_label,
                "confidence_score": detection_metrics.confidence_score,
                "is_shoplifting": detection_metrics.is_shoplifting,
                "processing_time_ms": detection_metrics.processing_time_ms,
                "alert_triggered": detection_metrics.alert_triggered,
                "alert_level": detection_metrics.alert_level,
                "timestamp": (
                    detection_metrics.timestamp.isoformat()
                    if detection_metrics.timestamp
                    else None
                ),
            },
            "timestamp": datetime.now().isoformat(),
        }
        await self.broadcast_to_topic("detection_metrics", message)

    async def broadcast_analytics_aggregates(self, aggregate: AnalyticsAggregates):
        """Broadcast analytics aggregates update."""
        message = {
            "type": "analytics_aggregates_update",
            "topic": "analytics_aggregates",
            "data": {
                "id": str(aggregate.id),
                "aggregation_type": aggregate.aggregation_type,
                "time_period": aggregate.time_period,
                "start_time": (
                    aggregate.start_time.isoformat() if aggregate.start_time else None
                ),
                "end_time": (
                    aggregate.end_time.isoformat() if aggregate.end_time else None
                ),
                "total_detections": aggregate.total_detections,
                "shoplifting_detections": aggregate.shoplifting_detections,
                "total_alerts": aggregate.total_alerts,
                "average_confidence": aggregate.average_confidence,
                "average_cpu_usage": aggregate.average_cpu_usage,
                "average_memory_usage": aggregate.average_memory_usage,
                "active_cameras_count": aggregate.active_cameras_count,
                "timestamp": datetime.now().isoformat(),
            },
            "timestamp": datetime.now().isoformat(),
        }
        await self.broadcast_to_topic("analytics_aggregates", message)

    async def broadcast_system_status(self, status_data: Dict[str, Any]):
        """Broadcast system status update."""
        message = {
            "type": "system_status_update",
            "topic": "system_status",
            "data": status_data,
            "timestamp": datetime.now().isoformat(),
        }
        await self.broadcast_to_topic("system_status", message)

    async def broadcast_alerts_summary(self, alerts_data: Dict[str, Any]):
        """Broadcast alerts summary update."""
        message = {
            "type": "alerts_summary_update",
            "topic": "alerts_summary",
            "data": alerts_data,
            "timestamp": datetime.now().isoformat(),
        }
        await self.broadcast_to_topic("alerts_summary", message)

    async def start_broadcasting(self):
        """Start the broadcasting service."""
        if self._running:
            return

        self._running = True
        self._broadcast_task = asyncio.create_task(self._broadcast_loop())
        logger.info("Analytics WebSocket broadcasting service started")

    async def stop_broadcasting(self):
        """Stop the broadcasting service."""
        self._running = False
        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass
        logger.info("Analytics WebSocket broadcasting service stopped")

    async def _broadcast_loop(self):
        """Main broadcasting loop for periodic updates."""
        while self._running:
            try:
                # Send periodic system status updates
                if self.active_connections:
                    await self._send_periodic_updates()

                # Wait before next update
                await asyncio.sleep(5)  # Update every 5 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(1)

    async def _send_periodic_updates(self):
        """Send periodic updates to all connected clients."""
        try:
            db = next(get_db())

            # Get latest system metrics
            latest_system = (
                db.query(SystemMetrics).order_by(SystemMetrics.timestamp.desc()).first()
            )
            if latest_system:
                await self.broadcast_system_metrics(latest_system)

            # Get latest camera metrics
            latest_cameras = (
                db.query(CameraMetrics)
                .order_by(CameraMetrics.timestamp.desc())
                .limit(5)
                .all()
            )
            for camera_metric in latest_cameras:
                await self.broadcast_camera_metrics(camera_metric)

            # Get latest detection metrics
            latest_detections = (
                db.query(DetectionMetrics)
                .order_by(DetectionMetrics.timestamp.desc())
                .limit(3)
                .all()
            )
            for detection_metric in latest_detections:
                await self.broadcast_detection_metrics(detection_metric)

            # Get latest analytics aggregates
            latest_aggregates = (
                db.query(AnalyticsAggregates)
                .order_by(AnalyticsAggregates.last_calculated.desc())
                .limit(2)
                .all()
            )
            for aggregate in latest_aggregates:
                await self.broadcast_analytics_aggregates(aggregate)

        except Exception as e:
            logger.error(f"Error sending periodic updates: {e}")

    async def handle_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Handle incoming WebSocket messages."""
        try:
            # Handle direct topic list subscription (from frontend)
            if isinstance(message, list):
                topics = message
                await self.subscribe(websocket, topics)
                return

            message_type = message.get("type")

            if message_type == "subscribe":
                topics = message.get("topics", [])
                await self.subscribe(websocket, topics)

            elif message_type == "unsubscribe":
                topics = message.get("topics", [])
                await self.unsubscribe(websocket, topics)

            elif message_type == "heartbeat":
                if websocket in self.connection_subscriptions:
                    self.connection_subscriptions[websocket][
                        "last_heartbeat"
                    ] = datetime.now()
                await self.send_personal_message(
                    websocket,
                    {
                        "type": "heartbeat_response",
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            elif message_type == "request_data":
                topic = message.get("topic")
                await self._handle_data_request(websocket, topic)

            else:
                logger.warning(f"Unknown message type: {message_type}")

        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self.send_personal_message(
                websocket,
                {
                    "type": "error",
                    "message": "Error processing message",
                    "timestamp": datetime.now().isoformat(),
                },
            )

    async def _handle_data_request(self, websocket: WebSocket, topic: str):
        """Handle data requests from clients."""
        try:
            db = next(get_db())

            if topic == "system_metrics":
                latest = (
                    db.query(SystemMetrics)
                    .order_by(SystemMetrics.timestamp.desc())
                    .limit(10)
                    .all()
                )
                data = [
                    {
                        "id": str(m.id),
                        "hostname": m.hostname,
                        "cpu_usage_percent": m.cpu_usage_percent,
                        "memory_usage_percent": m.memory_usage_percent,
                        "disk_usage_percent": m.disk_usage_percent,
                        "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                    }
                    for m in latest
                ]

                await self.send_personal_message(
                    websocket,
                    {
                        "type": "data_response",
                        "topic": topic,
                        "data": data,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            elif topic == "camera_metrics":
                latest = (
                    db.query(CameraMetrics)
                    .order_by(CameraMetrics.timestamp.desc())
                    .limit(20)
                    .all()
                )
                data = [
                    {
                        "id": str(m.id),
                        "camera_id": m.camera_id,
                        "connection_status": m.connection_status,
                        "fps_actual": m.fps_actual,
                        "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                    }
                    for m in latest
                ]

                await self.send_personal_message(
                    websocket,
                    {
                        "type": "data_response",
                        "topic": topic,
                        "data": data,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            elif topic == "detection_metrics":
                latest = (
                    db.query(DetectionMetrics)
                    .order_by(DetectionMetrics.timestamp.desc())
                    .limit(15)
                    .all()
                )
                data = [
                    {
                        "id": str(m.id),
                        "camera_id": m.camera_id,
                        "prediction_label": m.prediction_label,
                        "confidence_score": m.confidence_score,
                        "is_shoplifting": m.is_shoplifting,
                        "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                    }
                    for m in latest
                ]

                await self.send_personal_message(
                    websocket,
                    {
                        "type": "data_response",
                        "topic": topic,
                        "data": data,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            elif topic == "analytics_aggregates":
                latest = (
                    db.query(AnalyticsAggregates)
                    .order_by(AnalyticsAggregates.last_calculated.desc())
                    .limit(10)
                    .all()
                )
                data = [
                    {
                        "id": str(m.id),
                        "aggregation_type": m.aggregation_type,
                        "time_period": m.time_period,
                        "total_detections": m.total_detections,
                        "total_alerts": m.total_alerts,
                        "last_calculated": (
                            m.last_calculated.isoformat() if m.last_calculated else None
                        ),
                    }
                    for m in latest
                ]

                await self.send_personal_message(
                    websocket,
                    {
                        "type": "data_response",
                        "topic": topic,
                        "data": data,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

        except Exception as e:
            logger.error(f"Error handling data request for topic {topic}: {e}")
            await self.send_personal_message(
                websocket,
                {
                    "type": "error",
                    "message": f"Error retrieving data for topic: {topic}",
                    "timestamp": datetime.now().isoformat(),
                },
            )


# Global instance
analytics_websocket_manager = AnalyticsWebSocketManager()
