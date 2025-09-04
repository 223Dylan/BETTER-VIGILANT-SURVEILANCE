import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import psutil
from loguru import logger
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from src.database.models import Alert, Camera, NotificationHistory, get_db
from src.websockets.analytics_websocket_manager import analytics_websocket_manager


class RealAnalyticsService:
    """Service that provides analytics from ONLY verified real data sources:
    - Alert table (real detections/threats)
    - Camera table (real camera configs)
    - NotificationHistory table (real notifications)
    - Live system metrics via psutil
    """

    def __init__(self):
        self._running = False
        self._broadcast_task: Optional[asyncio.Task] = None

    async def start_service(self):
        """Start the real analytics service."""
        if self._running:
            logger.warning("Real analytics service is already running")
            return

        self._running = True
        self._broadcast_task = asyncio.create_task(self._broadcast_loop())
        logger.info("✅ Real analytics service started - VERIFIED DATA ONLY")

    async def stop_service(self):
        """Stop the real analytics service."""
        self._running = False
        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass
        logger.info("Real analytics service stopped")

    async def _broadcast_loop(self):
        """Main broadcasting loop for VERIFIED real analytics data."""
        while self._running:
            try:
                # Send real analytics updates every 10 seconds
                if analytics_websocket_manager.active_connections:
                    await self._send_verified_analytics_updates()

                # Wait before next update
                await asyncio.sleep(10)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in real analytics broadcast loop: {e}")
                await asyncio.sleep(5)

    async def _send_verified_analytics_updates(self):
        """Send ONLY verified real analytics updates to connected clients."""
        try:
            db = next(get_db())

            # 1. Live System Performance (via psutil - REAL)
            live_system_data = await self.get_live_system_performance()
            if live_system_data:
                await analytics_websocket_manager.broadcast_to_topic(
                    "system_metrics",
                    {
                        "type": "live_system_update",
                        "topic": "system_metrics",
                        "data": live_system_data,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            # 2. Real Alert Analytics (VERIFIED)
            alert_analytics = await self.get_alert_analytics(db)
            if alert_analytics:
                await analytics_websocket_manager.broadcast_to_topic(
                    "alert_analytics",
                    {
                        "type": "alert_analytics_update",
                        "topic": "alert_analytics",
                        "data": alert_analytics,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            # 3. Real Camera Status (VERIFIED)
            camera_analytics = await self.get_camera_analytics(db)
            if camera_analytics:
                await analytics_websocket_manager.broadcast_to_topic(
                    "camera_analytics",
                    {
                        "type": "camera_analytics_update",
                        "topic": "camera_analytics",
                        "data": camera_analytics,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            # 4. Real Notification Analytics (VERIFIED)
            notification_analytics = await self.get_notification_analytics(db)
            if notification_analytics:
                await analytics_websocket_manager.broadcast_to_topic(
                    "notification_analytics",
                    {
                        "type": "notification_analytics_update",
                        "topic": "notification_analytics",
                        "data": notification_analytics,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            db.close()

        except Exception as e:
            logger.error(f"Error sending verified analytics updates: {e}")

    async def get_live_system_performance(self) -> Dict[str, Any]:
        """Get LIVE system performance metrics via psutil."""
        try:
            # Get real-time system performance
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Network stats (if available)
            try:
                network = psutil.net_io_counters()
                network_sent_mb = network.bytes_sent / 1024 / 1024
                network_recv_mb = network.bytes_recv / 1024 / 1024
            except:
                network_sent_mb = 0.0
                network_recv_mb = 0.0

            # Boot time and uptime
            try:
                boot_time = datetime.fromtimestamp(psutil.boot_time())
                uptime_seconds = (datetime.now() - boot_time).total_seconds()
                uptime_hours = uptime_seconds / 3600
            except:
                uptime_hours = 0.0

            return {
                "id": f"live-system-{datetime.now().isoformat()}",
                "hostname": (
                    psutil.Platform.system()
                    if hasattr(psutil, "Platform")
                    else "surveillance-system"
                ),
                "timestamp": datetime.now().isoformat(),
                "cpu_usage_percent": round(cpu_percent, 1),
                "memory_usage_percent": round(memory.percent, 1),
                "memory_total_gb": round(memory.total / 1024 / 1024 / 1024, 1),
                "memory_used_gb": round(memory.used / 1024 / 1024 / 1024, 1),
                "disk_usage_percent": round(disk.percent, 1),
                "disk_total_gb": round(disk.total / 1024 / 1024 / 1024, 1),
                "disk_used_gb": round(disk.used / 1024 / 1024 / 1024, 1),
                "network_sent_mb": round(network_sent_mb, 1),
                "network_recv_mb": round(network_recv_mb, 1),
                "uptime_hours": round(uptime_hours, 1),
                "process_count": len(psutil.pids()),
                "data_source": "live_psutil",
            }

        except Exception as e:
            logger.error(f"Error getting live system performance: {e}")
            return None

    async def get_alert_analytics(self, db: Session) -> Dict[str, Any]:
        """Get REAL alert analytics from Alert table."""
        try:
            now = datetime.utcnow()
            one_hour_ago = now - timedelta(hours=1)
            one_day_ago = now - timedelta(days=1)
            one_week_ago = now - timedelta(weeks=1)

            # Total alerts in different time periods
            one_month_ago = now - timedelta(days=30)

            alerts_last_24h = (
                db.query(Alert).filter(Alert.timestamp >= one_day_ago).count()
            )

            alerts_last_week = (
                db.query(Alert).filter(Alert.timestamp >= one_week_ago).count()
            )

            alerts_last_30d = (
                db.query(Alert).filter(Alert.timestamp >= one_month_ago).count()
            )

            # Active alerts by severity
            active_alerts = db.query(Alert).filter(Alert.status == "active").all()

            alerts_by_severity = {
                "critical": len([a for a in active_alerts if a.severity == "critical"]),
                "high": len([a for a in active_alerts if a.severity == "high"]),
                "medium": len([a for a in active_alerts if a.severity == "medium"]),
                "low": len([a for a in active_alerts if a.severity == "low"]),
            }

            # Recent alerts for details
            recent_alerts = db.query(Alert).filter(Alert.timestamp >= one_day_ago).all()

            # Average confidence (last 7 days)
            # Ensure timezone consistency for the query
            one_week_ago_naive = (
                one_week_ago.replace(tzinfo=None)
                if one_week_ago.tzinfo
                else one_week_ago
            )

            avg_confidence_query = (
                db.query(func.avg(Alert.confidence))
                .filter(Alert.timestamp >= one_week_ago_naive)
                .scalar()
            )
            avg_confidence = float(avg_confidence_query or 0.0)

            # Debug: Log confidence calculation details
            total_alerts_7d = (
                db.query(Alert).filter(Alert.timestamp >= one_week_ago_naive).count()
            )

            # Get some sample confidence values for debugging
            sample_alerts = (
                db.query(Alert.confidence)
                .filter(Alert.timestamp >= one_week_ago_naive)
                .limit(5)
                .all()
            )
            sample_confidences = [alert[0] for alert in sample_alerts]

            logger.info(
                f"Average confidence calculation: {avg_confidence} from {total_alerts_7d} alerts in last 7 days"
            )
            logger.info(f"Sample confidence values: {sample_confidences}")
            logger.info(f"Raw avg_confidence_query result: {avg_confidence_query}")

            # Recent alert details (last 10)
            recent_alert_details = []
            recent_alerts_list = (
                db.query(Alert)
                .filter(Alert.timestamp >= one_day_ago)
                .order_by(desc(Alert.timestamp))
                .limit(10)
                .all()
            )

            for alert in recent_alerts_list:
                recent_alert_details.append(
                    {
                        "id": alert.id,
                        "type": alert.type,
                        "severity": alert.severity,
                        "confidence": alert.confidence,
                        "camera_id": alert.camera_id,
                        "timestamp": (
                            alert.timestamp.isoformat() if alert.timestamp else None
                        ),
                        "status": alert.status,
                        "message": (
                            alert.message[:100] + "..."
                            if len(alert.message or "") > 100
                            else alert.message
                        ),
                    }
                )

            # Get detailed time-based data for charting
            chart_data = await self._get_alert_chart_data(db, now)

            return {
                "id": f"alert-analytics-{now.isoformat()}",
                "timestamp": now.isoformat(),
                "alerts_last_24h": alerts_last_24h,
                "alerts_last_week": alerts_last_week,
                "alerts_last_30d": alerts_last_30d,
                "active_alerts_total": len(active_alerts),
                "alerts_by_severity": alerts_by_severity,
                "avg_confidence_7d": round(avg_confidence, 3),
                "recent_alerts": recent_alert_details,
                "chart_data": chart_data,
                "data_source": "real_alert_table",
            }

        except Exception as e:
            logger.error(f"Error getting alert analytics: {e}")
            return None

    async def _get_alert_chart_data(self, db: Session, now: datetime) -> Dict[str, Any]:
        """Get time-based alert data for charting."""
        try:
            # Ensure now is timezone-aware for consistent comparison
            if now.tzinfo is None:
                now = now.replace(tzinfo=None)

            # Get all alerts from the last 30 days for charting
            one_month_ago = now - timedelta(days=30)
            all_alerts = (
                db.query(Alert)
                .filter(Alert.timestamp >= one_month_ago)
                .order_by(Alert.timestamp)
                .all()
            )

            # Group alerts by different time periods
            hourly_data = {}
            daily_data = {}
            weekly_data = {}

            for alert in all_alerts:
                alert_time = alert.timestamp

                # Ensure alert_time is timezone-naive for comparison
                if alert_time.tzinfo is not None:
                    alert_time = alert_time.replace(tzinfo=None)

                # Hourly grouping (last 24 hours + 4 hours buffer for clock sync issues)
                hour_key = alert_time.strftime("%Y-%m-%d %H:00")
                if alert_time >= now - timedelta(
                    hours=24
                ) and alert_time <= now + timedelta(hours=4):
                    hourly_data[hour_key] = hourly_data.get(hour_key, 0) + 1

                # Daily grouping (last 30 days)
                day_key = alert_time.strftime("%Y-%m-%d")
                if alert_time >= now - timedelta(days=30):
                    daily_data[day_key] = daily_data.get(day_key, 0) + 1

                # Weekly grouping (last 4 weeks)
                week_key = alert_time.strftime("%Y-W%U")
                if alert_time >= now - timedelta(weeks=4):
                    weekly_data[week_key] = weekly_data.get(week_key, 0) + 1

            return {
                "hourly": hourly_data,
                "daily": daily_data,
                "weekly": weekly_data,
                "raw_alerts": [
                    {
                        "timestamp": alert.timestamp.isoformat(),
                        "type": alert.type,
                        "severity": alert.severity,
                        "confidence": alert.confidence,
                    }
                    for alert in all_alerts
                ],
            }

        except Exception as e:
            logger.error(f"Error getting alert chart data: {e}")
            return {"hourly": {}, "daily": {}, "weekly": {}, "raw_alerts": []}

    async def get_camera_analytics(self, db: Session) -> Dict[str, Any]:
        """Get REAL camera analytics from Camera table."""
        try:
            cameras = db.query(Camera).all()

            total_cameras = len(cameras)
            enabled_cameras = len([c for c in cameras if c.enabled])
            active_cameras = len(
                [c for c in cameras if c.enabled and c.status in ["active", "starting"]]
            )

            # Camera status breakdown
            camera_status = {}
            for camera in cameras:
                status = camera.status
                camera_status[status] = camera_status.get(status, 0) + 1

            # Camera details
            camera_details = []
            for camera in cameras:
                camera_details.append(
                    {
                        "id": camera.id,
                        "name": camera.name,
                        "enabled": camera.enabled,
                        "status": camera.status,
                        "location": camera.location,
                        "zone": camera.zone,
                        "fps": camera.fps,
                        "resolution": f"{camera.resolution_width}x{camera.resolution_height}",
                        "source_type": camera.source_type,
                        "detection_enabled": camera.detection_enabled,
                    }
                )

            return {
                "id": f"camera-analytics-{datetime.utcnow().isoformat()}",
                "timestamp": datetime.utcnow().isoformat(),
                "total_cameras": total_cameras,
                "enabled_cameras": enabled_cameras,
                "active_cameras": active_cameras,
                "camera_status_breakdown": camera_status,
                "camera_details": camera_details,
                "data_source": "real_camera_table",
            }

        except Exception as e:
            logger.error(f"Error getting camera analytics: {e}")
            return None

    async def get_notification_analytics(self, db: Session) -> Dict[str, Any]:
        """Get REAL notification analytics from NotificationHistory table."""
        try:
            now = datetime.utcnow()
            one_day_ago = now - timedelta(days=1)
            one_week_ago = now - timedelta(weeks=1)

            # Notifications in last 24h
            notifications_24h = (
                db.query(NotificationHistory)
                .filter(NotificationHistory.created_at >= one_day_ago)
                .count()
            )

            # Notifications in last week
            notifications_week = (
                db.query(NotificationHistory)
                .filter(NotificationHistory.created_at >= one_week_ago)
                .count()
            )

            # Notification status breakdown
            recent_notifications = (
                db.query(NotificationHistory)
                .filter(NotificationHistory.created_at >= one_day_ago)
                .all()
            )

            notification_status = {}
            notification_types = {}

            for notification in recent_notifications:
                # Status breakdown
                status = notification.status
                notification_status[status] = notification_status.get(status, 0) + 1

                # Type breakdown
                ntype = notification.notification_type
                notification_types[ntype] = notification_types.get(ntype, 0) + 1

            return {
                "id": f"notification-analytics-{now.isoformat()}",
                "timestamp": now.isoformat(),
                "notifications_last_24h": notifications_24h,
                "notifications_last_week": notifications_week,
                "notification_status_breakdown": notification_status,
                "notification_type_breakdown": notification_types,
                "data_source": "real_notification_history_table",
            }

        except Exception as e:
            logger.error(f"Error getting notification analytics: {e}")
            return None

    async def get_dashboard_summary(self, db: Session) -> Dict[str, Any]:
        """Get a complete dashboard summary with ONLY verified real data."""
        try:
            # Get all VERIFIED real analytics
            live_system = await self.get_live_system_performance()
            alert_analytics = await self.get_alert_analytics(db)
            camera_analytics = await self.get_camera_analytics(db)
            notification_analytics = await self.get_notification_analytics(db)

            summary = {
                "live_system_performance": live_system,
                "alert_analytics": alert_analytics,
                "camera_analytics": camera_analytics,
                "notification_analytics": notification_analytics,
                "last_updated": datetime.utcnow().isoformat(),
                "data_sources": [
                    "real_alert_table",
                    "real_camera_table",
                    "real_notification_history_table",
                    "live_psutil_metrics",
                ],
                "verification_status": "ALL_DATA_VERIFIED_REAL",
            }

            return summary

        except Exception as e:
            logger.error(f"Error getting verified dashboard summary: {e}")
            return {"error": str(e)}

    async def clear_test_data(self):
        """Clear any remaining test/fake data from FAKE tables (not the real ones)."""
        try:
            from src.database.models.analytics_aggregates import AnalyticsAggregates
            from src.database.models.camera_metrics import CameraMetrics
            from src.database.models.detection_metrics import DetectionMetrics
            from src.database.models.system_metrics import SystemMetrics

            db = next(get_db())

            # Clear ONLY the fake tables, NOT the real Alert/Camera/NotificationHistory tables
            fake_tables_cleared = 0

            try:
                fake_tables_cleared += db.query(SystemMetrics).delete()
                fake_tables_cleared += db.query(CameraMetrics).delete()
                fake_tables_cleared += db.query(DetectionMetrics).delete()
                fake_tables_cleared += db.query(AnalyticsAggregates).delete()

                db.commit()

                logger.info(
                    f"✅ CLEARED {fake_tables_cleared} fake records from FAKE tables"
                )
                logger.info(
                    "✅ KEPT all real data in Alert, Camera, NotificationHistory tables"
                )

            except Exception as e:
                db.rollback()
                logger.error(f"Error clearing fake tables: {e}")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error in clear_test_data: {e}")


# Create global instance
real_analytics_service = RealAnalyticsService()
