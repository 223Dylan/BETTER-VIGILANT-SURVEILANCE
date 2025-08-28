import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import aiohttp
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Import metrics service with fallback handling
try:
    from src.services.metrics_service import MetricsService
except ImportError:
    # Fallback if aiohttp not available
    from src.services.metrics_service_requests import (
        MetricsServiceRequests as MetricsService,
    )

from loguru import logger

from src.database.models import get_db
from src.services.analytics_aggregation_service import analytics_aggregation_service
from src.services.metrics_collection_service import metrics_collection_service

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

# Initialize metrics service
metrics_service = MetricsService()


class SystemMetricsResponse(BaseModel):
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_cameras: int


class CameraMetricsResponse(BaseModel):
    camera_id: str
    fps_actual: float
    fps_target: float
    latency_ms: float
    status: str
    last_detection: Optional[datetime] = None


class DetectionMetricsResponse(BaseModel):
    camera_id: str
    confidence: float
    label: str
    is_shoplifting: bool
    timestamp: datetime
    alert_triggered: bool


class MetricsSummaryResponse(BaseModel):
    system: SystemMetricsResponse
    cameras: List[CameraMetricsResponse]
    recent_detections: List[DetectionMetricsResponse]
    total_detections_today: int
    alert_count_today: int


@router.get("/system", response_model=List[SystemMetricsResponse])
async def get_system_metrics(
    time_range: str = Query("15m", description="Time range: 5m, 15m, 1h, 24h"),
    limit: int = Query(100, description="Maximum number of data points"),
):
    """Get system performance metrics over time."""
    try:
        metrics = await metrics_service.get_system_metrics(time_range, limit)
        return metrics
    except Exception as e:
        logger.error(f"Error fetching system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch system metrics")


@router.get("/cameras", response_model=List[CameraMetricsResponse])
async def get_camera_metrics():
    """Get current metrics for all cameras."""
    try:
        metrics = await metrics_service.get_camera_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error fetching camera metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch camera metrics")


@router.get("/cameras/{camera_id}/performance")
async def get_camera_performance(
    camera_id: str,
    time_range: str = Query("1h", description="Time range: 5m, 15m, 1h, 24h"),
):
    """Get detailed performance metrics for a specific camera."""
    try:
        metrics = await metrics_service.get_camera_performance(camera_id, time_range)
        return metrics
    except Exception as e:
        logger.error(f"Error fetching camera {camera_id} performance: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch camera {camera_id} metrics"
        )


@router.get("/detections", response_model=List[DetectionMetricsResponse])
async def get_detection_metrics(
    time_range: str = Query("1h", description="Time range: 5m, 15m, 1h, 24h"),
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    confidence_threshold: float = Query(
        0.0, description="Minimum confidence threshold"
    ),
):
    """Get detection metrics with optional filtering."""
    try:
        metrics = await metrics_service.get_detection_metrics(
            time_range, camera_id, confidence_threshold
        )
        return metrics
    except Exception as e:
        logger.error(f"Error fetching detection metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch detection metrics")


@router.get("/summary", response_model=MetricsSummaryResponse)
async def get_metrics_summary():
    """Get a comprehensive summary of all system metrics."""
    try:
        summary = await metrics_service.get_metrics_summary()
        return summary
    except Exception as e:
        logger.error(f"Error fetching metrics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics summary")


@router.get("/health")
async def get_metrics_health():
    """Get health status of metrics infrastructure."""
    try:
        health = await metrics_service.get_health_status()
        return health
    except Exception as e:
        logger.error(f"Error checking metrics health: {e}")
        raise HTTPException(status_code=500, detail="Failed to check metrics health")


@router.get("/alerts/recent")
async def get_recent_alerts(
    limit: int = Query(50, description="Maximum number of alerts"),
    severity: Optional[str] = Query(
        None, description="Filter by severity: low, medium, high, critical"
    ),
):
    """Get recent alerts from the system."""
    try:
        alerts = await metrics_service.get_recent_alerts(limit, severity)
        return alerts
    except Exception as e:
        logger.error(f"Error fetching recent alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch recent alerts")


