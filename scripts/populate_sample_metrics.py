#!/usr/bin/env python3
"""
Script to populate sample metrics data for testing the enhanced metrics system.
"""

import requests
import json
from datetime import datetime, timedelta
import random

def add_system_metrics():
    """Add sample system metrics data."""
    print("Adding sample system metrics...")
    
    # Generate data for the last hour
    base_time = datetime.now()
    
    for i in range(12):  # 12 data points over last hour
        timestamp = base_time - timedelta(minutes=i*5)
        
        # Generate realistic system metrics
        cpu_usage = random.uniform(20, 80)
        memory_usage = random.uniform(60, 95)
        disk_usage = random.uniform(30, 70)
        active_cameras = random.randint(1, 3)
        
        doc = {
            "@timestamp": timestamp.isoformat(),
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
            "active_cameras": active_cameras
        }
        
        response = requests.post(
            'http://localhost:9200/system_metrics/_doc',
            json=doc,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code in [200, 201]:
            print(f"[SUCCESS] Added system metrics for {timestamp.strftime('%H:%M')}")
        else:
            print(f"[ERROR] Failed to add system metrics: {response.status_code}")

def add_detection_metrics():
    """Add sample detection metrics data."""
    print("\nAdding sample detection metrics...")
    
    base_time = datetime.now()
    cameras = ["camera-1", "testing-camera", "camera-2"]
    labels = ["person", "shoplifting", "normal_activity", "suspicious_behavior"]
    
    for i in range(20):  # 20 detection events
        timestamp = base_time - timedelta(minutes=random.randint(0, 60))
        camera_id = random.choice(cameras)
        label = random.choice(labels)
        confidence = random.uniform(0.3, 0.95)
        is_shoplifting = label == "shoplifting" or (label == "suspicious_behavior" and confidence > 0.8)
        
        doc = {
            "@timestamp": timestamp.isoformat(),
            "camera_id": camera_id,
            "prediction": {
                "confidence": confidence,
                "label": label,
                "is_shoplifting": is_shoplifting
            },
            "alert": {
                "triggered": is_shoplifting and confidence > 0.7,
                "level": "high" if is_shoplifting and confidence > 0.9 else "medium" if is_shoplifting else "low",
                "type": "detection"
            },
            "fps_actual": random.uniform(25, 30),
            "fps_target": 30,
            "latency_ms": random.uniform(50, 200),
            "queue_depth": random.randint(0, 5),
            "dropped_frames": random.randint(0, 2)
        }
        
        response = requests.post(
            'http://localhost:9200/detection-metrics-2025.07.17/_doc',
            json=doc,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code in [200, 201]:
            print(f"[SUCCESS] Added detection for {camera_id}: {label} ({confidence:.2f})")
        else:
            print(f"[ERROR] Failed to add detection metrics: {response.status_code}")

def refresh_indices():
    """Refresh indices to make data immediately available."""
    print("\nRefreshing indices...")
    
    for index in ["system_metrics", "detection-metrics-2025.07.17"]:
        response = requests.post(f'http://localhost:9200/{index}/_refresh')
        if response.status_code == 200:
            print(f"[SUCCESS] Refreshed {index}")
        else:
            print(f"[ERROR] Failed to refresh {index}: {response.status_code}")

def test_metrics_endpoints():
    """Test the metrics endpoints to verify they work."""
    print("\nTesting metrics endpoints...")
    
    endpoints = [
        "/api/metrics/health",
        "/api/metrics/summary", 
        "/api/metrics/system?time_range=1h&limit=10",
        "/api/metrics/cameras",
        "/api/metrics/alerts/recent?limit=5"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f'http://localhost:8001{endpoint}', timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"[SUCCESS] {endpoint} - OK")
                if endpoint == "/api/metrics/summary":
                    print(f"   Detections today: {data.get('total_detections_today', 0)}")
                    print(f"   Alerts today: {data.get('alert_count_today', 0)}")
            else:
                print(f"[ERROR] {endpoint} - HTTP {response.status_code}")
        except Exception as e:
            print(f"[ERROR] {endpoint} - Error: {e}")

if __name__ == "__main__":
    print("Populating sample metrics data...")
    
    try:
        add_system_metrics()
        add_detection_metrics()
        refresh_indices()
        test_metrics_endpoints()
        
        print("\nSample metrics data populated successfully!")
        print("Your metrics dashboard should now display data!")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("Make sure Elasticsearch and your API server are running.") 