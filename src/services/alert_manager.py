import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio
from dataclasses import dataclass, asdict
from loguru import logger

from src.services.alert_database import get_alert_db_service


class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class AlertType(Enum):
    SHOPLIFTING = "shoplifting"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    OBJECT_DETECTION = "object_detection"
    MOTION = "motion"
    SYSTEM_ALERT = "system_alert"


@dataclass
class AlertRecord:
    """Internal alert record structure."""

    id: str
    camera_id: str
    timestamp: str
    type: str
    severity: str
    status: str
    confidence: float
    message: str
    source: str
    detection_data: Dict[str, Any]
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()


class AlertManager:
    """Core alert management system that processes Celery predictions."""

    def __init__(self):
        self.active_alerts: Dict[str, AlertRecord] = {}
        self.alert_history: List[AlertRecord] = []
        self.alert_thresholds = {
            "critical": 0.9,
            "high": 0.7,
            "medium": 0.5,
            "low": 0.0,
        }
        self.max_history_size = 10000  # Keep last 10k alerts in memory

        # Database service for persistent storage
        self.db_service = get_alert_db_service()

        logger.info("[INIT] Alert Manager initialized with database persistence")

    def process_prediction(self, prediction_result: Dict[str, Any]) -> Optional[str]:
        """
        Process a Celery prediction result and create an alert if needed.

        Args:
            prediction_result: Dict from Celery worker with prediction data

        Returns:
            Alert ID if alert was created, None otherwise
        """
        try:
            # Extract prediction data
            camera_id = prediction_result.get("camera_id", "unknown")
            confidence = prediction_result.get("confidence", 0.0)
            is_shoplifting = prediction_result.get("is_shoplifting", False)
            timestamp = prediction_result.get(
                "timestamp", datetime.utcnow().timestamp()
            )

            # Convert timestamp to ISO format if needed
            if isinstance(timestamp, (int, float)):
                timestamp_iso = datetime.fromtimestamp(timestamp).isoformat()
            else:
                timestamp_iso = str(timestamp)

            # Determine alert properties
            alert_type = self._determine_alert_type(confidence, is_shoplifting)
            severity = self._determine_severity(confidence, is_shoplifting)
            message = self._generate_alert_message(alert_type, confidence, camera_id)

            # Only create alerts for significant events
            if not self._should_create_alert(alert_type, severity, confidence):
                logger.debug(
                    f"Skipping alert creation for {camera_id}: {alert_type.value} (confidence: {confidence:.3f})"
                )
                return None

            # Create alert record
            alert_id = str(uuid.uuid4())
            alert = AlertRecord(
                id=alert_id,
                camera_id=camera_id,
                timestamp=timestamp_iso,
                type=alert_type.value,
                severity=severity.value,
                status=AlertStatus.ACTIVE.value,
                confidence=confidence,
                message=message,
                source="detection",
                detection_data={
                    "isShoplifting": is_shoplifting,
                    "modelLabel": prediction_result.get("label", 0),
                    "sequenceStats": prediction_result.get("sequence_stats", {}),
                    "processingTime": prediction_result.get("task_timestamp", 0),
                    "modelVersion": "lrcn_160S_90_90Q",
                },
            )

            # Store alert in memory
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)

            # Manage history size
            if len(self.alert_history) > self.max_history_size:
                self.alert_history = self.alert_history[-self.max_history_size :]

            # Save to database
            try:
                self.db_service.save_alert(alert)
                logger.debug(f"[DATABASE] Saved alert {alert_id} to database")
            except Exception as e:
                logger.error(
                    f"[ERROR] Failed to save alert {alert_id} to database: {e}"
                )

            logger.info(
                f"[ALERT] Created {severity.value.upper()} alert: {alert_type.value} for {camera_id} (confidence: {confidence:.3f})"
            )

            # Trigger real-time notifications (safely handle async)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._broadcast_alert(alert))
                else:
                    logger.debug("No running event loop for WebSocket broadcast")
            except RuntimeError:
                logger.debug("No event loop available for WebSocket broadcast")

            return alert_id

        except Exception as e:
            logger.error(f"[ERROR] Error processing prediction for alert: {e}")
            return None

    def _determine_alert_type(
        self, confidence: float, is_shoplifting: bool
    ) -> AlertType:
        """Determine alert type based on prediction results."""
        if is_shoplifting and confidence >= 0.7:
            return AlertType.SHOPLIFTING
        elif is_shoplifting and confidence >= 0.5:
            return AlertType.SUSPICIOUS_ACTIVITY
        elif confidence >= 0.3:
            return AlertType.OBJECT_DETECTION
        else:
            return AlertType.MOTION

    def _determine_severity(
        self, confidence: float, is_shoplifting: bool
    ) -> AlertSeverity:
        """Determine alert severity based on confidence and detection type."""
        if is_shoplifting and confidence >= self.alert_thresholds["critical"]:
            return AlertSeverity.CRITICAL
        elif is_shoplifting and confidence >= self.alert_thresholds["high"]:
            return AlertSeverity.HIGH
        elif is_shoplifting and confidence >= self.alert_thresholds["medium"]:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW

    def _should_create_alert(
        self, alert_type: AlertType, severity: AlertSeverity, confidence: float
    ) -> bool:
        """Determine if an alert should be created based on type and severity."""
        # Always create alerts for shoplifting detections
        if alert_type == AlertType.SHOPLIFTING:
            return True

        # Create alerts for suspicious activity above medium confidence
        if alert_type == AlertType.SUSPICIOUS_ACTIVITY and confidence >= 0.5:
            return True

        # Create alerts for high-confidence object detection
        if alert_type == AlertType.OBJECT_DETECTION and confidence >= 0.6:
            return True

        # Skip low-confidence motion alerts (just log them)
        return False

    def _generate_alert_message(
        self, alert_type: AlertType, confidence: float, camera_id: str
    ) -> str:
        """Generate human-readable alert message."""
        confidence_pct = int(confidence * 100)

        if alert_type == AlertType.SHOPLIFTING:
            if confidence >= 0.9:
                return f"[HIGH CONFIDENCE] SHOPLIFTING DETECTED on {camera_id} ({confidence_pct}%)"
            elif confidence >= 0.7:
                return (
                    f"[WARNING] SHOPLIFTING DETECTED on {camera_id} ({confidence_pct}%)"
                )
            else:
                return f"[WARNING] Potential shoplifting detected on {camera_id} ({confidence_pct}%)"
        elif alert_type == AlertType.SUSPICIOUS_ACTIVITY:
            return f"[SUSPICIOUS] Suspicious activity detected on {camera_id} ({confidence_pct}%)"
        elif alert_type == AlertType.OBJECT_DETECTION:
            return f"[OBJECT] Object detection alert on {camera_id} ({confidence_pct}%)"
        else:
            return f"[MOTION] Motion detected on {camera_id} ({confidence_pct}%)"

    async def _broadcast_alert(self, alert: AlertRecord):
        """Broadcast alert to connected WebSocket clients."""
        try:
            from src.websocket_manager import websocket_manager

            alert_data = {
                "id": alert.id,
                "type": "alert_created",
                "alert": asdict(alert),
            }

            # Broadcast to all connected clients (you might want to filter by camera)
            await websocket_manager.broadcast_alert(alert.camera_id, alert_data)
            logger.info(
                f"[BROADCAST] Broadcasted alert {alert.id} for camera {alert.camera_id}"
            )

        except Exception as e:
            logger.error(f"[ERROR] Error broadcasting alert: {e}")

    def acknowledge_alert(
        self, alert_id: str, user_id: str, notes: Optional[str] = None
    ) -> bool:
        """Acknowledge an active alert."""
        if alert_id not in self.active_alerts:
            logger.warning(f"[WARNING] Cannot acknowledge: Alert {alert_id} not found")
            return False

        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.ACKNOWLEDGED.value
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.utcnow().isoformat()
        alert.updated_at = datetime.utcnow().isoformat()

        if notes:
            alert.notes = notes

        # Save to database
        try:
            self.db_service.save_alert(alert)
            logger.debug(f"[DATABASE] Updated alert {alert_id} in database")
        except Exception as e:
            logger.error(f"[ERROR] Failed to update alert {alert_id} in database: {e}")

        logger.info(f"[SUCCESS] Alert {alert_id} acknowledged by {user_id}")

        # Broadcast status update (safely handle async)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._broadcast_alert_update(alert))
            else:
                logger.debug("No running event loop for WebSocket broadcast")
        except RuntimeError:
            logger.debug("No event loop available for WebSocket broadcast")

        return True

    def resolve_alert(
        self, alert_id: str, user_id: str, notes: Optional[str] = None
    ) -> bool:
        """Resolve an alert and move it from active to history."""
        if alert_id not in self.active_alerts:
            logger.warning(f"[WARNING] Cannot resolve: Alert {alert_id} not found")
            return False

        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.RESOLVED.value
        alert.resolved_by = user_id
        alert.resolved_at = datetime.utcnow().isoformat()
        alert.updated_at = datetime.utcnow().isoformat()

        if notes:
            current_notes = alert.notes or ""
            alert.notes = f"{current_notes}\nResolved: {notes}".strip()

        # Save to database before removing from memory
        try:
            self.db_service.save_alert(alert)
            logger.debug(f"[DATABASE] Updated resolved alert {alert_id} in database")
        except Exception as e:
            logger.error(
                f"[ERROR] Failed to update resolved alert {alert_id} in database: {e}"
            )

        # Remove from active alerts
        del self.active_alerts[alert_id]

        logger.info(f"[SUCCESS] Alert {alert_id} resolved by {user_id}")

        # Broadcast status update (safely handle async)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._broadcast_alert_update(alert))
            else:
                logger.debug("No running event loop for WebSocket broadcast")
        except RuntimeError:
            logger.debug("No event loop available for WebSocket broadcast")

        return True

    async def _broadcast_alert_update(self, alert: AlertRecord):
        """Broadcast alert status update."""
        try:
            from src.websocket_manager import websocket_manager

            alert_data = {
                "id": alert.id,
                "type": "alert_updated",
                "alert": asdict(alert),
            }

            await websocket_manager.broadcast_alert(alert.camera_id, alert_data)

        except Exception as e:
            logger.error(f"[ERROR] Error broadcasting alert update: {e}")

    def get_active_alerts(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get all active alerts with optional filtering."""
        try:
            # Try to get from database first
            alerts = self.db_service.get_active_alerts(filters)
            if alerts:
                return alerts
        except Exception as e:
            logger.error(
                f"[ERROR] Error getting alerts from database, falling back to memory: {e}"
            )

        # Fallback to in-memory data
        alerts = list(self.active_alerts.values())

        if filters:
            alerts = self._apply_filters(alerts, filters)

        # Convert to dict and sort by timestamp (newest first)
        result = [asdict(alert) for alert in alerts]
        return sorted(result, key=lambda x: x["timestamp"], reverse=True)

    def get_alert_history(
        self, limit: int = 100, filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Get alert history with optional filtering."""
        try:
            # Try to get from database first
            alerts = self.db_service.get_alert_history(filters, limit)
            if alerts:
                return alerts
        except Exception as e:
            logger.error(
                f"[ERROR] Error getting alert history from database, falling back to memory: {e}"
            )

        # Fallback to in-memory data
        alerts = self.alert_history[-limit:] if limit else self.alert_history

        if filters:
            alerts = self._apply_filters(alerts, filters)

        # Convert to dict and sort by timestamp (newest first)
        result = [asdict(alert) for alert in alerts]
        return sorted(result, key=lambda x: x["timestamp"], reverse=True)

    def get_alert_stats(self, days: int = 7) -> Dict:
        """Get alert statistics for the specified number of days."""
        try:
            # Try to get from database first
            stats = self.db_service.get_alert_stats(days)
            if stats:
                return stats
        except Exception as e:
            logger.error(
                f"[ERROR] Error getting alert stats from database, falling back to memory: {e}"
            )

        # Fallback to in-memory calculation
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Filter recent alerts
        recent_alerts = [
            alert
            for alert in self.alert_history
            if datetime.fromisoformat(alert.timestamp.replace("Z", "")) >= cutoff
        ]

        # Calculate statistics
        total_active = len(self.active_alerts)
        total_today = len([a for a in recent_alerts if self._is_today(a.timestamp)])
        total_week = len(recent_alerts)

        # Group by severity
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_camera = {}
        by_type = {}
        confidences = []

        for alert in recent_alerts:
            by_severity[alert.severity] = by_severity.get(alert.severity, 0) + 1
            by_camera[alert.camera_id] = by_camera.get(alert.camera_id, 0) + 1
            by_type[alert.type] = by_type.get(alert.type, 0) + 1
            confidences.append(alert.confidence)

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        # Calculate average response time for resolved alerts
        resolved_alerts = [a for a in recent_alerts if a.resolved_at]
        response_times = []

        for alert in resolved_alerts:
            if alert.acknowledged_at:
                created = datetime.fromisoformat(alert.created_at.replace("Z", ""))
                acked = datetime.fromisoformat(alert.acknowledged_at.replace("Z", ""))
                response_times.append((acked - created).total_seconds() / 60)  # minutes

        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )

        return {
            "totalActive": total_active,
            "totalToday": total_today,
            "totalWeek": total_week,
            "bySeverity": by_severity,
            "byCamera": by_camera,
            "byType": by_type,
            "avgConfidence": round(avg_confidence, 3),
            "avgResponseTime": round(avg_response_time, 1),
        }

    def _apply_filters(
        self, alerts: List[AlertRecord], filters: Dict
    ) -> List[AlertRecord]:
        """Apply filters to alert list."""
        filtered = alerts

        if "severity" in filters and filters["severity"]:
            filtered = [a for a in filtered if a.severity in filters["severity"]]

        if "status" in filters and filters["status"]:
            filtered = [a for a in filtered if a.status in filters["status"]]

        if "type" in filters and filters["type"]:
            filtered = [a for a in filtered if a.type in filters["type"]]

        if "cameraId" in filters and filters["cameraId"]:
            filtered = [a for a in filtered if a.camera_id in filters["cameraId"]]

        if "confidenceMin" in filters:
            filtered = [a for a in filtered if a.confidence >= filters["confidenceMin"]]

        if "confidenceMax" in filters:
            filtered = [a for a in filtered if a.confidence <= filters["confidenceMax"]]

        return filtered

    def _is_today(self, timestamp_str: str) -> bool:
        """Check if timestamp is from today."""
        try:
            alert_date = datetime.fromisoformat(timestamp_str.replace("Z", "")).date()
            return alert_date == datetime.utcnow().date()
        except:
            return False


# Global alert manager instance
alert_manager = AlertManager()


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance."""
    return alert_manager
