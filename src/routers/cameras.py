import os
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from loguru import logger

from src.auth.permissions import (
    Permission,
    get_current_user,
    require_any_permission,
    require_permission,
)
from src.database.models.camera import Camera
from src.database.models.user import User
from src.services.camera_db_service import camera_db_service

router = APIRouter(prefix="/cameras", tags=["cameras"])

# Global controller instance set by main.py
camera_controller = None


def get_controller():
    """Get camera controller instance."""
    if not camera_controller:
        raise HTTPException(status_code=500, detail="Camera controller not initialized")
    return camera_controller


@router.get("/available")
@require_permission(Permission.CAMERA_VIEW)
async def get_available_cameras(current_user: User = Depends(get_current_user)):
    """Get all cameras from database."""
    try:
        cameras = camera_db_service.get_all_cameras()
        return [camera.to_dict() for camera in cameras]
    except Exception as e:
        logger.error(f"Error getting cameras: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cameras")


@router.get("/status")
@require_permission(Permission.CAMERA_VIEW)
async def get_cameras_status(current_user: User = Depends(get_current_user)):
    """Get runtime status of all cameras."""
    try:
        controller = get_controller()
        return controller.get_all_camera_status()
    except Exception as e:
        logger.error(f"Error getting camera status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get camera status")


@router.post("/{camera_id}/start")
@require_permission(Permission.CAMERA_CONTROL)
async def start_camera(camera_id: str, current_user: User = Depends(get_current_user)):
    """Start a specific camera."""
    try:
        controller = get_controller()
        success = controller.start_camera(camera_id)
        if success:
            return {"status": "success", "message": f"Camera '{camera_id}' started."}
        else:
            raise HTTPException(
                status_code=400, detail=f"Failed to start camera '{camera_id}'"
            )
    except Exception as e:
        logger.error(f"Error starting camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{camera_id}/stop")
@require_permission(Permission.CAMERA_CONTROL)
async def stop_camera(camera_id: str, current_user: User = Depends(get_current_user)):
    """Stop a specific camera."""
    try:
        controller = get_controller()
        success = controller.stop_camera(camera_id)
        if success:
            return {"status": "success", "message": f"Camera '{camera_id}' stopped."}
        else:
            raise HTTPException(
                status_code=400, detail=f"Failed to stop camera '{camera_id}'"
            )
    except Exception as e:
        logger.error(f"Error stopping camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/")
