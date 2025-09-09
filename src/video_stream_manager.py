import asyncio
import json
import time
from collections import deque
from typing import Dict, Optional

import cv2
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger


class VideoStreamManager:
    """Manages frame buffering and processing for video streaming."""

    def __init__(self, buffer_size: int = 50):
        """Initialize the video stream manager."""
        self.buffer_size = buffer_size
        self.streams = {}  # camera_id -> deque of frames
        self.connections = {}  # camera_id -> WebSocket
        self._running = False
        self._initialized = False
        self._frames_processed = {}  # camera_id -> count
        self._frames_sent = {}  # camera_id -> count
        self._last_frame_time = {}  # camera_id -> timestamp
        self._fps = {}  # camera_id -> fps
        self._connection_status = {}  # camera_id -> status dict
        self._last_stats_time = {}  # camera_id -> last stats time
        self._frame_times = {}  # camera_id -> deque of frame times
        self._fps_window = 30  # Window size for FPS calculation
        self._min_frame_interval = (
            0.0  # Removed artificial rate limit - let system run at natural camera FPS
        )
        self._adaptive_interval = 0.0  # Dynamic interval based on buffer levels
        self._min_interval = 0.001  # Minimum interval to prevent CPU spinning
        self._max_interval = 0.1  # Maximum interval for slow consumption
        self._batch_size = 3  # Number of frames to send per batch
        self._max_batch_size = 5  # Maximum batch size
        self._last_frame_time = {}  # camera_id -> last frame time
        self._fps = {}  # camera_id -> current FPS
        self.frame_count = 0
        self.last_fps_log = 0

    def initialize(self) -> bool:
        """Initialize the stream manager."""
        try:
            self._initialized = True
            self._running = True
            logger.info("VideoStreamManager initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize VideoStreamManager: {e}")
            return False

    def process_frame(self, camera_id: str, frame: bytes) -> bool:
        """Process a frame and add it to the buffer."""
        if not self._running or not self._initialized:
            return False

        try:
            # Setup tracking for new cameras
            if camera_id not in self._frames_processed:
                self._frames_processed[camera_id] = 0
                self._last_frame_time[camera_id] = time.time()
                self._fps[camera_id] = 0
                logger.info(f"Initializing frame tracking for camera: {camera_id}")

            # Setup buffer for new cameras
            if camera_id not in self.streams:
                self.streams[camera_id] = deque(maxlen=self.buffer_size)
                logger.info(f"Initializing frame buffer for camera: {camera_id}")

            # Add frame to buffer with bulk dropping strategy
            current_size = len(self.streams[camera_id])
            if current_size >= 30:  # When buffer hits 30 frames
                # Drop first 20 frames to make room for new frames
                for _ in range(20):
                    if self.streams[camera_id]:
                        self.streams[camera_id].popleft()
                logger.debug(
                    f"Buffer at {current_size} for {camera_id}, dropped 20 oldest frames"
                )
            elif current_size >= self.buffer_size:
                # Fallback: single frame drop if we somehow exceed buffer size
                self.streams[camera_id].popleft()
                logger.debug(
                    f"Buffer exceeded max size for {camera_id}, dropped oldest frame"
                )

            self.streams[camera_id].append(frame)
            self._frames_processed[camera_id] += 1

            # Calculate FPS
            current_time = time.time()
            elapsed = current_time - self._last_frame_time[camera_id]
            if elapsed >= 10.0:  # Changed from 5 to 10 seconds to reduce logging
                self._fps[camera_id] = self._frames_processed[camera_id] / elapsed
                buffer_size = len(self.streams[camera_id])
                logger.debug(
                    f"Camera {camera_id} - FPS: {self._fps[camera_id]:.1f}, Buffer: {buffer_size}/{self.buffer_size}"
                )  # Changed to debug level
                self._frames_processed[camera_id] = 0
                self._last_frame_time[camera_id] = current_time

            return True

        except Exception as e:
            logger.error(f"Error processing frame for camera {camera_id}: {e}")
            return False

    async def start_stream(self, camera_id: str, websocket: WebSocket) -> None:
        """Start streaming frames to a WebSocket client."""
        if not self._running or not self._initialized:
            logger.error(
                f"Stream manager not running or initialized for camera {camera_id}"
            )
            raise RuntimeError("Stream manager not initialized")

        try:
            # Log the WebSocket URL
            ws_url = f"ws://{websocket.client.host}:{websocket.client.port}/api/video/stream/{camera_id}"
            logger.info(f"Starting stream for camera {camera_id} via {ws_url}")

            # Verify camera buffer exists
            if camera_id not in self.streams:
                logger.warning(
                    f"No frame buffer found for camera {camera_id}, initializing..."
                )
                self.streams[camera_id] = deque(maxlen=self.buffer_size)
                self._frame_times[camera_id] = deque(maxlen=self._fps_window)

            # Initialize tracking if needed
            if camera_id not in self._frames_processed:
                self._frames_processed[camera_id] = 0
                self._frames_sent[camera_id] = 0
                self._last_frame_time[camera_id] = time.time()
                self._fps[camera_id] = 0

            # FORCE REGISTER CONNECTION IMMEDIATELY
            self.connections[camera_id] = websocket
            self._connection_status[camera_id] = {
                "connected": True,
                "start_time": time.time(),
                "last_frame_time": time.time(),
                "frames_sent": 0,
                "errors": 0,
                "client": f"{websocket.client.host}:{websocket.client.port}",
                "url": ws_url,
            }

            logger.info(
                f"[SUCCESS] WebSocket connection FORCE REGISTERED for camera {camera_id}"
            )
            logger.info(
                f"[SUCCESS] Connection status: {self._connection_status[camera_id]}"
            )
            logger.info(f"[SUCCESS] Active connections: {len(self.connections)}")

            # Log buffer status
            buffer_size = len(self.streams.get(camera_id, []))
            logger.info(
                f"[SUCCESS] Buffer status for {camera_id}: {buffer_size}/{self.buffer_size} frames ready"
            )

            logger.info(
                f"[STREAMING] Started streaming for camera {camera_id} via {ws_url}"
            )

        except Exception as e:
            logger.error(f"[ERROR] Error starting stream for camera {camera_id}: {e}")
            if camera_id in self.connections:
                del self.connections[camera_id]
            if camera_id in self._connection_status:
                del self._connection_status[camera_id]
            raise

    async def stop_stream(self, camera_id: str) -> None:
        """Stop streaming frames to a WebSocket client."""
        try:
            if camera_id in self.connections:
                websocket = self.connections[camera_id]
                client_info = f"{websocket.client.host}:{websocket.client.port}"

                # Log connection statistics before removing
                if camera_id in self._connection_status:
                    stats = self._connection_status[camera_id]
                    duration = time.time() - stats["start_time"]
                    logger.info(
                        f"Connection stats for camera {camera_id} - Client: {client_info}:"
                    )
                    logger.info(f"  Duration: {duration:.1f}s")
                    logger.info(f"  Frames sent: {stats['frames_sent']}")
                    logger.info(f"  Errors: {stats['errors']}")
                    logger.info(f"  Average FPS: {stats['frames_sent']/duration:.1f}")

                del self.connections[camera_id]
                del self._connection_status[camera_id]
                logger.info(
                    f"Removed WebSocket connection for camera {camera_id} - Client: {client_info}"
                )

            if camera_id in self.streams:
                self.streams[camera_id].clear()
                logger.info(f"Cleared frame buffer for camera {camera_id}")

            logger.info(f"Stopped streaming for camera {camera_id}")

        except Exception as e:
            logger.error(f"Error stopping stream for camera {camera_id}: {e}")

    async def send_frame(self, camera_id: str) -> None:
        """Send the next frame in the buffer to the client."""
        if not self._running or not self._initialized:
            return

        try:
            # Verify connection is tracked
            if (
                camera_id not in self.connections
                and camera_id not in self._connection_status
            ):
                return

            # Check connection status first
            if (
                camera_id in self._connection_status
                and not self._connection_status[camera_id]["connected"]
            ):
                return

            # If we have connection status but no websocket, try to send error
            if camera_id not in self.connections:
                await self.send_error(camera_id, "WebSocket connection lost")
                return

            websocket = self.connections[camera_id]

            # Check WebSocket state
            if websocket.client_state.DISCONNECTED:
                logger.info(f"WebSocket disconnected for camera {camera_id}")
                await self.stop_stream(camera_id)
                return

            # Check frame availability
            if camera_id not in self.streams or not self.streams[camera_id]:
                # Send error message if no frames available
                await self.send_error(camera_id, "No frame available")
                return

            # Get next frame from buffer
            frame = self.streams[camera_id].popleft()

            # Send frame quickly without heavy logging
            try:
                await websocket.send_bytes(frame)

                # Update stats
                if camera_id not in self._frames_sent:
                    self._frames_sent[camera_id] = 0
                self._frames_sent[camera_id] += 1

                if camera_id in self._connection_status:
                    self._connection_status[camera_id]["frames_sent"] += 1
                    self._connection_status[camera_id]["last_frame_time"] = time.time()

                # Log success occasionally
                if (
                    self._frames_sent[camera_id] % 50 == 1
                ):  # Log first frame and every 50th
                    buffer_size = len(self.streams[camera_id])
                    logger.info(
                        f"[SUCCESS] Sent frame #{self._frames_sent[camera_id]} to {camera_id}, Buffer: {buffer_size}/{self.buffer_size}"
                    )

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for camera {camera_id}")
                if camera_id in self._connection_status:
                    self._connection_status[camera_id]["connected"] = False
                await self.stop_stream(camera_id)
                return
            except Exception as e:
                logger.error(f"Error sending frame for camera {camera_id}: {e}")
                if camera_id in self._connection_status:
                    self._connection_status[camera_id]["errors"] = (
                        self._connection_status[camera_id].get("errors", 0) + 1
                    )
                await self.send_error(camera_id, str(e))
                return

        except Exception as e:
            logger.error(f"Error in send_frame for camera {camera_id}: {e}")
            await self.send_error(camera_id, str(e))

    async def send_frame_batch(self, camera_id: str) -> bool:
        """Send multiple frames in a batch to the WebSocket client."""
        if camera_id not in self.connections:
            return False

        websocket = self.connections[camera_id]
        batch_size = self.get_adaptive_batch_size(camera_id)

        try:
            # Check frame availability
            if camera_id not in self.streams or not self.streams[camera_id]:
                await self.send_error(camera_id, "No frame available")
                return False

            # Collect frames for batch
            frames = []
            for _ in range(min(batch_size, len(self.streams[camera_id]))):
                if self.streams[camera_id]:
                    frames.append(self.streams[camera_id].popleft())

            if not frames:
                return False

            # Send batch as JSON message
            batch_data = {"type": "frame_batch", "count": len(frames), "frames": frames}

            try:
                await websocket.send_json(batch_data)

                # Update stats
                if camera_id not in self._frames_sent:
                    self._frames_sent[camera_id] = 0
                self._frames_sent[camera_id] += len(frames)

                if camera_id in self._connection_status:
                    self._connection_status[camera_id]["frames_sent"] += len(frames)
                    self._connection_status[camera_id]["last_frame_time"] = time.time()

                # Log success occasionally
                if self._frames_sent[camera_id] % 50 <= len(frames):
                    buffer_size = len(self.streams[camera_id])
                    logger.info(
                        f"[BATCH] Sent {len(frames)} frames to {camera_id}, Buffer: {buffer_size}/{self.buffer_size}"
                    )

                return True

            except Exception as send_error:
                logger.error(f"Error sending frame batch to {camera_id}: {send_error}")
                return False

        except Exception as e:
            logger.error(f"Error in send_frame_batch for {camera_id}: {e}")
            return False

    async def send_error(self, camera_id: str, error_message: str) -> None:
        """Send an error message to the client."""
        if not self._running or not self._initialized:
            logger.warning(
                f"Stream manager not running or initialized for camera {camera_id}"
            )
            return

        try:
            if camera_id in self.connections:
                await self.connections[camera_id].send_json({"error": error_message})
                logger.warning(f"Sent error to camera {camera_id}: {error_message}")
        except Exception as e:
            logger.error(f"Error sending error message for camera {camera_id}: {e}")

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self._running = False
            self._initialized = False
            self.streams.clear()
            self.connections.clear()
            self._frame_times.clear()
            self._frames_processed.clear()
            self._frames_sent.clear()
            self._last_stats_time.clear()
            self._connection_status.clear()
            logger.info("VideoStreamManager cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up stream manager: {e}")

    def get_adaptive_interval(self, camera_id: str) -> float:
        """Calculate adaptive interval based on buffer levels."""
        if camera_id not in self.streams:
            return self._min_interval

        buffer_size = len(self.streams[camera_id])
        buffer_ratio = buffer_size / self.buffer_size

        # Adaptive logic with bulk dropping consideration:
        # - Very high buffer (60+ frames): Send very fast to trigger bulk drop
        # - High buffer (40-60 frames): Send fast (min interval)
        # - Medium buffer (20-40 frames): Send at medium speed
        # - Low buffer (<20 frames): Send slow (max interval)
        if buffer_size >= 60:
            return self._min_interval * 0.5  # Very fast to trigger bulk drop
        elif buffer_ratio >= 0.8:  # 40+ frames
            return self._min_interval  # Fast consumption
        elif buffer_ratio >= 0.4:  # 20-40 frames
            return self._min_interval * 2  # Medium consumption
        else:  # <20 frames
            return self._max_interval  # Slow consumption

    def get_adaptive_batch_size(self, camera_id: str) -> int:
        """Calculate adaptive batch size based on buffer levels."""
        if camera_id not in self.streams:
            return 1

        buffer_size = len(self.streams[camera_id])
        buffer_ratio = buffer_size / self.buffer_size

        # Adaptive batch logic with bulk dropping consideration:
        # - Very high buffer (60+ frames): Very large batches to clear buffer quickly
        # - High buffer (40-60 frames): Large batches (max batch size)
        # - Medium buffer (20-40 frames): Medium batches
        # - Low buffer (<20 frames): Small batches (1 frame)
        if buffer_size >= 60:
            return self._max_batch_size * 2  # Very large batches to clear quickly
        elif buffer_ratio >= 0.8:  # 40+ frames
            return self._max_batch_size  # Large batches
        elif buffer_ratio >= 0.4:  # 20-40 frames
            return self._batch_size  # Medium batches
        else:  # <20 frames
            return 1  # Small batches

    def get_stats(self, camera_id: str) -> dict:
        """Get streaming statistics for a camera.
        Always report buffer size/connection, and compute FPS from recent ingestion times if available.
        """
        buffer_len = len(self.streams.get(camera_id, []))
        connected = camera_id in self.connections

        fps = 0.0
        if camera_id in self._frame_times and len(self._frame_times[camera_id]) >= 2:
            times = list(self._frame_times[camera_id])
            intervals = [times[i] - times[i - 1] for i in range(1, len(times))]
            avg_interval = sum(intervals) / len(intervals) if intervals else 0
            fps = 1.0 / avg_interval if avg_interval and avg_interval > 0 else 0.0
        elif (
            camera_id in self._connection_status
            and self._connection_status[camera_id].get("frames_sent", 0) > 0
        ):
            # Fallback: compute FPS from sending pace
            status = self._connection_status[camera_id]
            duration = max(1e-6, time.time() - status.get("start_time", time.time()))
            fps = status.get("frames_sent", 0) / duration

        adaptive_interval = self.get_adaptive_interval(camera_id)

        adaptive_batch_size = self.get_adaptive_batch_size(camera_id)

        return {
            "fps": fps,
            "buffer_size": buffer_len,
            "connected": connected,
            "frames_processed": self._frames_processed.get(camera_id, 0),
            "frames_sent": self._frames_sent.get(camera_id, 0),
            "adaptive_interval": adaptive_interval,
            "adaptive_batch_size": adaptive_batch_size,
        }

    def get_connection_status(self, camera_id: str) -> dict:
        """Get detailed connection status for a camera."""
        if camera_id not in self._connection_status:
            return {"connected": False, "error": "No connection status available"}

        status = self._connection_status[camera_id].copy()
        if status["connected"]:
            status["duration"] = time.time() - status["start_time"]
            if status["last_frame_time"]:
                status["time_since_last_frame"] = (
                    time.time() - status["last_frame_time"]
                )
            status["buffer_size"] = len(self.streams.get(camera_id, []))
            status["fps"] = (
                status["frames_sent"] / status["duration"]
                if status["duration"] > 0
                else 0
            )

        return status

    def inject_frame_for_streaming(self, camera_id: str, frame: bytes) -> bool:
        """Directly inject frame for streaming, bypassing slow processing."""
        if not self._running or not self._initialized:
            return False

        try:
            # Initialize if needed
            if camera_id not in self.streams:
                self.streams[camera_id] = deque(maxlen=self.buffer_size)
                self._frames_processed[camera_id] = 0
                self._last_frame_time[camera_id] = time.time()
                logger.info(f"Direct streaming initialized for camera: {camera_id}")

            # Add frame directly to stream buffer with bulk dropping strategy
            current_size = len(self.streams[camera_id])
            if current_size >= 30:  # When buffer hits 30 frames
                # Drop first 20 frames to make room for new frames
                for _ in range(20):
                    if self.streams[camera_id]:
                        self.streams[camera_id].popleft()
                logger.debug(
                    f"Buffer at {current_size} for {camera_id}, dropped 20 oldest frames"
                )
            elif current_size >= self.buffer_size:
                # Fallback: single frame drop if we somehow exceed buffer size
                self.streams[camera_id].popleft()
                logger.debug(
                    f"Buffer exceeded max size for {camera_id}, dropped oldest frame"
                )

            self.streams[camera_id].append(frame)

            # Update minimal stats
            if camera_id not in self._frames_processed:
                self._frames_processed[camera_id] = 0
            self._frames_processed[camera_id] += 1

            # Track ingestion times to derive FPS for status endpoint
            if camera_id not in self._frame_times:
                self._frame_times[camera_id] = deque(maxlen=self._fps_window)
            self._frame_times[camera_id].append(time.time())

            return True

        except Exception as e:
            logger.error(f"Error injecting frame for streaming {camera_id}: {e}")
            return False

    def get_buffer_status(self, camera_id: str) -> dict:
        """Get current buffer status for debugging."""
        if camera_id not in self.streams:
            return {
                "buffer_size": 0,
                "max_size": self.buffer_size,
                "status": "not_initialized",
            }

        buffer_size = len(self.streams[camera_id])
        return {
            "buffer_size": buffer_size,
            "max_size": self.buffer_size,
            "status": "full" if buffer_size >= self.buffer_size else "available",
            "frames_processed": self._frames_processed.get(camera_id, 0),
            "frames_sent": self._frames_sent.get(camera_id, 0),
        }

    def get_latest_frame(self, camera_id: str) -> Optional[bytes]:
        """Get the latest frame from the buffer for WebSocket streaming."""
        if not self._running or not self._initialized:
            return None

        try:
            if camera_id not in self.streams or not self.streams[camera_id]:
                return None

            # Return the latest frame without removing it from buffer
            return self.streams[camera_id][-1]

        except Exception as e:
            logger.error(f"Error getting latest frame for camera {camera_id}: {e}")
            return None

    def clear_camera_buffer(self, camera_id: str) -> bool:
        """Clear the frame buffer for a specific camera when it stops."""
        try:
            if camera_id in self.streams:
                self.streams[camera_id].clear()
                logger.info(f"Cleared frame buffer for stopped camera: {camera_id}")

            # Also clear tracking data
            if camera_id in self._frames_processed:
                self._frames_processed[camera_id] = 0
            if camera_id in self._frames_sent:
                self._frames_sent[camera_id] = 0
            if camera_id in self._last_frame_time:
                del self._last_frame_time[camera_id]
            if camera_id in self._fps:
                del self._fps[camera_id]

            logger.info(f"Cleared tracking data for stopped camera: {camera_id}")
            return True

        except Exception as e:
            logger.error(f"Error clearing buffer for camera {camera_id}: {e}")
            return False

    def force_register_connection(self, camera_id: str) -> bool:
        """Force register a connection for debugging (when WebSocket connects but tracking fails)."""
        try:
            # Create a dummy connection status for cameras that have buffers but no tracked connection
            if camera_id in self.streams and camera_id not in self._connection_status:
                self._connection_status[camera_id] = {
                    "connected": True,
                    "start_time": time.time(),
                    "last_frame_time": time.time(),
                    "frames_sent": 0,
                    "errors": 0,
                    "client": "force_registered",
                    "url": f"ws://localhost:8001/api/video/stream/{camera_id}",
                }
                logger.info(f"Force registered connection for camera {camera_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error force registering connection for {camera_id}: {e}")
            return False

    def fix_connection_tracking(self, camera_id: str) -> dict:
        """Fix connection tracking issues for debugging."""
        try:
            # If we have frames but no connection status, something is wrong
            if camera_id in self.streams and len(self.streams[camera_id]) > 0:
                buffer_size = len(self.streams[camera_id])

                # Check if connection tracking is broken
                if camera_id not in self._connection_status:
                    logger.warning(
                        f"Camera {camera_id} has {buffer_size} frames but no connection tracking!"
                    )
                    self.force_register_connection(camera_id)

                # Force enable connection
                if camera_id not in self.connections:
                    logger.warning(f"Camera {camera_id} missing from connections dict!")

                return {
                    "camera_id": camera_id,
                    "buffer_size": buffer_size,
                    "connection_tracked": camera_id in self._connection_status,
                    "websocket_registered": camera_id in self.connections,
                    "action": "fixed_tracking",
                }
            else:
                return {"camera_id": camera_id, "action": "no_frames_to_fix"}
        except Exception as e:
            logger.error(f"Error fixing connection tracking for {camera_id}: {e}")
            return {"error": str(e)}
