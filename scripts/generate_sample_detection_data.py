#!/usr/bin/env python3
"""
Generate sample detection data for today's index to test visualizations.
"""

import json
import random
from datetime import datetime, timedelta

import requests


def generate_detection_data():
    """Generate sample detection metrics data for today."""
    print("Generating sample detection data...")

    # Get today's date for index name
    today = datetime.now().strftime("%Y.%m.%d")
    index_name = f"detection-metrics-{today}"

    print(f"Using index: {index_name}")

    # Generate data for the last 2 hours
    base_time = datetime.now()
    cameras = ["camera-1", "camera-2", "camera-3", "testing-camera"]
    labels = ["person", "shoplifting", "normal_activity", "suspicious_behavior"]

    success_count = 0

    for i in range(30):  # 30 detection events
        timestamp = base_time - timedelta(minutes=random.randint(0, 120))
        camera_id = random.choice(cameras)
        label = random.choice(labels)
        confidence = random.uniform(0.3, 0.95)
        is_shoplifting = label == "shoplifting" or (
            label == "suspicious_behavior" and confidence > 0.8
        )

        # Determine confidence level based on confidence value
        if confidence >= 0.9:
            confidence_level = "critical"
        elif confidence >= 0.7:
            confidence_level = "high"
        elif confidence >= 0.5:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        # Determine detection outcome
        detection_outcome = "shoplifting" if is_shoplifting else "normal"

        doc = {
            "@timestamp": timestamp.isoformat(),
            "type": "detection_metrics",
            "camera_id": camera_id,
            "prediction": {
                "confidence": confidence,
                "label": label,
                "is_shoplifting": is_shoplifting,
                "sequence_length": 160,
            },
            "alert": {
                "triggered": is_shoplifting and confidence > 0.7,
                "level": (
                    "high"
                    if is_shoplifting and confidence > 0.9
                    else "medium" if is_shoplifting else "low"
                ),
                "threshold_used": 0.7,
            },
            "performance": {
                "fps_actual": random.uniform(25, 30),
                "fps_target": 30,
                "latency_ms": random.uniform(50, 200),
                "queue_depth": random.randint(0, 5),
                "dropped_frames": random.randint(0, 2),
            },
            "confidence_level": confidence_level,
            "detection_outcome": detection_outcome,
        }

        try:
            response = requests.post(
                f"http://localhost:9200/{index_name}/_doc",
                json=doc,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            if response.status_code in [200, 201]:
                success_count += 1
                print(
                    f"[SUCCESS] Added detection for {camera_id}: {label} ({confidence:.2f}) - {confidence_level}"
                )
            else:
                print(f"[ERROR] Failed to add detection: {response.status_code}")

        except Exception as e:
            print(f"[ERROR] Failed to add detection: {e}")

    # Refresh the index to make data immediately available
    try:
        response = requests.post(f"http://localhost:9200/{index_name}/_refresh")
        if response.status_code == 200:
            print(f"[SUCCESS] Refreshed index {index_name}")
        else:
            print(f"[ERROR] Failed to refresh index: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Failed to refresh index: {e}")

    print(f"\nGenerated {success_count} detection events")
    return success_count > 0


def generate_system_performance_data():
    """Generate sample system performance data."""
    print("\nGenerating sample system performance data...")

    today = datetime.now().strftime("%Y.%m.%d")
    index_name = f"system-performance-{today}"

    print(f"Using index: {index_name}")

    base_time = datetime.now()
    success_count = 0

    for i in range(15):  # 15 performance data points
        timestamp = base_time - timedelta(minutes=random.randint(0, 60))
        camera_id = random.choice(["camera-1", "camera-2", "camera-3"])

        doc = {
            "@timestamp": timestamp.isoformat(),
            "type": "system_performance",
            "camera_id": camera_id,
            "performance": {
                "fps_actual": random.uniform(25, 30),
                "fps_target": 30,
                "fps_efficiency": random.uniform(0.8, 1.0),
                "memory_usage_mb": random.uniform(100, 500),
                "cpu_usage_percent": random.uniform(20, 80),
                "queue_depth": random.randint(0, 5),
                "latency_ms": random.uniform(50, 200),
            },
            "fps_status": "good" if random.uniform(0, 1) > 0.2 else "degraded",
        }

        try:
            response = requests.post(
                f"http://localhost:9200/{index_name}/_doc",
                json=doc,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            if response.status_code in [200, 201]:
                success_count += 1
                print(f"[SUCCESS] Added performance data for {camera_id}")
            else:
                print(f"[ERROR] Failed to add performance data: {response.status_code}")

        except Exception as e:
            print(f"[ERROR] Failed to add performance data: {e}")

    # Refresh the index
    try:
        response = requests.post(f"http://localhost:9200/{index_name}/_refresh")
        if response.status_code == 200:
            print(f"[SUCCESS] Refreshed index {index_name}")
    except Exception as e:
        print(f"[ERROR] Failed to refresh index: {e}")

    print(f"Generated {success_count} performance events")
    return success_count > 0


def main():
    """Main function to generate sample data."""
    print("Generating Sample Detection Data")
    print("=" * 50)

    try:
        # Generate detection data
        detection_success = generate_detection_data()

        # Generate system performance data
        performance_success = generate_system_performance_data()

        print("\n" + "=" * 50)
        if detection_success and performance_success:
            print("✓ Sample data generated successfully!")
            print("\nYour visualizations should now show data:")
            print("1. Go to http://localhost:5601/app/visualize")
            print("2. Open your existing visualizations")
            print("3. They should now display the sample data")
            print("\nOr create new visualizations with these fields:")
            print("- confidence_level (critical, high, medium, low)")
            print("- detection_outcome (shoplifting, normal)")
            print("- camera_id")
            print("- prediction.confidence")
        else:
            print("✗ Some data generation failed")
            print("Check that Elasticsearch is running on localhost:9200")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Elasticsearch is running: docker ps")


if __name__ == "__main__":
    main()
