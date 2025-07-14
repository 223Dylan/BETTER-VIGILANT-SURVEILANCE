from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from datetime import datetime
from loguru import logger
import time

from src.services.alert_manager import get_alert_manager, AlertManager

router = APIRouter(prefix="/alerts", tags=["alerts"])

# Pydantic models for request/response
class AlertActionRequest(BaseModel):
    userId: str
    notes: Optional[str] = None

class AlertFilterRequest(BaseModel):
    severity: Optional[List[str]] = None
    status: Optional[List[str]] = None
    type: Optional[List[str]] = None
    cameraId: Optional[List[str]] = None
    confidenceMin: Optional[float] = None
    confidenceMax: Optional[float] = None
    dateRange: Optional[Dict[str, str]] = None

class AlertResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

def get_alert_service() -> AlertManager:
    """Dependency to get alert manager instance."""
    return get_alert_manager()

@router.get("/active", summary="Get active alerts")
async def get_active_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity (critical,high,medium,low)"),
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    limit: Optional[int] = Query(100, description="Maximum number of alerts to return"),
    alert_service: AlertManager = Depends(get_alert_service)
) -> AlertResponse:
    """Get all active alerts with optional filtering."""
    try:
        filters = {}
        
        if severity:
            filters['severity'] = severity.split(',')
        
        if camera_id:
            filters['cameraId'] = [camera_id]
        
        alerts = alert_service.get_active_alerts(filters)
        
        # Apply limit
        if limit and len(alerts) > limit:
            alerts = alerts[:limit]
        
        logger.info(f"[SUCCESS] Retrieved {len(alerts)} active alerts")
        
        return AlertResponse(
            success=True,
            message=f"Retrieved {len(alerts)} active alerts",
            data={
                "alerts": alerts,
                "total": len(alerts)
            }
        )
        
    except Exception as e:
        logger.error(f"[ERROR] Error getting active alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", summary="Get alert history")
