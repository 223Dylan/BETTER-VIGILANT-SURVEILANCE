#!/usr/bin/env python3
"""
Complete Elasticsearch index template setup for surveillance system
This script creates all necessary index templates with proper mappings for Kibana dashboards
"""

import json
import os
import sys
import time
from typing import Dict, List

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


def create_index_template(template_name: str, template_config: Dict) -> bool:
    """Create an index template in Elasticsearch."""
    url = f"{ELASTICSEARCH_URL}/_index_template/{template_name}"

    try:
        response = requests.put(url, json=template_config, timeout=30)

        if response.status_code in [200, 201]:
            print(f"✓ Created index template: {template_name}")
            return True
        else:
            print(f"✗ Failed to create template {template_name}: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error creating template {template_name}: {e}")
        return False


def get_detection_metrics_template() -> Dict:
    """Get the detection metrics index template configuration."""
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
                            "fps": {"type": "float"},
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


def get_system_performance_template() -> Dict:
    """Get the system performance index template configuration."""
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
                            "cpu_usage": {"type": "float"},
                            "memory_usage": {"type": "float"},
                            "disk_usage": {"type": "float"},
                            "gpu_usage": {"type": "float"},
                            "network_io": {"type": "float"},
                        }
                    },
                    "fps_status": {"type": "keyword"},
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


def get_camera_health_template() -> Dict:
    """Get the camera health index template configuration."""
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
                            "error_type": {"type": "keyword"},
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
                }
            },
        },
    }


def get_detection_analytics_template() -> Dict:
    """Get the detection analytics index template configuration."""
    return {
        "index_patterns": ["detection-analytics-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "refresh_interval": "30s",
            },
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "type": {"type": "keyword"},
                    "camera_id": {"type": "keyword"},
                    "analytics": {
                        "properties": {
                            "detection_count": {"type": "integer"},
                            "false_positive_rate": {"type": "float"},
                            "average_confidence": {"type": "float"},
                            "time_period": {"type": "keyword"},
                            "accuracy_percentage": {"type": "float"},
                            "total_processing_time": {"type": "float"},
                        }
                    },
                    "time_range": {
                        "properties": {
                            "start_time": {"type": "date"},
                            "end_time": {"type": "date"},
                            "duration_minutes": {"type": "integer"},
                        }
                    },
                }
            },
        },
    }


def get_camera_system_template() -> Dict:
    """Get the camera system index template configuration."""
    return {
        "index_patterns": ["camera-system-*"],
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
                    "level": {"type": "keyword"},
                    "message": {"type": "text"},
                    "module": {"type": "keyword"},
                    "function": {"type": "keyword"},
                    "line": {"type": "integer"},
                    "hostname": {"type": "keyword"},
                    "process_id": {"type": "integer"},
                    "thread_id": {"type": "integer"},
                    "thread_name": {"type": "keyword"},
                    "exception": {"type": "text"},
                }
            },
        },
    }


def get_system_metrics_template() -> Dict:
    """Get the system metrics index template configuration."""
    return {
        "index_patterns": ["system-metrics-*"],
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
                    "cpu_usage": {"type": "float"},
                    "memory_usage": {"type": "float"},
                    "disk_usage": {"type": "float"},
                    "network_io": {"type": "float"},
                    "process_count": {"type": "integer"},
                    "load_average": {"type": "float"},
                    "system": {
                        "properties": {
                            "hostname": {"type": "keyword"},
                            "os": {"type": "keyword"},
                            "uptime": {"type": "float"},
                        }
                    },
                }
            },
        },
    }


def create_all_templates() -> bool:
    """Create all index templates for the surveillance system."""
    templates = [
        ("detection-metrics", get_detection_metrics_template()),
        ("system-performance", get_system_performance_template()),
        ("camera-health", get_camera_health_template()),
        ("detection-analytics", get_detection_analytics_template()),
        ("camera-system", get_camera_system_template()),
        ("system-metrics", get_system_metrics_template()),
    ]

    success_count = 0
    total_count = len(templates)

    print(f"\nCreating {total_count} index templates...")
    print("=" * 50)

    for template_name, template_config in templates:
        if create_index_template(template_name, template_config):
            success_count += 1

    print("=" * 50)
    print(f"Successfully created {success_count}/{total_count} index templates")

    return success_count == total_count


def verify_templates() -> bool:
    """Verify that all templates were created successfully."""
    print("\nVerifying created templates...")

    try:
        response = requests.get(f"{ELASTICSEARCH_URL}/_index_template", timeout=10)
        if response.status_code == 200:
            templates = response.json()
            template_names = [
                template["name"] for template in templates.get("index_templates", [])
            ]

            expected_templates = [
                "detection-metrics",
                "system-performance",
                "camera-health",
                "detection-analytics",
                "camera-system",
                "system-metrics",
            ]

            missing_templates = [
                name for name in expected_templates if name not in template_names
            ]

            if missing_templates:
                print(f"✗ Missing templates: {missing_templates}")
                return False
            else:
                print("✓ All templates verified successfully")
                return True
        else:
            print(f"✗ Failed to verify templates: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error verifying templates: {e}")
        return False


def main():
    """Main function to set up Elasticsearch mappings."""
    print("Elasticsearch Index Template Setup")
    print("=" * 40)

    # Wait for Elasticsearch to be ready
    if not wait_for_elasticsearch():
        print("ERROR: Cannot proceed without Elasticsearch")
        sys.exit(1)

    # Create all templates
    if not create_all_templates():
        print("ERROR: Failed to create some templates")
        sys.exit(1)

    # Verify templates
    if not verify_templates():
        print("ERROR: Template verification failed")
        sys.exit(1)

    print("\n" + "=" * 40)
    print("✓ Elasticsearch index templates setup completed successfully!")
    print("\nNext steps:")
    print("1. Start your application to begin sending data")
    print("2. Create index patterns in Kibana")
    print("3. Import dashboard configurations")
    print("4. Access your dashboards at http://localhost:5601")


if __name__ == "__main__":
    main()