@router.get("/analytics")
async def get_analytics_data(
    time_range: str = Query("24h", description="Time range: 24h, 7d, 30d"),
):
    """Get comprehensive analytics data for dashboard."""
    try:
        # Get all the data needed for analytics
        [system_metrics, detection_metrics, summary, health_status, recent_alerts] = (
            await asyncio.gather(
                metrics_service.get_system_metrics(time_range, 200),
                metrics_service.get_detection_metrics(time_range),
                metrics_service.get_metrics_summary(),
                metrics_service.get_health_status(),
                metrics_service.get_recent_alerts(100),
            )
        )

        # Calculate additional analytics
        analytics_data = {
            "system_metrics": system_metrics,
            "detection_metrics": detection_metrics,
            "summary": summary,
            "health_status": health_status,
            "recent_alerts": recent_alerts,
            "time_range": time_range,
            "generated_at": datetime.now().isoformat(),
        }

        # Add computed analytics
        if detection_metrics:
            total_detections = len(detection_metrics)
            shoplifting_detections = len(
                [d for d in detection_metrics if d.get("is_shoplifting", False)]
            )
            avg_confidence = (
                sum(d.get("confidence", 0) for d in detection_metrics)
                / total_detections
                if total_detections > 0
                else 0
            )

            analytics_data["computed_stats"] = {
                "total_detections": total_detections,
                "shoplifting_detections": shoplifting_detections,
                "average_confidence": round(avg_confidence * 100, 2),
                "detection_rate": (
                    round((shoplifting_detections / total_detections * 100), 2)
                    if total_detections > 0
                    else 0
                ),
            }

        return analytics_data
    except Exception as e:
        logger.error(f"Error fetching analytics data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics data")


@router.get("/analytics/aggregates")
async def get_analytics_aggregates(
    aggregation_type: str = Query(
        "daily", description="Type: hourly, daily, weekly, monthly"
    ),
    time_period: Optional[str] = Query(
        None, description="Specific time period (e.g., 2024-01-15)"
    ),
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(100, description="Maximum number of aggregates"),
):
    """Get pre-computed analytics aggregates for fast dashboard queries."""
    try:
        db = next(get_db())
        aggregates = await analytics_aggregation_service.get_aggregates(
            db=db,
            aggregation_type=aggregation_type,
            time_period=time_period,
            camera_id=camera_id,
            user_id=user_id,
            limit=limit,
        )

        # Convert to dict for JSON serialization
        result = []
        for aggregate in aggregates:
            result.append(
                {
                    "id": str(aggregate.id),
                    "aggregation_type": aggregate.aggregation_type,
                    "time_period": aggregate.time_period,
                    "start_time": aggregate.start_time.isoformat(),
                    "end_time": aggregate.end_time.isoformat(),
                    "camera_id": aggregate.camera_id,
                    "user_id": aggregate.user_id,
                    "total_detections": aggregate.total_detections,
                    "shoplifting_detections": aggregate.shoplifting_detections,
                    "false_positives": aggregate.false_positives,
                    "average_confidence": aggregate.average_confidence,
                    "detection_rate_per_hour": aggregate.detection_rate_per_hour,
                    "total_alerts": aggregate.total_alerts,
                    "alerts_by_severity": aggregate.alerts_by_severity,
                    "alerts_by_type": aggregate.alerts_by_type,
                    "average_processing_time_ms": aggregate.average_processing_time_ms,
                    "average_fps": aggregate.average_fps,
                    "average_latency_ms": aggregate.average_latency_ms,
                    "system_uptime_percent": aggregate.system_uptime_percent,
                    "average_cpu_usage": aggregate.average_cpu_usage,
                    "average_memory_usage": aggregate.average_memory_usage,
                    "average_disk_usage": aggregate.average_disk_usage,
                    "peak_cpu_usage": aggregate.peak_cpu_usage,
                    "peak_memory_usage": aggregate.peak_memory_usage,
                    "active_cameras_count": aggregate.active_cameras_count,
                    "cameras_by_status": aggregate.cameras_by_status,
                    "average_camera_uptime": aggregate.average_camera_uptime,
                    "notifications_sent": aggregate.notifications_sent,
                    "notifications_delivered": aggregate.notifications_delivered,
                    "notifications_failed": aggregate.notifications_failed,
                    "average_delivery_time_ms": aggregate.average_delivery_time_ms,
                    "incidents_resolved": aggregate.incidents_resolved,
                    "average_response_time_minutes": aggregate.average_response_time_minutes,
                    "cost_savings_estimate": aggregate.cost_savings_estimate,
                    "hourly_breakdown": aggregate.hourly_breakdown,
                    "daily_breakdown": aggregate.daily_breakdown,
                    "data_completeness_percent": aggregate.data_completeness_percent,
                    "sample_count": aggregate.sample_count,
                    "last_calculated": aggregate.last_calculated.isoformat(),
                    "created_at": aggregate.created_at.isoformat(),
                    "updated_at": aggregate.updated_at.isoformat(),
                }
            )

        return result

    except Exception as e:
        logger.error(f"Error fetching analytics aggregates: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch analytics aggregates"
        )


