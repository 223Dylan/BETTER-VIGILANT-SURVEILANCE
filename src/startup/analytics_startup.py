"""
Analytics system startup script.

This module initializes the analytics infrastructure including:
- Metrics collection service
- Analytics aggregation service
- Database connections
- Background tasks
"""

import asyncio
from contextlib import asynccontextmanager

from loguru import logger

from src.database.models import get_db
from src.services.analytics_aggregation_service import analytics_aggregation_service
from src.services.metrics_collection_service import metrics_collection_service
from src.websockets.analytics_websocket_manager import analytics_websocket_manager


@asynccontextmanager
async def analytics_lifespan():
    """
    Context manager for analytics services lifecycle.

    This ensures proper startup and shutdown of analytics services.
    """
    logger.info("Starting analytics services...")

    try:
        # Start metrics collection service
        await metrics_collection_service.start_collection()
        logger.info("Metrics collection service started")

        # Start analytics aggregation service
        await analytics_aggregation_service.start_aggregation()
        logger.info("Analytics aggregation service started")

        # Start analytics WebSocket broadcasting service
        await analytics_websocket_manager.start_broadcasting()
        logger.info("Analytics WebSocket broadcasting service started")

        # Yield control back to the application
        yield

    except Exception as e:
        logger.error(f"Error starting analytics services: {e}")
        raise

    finally:
        logger.info("Shutting down analytics services...")

        try:
            # Stop analytics WebSocket broadcasting service
            await analytics_websocket_manager.stop_broadcasting()
            logger.info("Analytics WebSocket broadcasting service stopped")

            # Stop analytics aggregation service
            await analytics_aggregation_service.stop_aggregation()
            logger.info("Analytics aggregation service stopped")

            # Stop metrics collection service
            await metrics_collection_service.stop_collection()
            logger.info("Metrics collection service stopped")

        except Exception as e:
            logger.error(f"Error stopping analytics services: {e}")


async def initialize_analytics():
    """
    Initialize analytics services without lifespan management.

    This is useful for testing or when you want manual control.
    """
    logger.info("Initializing analytics services...")

    try:
        # Start metrics collection service
        await metrics_collection_service.start_collection()
        logger.info("Metrics collection service initialized")

        # Start analytics aggregation service
        await analytics_aggregation_service.start_aggregation()
        logger.info("Analytics aggregation service initialized")

        # Start analytics WebSocket broadcasting service
        await analytics_websocket_manager.start_broadcasting()
        logger.info("Analytics WebSocket broadcasting service initialized")

        return True

    except Exception as e:
        logger.error(f"Error initializing analytics services: {e}")
        return False


async def shutdown_analytics():
    """
    Shutdown analytics services.

    This is useful for testing or when you want manual control.
    """
    logger.info("Shutting down analytics services...")

    try:
        # Stop analytics WebSocket broadcasting service
        await analytics_websocket_manager.stop_broadcasting()
        logger.info("Analytics WebSocket broadcasting service stopped")

        # Stop analytics aggregation service
        await analytics_aggregation_service.stop_aggregation()
        logger.info("Analytics aggregation service stopped")

        # Stop metrics collection service
        await metrics_collection_service.stop_collection()
        logger.info("Metrics collection service stopped")

        return True

    except Exception as e:
        logger.error(f"Error shutting down analytics services: {e}")
        return False


async def populate_sample_data():
    """
    Populate the database with sample analytics data for testing.

    This creates sample metrics records to demonstrate the analytics system.
    """
    logger.info("Populating sample analytics data...")

    try:
        db = next(get_db())

        # Create sample system metrics
        await metrics_collection_service.collect_system_metrics(db)
        logger.info("Sample system metrics created")

        # Create sample camera metrics
        await metrics_collection_service.collect_camera_metrics(db)
        logger.info("Sample camera metrics created")

        # Create sample detection metrics
        sample_prediction = {
            "model_version": "v1.0.0",
            "model_name": "shoplifting_detector",
            "label": "person",
            "confidence": 0.85,
            "is_shoplifting": True,
            "alert_triggered": True,
            "alert_level": "medium",
            "alert_type": "shoplifting",
        }

        sample_performance = {
            "total_time_ms": 150.0,
            "inference_time_ms": 120.0,
            "preprocess_time_ms": 20.0,
            "postprocess_time_ms": 10.0,
            "fps_actual": 25.0,
            "fps_target": 30.0,
            "latency_ms": 40.0,
            "queue_depth": 2,
            "dropped_frames": 0,
            "memory_usage_mb": 512.0,
            "gpu_usage_percent": 45.0,
            "cpu_usage_percent": 30.0,
        }

        await metrics_collection_service.record_detection_metrics(
            db=db,
            camera_id="sample-camera-1",
            prediction_data=sample_prediction,
            performance_data=sample_performance,
        )
        logger.info("Sample detection metrics created")

        # Create sample analytics aggregates
        await analytics_aggregation_service.aggregate_hourly_data(db)
        await analytics_aggregation_service.aggregate_daily_data(db)
        logger.info("Sample analytics aggregates created")

        logger.info("Sample analytics data populated successfully")

    except Exception as e:
        logger.error(f"Error populating sample analytics data: {e}")
        if db:
            db.rollback()


async def health_check():
    """
    Perform a health check on the analytics services.

    Returns a dictionary with the status of each service.
    """
    try:
        health_status = {
            "metrics_collection": {
                "status": (
                    "running" if metrics_collection_service._running else "stopped"
                ),
                "collection_tasks": len(metrics_collection_service._collection_tasks),
            },
            "analytics_aggregation": {
                "status": (
                    "running" if analytics_aggregation_service._running else "stopped"
                ),
                "aggregation_tasks": len(
                    analytics_aggregation_service._aggregation_tasks
                ),
            },
            "websocket_broadcasting": {
                "status": (
                    "running" if analytics_websocket_manager._running else "stopped"
                ),
                "active_connections": len(
                    analytics_websocket_manager.active_connections
                ),
            },
            "database": "connected",  # Simplified for now
        }

        return health_status

    except Exception as e:
        logger.error(f"Error performing analytics health check: {e}")
        return {"error": str(e)}


# Export the lifespan context manager for FastAPI
__all__ = [
    "analytics_lifespan",
    "initialize_analytics",
    "shutdown_analytics",
    "populate_sample_data",
    "health_check",
]
