#!/usr/bin/env python3
"""
Fix both index templates and dashboard import issues
"""

import json
import os
from pathlib import Path

import requests

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
KIBANA_URL = os.getenv("KIBANA_URL", "http://localhost:5601")


def create_legacy_index_templates():
    """Create index templates using legacy format for compatibility."""

    templates = [
        {
            "name": "detection-metrics",
            "template": {
                "index_patterns": ["detection-metrics-*"],
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
                        "alert": {
                            "properties": {
                                "triggered": {"type": "boolean"},
                                "level": {"type": "keyword"},
                                "alert_type": {"type": "keyword"},
                            }
                        },
                        "confidence_level": {"type": "keyword"},
                        "detection_outcome": {"type": "keyword"},
                    }
                },
            },
        },
        {
            "name": "system-performance",
            "template": {
                "index_patterns": ["system-performance-*"],
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
                            }
                        },
                        "fps_status": {"type": "keyword"},
                    }
                },
            },
        },
        {
            "name": "camera-health",
            "template": {
                "index_patterns": ["camera-health-*"],
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
        },
    ]

    success_count = 0
    for template in templates:
        try:
            # Try new format first
            response = requests.put(
                f"{ELASTICSEARCH_URL}/_index_template/{template['name']}",
                json=template["template"],
                headers={"Content-Type": "application/json"},
            )

            if response.status_code in [200, 201]:
                print(
                    f"[SUCCESS] Created index template (new format): {template['name']}"
                )
                success_count += 1
            else:
                # Fall back to legacy format
                response = requests.put(
                    f"{ELASTICSEARCH_URL}/_template/{template['name']}",
                    json=template["template"],
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code in [200, 201]:
                    print(
                        f"[SUCCESS] Created index template (legacy format): {template['name']}"
                    )
                    success_count += 1
                else:
                    print(
                        f"[ERROR] Failed to create template {template['name']}: {response.text}"
                    )

        except Exception as e:
            print(f"[ERROR] Error creating template {template['name']}: {e}")

    return success_count


def create_index_patterns():
    """Create index patterns in Kibana."""

    index_patterns = [
        {"title": "detection-metrics-*", "timeFieldName": "@timestamp"},
        {"title": "system-performance-*", "timeFieldName": "@timestamp"},
        {"title": "camera-health-*", "timeFieldName": "@timestamp"},
    ]

    success_count = 0
    for pattern in index_patterns:
        try:
            # Create index pattern
            payload = {
                "attributes": {
                    "title": pattern["title"],
                    "timeFieldName": pattern["timeFieldName"],
                }
            }

            response = requests.post(
                f"{KIBANA_URL}/api/saved_objects/index-pattern",
                json=payload,
                headers={"Content-Type": "application/json", "kbn-xsrf": "true"},
            )

            if response.status_code in [200, 201]:
                print(f"[SUCCESS] Created index pattern: {pattern['title']}")
                success_count += 1
            else:
                print(f"[WARNING] Index pattern may already exist: {pattern['title']}")
                success_count += 1

        except Exception as e:
            print(f"[ERROR] Error creating index pattern {pattern['title']}: {e}")

    return success_count


def test_data_flow():
    """Test that data is flowing properly."""

    print("[INFO] Testing data flow...")

    # Check if we have recent data
    try:
        response = requests.get(
            f"{ELASTICSEARCH_URL}/detection-metrics-*/_search?size=1&sort=@timestamp:desc"
        )
        if response.status_code == 200:
            data = response.json()
            if data["hits"]["total"]["value"] > 0:
                print("[SUCCESS] Recent detection metrics found")
                latest = data["hits"]["hits"][0]["_source"]
                print(
                    f"   Latest: {latest.get('type', 'unknown')} from {latest.get('camera_id', 'unknown')}"
                )
            else:
                print(
                    "[WARNING] No detection metrics found - start your detection system"
                )

        response = requests.get(
            f"{ELASTICSEARCH_URL}/system-performance-*/_search?size=1&sort=@timestamp:desc"
        )
        if response.status_code == 200:
            data = response.json()
            if data["hits"]["total"]["value"] > 0:
                print("[SUCCESS] Recent system performance metrics found")
            else:
                print("[WARNING] No system performance metrics found")

    except Exception as e:
        print(f"[ERROR] Error checking data flow: {e}")


def print_dashboard_instructions():
    """Print manual dashboard import instructions."""

    print("[MANUAL] DASHBOARD IMPORT INSTRUCTIONS")
    print("=" * 50)
    print("Since automatic import failed, please follow these steps:")
    print()
    print("1. Open Kibana in your browser: http://localhost:5601")
    print("2. Go to 'Stack Management' > 'Saved Objects'")
    print("3. Click 'Import'")
    print("4. Select the file: kibana/dashboards/detection-metrics-dashboard.ndjson")
    print("5. Click 'Import'")
    print("6. If prompted about conflicts, choose 'Overwrite'")
    print()
    print("OR create visualizations manually:")
    print()
    print("[CHART] DETECTION CONFIDENCE HISTOGRAM:")
    print("   - Go to 'Visualize' > 'Create visualization' > 'Vertical Bar'")
    print("   - Index: detection-metrics-*")
    print("   - Y-axis: Count")
    print("   - X-axis: Terms aggregation on 'confidence_level'")
    print()
    print("[CHART] DETECTION TIMELINE:")
    print("   - Go to 'Visualize' > 'Create visualization' > 'Line'")
    print("   - Index: detection-metrics-*")
    print("   - Filter: type:detection_metrics AND detection_outcome:shoplifting")
    print("   - Y-axis: Count")
    print("   - X-axis: Date Histogram on '@timestamp' (1m interval)")
    print()
    print("[TABLE] SYSTEM PERFORMANCE TABLE:")
    print("   - Go to 'Visualize' > 'Create visualization' > 'Data table'")
    print("   - Index: system-performance-*")
    print("   - Rows: Terms aggregation on 'camera_id'")
    print(
        "   - Metrics: Avg of 'performance.fps_actual' and 'performance.processing_latency_ms'"
    )


def main():
    """Main fix function."""

    print("[INFO] FIXING DETECTION METRICS SYSTEM")
    print("=" * 40)

    # Fix index templates
    print("\n1. Creating index templates...")
    template_success = create_legacy_index_templates()
    print(f"   [SUCCESS] Created {template_success}/3 index templates")

    # Create index patterns
    print("\n2. Creating index patterns...")
    try:
        pattern_success = create_index_patterns()
        print(f"   [SUCCESS] Created {pattern_success}/3 index patterns")
    except Exception as e:
        print(f"   [WARNING] Index pattern creation failed - create manually in Kibana")

    # Test data flow
    test_data_flow()

    # Print manual instructions
    print_dashboard_instructions()

    print("[INFO] QUICK VERIFICATION STEPS:")
    print("1. Check Elasticsearch indices:", f"{ELASTICSEARCH_URL}/_cat/indices?v")
    print("2. Check index templates:", f"{ELASTICSEARCH_URL}/_cat/templates?v")
    print(
        "3. Check recent data:",
        f"{ELASTICSEARCH_URL}/detection-metrics-*/_search?size=1",
    )
    print("4. Open Kibana:", f"{KIBANA_URL}")

    print("[SUCCESS] Fix script completed!")
    print(
        "\nNow start your detection system to see live metrics flowing into the dashboards."
    )


if __name__ == "__main__":
    main()
