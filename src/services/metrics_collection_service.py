import asyncio
import json
import os
import platform
import socket
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import psutil
from loguru import logger
from sqlalchemy.orm import Session

from src.database.models import (
    AnalyticsAggregates,
    Camera,
    CameraMetrics,
    DetectionMetrics,
    SystemMetrics,
)
from src.utils.system_monitor import SystemMonitor
from src.websockets.analytics_websocket_manager import analytics_websocket_manager


class MetricsCollectionService:
    """Service for collecting and storing real-time metrics for analytics."""

    def __init__(self):
        self.system_monitor = SystemMonitor()
        self.hostname = socket.gethostname()
        self.system_type = "surveillance_system"

        # Collection intervals (in seconds)
        self.system_metrics_interval = int(os.getenv("SYSTEM_METRICS_INTERVAL", "60"))
        self.camera_metrics_interval = int(os.getenv("CAMERA_METRICS_INTERVAL", "30"))
        self.detection_metrics_interval = int(
            os.getenv("DETECTION_METRICS_INTERVAL", "5")
        )

        # Collection tasks
        self._collection_tasks = []
        self._running = False

    async def start_collection(self):
        """Start the metrics collection service."""
        if self._running:
            logger.warning("Metrics collection service is already running")
            return

        self._running = True
        logger.info("Starting metrics collection service")

        # Start collection tasks
        self._collection_tasks = [
            asyncio.create_task(self._collect_system_metrics_loop()),
            asyncio.create_task(self._collect_camera_metrics_loop()),
        ]

        logger.info("Metrics collection service started successfully")

    async def stop_collection(self):
        """Stop the metrics collection service."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping metrics collection service")

        # Cancel all collection tasks
        for task in self._collection_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._collection_tasks, return_exceptions=True)
        self._collection_tasks = []

        logger.info("Metrics collection service stopped")

    async def _collect_system_metrics_loop(self):
        """Continuous loop for collecting system metrics."""
        while self._running:
            try:
                await self.collect_system_metrics()
                await asyncio.sleep(self.system_metrics_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in system metrics collection loop: {e}")
                await asyncio.sleep(10)  # Wait before retrying

    async def _collect_camera_metrics_loop(self):
        """Continuous loop for collecting camera metrics."""
        while self._running:
            try:
                await self.collect_camera_metrics()
                await asyncio.sleep(self.camera_metrics_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in camera metrics collection loop: {e}")
                await asyncio.sleep(10)  # Wait before retrying

    async def collect_system_metrics(
        self, db: Session = None
    ) -> Optional[SystemMetrics]:
        """Collect current system metrics."""
        try:
            # Update system monitor
            self.system_monitor.update()
            current_metrics = self.system_monitor.get_metrics()

            # Get additional system information
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Get system load (Unix-like systems)
            system_load = None
            try:
                if platform.system() != "Windows":
                    system_load = os.getloadavg()
            except:
                pass

            # Get process information
            processes = psutil.process_iter(["pid", "status"])
            total_processes = len(list(processes))
            zombie_processes = 0  # Would need more complex logic to detect zombies

            # Create system metrics record
            system_metrics = SystemMetrics(
                hostname=self.hostname,
                system_type=self.system_type,
                cpu_usage_percent=current_metrics.get("cpu_usage", 0),
                cpu_count=cpu_count,
                cpu_frequency_mhz=(
                    psutil.cpu_freq().current if psutil.cpu_freq() else None
                ),
                memory_usage_percent=memory.percent,
                memory_total_gb=memory.total / (1024**3),
                memory_available_gb=memory.available / (1024**3),
                memory_used_gb=memory.used / (1024**3),
                disk_usage_percent=disk.percent,
                disk_total_gb=disk.total / (1024**3),
                disk_used_gb=disk.used / (1024**3),
                disk_free_gb=disk.free / (1024**3),
                system_load_1min=system_load[0] if system_load else None,
                system_load_5min=system_load[1] if system_load else None,
                system_load_15min=system_load[2] if system_load else None,
                total_processes=total_processes,
                zombie_processes=zombie_processes,
                active_cameras=current_metrics.get("active_cameras", 0),
                active_detections=current_metrics.get("active_detections", 0),
                active_alerts=current_metrics.get("active_alerts", 0),
                system_info={
                    "platform": platform.platform(),
                    "python_version": platform.python_version(),
                    "processor": platform.processor(),
                    "machine": platform.machine(),
                },
            )

            # Store in database if session provided
            if db:
                db.add(system_metrics)
                db.commit()
                db.refresh(system_metrics)
                logger.debug(
                    f"Stored system metrics: CPU {system_metrics.cpu_usage_percent}%, Memory {system_metrics.memory_usage_percent}%"
                )

                # Broadcast update via WebSocket
                try:
                    await analytics_websocket_manager.broadcast_system_metrics(
                        system_metrics
                    )
                except Exception as e:
                    logger.warning(f"Failed to broadcast system metrics: {e}")

            return system_metrics

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return None

    async def collect_camera_metrics(self, db: Session = None) -> List[CameraMetrics]:
        """Collect metrics for all active cameras."""
        try:
            if not db:
                logger.warning(
                    "No database session provided for camera metrics collection"
                )
                return []

            # Get all enabled cameras
            cameras = db.query(Camera).filter(Camera.enabled == True).all()
            camera_metrics_list = []

            for camera in cameras:
                try:
                    # Get camera performance data (this would integrate with actual camera system)
                    camera_metrics = await self._get_camera_performance_data(camera)

                    if camera_metrics:
                        # Store in database
                        db.add(camera_metrics)
                        camera_metrics_list.append(camera_metrics)

                except Exception as e:
                    logger.error(
                        f"Error collecting metrics for camera {camera.id}: {e}"
                    )
                    continue

            if camera_metrics_list:
                db.commit()
                logger.debug(f"Stored metrics for {len(camera_metrics_list)} cameras")

                # Broadcast updates via WebSocket
                for camera_metrics in camera_metrics_list:
                    try:
                        await analytics_websocket_manager.broadcast_camera_metrics(
                            camera_metrics
                        )
                    except Exception as e:
                        logger.warning(f"Failed to broadcast camera metrics: {e}")

            return camera_metrics_list

        except Exception as e:
            logger.error(f"Error collecting camera metrics: {e}")
            return []

    async def _get_camera_performance_data(
        self, camera: Camera
    ) -> Optional[CameraMetrics]:
        """Get performance data for a specific camera."""
        try:
            # This would integrate with the actual camera system
            # For now, we'll create sample data
            import random

            # Simulate camera performance metrics
            fps_actual = random.uniform(camera.fps * 0.8, camera.fps * 1.2)
            connection_status = "connected" if random.random() > 0.1 else "error"

            camera_metrics = CameraMetrics(
                camera_id=camera.id,
                connection_status=connection_status,
                connection_latency_ms=random.uniform(5, 50),
                last_heartbeat=datetime.utcnow(),
                fps_actual=fps_actual,
                fps_target=camera.fps,
                resolution_width=camera.resolution_width,
                resolution_height=camera.resolution_height,
                bitrate_kbps=random.randint(1000, 5000),
                frame_processing_time_ms=random.uniform(10, 100),
                queue_depth=random.randint(0, 10),
                dropped_frames=random.randint(0, 5),
                total_frames_processed=random.randint(1000, 10000),
                signal_strength=random.uniform(80, 100),
                noise_level=random.uniform(0, 20),
                brightness_level=random.uniform(40, 80),
                contrast_level=random.uniform(40, 80),
                recording_status=camera.recording_enabled,
                storage_used_gb=random.uniform(1, 50),
                storage_available_gb=random.uniform(100, 500),
                bandwidth_usage_mbps=random.uniform(5, 25),
                packet_loss_percent=random.uniform(0, 2),
                jitter_ms=random.uniform(1, 10),
            )

            return camera_metrics

        except Exception as e:
            logger.error(f"Error getting camera performance data for {camera.id}: {e}")
            return None

    async def record_detection_metrics(
        self,
        db: Session,
        camera_id: str,
        prediction_data: Dict[str, Any],
        performance_data: Dict[str, Any],
        frame_id: Optional[str] = None,
    ) -> Optional[DetectionMetrics]:
        """Record detection metrics from ML model inference."""
        try:
            detection_metrics = DetectionMetrics(
                camera_id=camera_id,
                frame_id=frame_id,
                model_version=prediction_data.get("model_version", "unknown"),
                model_name=prediction_data.get("model_name", "unknown"),
                prediction_label=prediction_data.get("label", "unknown"),
                confidence_score=prediction_data.get("confidence", 0.0),
                is_shoplifting=prediction_data.get("is_shoplifting", False),
                bounding_box=prediction_data.get("bounding_box"),
                object_count=prediction_data.get("object_count", 1),
                processing_time_ms=performance_data.get("total_time_ms", 0),
                inference_time_ms=performance_data.get("inference_time_ms", 0),
                preprocess_time_ms=performance_data.get("preprocess_time_ms", 0),
                postprocess_time_ms=performance_data.get("postprocess_time_ms", 0),
                fps_actual=performance_data.get("fps_actual", 30),
                fps_target=performance_data.get("fps_target", 30),
                latency_ms=performance_data.get("latency_ms", 0),
                queue_depth=performance_data.get("queue_depth", 0),
                dropped_frames=performance_data.get("dropped_frames", 0),
                memory_usage_mb=performance_data.get("memory_usage_mb"),
                gpu_usage_percent=performance_data.get("gpu_usage_percent"),
                cpu_usage_percent=performance_data.get("cpu_usage_percent"),
                alert_triggered=prediction_data.get("alert_triggered", False),
                alert_level=prediction_data.get("alert_level"),
                alert_type=prediction_data.get("alert_type"),
                location_data=prediction_data.get("location_data"),
                weather_data=prediction_data.get("weather_data"),
                lighting_conditions=prediction_data.get("lighting_conditions"),
            )

            db.add(detection_metrics)
            db.commit()
            db.refresh(detection_metrics)

            logger.debug(
                f"Recorded detection metrics for camera {camera_id}: {detection_metrics.prediction_label} ({detection_metrics.confidence_score:.2f})"
            )

            # Broadcast update via WebSocket
            try:
                await analytics_websocket_manager.broadcast_detection_metrics(
                    detection_metrics
                )
            except Exception as e:
                logger.warning(f"Failed to broadcast detection metrics: {e}")

            return detection_metrics

        except Exception as e:
            logger.error(f"Error recording detection metrics: {e}")
            if db:
                db.rollback()
            return None

    async def get_metrics_summary(
        self, db: Session, time_range: str = "24h"
    ) -> Dict[str, Any]:
        """Get a summary of metrics for the specified time range."""
        try:
            end_time = datetime.utcnow()

            if time_range == "1h":
                start_time = end_time - timedelta(hours=1)
            elif time_range == "24h":
                start_time = end_time - timedelta(days=1)
            elif time_range == "7d":
                start_time = end_time - timedelta(days=7)
            elif time_range == "30d":
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(hours=1)

            # Get system metrics summary
            system_metrics = (
                db.query(SystemMetrics)
                .filter(
                    SystemMetrics.timestamp >= start_time,
                    SystemMetrics.timestamp <= end_time,
                )
                .all()
            )

            # Get detection metrics summary
            detection_metrics = (
                db.query(DetectionMetrics)
                .filter(
                    DetectionMetrics.timestamp >= start_time,
                    DetectionMetrics.timestamp <= end_time,
                )
                .all()
            )

            # Get camera metrics summary
            camera_metrics = (
                db.query(CameraMetrics)
                .filter(
                    CameraMetrics.timestamp >= start_time,
                    CameraMetrics.timestamp <= end_time,
                )
                .all()
            )

            # Calculate summary statistics
            summary = {
                "time_range": time_range,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "system": {
                    "total_records": len(system_metrics),
                    "average_cpu": (
                        sum(m.cpu_usage_percent for m in system_metrics)
                        / len(system_metrics)
                        if system_metrics
                        else 0
                    ),
                    "average_memory": (
                        sum(m.memory_usage_percent for m in system_metrics)
                        / len(system_metrics)
                        if system_metrics
                        else 0
                    ),
                    "average_disk": (
                        sum(m.disk_usage_percent for m in system_metrics)
                        / len(system_metrics)
                        if system_metrics
                        else 0
                    ),
                    "peak_cpu": (
                        max(m.cpu_usage_percent for m in system_metrics)
                        if system_metrics
                        else 0
                    ),
                    "peak_memory": (
                        max(m.memory_usage_percent for m in system_metrics)
                        if system_metrics
                        else 0
                    ),
                },
                "detections": {
                    "total_detections": len(detection_metrics),
                    "shoplifting_detections": len(
                        [d for d in detection_metrics if d.is_shoplifting]
                    ),
                    "average_confidence": (
                        sum(d.confidence_score for d in detection_metrics)
                        / len(detection_metrics)
                        if detection_metrics
                        else 0
                    ),
                    "average_processing_time": (
                        sum(d.processing_time_ms for d in detection_metrics)
                        / len(detection_metrics)
                        if detection_metrics
                        else 0
                    ),
                },
                "cameras": {
                    "total_records": len(camera_metrics),
                    "active_cameras": len(set(m.camera_id for m in camera_metrics)),
                    "average_fps": (
                        sum(m.fps_actual for m in camera_metrics) / len(camera_metrics)
                        if camera_metrics
                        else 0
                    ),
                    "average_latency": (
                        sum(m.latency_ms for m in camera_metrics) / len(camera_metrics)
                        if camera_metrics
                        else 0
                    ),
                },
            }

            return summary

        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {}

    async def cleanup_old_metrics(self, db: Session, days_to_keep: int = 30):
        """Clean up old metrics data to prevent database bloat."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            # Delete old system metrics
            deleted_system = (
                db.query(SystemMetrics)
                .filter(SystemMetrics.timestamp < cutoff_date)
                .delete()
            )

            # Delete old camera metrics
            deleted_camera = (
                db.query(CameraMetrics)
                .filter(CameraMetrics.timestamp < cutoff_date)
                .delete()
            )

            # Delete old detection metrics
            deleted_detection = (
                db.query(DetectionMetrics)
                .filter(DetectionMetrics.timestamp < cutoff_date)
                .delete()
            )

            db.commit()

            logger.info(
                f"Cleaned up old metrics: {deleted_system} system, {deleted_camera} camera, {deleted_detection} detection records"
            )

        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")
            if db:
                db.rollback()


# Global instance
metrics_collection_service = MetricsCollectionService()
