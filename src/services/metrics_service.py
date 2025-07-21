import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import aiohttp
import psutil
from loguru import logger

from src.utils.system_monitor import SystemMonitor

# Import monitoring with error handling
try:
    from utils.monitoring import SystemMonitor as PrometheusMonitor
    from utils.monitoring import get_monitor
except ImportError as e:
    logger.warning(f"Failed to import Prometheus monitoring: {e}")
    PrometheusMonitor = None
    get_monitor = None


class MetricsService:
    """Unified service for aggregating metrics from multiple sources."""

    def __init__(self):
        self.elasticsearch_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.prometheus_url = os.getenv("PROMETHEUS_URL", "http://localhost:8000")

        # Initialize monitoring components
        self.system_monitor = SystemMonitor()

        # Use existing Prometheus monitor if available (lazy initialization)
        self.prometheus_monitor = None
        self._prometheus_init_attempted = False

    async def _query_elasticsearch(self, index: str, query: dict) -> dict:
        """Execute query against Elasticsearch."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.elasticsearch_url}/{index}/_search",
                    json=query,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Elasticsearch query failed: {response.status}")
                        return {"hits": {"hits": []}}
        except Exception as e:
            logger.error(f"Error querying Elasticsearch: {e}")
            return {"hits": {"hits": []}}

    def _parse_time_range(self, time_range: str) -> str:
        """Convert time range string to Elasticsearch format."""
        time_map = {"5m": "now-5m", "15m": "now-15m", "1h": "now-1h", "24h": "now-24h"}
        return time_map.get(time_range, "now-15m")

    async def get_system_metrics(
        self, time_range: str = "15m", limit: int = 100
    ) -> List[dict]:
        """Get system performance metrics from Elasticsearch."""
        query = {
            "size": limit,
            "sort": [{"@timestamp": "desc"}],
            "query": {
                "bool": {
                    "filter": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": self._parse_time_range(time_range),
                                    "lte": "now",
                                }
                            }
                        }
                    ]
                }
            },
            "_source": [
                "@timestamp",
                "cpu_usage",
                "memory_usage",
                "disk_usage",
                "active_cameras",
            ],
        }

        result = await self._query_elasticsearch("system_metrics", query)

        metrics = []
        for hit in result.get("hits", {}).get("hits", []):
            source = hit["_source"]
            metrics.append(
                {
                    "timestamp": source.get("@timestamp"),
                    "cpu_usage": source.get("cpu_usage", 0),
                    "memory_usage": source.get("memory_usage", 0),
                    "disk_usage": source.get("disk_usage", 0),
                    "active_cameras": source.get("active_cameras", 0),
                }
            )

        # If no Elasticsearch data, get current system metrics
        if not metrics:
            self.system_monitor.update()
            current_metrics = self.system_monitor.get_metrics()
            metrics.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "cpu_usage": current_metrics.get("cpu_usage", 0),
                    "memory_usage": current_metrics.get("memory_usage", 0),
                    "disk_usage": current_metrics.get("disk_usage", 0),
                    "active_cameras": current_metrics.get("active_cameras", 0),
                }
            )

        return list(reversed(metrics))  # Return chronological order

    async def get_camera_metrics(self) -> List[dict]:
        """Get current metrics for all cameras."""
        query = {
            "size": 0,
            "aggs": {
                "cameras": {
                    "terms": {"field": "camera_id.keyword", "size": 100},
                    "aggs": {
                        "latest_metrics": {
                            "top_hits": {
                                "sort": [{"@timestamp": {"order": "desc"}}],
                                "size": 1,
                                "_source": [
                                    "fps_actual",
                                    "fps_target",
                                    "latency_ms",
                                    "status",
                                    "last_detection",
                                ],
                            }
                        }
                    },
                }
            },
            "query": {"range": {"@timestamp": {"gte": "now-5m"}}},
        }

        result = await self._query_elasticsearch("detection-metrics-*", query)

        cameras = []
        for bucket in (
            result.get("aggregations", {}).get("cameras", {}).get("buckets", [])
        ):
            camera_id = bucket["key"]
            latest = bucket["latest_metrics"]["hits"]["hits"]

            if latest:
                source = latest[0]["_source"]
                cameras.append(
                    {
                        "camera_id": camera_id,
                        "fps_actual": source.get("fps_actual", 0),
                        "fps_target": source.get("fps_target", 30),
                        "latency_ms": source.get("latency_ms", 0),
                        "status": source.get("status", "unknown"),
                        "last_detection": source.get("last_detection"),
                    }
                )
            else:
                cameras.append(
                    {
                        "camera_id": camera_id,
                        "fps_actual": 0,
                        "fps_target": 30,
                        "latency_ms": 0,
                        "status": "offline",
                        "last_detection": None,
                    }
                )

        return cameras

    async def get_camera_performance(
        self, camera_id: str, time_range: str = "1h"
    ) -> dict:
        """Get detailed performance metrics for a specific camera."""
        query = {
            "size": 100,
            "sort": [{"@timestamp": "desc"}],
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"camera_id.keyword": camera_id}},
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": self._parse_time_range(time_range),
                                    "lte": "now",
                                }
                            }
                        },
                    ]
                }
            },
            "_source": [
                "@timestamp",
                "fps_actual",
                "latency_ms",
                "queue_depth",
                "dropped_frames",
            ],
        }

        result = await self._query_elasticsearch("detection-metrics-*", query)

        performance_data = []
        for hit in result.get("hits", {}).get("hits", []):
            source = hit["_source"]
            performance_data.append(
                {
                    "timestamp": source.get("@timestamp"),
                    "fps_actual": source.get("fps_actual", 0),
                    "latency_ms": source.get("latency_ms", 0),
                    "queue_depth": source.get("queue_depth", 0),
                    "dropped_frames": source.get("dropped_frames", 0),
                }
            )

        return {
            "camera_id": camera_id,
            "time_range": time_range,
            "data": list(reversed(performance_data)),
        }

    async def get_detection_metrics(
        self,
        time_range: str = "1h",
        camera_id: Optional[str] = None,
        confidence_threshold: float = 0.0,
    ) -> List[dict]:
        """Get detection metrics with optional filtering."""
        filters = [
            {
                "range": {
                    "@timestamp": {
                        "gte": self._parse_time_range(time_range),
                        "lte": "now",
                    }
                }
            },
            {"range": {"prediction.confidence": {"gte": confidence_threshold}}},
        ]

        if camera_id:
            filters.append({"term": {"camera_id.keyword": camera_id}})

        query = {
            "size": 100,
            "sort": [{"@timestamp": "desc"}],
            "query": {"bool": {"filter": filters}},
            "_source": [
                "@timestamp",
                "camera_id",
                "prediction.confidence",
                "prediction.label",
                "prediction.is_shoplifting",
                "alert.triggered",
            ],
        }

        result = await self._query_elasticsearch("detection-metrics-*", query)

        detections = []
        for hit in result.get("hits", {}).get("hits", []):
            source = hit["_source"]
            prediction = source.get("prediction", {})
            alert = source.get("alert", {})

            detections.append(
                {
                    "camera_id": source.get("camera_id", "unknown"),
                    "confidence": prediction.get("confidence", 0),
                    "label": prediction.get("label", "unknown"),
                    "is_shoplifting": prediction.get("is_shoplifting", False),
                    "timestamp": source.get("@timestamp"),
                    "alert_triggered": alert.get("triggered", False),
                }
            )

        return detections

    async def get_metrics_summary(self) -> dict:
        """Get comprehensive metrics summary."""
        # Get latest system metrics
        system_metrics = await self.get_system_metrics(time_range="5m", limit=1)
        latest_system = (
            system_metrics[0]
            if system_metrics
            else {
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": 0,
                "memory_usage": 0,
                "disk_usage": 0,
                "active_cameras": 0,
            }
        )

        # Get camera metrics
        cameras = await self.get_camera_metrics()

        # Get recent detections
        recent_detections = await self.get_detection_metrics(
            time_range="1h", confidence_threshold=0.5
        )

        # Count today's detections and alerts
        today_detections = await self.get_detection_metrics(time_range="24h")
        today_alerts = [d for d in today_detections if d.get("alert_triggered", False)]

        return {
            "system": latest_system,
            "cameras": cameras,
            "recent_detections": recent_detections[:10],  # Last 10 detections
            "total_detections_today": len(today_detections),
            "alert_count_today": len(today_alerts),
        }

    def _ensure_prometheus_monitor(self):
        """Lazy initialization of Prometheus monitor to avoid timing issues."""
        if self._prometheus_init_attempted:
            return

        self._prometheus_init_attempted = True
        try:
            if get_monitor:
                self.prometheus_monitor = get_monitor()
                logger.info("Successfully connected to existing Prometheus monitor")
            elif PrometheusMonitor:
                self.prometheus_monitor = PrometheusMonitor()
                logger.info("Successfully initialized new Prometheus monitor")
            else:
                logger.info("Prometheus monitoring not available")
        except Exception as e:
            logger.debug(f"Prometheus monitor not yet available: {e}")
            # Reset flag to try again later
            self._prometheus_init_attempted = False

    async def get_health_status(self) -> dict:
        """Check health of metrics infrastructure."""
        # Try to initialize Prometheus monitor if not done yet
        self._ensure_prometheus_monitor()

        health = {
            "elasticsearch": False,
            "prometheus": False,
            "system_monitor": True,
            "timestamp": datetime.now().isoformat(),
        }

        # Check Elasticsearch
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.elasticsearch_url}/_cluster/health"
                ) as response:
                    if response.status == 200:
                        health["elasticsearch"] = True
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")

        # Check Prometheus
        if self.prometheus_monitor:
            health["prometheus"] = True

        return health

    async def get_recent_alerts(
        self, limit: int = 50, severity: Optional[str] = None
    ) -> List[dict]:
        """Get recent alerts from the system."""
        filters = [
            {"term": {"alert.triggered": True}},
            {"range": {"@timestamp": {"gte": "now-24h"}}},
        ]

        if severity:
            filters.append({"term": {"alert.level.keyword": severity}})

        query = {
            "size": limit,
            "sort": [{"@timestamp": "desc"}],
            "query": {"bool": {"filter": filters}},
            "_source": [
                "@timestamp",
                "camera_id",
                "alert.level",
                "alert.type",
                "prediction.confidence",
                "prediction.label",
            ],
        }

        result = await self._query_elasticsearch("detection-metrics-*", query)

        alerts = []
        for hit in result.get("hits", {}).get("hits", []):
            source = hit["_source"]
            alert = source.get("alert", {})
            prediction = source.get("prediction", {})

            alerts.append(
                {
                    "timestamp": source.get("@timestamp"),
                    "camera_id": source.get("camera_id", "unknown"),
                    "level": alert.get("level", "unknown"),
                    "type": alert.get("type", "detection"),
                    "confidence": prediction.get("confidence", 0),
                    "label": prediction.get("label", "unknown"),
                }
            )

        return alerts
