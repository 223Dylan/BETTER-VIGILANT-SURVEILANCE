from prometheus_client import Counter, Gauge, Histogram, start_http_server
import psutil
import time
from typing import Dict, Optional
import threading

class SystemMonitor:
    """System monitoring using Prometheus metrics."""
    
    def __init__(self, port: int = 8000):
        # Camera metrics
        self.active_cameras = Gauge('active_cameras', 'Number of active cameras')
        self.camera_fps = Gauge('camera_fps', 'Frames per second per camera', ['camera_id'])
        self.camera_latency = Histogram('camera_latency', 'Processing latency per camera', ['camera_id'])
        self.camera_errors = Counter('camera_errors', 'Error count per camera', ['camera_id', 'error_type'])
        
        # System metrics
        self.cpu_usage = Gauge('cpu_usage', 'CPU usage percentage')
        self.memory_usage = Gauge('memory_usage', 'Memory usage percentage')
        self.gpu_usage = Gauge('gpu_usage', 'GPU usage percentage')
        self.disk_usage = Gauge('disk_usage', 'Disk usage percentage')
        
        # Model metrics
        self.model_inference_time = Histogram('model_inference_time', 'Model inference time in seconds', ['camera_id'])
        self.model_confidence = Gauge('model_confidence', 'Model confidence score', ['camera_id'])
        
        # Start Prometheus metrics server
        start_http_server(port)
        
        # Start background monitoring
        self._stop_event = threading.Event()
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while not self._stop_event.is_set():
            try:
                # Update system metrics
                self.cpu_usage.set(psutil.cpu_percent())
                self.memory_usage.set(psutil.virtual_memory().percent)
                self.disk_usage.set(psutil.disk_usage('/').percent)
                
                # TODO: Add GPU monitoring if available
                # self.gpu_usage.set(get_gpu_usage())
                
                time.sleep(5)  # Update every 5 seconds
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
    
    def record_camera_metrics(self, camera_id: str, fps: float, latency: float):
        """Record metrics for a specific camera."""
        self.camera_fps.labels(camera_id=camera_id).set(fps)
        self.camera_latency.labels(camera_id=camera_id).observe(latency)
    
    def record_model_metrics(self, camera_id: str, inference_time: float, confidence: float):
        """Record model-related metrics."""
        self.model_inference_time.labels(camera_id=camera_id).observe(inference_time)
        self.model_confidence.labels(camera_id=camera_id).set(confidence)
    
    def record_error(self, camera_id: str, error_type: str):
        """Record an error occurrence."""
        self.camera_errors.labels(camera_id=camera_id, error_type=error_type).inc()
    
    def update_active_cameras(self, count: int):
        """Update the count of active cameras."""
        self.active_cameras.set(count)
    
    def stop(self):
        """Stop the monitoring loop."""
        self._stop_event.set()
        self._monitor_thread.join()

# Global monitor instance
system_monitor: Optional[SystemMonitor] = None

def init_monitoring(port: int = 8000) -> SystemMonitor:
    """Initialize the system monitor."""
    global system_monitor
    if system_monitor is None:
        system_monitor = SystemMonitor(port)
    return system_monitor

def get_monitor() -> SystemMonitor:
    """Get the global monitor instance."""
    if system_monitor is None:
        raise RuntimeError("Monitoring not initialized. Call init_monitoring first.")
    return system_monitor 