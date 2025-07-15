from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml
from loguru import logger
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from src.database.models.base import get_db
from src.database.models.camera import Camera
from src.utils.config import CameraConfig


class CameraDatabaseService:
    """Service for managing camera configurations in database."""

    def __init__(self):
        # Remove persistent session - use fresh sessions for each operation
        pass

    def get_session(self) -> Session:
        """Get a new database session for each operation."""
        return next(get_db())

    def close_session(self):
        """Close database session - no longer needed since we use fresh sessions."""
        pass

    def get_all_cameras(self) -> List[Camera]:
        """Get all cameras from database."""
        session = self.get_session()
        try:
            cameras = session.query(Camera).all()
            logger.info(f"Retrieved {len(cameras)} cameras from database")
            return cameras
        except Exception as e:
            logger.error(f"Error retrieving cameras: {e}")
            return []
        finally:
            session.close()

    def get_camera_by_id(self, camera_id: str) -> Optional[Camera]:
        """Get camera by ID."""
        session = self.get_session()
        try:
            camera = session.query(Camera).filter(Camera.id == camera_id).first()
            return camera
        except Exception as e:
            logger.error(f"Error retrieving camera {camera_id}: {e}")
            return None
        finally:
            session.close()

    def get_enabled_cameras(self) -> List[Camera]:
        """Get only enabled cameras."""
        session = self.get_session()
        try:
            cameras = session.query(Camera).filter(Camera.enabled == True).all()
            logger.info(f"Retrieved {len(cameras)} enabled cameras from database")
            return cameras
        except Exception as e:
            logger.error(f"Error retrieving enabled cameras: {e}")
            return []
        finally:
            session.close()

    def create_camera(self, camera: Camera) -> bool:
        """Create new camera configuration."""
        session = self.get_session()
        try:
            session.add(camera)
            session.commit()
            logger.info(f"Created camera: {camera.id}")
            return True
        except Exception as e:
            logger.error(f"Error creating camera {camera.id}: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def update_camera(self, camera_id: str, updates: Dict[str, Any]) -> bool:
        """Update camera configuration."""
        session = self.get_session()
        try:
            camera = session.query(Camera).filter(Camera.id == camera_id).first()

            if not camera:
                logger.warning(f"Camera {camera_id} not found for update")
                return False

            # Update fields
            for key, value in updates.items():
                if hasattr(camera, key):
                    setattr(camera, key, value)
                    logger.debug(f"Updated {camera_id}.{key} = {value}")

            camera.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Successfully updated camera: {camera_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating camera {camera_id}: {e}")
            try:
                session.rollback()
            except:
                pass  # Ignore rollback errors if session is already closed
            return False
        finally:
            session.close()

    def delete_camera(self, camera_id: str) -> bool:
        """Delete camera configuration."""
        session = self.get_session()
        try:
            camera = session.query(Camera).filter(Camera.id == camera_id).first()

            if not camera:
                logger.warning(f"Camera {camera_id} not found for deletion")
                return False

            session.delete(camera)
            session.commit()
            logger.info(f"Deleted camera: {camera_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting camera {camera_id}: {e}")
            try:
                session.rollback()
            except:
                pass  # Ignore rollback errors if session is already closed
            return False
        finally:
            session.close()

    def update_camera_status(
        self, camera_id: str, status: str, error_message: str = None
    ):
        """Update camera runtime status."""
        session = self.get_session()
        try:
            camera = session.query(Camera).filter(Camera.id == camera_id).first()

            if camera:
                camera.status = status
                camera.error_message = error_message
                if status == "active":
                    camera.last_online = datetime.utcnow()
                session.commit()
                logger.debug(f"Updated camera {camera_id} status to {status}")

        except Exception as e:
            logger.error(f"Error updating camera status for {camera_id}: {e}")
            try:
                session.rollback()
            except:
                pass  # Ignore rollback errors if session is already closed
        finally:
            session.close()

    def migrate_from_yaml_config(self, config_file_path: str) -> bool:
        """Migrate existing YAML configuration to database."""
        try:
            # Load existing config
            with open(config_file_path, "r") as file:
                config = yaml.safe_load(file)

            # Handle both list and dict format for cameras
            cameras_config = config.get("cameras", [])
            migrated_count = 0

            # Check if cameras is a list (your current format)
            if isinstance(cameras_config, list):
                logger.info(f"Found {len(cameras_config)} cameras in list format")

                for camera_config in cameras_config:
                    camera_id = camera_config.get("id")
                    if not camera_id:
                        logger.warning(f"Skipping camera without ID: {camera_config}")
                        continue

                    # Check if camera already exists
                    existing_camera = self.get_camera_by_id(camera_id)

                    if not existing_camera:
                        # Create new camera from config
                        camera = self._create_camera_from_list_config(camera_config)
                        if camera and self.create_camera(camera):
                            migrated_count += 1
                    else:
                        logger.info(
                            f"Camera {camera_id} already exists in database, skipping"
                        )

            # Handle dict format (legacy support)
            elif isinstance(cameras_config, dict):
                logger.info(f"Found {len(cameras_config)} cameras in dict format")

                for camera_id, camera_config in cameras_config.items():
                    existing_camera = self.get_camera_by_id(camera_id)

                    if not existing_camera:
                        camera = Camera.from_config_dict(camera_id, camera_config)
                        if self.create_camera(camera):
                            migrated_count += 1
                    else:
                        logger.info(
                            f"Camera {camera_id} already exists in database, skipping"
                        )

            logger.info(
                f"Successfully migrated {migrated_count} cameras from YAML to database"
            )
            return True

        except Exception as e:
            logger.error(f"Error migrating cameras from YAML config: {e}")
            return False

    def _create_camera_from_list_config(self, camera_config: dict) -> Optional[Camera]:
        """Create Camera instance from list-style YAML config."""
        try:
            camera_id = camera_config.get("id")
            if not camera_id:
                return None

            # Map YAML fields to database fields
            resolution = camera_config.get("resolution", {})
            credentials = camera_config.get("credentials", {})

            # Determine if camera is enabled based on status
            status = camera_config.get("status", "inactive")
            enabled = status == "active"

            # Create advanced settings from extra fields
            advanced_settings = {
                "location_id": camera_config.get("location_id"),
                "zone_name": camera_config.get("zone_name"),
                "camera_type": camera_config.get("camera_type"),
                "credentials": credentials if credentials else None,
            }

            camera = Camera(
                id=camera_id,
                name=camera_config.get("name", camera_id),
                description=f"Migrated from YAML config - {camera_config.get('camera_type', 'unknown')} camera",
                enabled=enabled,
                source=str(camera_config.get("source", 0)),
                source_type=self._map_camera_type(
                    camera_config.get("camera_type", "usb")
                ),
                fps=camera_config.get("fps", 15),
                resolution_width=resolution.get("width", 640),
                resolution_height=resolution.get("height", 480),
                detection_enabled=True,  # Default to enabled
                detection_sensitivity=0.5,  # Default sensitivity
                recording_enabled=False,  # Default to disabled
                location=camera_config.get("location_id"),
                zone=camera_config.get("zone_name"),
                advanced_settings=advanced_settings,
                status="stopped",  # Default to stopped, will be updated when started
            )

            logger.info(f"Created camera object for {camera_id}")
            return camera

        except Exception as e:
            logger.error(f"Error creating camera from config {camera_config}: {e}")
            return None

    def _map_camera_type(self, camera_type: str) -> str:
        """Map YAML camera_type to database source_type."""
        mapping = {"usb": "webcam", "ip": "rtsp", "file": "file"}
        return mapping.get(camera_type.lower(), "webcam")

    def convert_to_camera_config(self, camera: Camera) -> CameraConfig:
        """Convert database Camera to CameraConfig object."""
        # Extract advanced settings for additional fields
        advanced_settings = camera.advanced_settings or {}

        # Convert source back to appropriate type
        source = camera.source
        if camera.source_type == "webcam" and str(source).isdigit():
            source = int(source)  # Convert back to integer for USB cameras

        # Map database source_type back to camera_type
        camera_type = self._reverse_map_camera_type(camera.source_type)

        return CameraConfig(
            id=camera.id,
            name=camera.name,
            location_id=advanced_settings.get(
                "location_id", camera.location or "unknown"
            ),
            zone_name=advanced_settings.get("zone_name", camera.zone or "default"),
            source=source,
            camera_type=advanced_settings.get("camera_type", camera_type),
            enabled=camera.enabled,
            fps=camera.fps,
            resolution_width=camera.resolution_width,
            resolution_height=camera.resolution_height,
            credentials=advanced_settings.get("credentials"),
            # Pass individual camera brightness to preprocessing
            preprocessing={"brightness": camera.brightness},
        )

    def _reverse_map_camera_type(self, source_type: str) -> str:
        """Map database source_type back to YAML camera_type."""
        mapping = {"webcam": "usb", "rtsp": "ip", "file": "file"}
        return mapping.get(source_type.lower(), "usb")


# Global service instance
camera_db_service = CameraDatabaseService()
