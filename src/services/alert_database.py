from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from datetime import datetime, timedelta
from loguru import logger

from src.database.models.base import SessionLocal
from src.database.models.alert import Alert


class AlertDatabaseService:
    """Database service for managing alerts in PostgreSQL."""

    def __init__(self):
        self.session_factory = SessionLocal

    def get_session(self) -> Session:
        """Get database session."""
        return self.session_factory()

    def save_alert(self, alert_record) -> bool:
        """Save an alert to the database."""
        try:
            with self.get_session() as db:
                # Check if alert already exists
                existing = db.query(Alert).filter(Alert.id == alert_record.id).first()

                if existing:
                    # Update existing alert
                    existing.update_from_alert_record(alert_record)
                    logger.debug(f"Updated existing alert {alert_record.id}")
                else:
                    # Create new alert
                    alert = Alert.from_alert_record(alert_record)
                    db.add(alert)
                    logger.debug(f"Created new alert {alert_record.id}")

                db.commit()
                return True

        except Exception as e:
            logger.error(f"Error saving alert {alert_record.id}: {e}")
            return False

    def get_alert_by_id(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific alert by ID."""
        try:
            with self.get_session() as db:
                alert = db.query(Alert).filter(Alert.id == alert_id).first()
                return alert.to_dict() if alert else None

        except Exception as e:
            logger.error(f"Error getting alert {alert_id}: {e}")
            return None

    def get_active_alerts(
        self, filters: Optional[Dict] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get active alerts with optional filtering."""
        try:
            with self.get_session() as db:
                query = db.query(Alert).filter(Alert.status == "active")

                # Apply filters
                if filters:
                    query = self._apply_filters(query, filters)

                # Order by timestamp (newest first) and apply limit
                alerts = query.order_by(desc(Alert.timestamp)).limit(limit).all()

                return [alert.to_dict() for alert in alerts]

        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []

    def get_alert_history(
        self, filters: Optional[Dict] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get alert history with optional filtering."""
        try:
            with self.get_session() as db:
                query = db.query(Alert)

                # Apply filters
                if filters:
                    query = self._apply_filters(query, filters)

                # Order by timestamp (newest first) and apply limit
                alerts = query.order_by(desc(Alert.timestamp)).limit(limit).all()

                return [alert.to_dict() for alert in alerts]

        except Exception as e:
            logger.error(f"Error getting alert history: {e}")
            return []

    def update_alert_status(
        self, alert_id: str, status: str, user_id: str, notes: Optional[str] = None
    ) -> bool:
        """Update alert status (acknowledge, resolve, etc.)."""
        try:
            with self.get_session() as db:
                alert = db.query(Alert).filter(Alert.id == alert_id).first()

                if not alert:
                    logger.warning(f"Alert {alert_id} not found for status update")
                    return False

                alert.status = status
                alert.updated_at = datetime.utcnow()

                if status == "acknowledged":
                    alert.acknowledged_by = user_id
                    alert.acknowledged_at = datetime.utcnow()
                elif status == "resolved":
                    alert.resolved_by = user_id
                    alert.resolved_at = datetime.utcnow()

                if notes:
                    current_notes = alert.notes or ""
                    alert.notes = f"{current_notes}\n{status.title()}: {notes}".strip()

                db.commit()
                logger.info(f"Updated alert {alert_id} status to {status}")
                return True

        except Exception as e:
            logger.error(f"Error updating alert {alert_id} status: {e}")
            return False

    def get_alert_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get alert statistics for the specified number of days."""
        try:
            with self.get_session() as db:
                cutoff = datetime.utcnow() - timedelta(days=days)
                today_start = datetime.utcnow().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )

                # Get recent alerts
                recent_alerts = db.query(Alert).filter(Alert.timestamp >= cutoff).all()

                # Basic counts
                total_active = db.query(Alert).filter(Alert.status == "active").count()
                total_today = (
                    db.query(Alert).filter(Alert.timestamp >= today_start).count()
                )
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

                avg_confidence = (
                    sum(confidences) / len(confidences) if confidences else 0
                )

                # Calculate average response time for resolved alerts
                resolved_alerts = [
                    a for a in recent_alerts if a.resolved_at and a.acknowledged_at
                ]
                response_times = []

                for alert in resolved_alerts:
                    response_time = (
                        alert.acknowledged_at - alert.created_at
                    ).total_seconds() / 60  # minutes
                    response_times.append(response_time)

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

        except Exception as e:
            logger.error(f"Error getting alert statistics: {e}")
            return {}

    def delete_old_alerts(self, days: int = 30) -> int:
        """Delete alerts older than specified days (for cleanup)."""
        try:
            with self.get_session() as db:
                cutoff = datetime.utcnow() - timedelta(days=days)

                deleted = (
                    db.query(Alert)
                    .filter(
                        and_(
                            Alert.timestamp < cutoff,
                            Alert.status.in_(["resolved", "dismissed"]),
                        )
                    )
                    .delete()
                )

                db.commit()
                logger.info(f"Deleted {deleted} old alerts")
                return deleted

        except Exception as e:
            logger.error(f"Error deleting old alerts: {e}")
            return 0

    def _apply_filters(self, query, filters: Dict):
        """Apply filters to alert query."""
        if "severity" in filters and filters["severity"]:
            if isinstance(filters["severity"], list):
                query = query.filter(Alert.severity.in_(filters["severity"]))
            else:
                query = query.filter(Alert.severity == filters["severity"])

        if "status" in filters and filters["status"]:
            if isinstance(filters["status"], list):
                query = query.filter(Alert.status.in_(filters["status"]))
            else:
                query = query.filter(Alert.status == filters["status"])

        if "type" in filters and filters["type"]:
            if isinstance(filters["type"], list):
                query = query.filter(Alert.type.in_(filters["type"]))
            else:
                query = query.filter(Alert.type == filters["type"])

        if "cameraId" in filters and filters["cameraId"]:
            if isinstance(filters["cameraId"], list):
                query = query.filter(Alert.camera_id.in_(filters["cameraId"]))
            else:
                query = query.filter(Alert.camera_id == filters["cameraId"])

        if "confidenceMin" in filters:
            query = query.filter(Alert.confidence >= filters["confidenceMin"])

        if "confidenceMax" in filters:
            query = query.filter(Alert.confidence <= filters["confidenceMax"])

        if "dateRange" in filters and filters["dateRange"]:
            date_range = filters["dateRange"]
            if "start" in date_range:
                start_date = datetime.fromisoformat(
                    date_range["start"].replace("Z", "")
                )
                query = query.filter(Alert.timestamp >= start_date)
            if "end" in date_range:
                end_date = datetime.fromisoformat(date_range["end"].replace("Z", ""))
                query = query.filter(Alert.timestamp <= end_date)

        return query


# Global service instance
alert_db_service = AlertDatabaseService()


def get_alert_db_service() -> AlertDatabaseService:
    """Get the global alert database service instance."""
    return alert_db_service
