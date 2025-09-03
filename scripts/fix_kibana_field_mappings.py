#!/usr/bin/env python3
"""
Fix Kibana field mappings to match dashboard requirements
This script updates index templates to include all fields referenced in dashboards
"""

import json
import os
import sys
import time
from typing import Dict

import requests

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")


def wait_for_elasticsearch(max_retries: int = 30) -> bool:
    """Wait for Elasticsearch to be ready."""
    print("Waiting for Elasticsearch to be ready...")

    for i in range(max_retries):
        try:
            response = requests.get(f"{ELASTICSEARCH_URL}/_cluster/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                if health["status"] in ["green", "yellow"]:
                    print(f"Elasticsearch is ready! Status: {health['status']}")
                    return True
        except requests.exceptions.RequestException:
            pass

        print(f"Attempt {i+1}/{max_retries} - Elasticsearch not ready yet...")
        time.sleep(2)

    print("ERROR: Elasticsearch is not ready after maximum retries")
    return False


def update_index_template(template_name: str, template_config: Dict) -> bool:
    """Update an index template in Elasticsearch."""
    url = f"{ELASTICSEARCH_URL}/_index_template/{template_name}"

    try:
        response = requests.put(url, json=template_config, timeout=30)

        if response.status_code in [200, 201]:
            print(f"✓ Updated index template: {template_name}")
            return True
        else:
            print(f"✗ Failed to update template {template_name}: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error updating template {template_name}: {e}")
        return False


def get_enhanced_detection_metrics_template() -> Dict:
    """Get enhanced detection metrics template with all dashboard fields."""
    return {
        "index_patterns": ["detection-metrics-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "refresh_interval": "1s",
                "index.mapping.total_fields.limit": 1000,
            },
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "type": {"type": "keyword"},
                    "camera_id": {"type": "keyword"},
                    "prediction": {
                        "properties": {
                            "confidence": {"type": "float"},
                            "is_shoplifting": {"type": "boolean"},
                            "prediction_time_ms": {"type": "float"},
                            "label": {"type": "keyword"},
                            "model_version": {"type": "keyword"},
                        }
                    },
                    "alert": {
                        "properties": {
                            "triggered": {"type": "boolean"},
                            "level": {"type": "keyword"},
                            "alert_type": {"type": "keyword"},
                            "alert_id": {"type": "keyword"},
                        }
                    },
                    "confidence_level": {"type": "keyword"},
                    "detection_outcome": {"type": "keyword"},
                    "performance": {
                        "properties": {
                            "processing_time_ms": {"type": "float"},
                            "fps": {
                                "type": "float"
                            },  # Added for dashboard compatibility
                            "fps_actual": {"type": "float"},
                            "memory_usage_mb": {"type": "float"},
                            "gpu_usage_percent": {"type": "float"},
                        }
                    },
                    "location": {
                        "properties": {
                            "lat": {"type": "float"},
                            "lon": {"type": "float"},
                        }
                    },
                    "camera_location": {
                        "properties": {
                            "lat": {"type": "float"},
                            "lon": {"type": "float"},
                            "name": {"type": "keyword"},
                            "zone": {"type": "keyword"},
                        }
                    },
                }
            },
        },
    }


def get_enhanced_system_performance_template() -> Dict:
    """Get enhanced system performance template with all dashboard fields."""
    return {
        "index_patterns": ["system-performance-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "refresh_interval": "5s",
            },
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "type": {"type": "keyword"},
                    "camera_id": {"type": "keyword"},
                    "performance": {
                        "properties": {
                            "fps_actual": {"type": "float"},
                            "fps_target": {"type": "float"},
                            "processing_latency_ms": {"type": "float"},
                            "queue_depth": {"type": "integer"},
                            "dropped_frames": {"type": "integer"},
                            "cpu_usage": {
                                "type": "float"
                            },  # Added for dashboard compatibility
                            "memory_usage": {
                                "type": "float"
                            },  # Added for dashboard compatibility
                            "disk_usage": {
                                "type": "float"
                            },  # Added for dashboard compatibility
                            "gpu_usage": {"type": "float"},
                            "network_io": {"type": "float"},
                        }
                    },
                    "fps_status": {"type": "keyword"},
                    # Add top-level fields for dashboard compatibility
                    "fps": {"type": "float"},  # Dashboard references this directly
                    "cpu_usage": {
                        "type": "float"
                    },  # Dashboard references this directly
                    "memory_usage": {
                        "type": "float"
                    },  # Dashboard references this directly
                    "disk_usage": {
                        "type": "float"
                    },  # Dashboard references this directly
                    "system": {
                        "properties": {
                            "hostname": {"type": "keyword"},
                            "os": {"type": "keyword"},
                            "python_version": {"type": "keyword"},
                        }
                    },
                }
            },
        },
    }


def get_enhanced_camera_health_template() -> Dict:
    """Get enhanced camera health template with all dashboard fields."""
    return {
        "index_patterns": ["camera-health-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "refresh_interval": "10s",
            },
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "type": {"type": "keyword"},
                    "camera_id": {"type": "keyword"},
                    "health": {
                        "properties": {
                            "is_connected": {"type": "boolean"},
                            "current_fps": {"type": "float"},
                            "last_frame_timestamp": {"type": "date"},
                            "error_count": {"type": "integer"},
                            "status": {"type": "keyword"},
                            "uptime_seconds": {"type": "float"},
                            "connection_quality": {"type": "keyword"},
                        }
                    },
                    "errors": {
                        "properties": {
                            "error_type": {
                                "type": "keyword"
                            },  # Added for dashboard compatibility
                            "error_message": {"type": "text"},
                            "error_count": {"type": "integer"},
                            "last_error_time": {"type": "date"},
                        }
                    },
                    "camera_info": {
                        "properties": {
                            "model": {"type": "keyword"},
                            "resolution": {"type": "keyword"},
                            "fps": {"type": "integer"},
                            "location": {"type": "keyword"},
                        }
                    },
                    # Add top-level error_type for dashboard compatibility
                    "error_type": {"type": "keyword"},
                }
            },
        },
    }


def main():
    """Main function to fix Kibana field mappings."""
    print("Kibana Field Mapping Fix")
    print("=" * 40)

    # Wait for Elasticsearch to be ready
    if not wait_for_elasticsearch():
        print("ERROR: Cannot proceed without Elasticsearch")
        sys.exit(1)

    # Update templates with enhanced field mappings
    templates = [
        ("detection-metrics", get_enhanced_detection_metrics_template()),
        ("system-performance", get_enhanced_system_performance_template()),
        ("camera-health", get_enhanced_camera_health_template()),
    ]

    success_count = 0
    total_count = len(templates)

    print(f"\nUpdating {total_count} index templates with enhanced field mappings...")
    print("=" * 60)

    for template_name, template_config in templates:
        if update_index_template(template_name, template_config):
            success_count += 1

    print("=" * 60)
    print(f"Successfully updated {success_count}/{total_count} index templates")

    if success_count == total_count:
        print("\n✓ All templates updated successfully!")
        print("\nNext steps:")
        print("1. Try importing the detection dashboard again:")
        print("   python scripts/fix_dashboard_import.py")
        print("2. Or create dashboards manually in Kibana")
        print("3. The field mappings now match your dashboard requirements")
    else:
        print("\n✗ Some templates failed to update")
        sys.exit(1)


if __name__ == "__main__":
    main()
