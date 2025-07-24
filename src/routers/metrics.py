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
