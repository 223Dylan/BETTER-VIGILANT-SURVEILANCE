import multiprocessing
import time
from typing import Dict, List, Optional
from loguru import logger
from src.utils.config import CameraConfig
from src.camera_pipeline import CameraPipelineProcess
from src.services.camera_db_service import camera_db_service
from src.database.models.camera import Camera

class CameraController:
    """Manages the lifecycle of camera pipeline processes using database configuration."""

    def __init__(self, shared_data: Dict):
        """
        Initializes the CameraController with database-backed configuration.
        Args:
            shared_data: A multiprocessing Manager dict for sharing data between processes.
        """
        self.shared_data = shared_data
        self.processes: Dict[str, CameraPipelineProcess] = {}
        self.camera_status: Dict[str, str] = {}
        
        # Caching for reducing database queries
        self._status_cache: Dict[str, str] = {}
        self._cache_timestamp: float = 0
        self._cache_duration: float = 2.0  # Cache for 2 seconds
        
        # Load cameras from database
        self._load_cameras_from_database()
        
    def _load_cameras_from_database(self):
        """Load camera configurations from database."""
        try:
            cameras = camera_db_service.get_all_cameras()
            logger.info(f"Loaded {len(cameras)} cameras from database")
            
            # Initialize status tracking
            for camera in cameras:
                self.camera_status[camera.id] = camera.status or "stopped"
                
        except Exception as e:
            logger.error(f"Error loading cameras from database: {e}")

    def get_available_cameras(self) -> List[Dict]:
        """Get all available cameras from database."""
        try:
            cameras = camera_db_service.get_all_cameras()
            return [camera.to_dict() for camera in cameras]
        except Exception as e:
            logger.error(f"Error getting available cameras: {e}")
            return []

    def get_camera_status(self, camera_id: str) -> str:
        """Get current status of a camera."""
        if camera_id in self.processes and self.processes[camera_id].is_alive():
            return "active"
        
        # Check database status
        camera = camera_db_service.get_camera_by_id(camera_id)
        return camera.status if camera else "unknown"

    def start_camera(self, camera_id: str) -> bool:
        """Starts the pipeline for a specific camera using database config."""
        try:
            # Get camera from database
            camera = camera_db_service.get_camera_by_id(camera_id)
            if not camera:
                logger.error(f"Camera '{camera_id}' not found in database")
                return False

            if camera_id in self.processes and self.processes[camera_id].is_alive():
                logger.warning(f"Camera '{camera_id}' is already running")
                return True

            # Enable the camera in database when starting (this is the key fix)
            if not camera.enabled:
                logger.info(f"Enabling camera '{camera_id}' as part of start process")
                camera_db_service.update_camera(camera_id, {"enabled": True})
                # Reload camera data to get updated config
                camera = camera_db_service.get_camera_by_id(camera_id)

            # Convert to CameraConfig
            camera_config = camera_db_service.convert_to_camera_config(camera)
            
            # Update status to starting
            camera_db_service.update_camera_status(camera_id, "starting")
            
            # Create and start process
            process = CameraPipelineProcess(camera_config, self.shared_data)
            process.start()
            
            # Wait a moment to check if process started successfully
            process.join(timeout=2)
            
            if process.is_alive():
                self.processes[camera_id] = process
                self.camera_status[camera_id] = "active"
                camera_db_service.update_camera_status(camera_id, "active")
                self._invalidate_cache()  # Invalidate cache on status change
                logger.info(f"Started camera process for {camera_id}")
                return True
            else:
                self.camera_status[camera_id] = "error"
                camera_db_service.update_camera_status(camera_id, "error", "Failed to start process")
                self._invalidate_cache()  # Invalidate cache on status change
                logger.error(f"Failed to start camera process for {camera_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting camera {camera_id}: {e}")
            camera_db_service.update_camera_status(camera_id, "error", str(e))
            return False

    def stop_camera(self, camera_id: str) -> bool:
        """Stops the pipeline for a specific camera and updates database."""
        if camera_id not in self.processes or not self.processes[camera_id].is_alive():
            logger.warning(f"Camera '{camera_id}' is not running.")
            camera_db_service.update_camera_status(camera_id, "stopped")
            # Disable camera when stopping
            camera_db_service.update_camera(camera_id, {"enabled": False})
            if camera_id in self.camera_status:
                self.camera_status[camera_id] = "stopped"
            self._invalidate_cache()  # Invalidate cache on status change
            return True

        try:
            process = self.processes[camera_id]
            process.stop()
            process.join(timeout=10)

            if process.is_alive():
                logger.warning(f"Process for camera '{camera_id}' did not terminate gracefully. Forcing termination.")
                process.terminate()
                process.join()

            # Clear stream buffer
            from src.api.video_stream import stream_manager
            if stream_manager:
                stream_manager.clear_camera_buffer(camera_id)

            del self.processes[camera_id]
            self.camera_status[camera_id] = "stopped"
            camera_db_service.update_camera_status(camera_id, "stopped")
            # Disable camera when stopping
            camera_db_service.update_camera(camera_id, {"enabled": False})
            self._invalidate_cache()  # Invalidate cache on status change
            logger.info(f"Stopped camera '{camera_id}'")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping camera {camera_id}: {e}")
            camera_db_service.update_camera_status(camera_id, "error", str(e))
            return False

    def get_all_camera_status(self) -> Dict[str, str]:
        """Get status of all cameras with caching to reduce DB queries."""
        current_time = time.time()
        
        # Return cached result if still valid
        if (current_time - self._cache_timestamp) < self._cache_duration and self._status_cache:
            return self._status_cache.copy()
        
        # Rebuild cache
        status_dict = {}
        cameras = camera_db_service.get_all_cameras()
        
        for camera in cameras:
            if camera.id in self.processes and self.processes[camera.id].is_alive():
                status_dict[camera.id] = "active"
                # Update database if needed
                if camera.status != "active":
                    camera_db_service.update_camera_status(camera.id, "active")
            else:
                status_dict[camera.id] = camera.status or "stopped"
        
        # Update cache
        self._status_cache = status_dict.copy()
        self._cache_timestamp = current_time
        
        return status_dict
    
    def _invalidate_cache(self):
        """Invalidate the status cache to force refresh on next request."""
        self._cache_timestamp = 0
        self._status_cache = {}

    def stop_all_cameras(self):
        """Stops all camera processes and updates database."""
        logger.info("Stopping all camera processes...")
        for camera_id in list(self.processes.keys()):
            self.stop_camera(camera_id)
        logger.info("All camera processes stopped.")
        
        # Close database session
        camera_db_service.close_session()

    def add_camera(self, camera_data: Dict) -> bool:
        """Add new camera to database."""
        try:
            camera = Camera(**camera_data)
            success = camera_db_service.create_camera(camera)
            if success:
                self.camera_status[camera.id] = "stopped"
            return success
        except Exception as e:
            logger.error(f"Error adding camera: {e}")
            return False

    def update_camera_config(self, camera_id: str, updates: Dict) -> bool:
        """Update camera configuration in database and apply changes dynamically."""
        try:
            # Check if camera is currently running
            is_running = camera_id in self.processes and self.processes[camera_id].is_alive()
            
            # Update database first
            success = camera_db_service.update_camera(camera_id, updates)
            
            if success and is_running:
                # Handle brightness updates dynamically (no restart needed)
                if 'brightness' in updates:
                    brightness_key = f"brightness_update_{camera_id}"
                    self.shared_data[brightness_key] = updates['brightness']
                    logger.info(f"Sent dynamic brightness update: {updates['brightness']} for camera '{camera_id}'")
                
                # Other settings still require restart
                restart_needed_keys = ['fps', 'resolution_width', 'resolution_height']
                restart_needed = any(key in updates for key in restart_needed_keys)
                
                if restart_needed:
                    logger.info(f"Restarting camera '{camera_id}' due to configuration change requiring restart")
                    # Stop and restart camera to apply new settings
                    self.stop_camera(camera_id)
                    # Small delay to ensure clean shutdown
                    import time
                    time.sleep(0.5)
                    self.start_camera(camera_id)
            
            return success
        except Exception as e:
            logger.error(f"Error updating camera config {camera_id}: {e}")
            return False

    def delete_camera(self, camera_id: str) -> bool:
        """Delete camera from database."""
        # Stop camera if running
        if camera_id in self.processes:
            self.stop_camera(camera_id)
        
        success = camera_db_service.delete_camera(camera_id)
        if success and camera_id in self.camera_status:
            del self.camera_status[camera_id]
        return success 