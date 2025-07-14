import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import time

@dataclass
class PredictionMetrics:
    """Structure for prediction-related metrics."""
    confidence: float
    label: str
    is_shoplifting: bool
    prediction_time_ms: float
    sequence_frames: int
    model_version: str = "lrcn_160S_90_90Q"

@dataclass
class AlertMetrics:
    """Structure for alert-related metrics."""
    triggered: bool
    level: str
    threshold_used: float
    alert_type: str

@dataclass
class PerformanceMetrics:
    """Structure for system performance metrics."""
    fps_actual: float
    fps_target: float
    processing_latency_ms: float
    queue_depth: int
    dropped_frames: int
    memory_usage_mb: Optional[float] = None

class DetectionMetricsLogger:
    """Centralized logging for detection metrics that feeds into ELK stack."""
    
    def __init__(self):
        self.logger = logging.getLogger("detection_metrics")
        self.setup_elasticsearch_logger()
        
    def setup_elasticsearch_logger(self):
        """Setup structured logger for Elasticsearch ingestion."""
        # Create a specific handler for Elasticsearch metrics
        formatter = logging.Formatter('%(message)s')
        
        # Add handler that will send to Logstash/Elasticsearch
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_prediction_result(
        self, 
        camera_id: str, 
        prediction_result: Dict[str, Any], 
        processing_time: float,
        performance_data: Optional[Dict] = None
    ):
        """Log structured prediction metrics."""
        
        confidence = prediction_result.get('confidence', 0.0)
        is_shoplifting = prediction_result.get('is_shoplifting', False)
        
        # Create prediction metrics
        prediction_metrics = PredictionMetrics(
            confidence=confidence,
            label=prediction_result.get('label', 'unknown'),
            is_shoplifting=is_shoplifting,
            prediction_time_ms=processing_time * 1000,
            sequence_frames=prediction_result.get('sequence_length', 160)
        )
        
        # Create alert metrics
        alert_level = self._determine_alert_level(confidence, is_shoplifting)
        alert_metrics = AlertMetrics(
            triggered=confidence > 0.5 and is_shoplifting,
            level=alert_level,
            threshold_used=self._get_threshold_for_level(alert_level),
            alert_type=self._determine_alert_type(confidence, is_shoplifting)
        )
        
        # Structure the complete metrics payload
        metrics_payload = {
            "type": "detection_metrics",
            "camera_id": camera_id,
            "timestamp": datetime.utcnow().isoformat(),
            "prediction": asdict(prediction_metrics),
            "alert": asdict(alert_metrics),
            "performance": performance_data or {}
        }
        
        # Log as JSON for Logstash consumption
        self.logger.info(json.dumps(metrics_payload))
    
    def log_system_performance(
        self, 
        camera_id: str, 
        performance_metrics: PerformanceMetrics
    ):
        """Log system performance metrics."""
        
        metrics_payload = {
            "type": "system_performance",
            "camera_id": camera_id,
            "timestamp": datetime.utcnow().isoformat(),
            "performance": asdict(performance_metrics)
        }
        
        self.logger.info(json.dumps(metrics_payload))
    
    def log_detection_analytics(
        self, 
        camera_id: str, 
        time_window: str,
        analytics_data: Dict[str, Any]
    ):
        """Log aggregated detection analytics."""
        
        metrics_payload = {
            "type": "detection_analytics",
            "camera_id": camera_id,
            "timestamp": datetime.utcnow().isoformat(),
            "time_window": time_window,
            "metrics": analytics_data
        }
        
        self.logger.info(json.dumps(metrics_payload))
    
    def log_camera_health(
        self, 
        camera_id: str, 
        health_data: Dict[str, Any]
    ):
        """Log camera health and connectivity metrics."""
        
        metrics_payload = {
            "type": "camera_health",
            "camera_id": camera_id,
            "timestamp": datetime.utcnow().isoformat(),
            "health": health_data
        }
        
        self.logger.info(json.dumps(metrics_payload))
    
    def _determine_alert_level(self, confidence: float, is_shoplifting: bool) -> str:
        """Determine alert level based on confidence and prediction."""
        if not is_shoplifting:
            return "none"
        
        if confidence >= 0.9:
            return "critical"
        elif confidence >= 0.7:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        else:
            return "low"
    
    def _determine_alert_type(self, confidence: float, is_shoplifting: bool) -> str:
        """Determine the type of alert based on prediction."""
        if is_shoplifting and confidence > 0.7:
            return "shoplifting"
        elif is_shoplifting and confidence > 0.5:
            return "suspicious_activity"
        elif confidence > 0.3:
            return "object_detection"
        else:
            return "motion"
    
    def _get_threshold_for_level(self, level: str) -> float:
        """Get the threshold value for a given alert level."""
        thresholds = {
            "critical": 0.9,
            "high": 0.7,
            "medium": 0.5,
            "low": 0.3,
            "none": 0.0
        }
        return thresholds.get(level, 0.0)

# Global metrics logger instance
detection_metrics_logger = DetectionMetricsLogger()

def log_prediction_metrics(camera_id: str, prediction_result: Dict, processing_time: float, performance_data: Dict = None):
    """Convenience function for logging prediction metrics."""
    detection_metrics_logger.log_prediction_result(camera_id, prediction_result, processing_time, performance_data)

def log_system_metrics(camera_id: str, fps_actual: float, fps_target: float, latency_ms: float, queue_depth: int, dropped_frames: int):
    """Convenience function for logging system performance metrics."""
    performance = PerformanceMetrics(
        fps_actual=fps_actual,
        fps_target=fps_target,
        processing_latency_ms=latency_ms,
        queue_depth=queue_depth,
        dropped_frames=dropped_frames
    )
    detection_metrics_logger.log_system_performance(camera_id, performance)

def log_camera_health_metrics(camera_id: str, is_connected: bool, frame_rate: float, last_frame_time: float, error_count: int):
    """Convenience function for logging camera health metrics."""
    health_data = {
        "is_connected": is_connected,
        "current_fps": frame_rate,
        "last_frame_timestamp": last_frame_time,
        "error_count": error_count,
        "status": "online" if is_connected else "offline"
    }
    detection_metrics_logger.log_camera_health(camera_id, health_data) 