@require_permission(Permission.CAMERA_CREATE)
async def create_camera(
    camera_data: Dict[str, Any], current_user: User = Depends(get_current_user)
):
    """Create new camera configuration."""
    try:
        # Validate required fields
        required_fields = ["id", "name", "source", "source_type"]
        for field in required_fields:
            if field not in camera_data or not camera_data[field]:
                raise HTTPException(
                    status_code=400, detail=f"Missing required field: {field}"
                )

        # Check if camera ID already exists
        existing_camera = camera_db_service.get_camera_by_id(camera_data["id"])
        if existing_camera:
            raise HTTPException(
                status_code=409,
                detail=f"Camera with ID '{camera_data['id']}' already exists",
            )

        # Validate source_type
        valid_source_types = ["webcam", "rtsp", "file"]
        if camera_data["source_type"] not in valid_source_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid source_type. Must be one of: {valid_source_types}",
            )

        # Convert and validate source based on type
        if camera_data["source_type"] == "webcam":
            try:
                # For webcam, source should be an integer (device index)
                camera_data["source"] = str(int(camera_data["source"]))
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=400,
                    detail="For webcam source_type, source must be a valid integer device index",
                )

        # Set defaults for optional fields
        camera_data.setdefault("enabled", True)
        camera_data.setdefault("fps", 15)
        camera_data.setdefault("detection_enabled", True)  # Always enabled
        camera_data.setdefault("detection_sensitivity", 0.5)
        camera_data.setdefault("recording_enabled", False)  # Always disabled
        camera_data.setdefault("status", "stopped")

        # Handle resolution
        resolution = camera_data.get("resolution", {})
        camera_data["resolution_width"] = resolution.get("width", 640)
        camera_data["resolution_height"] = resolution.get("height", 480)

        # Remove nested resolution object as it's not part of the database model
        if "resolution" in camera_data:
            del camera_data["resolution"]

        # Create camera instance
        camera = Camera(**camera_data)
        success = camera_db_service.create_camera(camera)

        if success:
            logger.info(f"Successfully created camera: {camera_data['id']}")
            return {
                "status": "success",
                "message": "Camera created successfully",
                "camera": camera.to_dict(),
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create camera")

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error creating camera: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{camera_id}")
@require_permission(Permission.CAMERA_UPDATE)
async def update_camera(
    camera_id: str,
    updates: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    """Update camera configuration in database."""
    try:
        logger.info(f"Updating camera {camera_id} with data: {updates}")

        # Validate brightness value if provided
        if "brightness" in updates:
            brightness = updates["brightness"]
            if (
                not isinstance(brightness, (int, float))
                or brightness < 0.0
                or brightness > 2.0
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Brightness must be a number between 0.0 and 2.0",
                )

        # Use controller to update camera (handles restart if needed)
        controller = get_controller()
        success = controller.update_camera_config(camera_id, updates)

        if success:
            logger.info(f"Successfully updated camera {camera_id}")
            return {"status": "success", "message": f"Camera '{camera_id}' updated"}
        else:
            logger.warning(f"Camera {camera_id} not found for update")
            raise HTTPException(
                status_code=404, detail=f"Camera '{camera_id}' not found"
            )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error updating camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{camera_id}/brightness")
@require_permission(Permission.CAMERA_CONFIG)
async def update_camera_brightness(
    camera_id: str,
    brightness_data: Dict[str, float],
    current_user: User = Depends(get_current_user),
):
    """Update individual camera brightness."""
    try:
        brightness = brightness_data.get("brightness")
        if brightness is None:
            raise HTTPException(status_code=400, detail="Brightness value is required")

        if (
            not isinstance(brightness, (int, float))
            or brightness < 0.0
            or brightness > 2.0
        ):
            raise HTTPException(
                status_code=400,
                detail="Brightness must be a number between 0.0 and 2.0",
            )

        # Use controller to update camera (handles restart if needed)
        controller = get_controller()
        success = controller.update_camera_config(camera_id, {"brightness": brightness})

        if success:
            logger.info(
                f"Successfully updated brightness for camera {camera_id} to {brightness}"
            )
            return {
                "status": "success",
                "message": f"Camera '{camera_id}' brightness updated to {brightness}",
            }
        else:
            raise HTTPException(
                status_code=404, detail=f"Camera '{camera_id}' not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating camera brightness {camera_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{camera_id}")
@require_permission(Permission.CAMERA_DELETE)
async def delete_camera(camera_id: str, current_user: User = Depends(get_current_user)):
    """Delete camera configuration."""
    try:
        controller = get_controller()
        success = controller.delete_camera(camera_id)
        if success:
            return {"status": "success", "message": f"Camera '{camera_id}' deleted"}
        else:
            raise HTTPException(
                status_code=404, detail=f"Camera '{camera_id}' not found"
            )
    except Exception as e:
        logger.error(f"Error deleting camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/upload-video")
@require_any_permission([Permission.CAMERA_CREATE, Permission.CAMERA_UPDATE])
async def upload_video_file(
    file: UploadFile = File(...), current_user: User = Depends(get_current_user)
):
    """Upload a video file for camera source."""
    try:
        # Validate file type
        allowed_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv"}
        file_extension = (
            os.path.splitext(file.filename)[1].lower() if file.filename else ""
        )

        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}",
            )

        # Create uploads directory if it doesn't exist
        upload_dir = "uploads/videos"
        os.makedirs(upload_dir, exist_ok=True)

        # Generate unique filename
        import uuid

        unique_id = str(uuid.uuid4())[:8]
        safe_filename = f"{unique_id}_{file.filename}"
        file_path = os.path.join(upload_dir, safe_filename)

        # Save the file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Return the file path for use as camera source
        logger.info(f"Video file uploaded successfully: {file_path}")
        return {
            "status": "success",
            "message": "Video file uploaded successfully",
            "file_path": file_path,
            "original_filename": file.filename,
            "size_bytes": len(content),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading video file: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload video file")


def initialize_controller(controller):
    """Initialize camera controller for this router."""
    global camera_controller
    camera_controller = controller
