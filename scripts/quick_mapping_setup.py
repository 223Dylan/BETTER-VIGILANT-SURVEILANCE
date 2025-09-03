#!/usr/bin/env python3
"""
Quick Elasticsearch mapping setup using curl commands
This script provides curl commands you can run directly in the console
"""

import json


def print_curl_commands():
    """Print curl commands for creating index templates."""

    print("=" * 60)
    print("ELASTICSEARCH INDEX MAPPING SETUP")
    print("=" * 60)
    print("\nRun these curl commands in your terminal to create index templates:")
    print("\n1. Detection Metrics Template:")
    print("-" * 40)

    detection_template = {
        "index_patterns": ["detection-metrics-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "refresh_interval": "1s",
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
                        }
                    },
                    "confidence_level": {"type": "keyword"},
                    "detection_outcome": {"type": "keyword"},
                    "performance": {
                        "properties": {
                            "processing_time_ms": {"type": "float"},
                            "fps": {"type": "float"},
                            "memory_usage_mb": {"type": "float"},
                        }
                    },
                }
            },
        },
    }

    print(f'curl -X PUT "localhost:9200/_index_template/detection-metrics" \\')
    print(f'  -H "Content-Type: application/json" \\')
    print(f"  -d '{json.dumps(detection_template, indent=2)}'")

    print("\n2. System Performance Template:")
    print("-" * 40)

    performance_template = {
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
                            "cpu_usage": {"type": "float"},
                            "memory_usage": {"type": "float"},
                            "disk_usage": {"type": "float"},
                        }
                    },
                    "fps_status": {"type": "keyword"},
                }
            },
        },
    }

    print(f'curl -X PUT "localhost:9200/_index_template/system-performance" \\')
    print(f'  -H "Content-Type: application/json" \\')
    print(f"  -d '{json.dumps(performance_template, indent=2)}'")

    print("\n3. Camera Health Template:")
    print("-" * 40)

    health_template = {
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
                        }
                    },
                }
            },
        },
    }

    print(f'curl -X PUT "localhost:9200/_index_template/camera-health" \\')
    print(f'  -H "Content-Type: application/json" \\')
    print(f"  -d '{json.dumps(health_template, indent=2)}'")

    print("\n4. Detection Analytics Template:")
    print("-" * 40)

    analytics_template = {
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
                        }
                    },
                }
            },
        },
    }

    print(f'curl -X PUT "localhost:9200/_index_template/detection-analytics" \\')
    print(f'  -H "Content-Type: application/json" \\')
    print(f"  -d '{json.dumps(analytics_template, indent=2)}'")

    print("\n" + "=" * 60)
    print("VERIFICATION COMMANDS")
    print("=" * 60)
    print("\nAfter running the above commands, verify with:")
    print('curl -X GET "localhost:9200/_index_template"')
    print('curl -X GET "localhost:9200/_cat/indices?v"')

    print("\n" + "=" * 60)
    print("ALTERNATIVE: USE THE AUTOMATED SCRIPT")
    print("=" * 60)
    print("\nInstead of running curl commands manually, you can use:")
    print("python scripts/setup_elasticsearch_mappings.py")
    print("\nThis script will:")
    print("- Wait for Elasticsearch to be ready")
    print("- Create all templates automatically")
    print("- Verify the setup")
    print("- Provide next steps")


if __name__ == "__main__":
    print_curl_commands()
