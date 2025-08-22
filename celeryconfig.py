# Celery Configuration
import os

broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
result_backend = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Task settings
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "UTC"
enable_utc = True

# Worker settings
worker_concurrency = 1  # Reduced concurrency for Windows
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 50
worker_max_memory_per_child = 200000  # 200MB

# Task execution settings
task_time_limit = 300  # 5 minutes
task_soft_time_limit = 240  # 4 minutes
task_acks_late = True
task_reject_on_worker_lost = True

# Queue settings
task_default_queue = "default"
task_queues = {
    "default": {
        "exchange": "default",
        "routing_key": "default",
    },
    "camera_pipeline": {
        "exchange": "camera_pipeline",
        "routing_key": "camera_pipeline",
    },
}

# Windows-specific settings
worker_pool = "solo"  # Use solo pool for Windows
worker_pool_restarts = True
worker_enable_remote_control = False

# Logging settings
worker_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
worker_task_log_format = "[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s"

# Beat schedule for periodic tasks


def get_auto_clear_interval():
    """Get auto-clear interval from environment variables."""
    interval_minutes = int(os.getenv("ALERT_AUTO_CLEAR_INTERVAL_MINUTES", "60"))
    return interval_minutes * 60.0  # Convert to seconds


beat_schedule = {
    "auto-clear-alerts": {
        "task": "shoplifting_detection.auto_clear_alerts",
        "schedule": get_auto_clear_interval(),
        "options": {
            "expires": int(
                get_auto_clear_interval()
            ),  # Task expires after one interval if not picked up
        },
    },
}
