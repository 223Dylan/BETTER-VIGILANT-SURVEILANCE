import asyncio
import threading
import time
from typing import Dict, Any
from loguru import logger
from src.services.alert_manager import get_alert_manager

# Global event loop for WebSocket operations
_websocket_loop = None
_websocket_thread = None

def start_websocket_loop():
    """Start the WebSocket event loop in a separate thread."""
    global _websocket_loop, _websocket_thread
    
    def run_loop():
        global _websocket_loop
        try:
            _websocket_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_websocket_loop)
            logger.info("🔄 WebSocket event loop thread started")
            _websocket_loop.run_forever()
        except Exception as e:
            logger.error(f"[ERROR] Error in WebSocket event loop: {e}")
    
    if _websocket_thread is None or not _websocket_thread.is_alive():
        _websocket_thread = threading.Thread(target=run_loop, daemon=True)
        _websocket_thread.start()
        # Give the loop a moment to start
        time.sleep(0.1)
        logger.info("🔄 WebSocket event loop started in background thread")

def route_prediction_to_websocket(camera_id: str, prediction_result: Dict[Any, Any]):
    """Route a prediction result to the appropriate WebSocket connections."""
    global _websocket_loop
    
    try:
        # Ensure WebSocket loop is running
        if _websocket_loop is None:
            start_websocket_loop()
        
        # Process prediction through alert manager
        alert_manager = get_alert_manager()
        alert_id = alert_manager.process_prediction(prediction_result)
        
        if alert_id:
            logger.info(f"[ALERT] Created alert {alert_id} for camera {camera_id}")
        
        # Format for frontend compatibility
        alert_data = format_prediction_for_alert(prediction_result)
        
        # Add alert ID to the data if alert was created
        if alert_id:
            alert_data['alert_id'] = alert_id
        
        # Schedule the WebSocket broadcast
        if _websocket_loop and not _websocket_loop.is_closed():
            future = asyncio.run_coroutine_threadsafe(
                send_prediction_to_websocket(camera_id, alert_data),
                _websocket_loop
            )
            # Don't wait for result to avoid blocking Celery worker
            logger.info(f"[SCHEDULED] Scheduled prediction broadcast for camera {camera_id}")
        else:
            logger.error("[ERROR] WebSocket loop is not available")
            
    except Exception as e:
        logger.error(f"[ERROR] Error routing prediction to WebSocket for {camera_id}: {e}")

def format_prediction_for_alert(prediction_result: Dict[Any, Any]) -> Dict[str, Any]:
    """Format a Celery prediction result for the frontend alert system."""
    
    confidence = prediction_result.get('confidence', 0.0)
    is_shoplifting = prediction_result.get('is_shoplifting', False)
    
    # Determine alert type and message based on prediction
    if is_shoplifting and confidence > 0.7:
        alert_type = 'shoplifting'
        message = f"[HIGH CONFIDENCE] SHOPLIFTING DETECTED - High Confidence"
    elif is_shoplifting and confidence > 0.5:
        alert_type = 'shoplifting'
        message = f"[WARNING] Potential shoplifting detected"
    elif confidence > 0.3:
        alert_type = 'object_detection' 
        message = f"[SUSPICIOUS] Suspicious activity detected"
    else:
        alert_type = 'motion'
        message = f"[NORMAL] Normal activity monitored"
    
    # Format for frontend
    alert_data = {
        'type': alert_type,
        'confidence': confidence,
        'message': message,
        'is_shoplifting': is_shoplifting,
        'timestamp': prediction_result.get('timestamp'),
        'sequence_stats': prediction_result.get('sequence_stats', {}),
        'model_label': prediction_result.get('label', 0),
        'camera_id': prediction_result.get('camera_id')
    }
    
    logger.info(f"[ALERT] Formatted alert: {alert_type} (confidence: {confidence:.2f}) for camera {prediction_result.get('camera_id')}")
    return alert_data

async def send_prediction_to_websocket(camera_id: str, alert_data: Dict[str, Any]):
    """Send prediction data to WebSocket connections for a specific camera."""
    try:
        # Import here to avoid circular imports
        from src.websocket_manager import websocket_manager
        
        # Broadcast to prediction WebSocket connections
        await websocket_manager.broadcast_prediction(camera_id, alert_data)
        
        logger.info(f"[SUCCESS] Successfully sent prediction to WebSocket for camera {camera_id}")
        
    except Exception as e:
        logger.error(f"[ERROR] Error sending prediction to WebSocket for {camera_id}: {e}")

# Initialize the WebSocket loop when module is imported
start_websocket_loop() 