async def get_alert_history(
    limit: Optional[int] = Query(100, description="Maximum number of alerts to return"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    alert_service: AlertManager = Depends(get_alert_service)
) -> AlertResponse:
    """Get alert history with optional filtering."""
    try:
        filters = {}
        
        if severity:
            filters['severity'] = severity.split(',')
        
        if camera_id:
            filters['cameraId'] = [camera_id]
        
        alerts = alert_service.get_alert_history(limit, filters)
        
        logger.info(f"[SUCCESS] Retrieved {len(alerts)} historical alerts")
        
        return AlertResponse(
            success=True,
            message=f"Retrieved {len(alerts)} historical alerts",
            data={
                "alerts": alerts,
                "total": len(alerts)
            }
        )
        
    except Exception as e:
        logger.error(f"[ERROR] Error getting alert history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", summary="Get alert statistics")
async def get_alert_stats(
    days: Optional[int] = Query(7, description="Number of days to include in statistics"),
    alert_service: AlertManager = Depends(get_alert_service)
) -> AlertResponse:
    """Get alert statistics for the specified time period."""
    try:
        stats = alert_service.get_alert_stats(days)
        
        logger.info(f"[SUCCESS] Retrieved alert statistics for {days} days")
        
        return AlertResponse(
            success=True,
            message=f"Retrieved statistics for {days} days",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"[ERROR] Error getting alert statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", summary="Search alerts with advanced filters")
async def search_alerts(
    filters: AlertFilterRequest,
    limit: Optional[int] = Query(100, description="Maximum number of alerts to return"),
    alert_service: AlertManager = Depends(get_alert_service)
) -> AlertResponse:
    """Search alerts with advanced filtering options."""
    try:
        # Convert Pydantic model to dict for the alert service
        filter_dict = filters.dict(exclude_unset=True)
        
        # Get both active and historical alerts
        active_alerts = alert_service.get_active_alerts(filter_dict)
        historical_alerts = alert_service.get_alert_history(limit * 2, filter_dict)  # Get more history for better results
        
        # Combine and deduplicate
        all_alerts = active_alerts + historical_alerts
        seen_ids = set()
        unique_alerts = []
        
        for alert in all_alerts:
            if alert['id'] not in seen_ids:
                unique_alerts.append(alert)
                seen_ids.add(alert['id'])
        
        # Sort by timestamp (newest first) and apply limit
        unique_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        if limit:
            unique_alerts = unique_alerts[:limit]
        
        logger.info(f"[SUCCESS] Found {len(unique_alerts)} alerts matching search criteria")
        
        return AlertResponse(
            success=True,
            message=f"Found {len(unique_alerts)} alerts",
            data={
                "alerts": unique_alerts,
                "total": len(unique_alerts),
                "filters_applied": filter_dict
            }
        )
        
    except Exception as e:
        logger.error(f"[ERROR] Error searching alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{alert_id}/acknowledge", summary="Acknowledge an alert")
async def acknowledge_alert(
    alert_id: str,
    action: AlertActionRequest,
    alert_service: AlertManager = Depends(get_alert_service)
) -> AlertResponse:
    """Acknowledge an active alert."""
    try:
        success = alert_service.acknowledge_alert(alert_id, action.userId, action.notes)
        
        if success:
            logger.info(f"[SUCCESS] Alert {alert_id} acknowledged by {action.userId}")
            return AlertResponse(
                success=True,
                message=f"Alert {alert_id} acknowledged successfully",
                data={"alert_id": alert_id, "acknowledged_by": action.userId}
            )
        else:
            raise HTTPException(status_code=404, detail="Alert not found or cannot be acknowledged")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Error acknowledging alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{alert_id}/resolve", summary="Resolve an alert")
async def resolve_alert(
    alert_id: str,
    action: AlertActionRequest,
    alert_service: AlertManager = Depends(get_alert_service)
) -> AlertResponse:
    """Resolve an active alert."""
    try:
        success = alert_service.resolve_alert(alert_id, action.userId, action.notes)
        
        if success:
            logger.info(f"[SUCCESS] Alert {alert_id} resolved by {action.userId}")
            return AlertResponse(
                success=True,
                message=f"Alert {alert_id} resolved successfully",
                data={"alert_id": alert_id, "resolved_by": action.userId}
            )
        else:
            raise HTTPException(status_code=404, detail="Alert not found or cannot be resolved")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Error resolving alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{alert_id}", summary="Get specific alert details")
async def get_alert_details(
    alert_id: str,
    alert_service: AlertManager = Depends(get_alert_service)
) -> AlertResponse:
    """Get detailed information about a specific alert."""
    try:
        # Check active alerts first
        active_alerts = alert_service.get_active_alerts()
        alert = next((a for a in active_alerts if a['id'] == alert_id), None)
        
        # If not found in active, check history
        if not alert:
            historical_alerts = alert_service.get_alert_history(1000)  # Search more history
            alert = next((a for a in historical_alerts if a['id'] == alert_id), None)
        
        if alert:
            logger.info(f"[SUCCESS] Retrieved details for alert {alert_id}")
            return AlertResponse(
                success=True,
                message=f"Alert {alert_id} details retrieved",
                data=alert
            )
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Error getting alert details for {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-acknowledge", summary="Acknowledge multiple alerts")
async def bulk_acknowledge_alerts(
    alert_ids: List[str],
    action: AlertActionRequest,
    alert_service: AlertManager = Depends(get_alert_service)
) -> AlertResponse:
    """Acknowledge multiple alerts at once."""
    try:
        results = []
        success_count = 0
        
        for alert_id in alert_ids:
            success = alert_service.acknowledge_alert(alert_id, action.userId, action.notes)
            results.append({"alert_id": alert_id, "success": success})
            if success:
                success_count += 1
        
        logger.info(f"[SUCCESS] Bulk acknowledged {success_count}/{len(alert_ids)} alerts by {action.userId}")
        
        return AlertResponse(
            success=True,
            message=f"Acknowledged {success_count} out of {len(alert_ids)} alerts",
            data={
                "results": results,
                "total_processed": len(alert_ids),
                "successful": success_count,
                "failed": len(alert_ids) - success_count
            }
        )
        
    except Exception as e:
        logger.error(f"[ERROR] Error bulk acknowledging alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{alert_id}", summary="Dismiss an alert")
async def dismiss_alert(
    alert_id: str,
    action: AlertActionRequest,
    alert_service: AlertManager = Depends(get_alert_service)
) -> AlertResponse:
    """Dismiss an alert (mark as dismissed without resolving)."""
    try:
        # For now, we'll use resolve with special notes to indicate dismissal
        success = alert_service.resolve_alert(alert_id, action.userId, f"DISMISSED: {action.notes or 'No reason provided'}")
        
        if success:
            logger.info(f"[SUCCESS] Alert {alert_id} dismissed by {action.userId}")
            return AlertResponse(
                success=True,
                message=f"Alert {alert_id} dismissed successfully",
                data={"alert_id": alert_id, "dismissed_by": action.userId}
            )
        else:
            raise HTTPException(status_code=404, detail="Alert not found or cannot be dismissed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Error dismissing alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/create-sample-alerts", summary="Create sample alerts for testing")
async def create_sample_alerts(
    alert_service: AlertManager = Depends(get_alert_service)
) -> AlertResponse:
    """Create sample alerts for testing purposes."""
    try:
        # Create test prediction data
        test_predictions = [
            {
                'camera_id': 'store-entrance',
                'confidence': 0.95,
                'is_shoplifting': True,
                'timestamp': datetime.now().timestamp(),
                'label': 1,
                'sequence_stats': {'mean': 0.85, 'std': 0.12, 'frames': 160},
                'task_timestamp': time.time()
            },
            {
                'camera_id': 'store-aisle-1',
                'confidence': 0.73,
                'is_shoplifting': True,
                'timestamp': datetime.now().timestamp(),
                'label': 1,
                'sequence_stats': {'mean': 0.68, 'std': 0.15, 'frames': 160},
                'task_timestamp': time.time()
            },
            {
                'camera_id': 'checkout-area',
                'confidence': 0.55,
                'is_shoplifting': True,
                'timestamp': datetime.now().timestamp(),
                'label': 1,
                'sequence_stats': {'mean': 0.45, 'std': 0.18, 'frames': 160},
                'task_timestamp': time.time()
            }
        ]
        
        created_alerts = []
        for prediction in test_predictions:
            alert_id = alert_service.process_prediction(prediction)
            if alert_id:
                created_alerts.append(alert_id)
        
        logger.info(f"[SUCCESS] Created {len(created_alerts)} sample alerts for testing")
        
        return AlertResponse(
            success=True,
            message=f"Created {len(created_alerts)} sample alerts",
            data={
                "created_alert_ids": created_alerts,
                "total": len(created_alerts)
            }
        )
        
    except Exception as e:
        logger.error(f"[ERROR] Error creating sample alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 