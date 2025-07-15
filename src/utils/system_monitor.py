import logging
from typing import Any, Dict

import psutil

logger = logging.getLogger(__name__)


class SystemMonitor:
    def __init__(self):
        self.active_cameras = 0
        self.metrics = {}
        self.thresholds = {
            "cpu_usage": 80.0,  # 80% CPU usage threshold
            "memory_usage": 85.0,  # 85% memory usage threshold
            "disk_usage": 90.0,  # 90% disk usage threshold
        }

    def update_active_cameras(self, count: int) -> None:
        """Update the count of active cameras."""
        self.active_cameras = count
        logger.info(f"Active cameras updated: {count}")

    def update(self) -> None:
        """Update system metrics."""
        try:
            # Get CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)

            # Get memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent

            # Get disk usage
            disk = psutil.disk_usage("/")
            disk_usage = disk.percent

            # Update metrics
            self.metrics = {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
                "active_cameras": self.active_cameras,
            }

            # Log if any metric exceeds threshold
            for metric, value in self.metrics.items():
                if metric in self.thresholds and value > self.thresholds[metric]:
                    logger.warning(
                        f"High {metric}: {value}% (threshold: {self.thresholds[metric]}%)"
                    )

        except Exception as e:
            logger.error(f"Error updating system metrics: {str(e)}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        return self.metrics

    def stop(self) -> None:
        """Clean up resources."""
        logger.info("System monitor stopped")
