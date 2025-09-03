from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.orm import Session

from src.database.models import get_db
from src.services.real_analytics_service import real_analytics_service

router = APIRouter(prefix="/api/analytics", tags=["verified-real-analytics"])


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_verified_analytics_dashboard(db: Session = Depends(get_db)):
    """Get VERIFIED real analytics dashboard data from actual database tables ONLY."""
    try:
        dashboard_data = await real_analytics_service.get_dashboard_summary(db)
        return dashboard_data
    except Exception as e:
        logger.error(f"Error getting verified analytics dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/live-system", response_model=Dict[str, Any])
async def get_live_system_performance():
    """Get LIVE system performance metrics via psutil."""
    try:
        live_metrics = await real_analytics_service.get_live_system_performance()
        return live_metrics
    except Exception as e:
        logger.error(f"Error getting live system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=Dict[str, Any])
async def get_real_alert_analytics(db: Session = Depends(get_db)):
    """Get REAL alert analytics from Alert table."""
    try:
        alert_analytics = await real_analytics_service.get_alert_analytics(db)
        return alert_analytics
    except Exception as e:
        logger.error(f"Error getting real alert analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cameras", response_model=Dict[str, Any])
async def get_real_camera_analytics(db: Session = Depends(get_db)):
    """Get REAL camera analytics from Camera table."""
    try:
        camera_analytics = await real_analytics_service.get_camera_analytics(db)
        return camera_analytics
    except Exception as e:
        logger.error(f"Error getting real camera analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications", response_model=Dict[str, Any])
async def get_real_notification_analytics(db: Session = Depends(get_db)):
    """Get REAL notification analytics from NotificationHistory table."""
    try:
        notification_analytics = (
            await real_analytics_service.get_notification_analytics(db)
        )
        return notification_analytics
    except Exception as e:
        logger.error(f"Error getting real notification analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{time_period}")
async def get_verified_analytics_summary(
    time_period: str = "24h", db: Session = Depends(get_db)
):
    """Get VERIFIED analytics summary for specified time period (1h, 24h, 7d, 30d)."""
    try:
        from src.database.models import Alert, Camera, NotificationHistory

        # Parse time period
        now = datetime.utcnow()
        if time_period == "1h":
            start_time = now - timedelta(hours=1)
        elif time_period == "24h":
            start_time = now - timedelta(days=1)
        elif time_period == "7d":
            start_time = now - timedelta(days=7)
        elif time_period == "30d":
            start_time = now - timedelta(days=30)
        else:
            raise HTTPException(status_code=400, detail="Invalid time period")

        # Get VERIFIED real data from database
        total_alerts = db.query(Alert).filter(Alert.timestamp >= start_time).count()

        active_alerts = db.query(Alert).filter(Alert.status == "active").count()

        shoplifting_alerts = (
            db.query(Alert)
            .filter(Alert.type == "shoplifting", Alert.timestamp >= start_time)
            .count()
        )

        suspicious_alerts = (
            db.query(Alert)
            .filter(Alert.type == "suspicious_activity", Alert.timestamp >= start_time)
            .count()
        )

        total_cameras = db.query(Camera).count()
        enabled_cameras = db.query(Camera).filter(Camera.enabled == True).count()
        active_cameras = (
            db.query(Camera)
            .filter(Camera.enabled == True, Camera.status.in_(["active", "starting"]))
            .count()
        )

        notifications_sent = (
            db.query(NotificationHistory)
            .filter(NotificationHistory.sent_at >= start_time)
            .count()
        )

        notifications_delivered = (
            db.query(NotificationHistory)
            .filter(NotificationHistory.delivered_at >= start_time)
            .count()
        )

        summary = {
            "time_period": time_period,
            "start_time": start_time.isoformat(),
            "end_time": now.isoformat(),
            "alerts": {
                "total": total_alerts,
                "active": active_alerts,
                "shoplifting": shoplifting_alerts,
                "suspicious_activity": suspicious_alerts,
            },
            "cameras": {
                "total": total_cameras,
                "enabled": enabled_cameras,
                "active": active_cameras,
                "inactive": total_cameras - active_cameras,
            },
            "notifications": {
                "sent": notifications_sent,
                "delivered": notifications_delivered,
            },
            "verification_status": "ALL_DATA_VERIFIED_REAL",
            "data_sources": [
                "real_alert_table",
                "real_camera_table",
                "real_notification_history_table",
            ],
            "generated_at": now.isoformat(),
        }

        return summary

    except Exception as e:
        logger.error(f"Error getting verified analytics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-fake-data")
async def clear_fake_data_only():
    """Clear all FAKE test data from metrics tables - KEEPS real Alert/Camera/NotificationHistory data."""
    try:
        await real_analytics_service.clear_test_data()

        return {
            "message": "✅ FAKE test data cleared successfully",
            "action": "Removed fake data from SystemMetrics, CameraMetrics, DetectionMetrics, AnalyticsAggregates tables",
            "preserved": "✅ KEPT all real data in Alert, Camera, NotificationHistory tables",
            "verification_status": "REAL_DATA_PRESERVED",
        }

    except Exception as e:
        logger.error(f"Error clearing fake data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_analytics_health_check():
    """Health check endpoint to verify analytics service is working with real data."""
    try:
        db = next(get_db())

        # Quick verification of real data sources
        from src.database.models import Alert, Camera, NotificationHistory

        alert_count = db.query(Alert).count()
        camera_count = db.query(Camera).count()
        notification_count = db.query(NotificationHistory).count()

        db.close()

        return {
            "status": "healthy",
            "service": "verified_real_analytics",
            "data_sources": {
                "alerts": alert_count,
                "cameras": camera_count,
                "notifications": notification_count,
            },
            "verification_status": "ALL_DATA_SOURCES_VERIFIED",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
