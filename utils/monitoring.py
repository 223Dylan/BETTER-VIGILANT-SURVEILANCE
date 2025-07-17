from prometheus_client import Counter, Gauge, Histogram, start_http_server, CollectorRegistry, REGISTRY
import psutil
import time
from typing import Dict, Optional
import threading

class SystemMonitor:
    """System monitoring using Prometheus metrics."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, port: int = 8000):
        if cls._instance is None:
            cls._instance = super(SystemMonitor, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, port: int = 8000):
        if self._initialized:
            return
        
        self.port = port
        self._stop_event = threading.Event()
        self._monitor_thread = None
        
        try:
            # Create metrics with collision handling
            self.active_cameras = self._create_or_get_gauge('active_cameras', 'Number of active cameras')
            self.camera_fps = self._create_or_get_gauge('camera_fps', 'Frames per second per camera', ['camera_id'])
            self.camera_latency = self._create_or_get_histogram('camera_latency', 'Processing latency per camera', ['camera_id'])
            self.camera_errors = self._create_or_get_counter('camera_errors', 'Error count per camera', ['camera_id', 'error_type'])
            
            # System metrics
            self.cpu_usage = self._create_or_get_gauge('cpu_usage', 'CPU usage percentage')
            self.memory_usage = self._create_or_get_gauge('memory_usage', 'Memory usage percentage')
            self.gpu_usage = self._create_or_get_gauge('gpu_usage', 'GPU usage percentage')
            self.disk_usage = self._create_or_get_gauge('disk_usage', 'Disk usage percentage')
            
            # Model metrics
            self.model_inference_time = self._create_or_get_histogram('model_inference_time', 'Model inference time in seconds', ['camera_id'])
            self.model_confidence = self._create_or_get_gauge('model_confidence', 'Model confidence score', ['camera_id'])
            
            # Start Prometheus metrics server
            try:
                start_http_server(port)
                print(f"Prometheus metrics server started on port {port}")
            except OSError as e:
                if "Address already in use" in str(e):
                    print(f"Prometheus metrics server already running on port {port}")
                else:
                    raise
            
            # Start background monitoring
            self._start_monitoring()
            
        except Exception as e:
            print(f"Warning: Failed to initialize some Prometheus metrics: {e}")
        
        SystemMonitor._initialized = True
    
    def _create_or_get_gauge(self, name: str, description: str, labelnames: list = None):
        """Create a Gauge or return existing one if already registered."""
        try:
            if labelnames:
                return Gauge(name, description, labelnames)
            else:
                return Gauge(name, description)
        except ValueError as e:
            if "Duplicated timeseries" in str(e):
                # Return existing metric from registry
                for collector in list(REGISTRY._collector_to_names.keys()):
                    if hasattr(collector, '_name') and collector._name == name:
                        return collector
                # If not found, create with a different name
                return Gauge(f"{name}_alt", description, labelnames or [])
            raise
    
    def _create_or_get_histogram(self, name: str, description: str, labelnames: list = None):
        """Create a Histogram or return existing one if already registered."""
        try:
            if labelnames:
                return Histogram(name, description, labelnames)
            else:
                return Histogram(name, description)
        except ValueError as e:
            if "Duplicated timeseries" in str(e):
                # Return existing metric from registry
                for collector in list(REGISTRY._collector_to_names.keys()):
                    if hasattr(collector, '_name') and collector._name == name:
                        return collector
                # If not found, create with a different name
                return Histogram(f"{name}_alt", description, labelnames or [])
            raise
    
    def _create_or_get_counter(self, name: str, description: str, labelnames: list = None):
        """Create a Counter or return existing one if already registered."""
        try:
            if labelnames:
                return Counter(name, description, labelnames)
            else:
                return Counter(name, description)
        except ValueError as e:
            if "Duplicated timeseries" in str(e):
                # Return existing metric from registry
                for collector in list(REGISTRY._collector_to_names.keys()):
                    if hasattr(collector, '_name') and collector._name == name:
                        return collector
                # If not found, create with a different name
                return Counter(f"{name}_alt", description, labelnames or [])
            raise
    
    def _start_monitoring(self):
        """Start the background monitoring thread."""
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
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