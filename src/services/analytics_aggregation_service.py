import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from src.database.models import (
    AnalyticsAggregates,
    Camera,
    CameraMetrics,
    DetectionMetrics,
    SystemMetrics,
    User,
)


class AnalyticsAggregationService:
    """Service for pre-computing analytics aggregates for fast dashboard queries."""

    def __init__(self):
        self.aggregation_intervals = {
            "hourly": timedelta(hours=1),
            "daily": timedelta(days=1),
            "weekly": timedelta(weeks=1),
            "monthly": timedelta(days=30),
        }

        # Aggregation tasks
        self._aggregation_tasks = []
        self._running = False

    async def start_aggregation(self):
        """Start the analytics aggregation service."""
        if self._running:
            logger.warning("Analytics aggregation service is already running")
            return

        self._running = True
        logger.info("Starting analytics aggregation service")

        # Start aggregation tasks
        self._aggregation_tasks = [
            asyncio.create_task(self._hourly_aggregation_loop()),
            asyncio.create_task(self._daily_aggregation_loop()),
            asyncio.create_task(self._weekly_aggregation_loop()),
            asyncio.create_task(self._monthly_aggregation_loop()),
        ]

        logger.info("Analytics aggregation service started successfully")

    async def stop_aggregation(self):
        """Stop the analytics aggregation service."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping analytics aggregation service")

        # Cancel all aggregation tasks
        for task in self._aggregation_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._aggregation_tasks, return_exceptions=True)
        self._aggregation_tasks = []

        logger.info("Analytics aggregation service stopped")

    async def _hourly_aggregation_loop(self):
        """Continuous loop for hourly aggregations."""
        while self._running:
            try:
                # Wait until the next hour
                now = datetime.utcnow()
                next_hour = (now + timedelta(hours=1)).replace(
                    minute=0, second=0, microsecond=0
                )
                wait_seconds = (next_hour - now).total_seconds()

                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)

                if self._running:
                    await self.aggregate_hourly_data()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in hourly aggregation loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

    async def _daily_aggregation_loop(self):
        """Continuous loop for daily aggregations."""
        while self._running:
            try:
                # Wait until the next day
                now = datetime.utcnow()
                next_day = (now + timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                wait_seconds = (next_day - now).total_seconds()

                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)

                if self._running:
                    await self.aggregate_daily_data()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in daily aggregation loop: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying

    async def _weekly_aggregation_loop(self):
        """Continuous loop for weekly aggregations."""
        while self._running:
            try:
                # Wait until the next Monday
                now = datetime.utcnow()
                days_ahead = 7 - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                next_monday = (now + timedelta(days=days_ahead)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                wait_seconds = (next_monday - now).total_seconds()

                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)

                if self._running:
                    await self.aggregate_weekly_data()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in weekly aggregation loop: {e}")
                await asyncio.sleep(86400)  # Wait 1 day before retrying

    async def _monthly_aggregation_loop(self):
        """Continuous loop for monthly aggregations."""
        while self._running:
            try:
                # Wait until the next month
                now = datetime.utcnow()
                if now.month == 12:
                    next_month = now.replace(
                        year=now.year + 1,
                        month=1,
                        day=1,
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0,
                    )
                else:
                    next_month = now.replace(
                        month=now.month + 1,
                        day=1,
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0,
                    )

                wait_seconds = (next_month - now).total_seconds()

                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)

                if self._running:
                    await self.aggregate_monthly_data()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monthly aggregation loop: {e}")
                await asyncio.sleep(86400)  # Wait 1 day before retrying

    async def aggregate_hourly_data(
        self, db: Session = None, target_time: Optional[datetime] = None
    ):
        """Aggregate data for a specific hour."""
        if not db:
            logger.warning("No database session provided for hourly aggregation")
            return

        try:
            if target_time is None:
                target_time = datetime.utcnow().replace(
                    minute=0, second=0, microsecond=0
                )

            start_time = target_time
            end_time = start_time + timedelta(hours=1)
            time_period = start_time.strftime("%Y-%m-%d %H:00")

            # Check if aggregation already exists
            existing = (
                db.query(AnalyticsAggregates)
                .filter(
                    and_(
                        AnalyticsAggregates.aggregation_type == "hourly",
                        AnalyticsAggregates.time_period == time_period,
                    )
                )
                .first()
            )

            if existing:
                logger.debug(f"Hourly aggregation for {time_period} already exists")
                return existing

            # Aggregate system metrics
            system_summary = await self._aggregate_system_metrics(
                db, start_time, end_time
            )

            # Aggregate detection metrics
            detection_summary = await self._aggregate_detection_metrics(
                db, start_time, end_time
            )

            # Aggregate camera metrics
            camera_summary = await self._aggregate_camera_metrics(
                db, start_time, end_time
            )

            # Create hourly aggregate
            hourly_aggregate = AnalyticsAggregates(
                aggregation_type="hourly",
                time_period=time_period,
                start_time=start_time,
                end_time=end_time,
                **system_summary,
                **detection_summary,
                **camera_summary,
                last_calculated=datetime.utcnow(),
            )

            db.add(hourly_aggregate)
            db.commit()
            db.refresh(hourly_aggregate)

            logger.info(f"Created hourly aggregation for {time_period}")
            return hourly_aggregate

        except Exception as e:
            logger.error(f"Error in hourly aggregation: {e}")
            if db:
                db.rollback()
            return None

    async def aggregate_daily_data(
        self, db: Session = None, target_date: Optional[datetime] = None
    ):
        """Aggregate data for a specific day."""
        if not db:
            logger.warning("No database session provided for daily aggregation")
            return

        try:
            if target_date is None:
                target_date = datetime.utcnow().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )

            start_time = target_date
            end_time = start_time + timedelta(days=1)
            time_period = start_time.strftime("%Y-%m-%d")

            # Check if aggregation already exists
            existing = (
                db.query(AnalyticsAggregates)
                .filter(
                    and_(
                        AnalyticsAggregates.aggregation_type == "daily",
                        AnalyticsAggregates.time_period == time_period,
                    )
                )
                .first()
            )

            if existing:
                logger.debug(f"Daily aggregation for {time_period} already exists")
                return existing

            # Aggregate system metrics
            system_summary = await self._aggregate_system_metrics(
                db, start_time, end_time
            )

            # Aggregate detection metrics
            detection_summary = await self._aggregate_detection_metrics(
                db, start_time, end_time
            )

            # Aggregate camera metrics
            camera_summary = await self._aggregate_camera_metrics(
                db, start_time, end_time
            )

            # Create daily aggregate
            daily_aggregate = AnalyticsAggregates(
                aggregation_type="daily",
                time_period=time_period,
                start_time=start_time,
                end_time=end_time,
                **system_summary,
                **detection_summary,
                **camera_summary,
                last_calculated=datetime.utcnow(),
            )

            db.add(daily_aggregate)
            db.commit()
            db.refresh(daily_aggregate)

            logger.info(f"Created daily aggregation for {time_period}")
            return daily_aggregate

        except Exception as e:
            logger.error(f"Error in daily aggregation: {e}")
            if db:
                db.rollback()
            return None

    async def aggregate_weekly_data(
        self, db: Session = None, target_week: Optional[datetime] = None
    ):
        """Aggregate data for a specific week."""
        if not db:
            logger.warning("No database session provided for weekly aggregation")
            return

        try:
            if target_week is None:
                target_week = datetime.utcnow()

            # Find the start of the week (Monday)
            days_since_monday = target_week.weekday()
            start_time = target_week.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - timedelta(days=days_since_monday)
            end_time = start_time + timedelta(weeks=1)
            time_period = f"{start_time.year}-W{start_time.isocalendar()[1]:02d}"

            # Check if aggregation already exists
            existing = (
                db.query(AnalyticsAggregates)
                .filter(
                    and_(
                        AnalyticsAggregates.aggregation_type == "weekly",
                        AnalyticsAggregates.time_period == time_period,
                    )
                )
                .first()
            )

            if existing:
                logger.debug(f"Weekly aggregation for {time_period} already exists")
                return existing

            # Aggregate system metrics
            system_summary = await self._aggregate_system_metrics(
                db, start_time, end_time
            )

            # Aggregate detection metrics
            detection_summary = await self._aggregate_detection_metrics(
                db, start_time, end_time
            )

            # Aggregate camera metrics
            camera_summary = await self._aggregate_camera_metrics(
                db, start_time, end_time
            )

            # Create weekly aggregate
            weekly_aggregate = AnalyticsAggregates(
                aggregation_type="weekly",
                time_period=time_period,
                start_time=start_time,
                end_time=end_time,
                **system_summary,
                **detection_summary,
                **camera_summary,
                last_calculated=datetime.utcnow(),
            )

            db.add(weekly_aggregate)
            db.commit()
            db.refresh(weekly_aggregate)

            # Broadcast update via WebSocket

            logger.info(f"Created weekly aggregation for {time_period}")
            return weekly_aggregate

        except Exception as e:
            logger.error(f"Error in weekly aggregation: {e}")
            if db:
                db.rollback()
            return None

    async def aggregate_monthly_data(
        self, db: Session = None, target_month: Optional[datetime] = None
    ):
        """Aggregate data for a specific month."""
        if not db:
            logger.warning("No database session provided for monthly aggregation")
            return

        try:
            if target_month is None:
                target_month = datetime.utcnow()

            start_time = target_month.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            if start_time.month == 12:
                end_time = start_time.replace(year=start_time.year + 1, month=1)
            else:
                end_time = start_time.replace(month=start_time.month + 1)

            time_period = start_time.strftime("%Y-%m")

            # Check if aggregation already exists
            existing = (
                db.query(AnalyticsAggregates)
                .filter(
                    and_(
                        AnalyticsAggregates.aggregation_type == "monthly",
                        AnalyticsAggregates.time_period == time_period,
                    )
                )
                .first()
            )

            if existing:
                logger.debug(f"Monthly aggregation for {time_period} already exists")
                return existing

            # Aggregate system metrics
            system_summary = await self._aggregate_system_metrics(
                db, start_time, end_time
            )

            # Aggregate detection metrics
            detection_summary = await self._aggregate_detection_metrics(
                db, start_time, end_time
            )

            # Aggregate camera metrics
            camera_summary = await self._aggregate_camera_metrics(
                db, start_time, end_time
            )

            # Create monthly aggregate
            monthly_aggregate = AnalyticsAggregates(
                aggregation_type="monthly",
                time_period=time_period,
                start_time=start_time,
                end_time=end_time,
                **system_summary,
                **detection_summary,
                **camera_summary,
                last_calculated=datetime.utcnow(),
            )

            db.add(monthly_aggregate)
            db.commit()
            db.refresh(monthly_aggregate)

            logger.info(f"Created monthly aggregation for {time_period}")
            return monthly_aggregate

        except Exception as e:
            logger.error(f"Error in monthly aggregation: {e}")
            if db:
                db.rollback()
            return None

    async def _aggregate_system_metrics(
        self, db: Session, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """Aggregate system metrics for the given time range."""
        try:
            metrics = (
                db.query(SystemMetrics)
                .filter(
                    and_(
                        SystemMetrics.timestamp >= start_time,
                        SystemMetrics.timestamp < end_time,
                    )
                )
                .all()
            )

            if not metrics:
                return {
                    "average_cpu_usage": 0.0,
                    "average_memory_usage": 0.0,
                    "average_disk_usage": 0.0,
                    "peak_cpu_usage": 0.0,
                    "peak_memory_usage": 0.0,
                    "system_uptime_percent": 0.0,
                }

            return {
                "average_cpu_usage": sum(m.cpu_usage_percent for m in metrics)
                / len(metrics),
                "average_memory_usage": sum(m.memory_usage_percent for m in metrics)
                / len(metrics),
                "average_disk_usage": sum(m.disk_usage_percent for m in metrics)
                / len(metrics),
                "peak_cpu_usage": max(m.cpu_usage_percent for m in metrics),
                "peak_memory_usage": max(m.memory_usage_percent for m in metrics),
                "system_uptime_percent": 100.0,  # Simplified for now
            }

        except Exception as e:
            logger.error(f"Error aggregating system metrics: {e}")
            return {}

    async def _aggregate_detection_metrics(
        self, db: Session, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """Aggregate detection metrics for the given time range."""
        try:
            metrics = (
                db.query(DetectionMetrics)
                .filter(
                    and_(
                        DetectionMetrics.timestamp >= start_time,
                        DetectionMetrics.timestamp < end_time,
                    )
                )
                .all()
            )

            if not metrics:
                return {
                    "total_detections": 0,
                    "shoplifting_detections": 0,
                    "false_positives": 0,
                    "average_confidence": 0.0,
                    "detection_rate_per_hour": 0.0,
                    "average_processing_time_ms": 0.0,
                }

            total_detections = len(metrics)
            shoplifting_detections = len([m for m in metrics if m.is_shoplifting])
            hours_in_range = (end_time - start_time).total_seconds() / 3600

            return {
                "total_detections": total_detections,
                "shoplifting_detections": shoplifting_detections,
                "false_positives": 0,  # Would need additional logic to determine false positives
                "average_confidence": sum(m.confidence_score for m in metrics)
                / total_detections,
                "detection_rate_per_hour": (
                    total_detections / hours_in_range if hours_in_range > 0 else 0
                ),
                "average_processing_time_ms": sum(m.processing_time_ms for m in metrics)
                / total_detections,
            }

        except Exception as e:
            logger.error(f"Error aggregating detection metrics: {e}")
            return {}

    async def _aggregate_camera_metrics(
        self, db: Session, start_time: datetime, end_time: datetime
    ) -> Dict[str, Any]:
        """Aggregate camera metrics for the given time range."""
        try:
            metrics = (
                db.query(CameraMetrics)
                .filter(
                    and_(
                        CameraMetrics.timestamp >= start_time,
                        CameraMetrics.timestamp < end_time,
                    )
                )
                .all()
            )

            if not metrics:
                return {
                    "active_cameras_count": 0,
                    "cameras_by_status": {},
                    "average_camera_uptime": 0.0,
                    "average_fps": 0.0,
                    "average_latency_ms": 0.0,
                }

            # Group by camera and get latest status for each
            camera_statuses = {}
            for metric in metrics:
                camera_statuses[metric.camera_id] = metric.connection_status

            active_cameras = len(
                [status for status in camera_statuses.values() if status == "connected"]
            )

            return {
                "active_cameras_count": active_cameras,
                "cameras_by_status": {
                    "connected": len(
                        [s for s in camera_statuses.values() if s == "connected"]
                    ),
                    "disconnected": len(
                        [s for s in camera_statuses.values() if s == "disconnected"]
                    ),
                    "error": len([s for s in camera_statuses.values() if s == "error"]),
                },
                "average_camera_uptime": 100.0,  # Simplified for now
                "average_fps": sum(m.fps_actual for m in metrics) / len(metrics),
                "average_latency_ms": sum(m.latency_ms for m in metrics) / len(metrics),
            }

        except Exception as e:
            logger.error(f"Error aggregating camera metrics: {e}")
            return {}

    async def get_aggregates(
        self,
        db: Session,
        aggregation_type: str,
        time_period: Optional[str] = None,
        camera_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AnalyticsAggregates]:
        """Get analytics aggregates with optional filtering."""
        try:
            query = db.query(AnalyticsAggregates).filter(
                AnalyticsAggregates.aggregation_type == aggregation_type
            )

            if time_period:
                query = query.filter(AnalyticsAggregates.time_period == time_period)

            if camera_id:
                query = query.filter(AnalyticsAggregates.camera_id == camera_id)

            if user_id:
                query = query.filter(AnalyticsAggregates.user_id == user_id)

            aggregates = (
                query.order_by(AnalyticsAggregates.start_time.desc()).limit(limit).all()
            )

            return aggregates

        except Exception as e:
            logger.error(f"Error getting aggregates: {e}")
            return []

    async def cleanup_old_aggregates(self, db: Session, days_to_keep: int = 90):
        """Clean up old analytics aggregates to prevent database bloat."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            deleted = (
                db.query(AnalyticsAggregates)
                .filter(AnalyticsAggregates.start_time < cutoff_date)
                .delete()
            )

            db.commit()

            logger.info(f"Cleaned up {deleted} old analytics aggregates")

        except Exception as e:
            logger.error(f"Error cleaning up old aggregates: {e}")
            if db:
                db.rollback()


# Global instance
analytics_aggregation_service = AnalyticsAggregationService()
