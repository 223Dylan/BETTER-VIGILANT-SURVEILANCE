import asyncio
import json
import os
from typing import Any, Dict
from urllib.parse import urlparse

import redis
from loguru import logger


class RedisWebSocketBridge:
    """Bridge Redis pub/sub with WebSocket broadcasting for cross-process communication."""

    def __init__(self):
        self.redis_client = None
        self.pubsub = None
        self.subscriber_task = None
        self.websocket_manager = None
        self.channel_name = "websocket_events"

        self._setup_redis()

    def _setup_redis(self):
        """Initialize Redis connection using same pattern as frame_storage_service."""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            parsed_url = urlparse(redis_url)

            self.redis_client = redis.Redis(
                host=parsed_url.hostname or "localhost",
                port=parsed_url.port or 6379,
                db=int(parsed_url.path[1:]) if parsed_url.path else 0,
                decode_responses=True,  # Enable for JSON handling
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )

            # Test connection
            self.redis_client.ping()
            logger.info(f"Redis WebSocket bridge connected at {redis_url}")

        except Exception as e:
            logger.error(f"Failed to connect Redis WebSocket bridge: {e}")
            self.redis_client = None

    def publish_websocket_event(
        self, camera_id: str, event_type: str, data: Dict[str, Any]
    ) -> bool:
        """Publish WebSocket event to Redis (called from Celery workers)."""
        if not self.redis_client:
            logger.error("Redis client not available for WebSocket event publishing")
            return False

        try:
            event = {
                "camera_id": camera_id,
                "event_type": event_type,  # "prediction", "alert", etc.
                "data": data,
                "timestamp": data.get("timestamp", None),
            }

            # Publish to Redis channel
            self.redis_client.publish(self.channel_name, json.dumps(event))
            logger.info(f"[REDIS] Published {event_type} event for camera {camera_id}")
            return True

        except Exception as e:
            logger.error(f"Error publishing WebSocket event to Redis: {e}")
            return False

    async def start_subscriber(self, websocket_manager):
        """Start Redis subscriber to listen for WebSocket events (API server only)."""
        if not self.redis_client:
            logger.error("Redis client not available for subscription")
            return

        self.websocket_manager = websocket_manager

        try:
            # Create pubsub connection
            self.pubsub = self.redis_client.pubsub()
            self.pubsub.subscribe(self.channel_name)

            logger.info(
                f"[REDIS] Started WebSocket event subscriber on channel: {self.channel_name}"
            )

            # Start background task to process messages
            self.subscriber_task = asyncio.create_task(self._process_redis_messages())

        except Exception as e:
            logger.error(f"Error starting Redis subscriber: {e}")

    async def _process_redis_messages(self):
        """Process incoming Redis messages and broadcast to WebSockets."""
        logger.info("[REDIS] WebSocket event processor started")

        try:
            while True:
                try:
                    # Get message from Redis (non-blocking)
                    message = self.pubsub.get_message(timeout=1.0)

                    if message and message["type"] == "message":
                        try:
                            # Parse event data
                            event = json.loads(message["data"])
                            camera_id = event["camera_id"]
                            event_type = event["event_type"]
                            data = event["data"]

                            logger.info(
                                f"[REDIS] Received {event_type} event for camera {camera_id}"
                            )

                            # Broadcast to WebSockets based on event type
                            if event_type == "prediction":
                                await self.websocket_manager.broadcast_prediction(
                                    camera_id, data
                                )
                            elif event_type == "alert":
                                await self.websocket_manager.broadcast_alert(
                                    camera_id, data
                                )
                            else:
                                logger.warning(f"Unknown event type: {event_type}")

                        except json.JSONDecodeError as e:
                            logger.error(f"Error parsing Redis message: {e}")
                        except Exception as e:
                            logger.error(f"Error processing Redis event: {e}")

                    # Small delay to prevent busy waiting
                    await asyncio.sleep(0.1)

                except Exception as e:
                    logger.error(f"Error in Redis message loop: {e}")
                    await asyncio.sleep(1.0)  # Wait longer on error

        except asyncio.CancelledError:
            logger.info("[REDIS] WebSocket event processor stopped")
        except Exception as e:
            logger.error(f"Fatal error in Redis message processor: {e}")

    async def stop_subscriber(self):
        """Stop the Redis subscriber."""
        if self.subscriber_task:
            self.subscriber_task.cancel()
            try:
                await self.subscriber_task
            except asyncio.CancelledError:
                pass

        if self.pubsub:
            self.pubsub.close()

        logger.info("[REDIS] WebSocket event subscriber stopped")

    def close(self):
        """Close Redis connections."""
        if self.redis_client:
            self.redis_client.close()


# Global instance for cross-process communication
redis_websocket_bridge = RedisWebSocketBridge()
