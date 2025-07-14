#!/usr/bin/env python3
"""
Fix index templates for Elasticsearch compatibility
"""

import json
import requests
import os

ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')

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
                    "refresh_interval": "1s"
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
                                "label": {"type": "keyword"}
                            }
                        },
                        "alert": {
                            "properties": {
                                "triggered": {"type": "boolean"},
                                "level": {"type": "keyword"},
                                "alert_type": {"type": "keyword"}
                            }
                        },
                        "confidence_level": {"type": "keyword"},
                        "detection_outcome": {"type": "keyword"}
                    }
                }
            }
        },
        {
            "name": "system-performance",
            "template": {
                "index_patterns": ["system-performance-*"],
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "refresh_interval": "5s"
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
                                "dropped_frames": {"type": "integer"}
                            }
                        },
                        "fps_status": {"type": "keyword"}
                    }
                }
            }
        },
        {
            "name": "camera-health",
            "template": {
                "index_patterns": ["camera-health-*"],
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "refresh_interval": "10s"
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
                                "status": {"type": "keyword"}
                            }
                        }
                    }
                }
            }
        }
    ]
    
    success_count = 0
    for template in templates:
        try:
            # Try new format first
            response = requests.put(
                f"{ELASTICSEARCH_URL}/_index_template/{template['name']}",
                json=template['template'],
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                print(f"[SUCCESS] Created index template (new format): {template['name']}")
                success_count += 1
            else:
                # Fall back to legacy format
                response = requests.put(
                    f"{ELASTICSEARCH_URL}/_template/{template['name']}",
                    json=template['template'],
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code in [200, 201]:
                    print(f"[SUCCESS] Created index template (legacy format): {template['name']}")
                    success_count += 1
                else:
                    print(f"[FAILED] Failed to create template {template['name']}: {response.text}")
                    
        except Exception as e:
            print(f"[ERROR] Error creating template {template['name']}: {e}")
    
    return success_count

if __name__ == "__main__":
    print("[INFO] Fixing index templates for Elasticsearch compatibility...")
    success = create_legacy_index_templates()
    print(f"\n[SUCCESS] Successfully created {success}/3 index templates") 