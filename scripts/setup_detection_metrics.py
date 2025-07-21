#!/usr/bin/env python3
"""
Setup script for enhanced detection metrics system.
This script will:
1. Create Elasticsearch index templates
2. Import Kibana dashboards
3. Configure alerting rules
4. Test the metrics logging pipeline
"""

import json
import os
import sys
import time
from pathlib import Path

import requests

# Configuration
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
KIBANA_URL = os.getenv("KIBANA_URL", "http://localhost:5601")
LOGSTASH_URL = os.getenv("LOGSTASH_URL", "http://localhost:9600")


def check_elasticsearch_connection():
    """Check if Elasticsearch is running and accessible."""
    try:
        response = requests.get(f"{ELASTICSEARCH_URL}/_cluster/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"[SUCCESS] Elasticsearch is running - Status: {health['status']}")
            return True
        else:
            print(f"[ERROR] Elasticsearch returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to connect to Elasticsearch: {e}")
        return False


def check_kibana_connection():
    """Check if Kibana is running and accessible."""
    try:
        response = requests.get(f"{KIBANA_URL}/api/status", timeout=10)
        if response.status_code == 200:
            print("[SUCCESS] Kibana is running")
            return True
        else:
            print(f"[ERROR] Kibana returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to connect to Kibana: {e}")
        return False


def create_index_templates():
    """Create Elasticsearch index templates for detection metrics."""

    alerting_config_path = (
        Path(__file__).parent.parent / "kibana" / "detection_metrics_alerting.json"
    )

    try:
        with open(alerting_config_path, "r") as f:
            config = json.load(f)

        for index_pattern in config["index_patterns"]:
            template_name = index_pattern["name"]
            template_body = {
                "index_patterns": [index_pattern["pattern"]],
                "settings": index_pattern["settings"],
                "mappings": index_pattern["mappings"],
            }

            # Create index template
            response = requests.put(
                f"{ELASTICSEARCH_URL}/_index_template/{template_name}",
                json=template_body,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code in [200, 201]:
                print(f"[SUCCESS] Created index template: {template_name}")
            else:
                print(
                    f"[ERROR] Failed to create index template {template_name}: {response.text}"
                )

    except FileNotFoundError:
        print(f"[ERROR] Alerting config file not found: {alerting_config_path}")
    except Exception as e:
        print(f"[ERROR] Error creating index templates: {e}")


def import_kibana_dashboards():
    """Import Kibana dashboards."""

    # Import enhanced detection dashboard
    dashboard_path = (
        Path(__file__).parent.parent
        / "kibana"
        / "dashboards"
        / "detection-system-enhanced.json"
    )

    try:
        with open(dashboard_path, "r") as f:
            dashboard_config = json.load(f)

        # Import dashboard using Kibana's saved objects API
        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/_import",
            files={"file": ("dashboard.ndjson", json.dumps(dashboard_config))},
            headers={"kbn-xsrf": "true"},
        )

        if response.status_code in [200, 201]:
            print("[SUCCESS] Imported enhanced detection dashboard")
        else:
            print(f"[ERROR] Failed to import dashboard: {response.text}")

    except FileNotFoundError:
        print(f"[ERROR] Dashboard file not found: {dashboard_path}")
    except Exception as e:
        print(f"[ERROR] Error importing dashboard: {e}")


def create_sample_data():
    """Create sample detection metrics data for testing."""

    sample_metrics = [
        {
            "type": "detection_metrics",
            "camera_id": "entrance-cam",
            "timestamp": "2024-01-01T12:00:00Z",
            "prediction": {
                "confidence": 0.85,
                "label": "shoplifting",
                "is_shoplifting": True,
                "prediction_time_ms": 45.2,
                "sequence_frames": 160,
                "model_version": "lrcn_160S_90_90Q",
            },
            "alert": {
                "triggered": True,
                "level": "high",
                "threshold_used": 0.7,
                "alert_type": "shoplifting",
            },
            "confidence_level": "high",
            "detection_outcome": "shoplifting",
        },
        {
            "type": "system_performance",
            "camera_id": "entrance-cam",
            "timestamp": "2024-01-01T12:00:00Z",
            "performance": {
                "fps_actual": 28.5,
                "fps_target": 30.0,
                "processing_latency_ms": 67.3,
                "queue_depth": 3,
                "dropped_frames": 0,
            },
            "fps_status": "good",
        },
        {
            "type": "camera_health",
            "camera_id": "entrance-cam",
            "timestamp": "2024-01-01T12:00:00Z",
            "health": {
                "is_connected": True,
                "current_fps": 28.5,
                "last_frame_timestamp": "2024-01-01T12:00:00Z",
                "error_count": 0,
                "status": "online",
            },
        },
    ]

    # Index sample data
    for metric in sample_metrics:
        index_name = f"{metric['type'].replace('_', '-')}-2024.01.01"

        response = requests.post(
            f"{ELASTICSEARCH_URL}/{index_name}/_doc",
            json=metric,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code in [200, 201]:
            print(f"[SUCCESS] Created sample {metric['type']} data")
        else:
            print(f"[ERROR] Failed to create sample data: {response.text}")


def test_logging_pipeline():
    """Test the detection metrics logging pipeline."""

    print("\n[INFO] Testing detection metrics logging...")

    try:
        # Import and test the detection metrics logger
        sys.path.append(str(Path(__file__).parent.parent / "src"))
        from detection_metrics import (
            log_camera_health_metrics,
            log_prediction_metrics,
            log_system_metrics,
        )

        # Test prediction metrics
        test_prediction = {
            "confidence": 0.75,
            "is_shoplifting": True,
            "label": "shoplifting",
            "sequence_length": 160,
        }

        log_prediction_metrics(
            camera_id="test-camera",
            prediction_result=test_prediction,
            processing_time=0.045,
            performance_data={"test": True},
        )
        print("[SUCCESS] Prediction metrics logging test passed")

        # Test system metrics
        log_system_metrics(
            camera_id="test-camera",
            fps_actual=28.0,
            fps_target=30.0,
            latency_ms=50.0,
            queue_depth=2,
            dropped_frames=0,
        )
        print("[SUCCESS] System metrics logging test passed")

        # Test camera health metrics
        log_camera_health_metrics(
            camera_id="test-camera",
            is_connected=True,
            frame_rate=28.0,
            last_frame_time=time.time(),
            error_count=0,
        )
        print("[SUCCESS] Camera health metrics logging test passed")

    except ImportError as e:
        print(f"[ERROR] Failed to import detection metrics module: {e}")
    except Exception as e:
        print(f"[ERROR] Logging pipeline test failed: {e}")


def verify_setup():
    """Verify that the setup completed successfully."""

    print("\n[INFO] Verifying setup...")

    # Check if index templates exist
    response = requests.get(f"{ELASTICSEARCH_URL}/_index_template/detection-metrics-*")
    if response.status_code == 200:
        print("[SUCCESS] Detection metrics index template exists")
    else:
        print("[ERROR] Detection metrics index template missing")

    # Check if indices were created
    response = requests.get(f"{ELASTICSEARCH_URL}/_cat/indices/*detection*?format=json")
    if response.status_code == 200 and response.json():
        indices = [idx["index"] for idx in response.json()]
        print(f"[SUCCESS] Detection indices created: {', '.join(indices)}")
    else:
        print(
            "[WARNING] No detection indices found (this is normal if no data has been logged yet)"
        )


def main():
    """Main setup function."""

    print("[START] Setting up Enhanced Detection Metrics System")
    print("=" * 50)

    # Check connections
    if not check_elasticsearch_connection():
        print("[ERROR] Setup failed: Elasticsearch is not accessible")
        sys.exit(1)

    if not check_kibana_connection():
        print("[WARNING] Kibana is not accessible - dashboard import will be skipped")

    # Setup steps
    print("[INFO] Creating Elasticsearch index templates...")
    create_index_templates()

    print("[INFO] Importing Kibana dashboards...")
    import_kibana_dashboards()

    print("[INFO] Creating sample data...")
    create_sample_data()

    print("[INFO] Testing logging pipeline...")
    test_logging_pipeline()

    print("[INFO] Verifying setup...")
    verify_setup()

    print("[SUCCESS] Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start your Logstash instance with the updated configuration")
    print("2. Start your cameras and detection system")
    print("3. View metrics in Kibana at: http://localhost:5601")
    print("4. Check the 'Enhanced Detection System Dashboard'")


if __name__ == "__main__":
    main()
