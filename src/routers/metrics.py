from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import asyncio

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import aiohttp
import json

# Import metrics service with fallback handling
try:
    from src.services.metrics_service import MetricsService
except ImportError:
    # Fallback if aiohttp not available
    from src.services.metrics_service_requests import MetricsServiceRequests as MetricsService
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
    limit: int = Query(100, description="Maximum number of data points")
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
    time_range: str = Query("1h", description="Time range: 5m, 15m, 1h, 24h")
):
    """Get detailed performance metrics for a specific camera."""
    try:
        metrics = await metrics_service.get_camera_performance(camera_id, time_range)
        return metrics
    except Exception as e:
        logger.error(f"Error fetching camera {camera_id} performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch camera {camera_id} metrics")


@router.get("/detections", response_model=List[DetectionMetricsResponse])
async def get_detection_metrics(
    time_range: str = Query("1h", description="Time range: 5m, 15m, 1h, 24h"),
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    confidence_threshold: float = Query(0.0, description="Minimum confidence threshold")
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
    severity: Optional[str] = Query(None, description="Filter by severity: low, medium, high, critical")
):
    """Get recent alerts from the system."""
    try:
        alerts = await metrics_service.get_recent_alerts(limit, severity)
        return alerts
    except Exception as e:
        logger.error(f"Error fetching recent alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch recent alerts") 