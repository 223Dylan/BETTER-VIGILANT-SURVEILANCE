#!/usr/bin/env python3
import requests
import time

KIBANA_URL = "http://localhost:5601"

patterns = [
    "detection-metrics-*",
    "system-performance-*", 
    "detection-alerts-*",
    "camera-events-*"
]

def create_pattern(pattern):
    url = f"{KIBANA_URL}/api/saved_objects/index-pattern/{pattern.replace('*', 'pattern')}"
    
    payload = {
        "attributes": {
            "title": pattern,
            "timeFieldName": "@timestamp"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "kbn-xsrf": "true"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 409]:
            print(f"[SUCCESS] Created pattern: {pattern}")
            return True
        else:
            print(f"[FAILED] Failed: {pattern} - {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

# Wait for Kibana
print("[INFO] Waiting for Kibana...")
for _ in range(30):
    try:
        requests.get(f"{KIBANA_URL}/api/status", timeout=5)
        break
    except:
        time.sleep(10)

# Create patterns
for pattern in patterns:
    create_pattern(pattern)
    time.sleep(1)

print("[DONE] Check Kibana at http://localhost:5601")