@router.post("/collection/start")
async def start_metrics_collection():
    """Start the metrics collection service."""
    try:
        await metrics_collection_service.start_collection()
        return {"message": "Metrics collection service started successfully"}
    except Exception as e:
        logger.error(f"Error starting metrics collection: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to start metrics collection"
        )


@router.post("/collection/stop")
async def stop_metrics_collection():
    """Stop the metrics collection service."""
    try:
        await metrics_collection_service.stop_collection()
        return {"message": "Metrics collection service stopped successfully"}
    except Exception as e:
        logger.error(f"Error stopping metrics collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop metrics collection")


@router.post("/aggregation/start")
async def start_analytics_aggregation():
    """Start the analytics aggregation service."""
    try:
        await analytics_aggregation_service.start_aggregation()
        return {"message": "Analytics aggregation service started successfully"}
    except Exception as e:
        logger.error(f"Error starting analytics aggregation: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to start analytics aggregation"
        )


@router.post("/aggregation/stop")
async def stop_analytics_aggregation():
    """Stop the analytics aggregation service."""
    try:
        await analytics_aggregation_service.stop_aggregation()
        return {"message": "Analytics aggregation service stopped successfully"}
    except Exception as e:
        logger.error(f"Error stopping analytics aggregation: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to stop analytics aggregation"
        )


@router.post("/detection/record")
async def record_detection_metrics(
    camera_id: str,
    prediction_data: dict,
    performance_data: dict,
    frame_id: Optional[str] = None,
):
    """Record detection metrics from ML model inference."""
    try:
        db = next(get_db())
        metrics = await metrics_collection_service.record_detection_metrics(
            db=db,
            camera_id=camera_id,
            prediction_data=prediction_data,
            performance_data=performance_data,
            frame_id=frame_id,
        )

        if metrics:
            return {
                "message": "Detection metrics recorded successfully",
                "metrics_id": str(metrics.id),
            }
        else:
            raise HTTPException(
                status_code=500, detail="Failed to record detection metrics"
            )

    except Exception as e:
        logger.error(f"Error recording detection metrics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to record detection metrics"
        )


@router.get("/summary/enhanced")
async def get_enhanced_metrics_summary(
    time_range: str = Query("24h", description="Time range: 1h, 24h, 7d, 30d")
):
    """Get enhanced metrics summary using the new analytics system."""
    try:
        db = next(get_db())
        summary = await metrics_collection_service.get_metrics_summary(db, time_range)
        return summary
    except Exception as e:
        logger.error(f"Error fetching enhanced metrics summary: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch enhanced metrics summary"
        )
