#!/usr/bin/env python3
"""
Fixed dashboard import script for Kibana
Handles different dashboard formats and provides better error handling
"""

import json
import os
import time
from pathlib import Path

import requests

KIBANA_URL = "http://localhost:5601"


def wait_for_kibana(max_retries=30):
    """Wait for Kibana to be ready."""
    print("Waiting for Kibana to be ready...")

    for i in range(max_retries):
        try:
            response = requests.get(f"{KIBANA_URL}/api/status", timeout=5)
            if response.status_code == 200:
                print("Kibana is ready!")
                return True
        except requests.exceptions.ConnectionError:
            pass

        print(f"Attempt {i+1}/{max_retries} - Kibana not ready yet...")
        time.sleep(2)

    print("ERROR: Kibana is not ready after maximum retries")
    return False


def import_ndjson_dashboard(file_path):
    """Import a dashboard from NDJSON format."""
    print(f"Importing dashboard from: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        # Import using the correct format
        import_url = f"{KIBANA_URL}/api/saved_objects/_import"

        files = {"file": ("dashboard.ndjson", content, "application/json")}

        # Add required headers
        headers = {"kbn-xsrf": "true"}

        response = requests.post(import_url, files=files, headers=headers, timeout=30)

        if response.status_code in [200, 201]:
            print("✓ Dashboard imported successfully!")
            return True
        else:
            print(f"✗ Failed to import dashboard: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error importing dashboard: {e}")
        return False


def import_json_dashboard(file_path):
    """Import a dashboard from JSON format."""
    print(f"Importing dashboard from: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            dashboard_data = json.load(f)

        # Convert to NDJSON format
        ndjson_content = json.dumps(dashboard_data)

        import_url = f"{KIBANA_URL}/api/saved_objects/_import"

        files = {"file": ("dashboard.ndjson", ndjson_content, "application/json")}

        headers = {"kbn-xsrf": "true"}

        response = requests.post(import_url, files=files, headers=headers, timeout=30)

        if response.status_code in [200, 201]:
            print("✓ Dashboard imported successfully!")
            return True
        else:
            print(f"✗ Failed to import dashboard: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error importing dashboard: {e}")
        return False


def create_simple_dashboard():
    """Create a simple dashboard manually using the API."""
    print("Creating a simple detection dashboard...")

    # Create index pattern first
    index_pattern_data = {
        "attributes": {"title": "detection-metrics-*", "timeFieldName": "@timestamp"}
    }

    try:
        # Create index pattern
        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/index-pattern/detection-metrics-*",
            json=index_pattern_data,
            headers={"kbn-xsrf": "true", "Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code in [200, 201]:
            print("✓ Index pattern created")
        else:
            print(f"Index pattern may already exist: {response.status_code}")

        # Create a simple visualization
        viz_data = {
            "attributes": {
                "title": "Detection Confidence Distribution",
                "visState": json.dumps(
                    {
                        "title": "Detection Confidence Distribution",
                        "type": "histogram",
                        "params": {
                            "grid": {
                                "categoryLines": False,
                                "style": {"color": "#eee"},
                            },
                            "categoryAxes": [
                                {
                                    "id": "CategoryAxis-1",
                                    "type": "category",
                                    "position": "bottom",
                                    "show": True,
                                    "style": {},
                                    "scale": {"type": "linear"},
                                    "labels": {
                                        "show": True,
                                        "filter": True,
                                        "truncate": 100,
                                    },
                                    "title": {},
                                }
                            ],
                            "valueAxes": [
                                {
                                    "id": "ValueAxis-1",
                                    "name": "LeftAxis-1",
                                    "type": "value",
                                    "position": "left",
                                    "show": True,
                                    "style": {},
                                    "scale": {"type": "linear", "mode": "normal"},
                                    "labels": {
                                        "show": True,
                                        "rotate": 0,
                                        "filter": False,
                                        "truncate": 100,
                                    },
                                    "title": {"text": "Count"},
                                }
                            ],
                            "seriesParams": [
                                {
                                    "show": "true",
                                    "type": "histogram",
                                    "mode": "stacked",
                                    "data": {"label": "Count", "id": "1"},
                                    "valueAxis": "ValueAxis-1",
                                    "drawLinesBetweenPoints": True,
                                    "showCircles": True,
                                }
                            ],
                            "addTooltip": True,
                            "addLegend": True,
                            "legendPosition": "right",
                            "times": [],
                            "addTimeMarker": False,
                        },
                        "aggs": [
                            {
                                "id": "1",
                                "enabled": True,
                                "type": "count",
                                "schema": "metric",
                                "params": {},
                            },
                            {
                                "id": "2",
                                "enabled": True,
                                "type": "terms",
                                "schema": "segment",
                                "params": {
                                    "field": "confidence_level",
                                    "size": 5,
                                    "order": "desc",
                                    "orderBy": "1",
                                    "otherBucket": False,
                                    "otherBucketLabel": "Other",
                                    "missingBucket": False,
                                    "missingBucketLabel": "Missing",
                                },
                            },
                        ],
                    }
                ),
                "uiStateJSON": "{}",
                "description": "",
                "kibanaSavedObjectMeta": json.dumps(
                    {
                        "searchSourceJSON": json.dumps(
                            {
                                "index": "detection-metrics-*",
                                "query": {"match": {"type": "detection_metrics"}},
                                "filter": [],
                            }
                        )
                    }
                ),
            }
        }

        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/visualization/detection-confidence-histogram",
            json=viz_data,
            headers={"kbn-xsrf": "true", "Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code in [200, 201]:
            print("✓ Visualization created")
            return True
        else:
            print(f"✗ Failed to create visualization: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error creating dashboard: {e}")
        return False


def main():
    """Main function to import dashboards."""
    print("Kibana Dashboard Import Fix")
    print("=" * 40)

    # Wait for Kibana
    if not wait_for_kibana():
        return

    # Try to import existing dashboards
    dashboard_dir = Path("kibana/dashboards")

    if dashboard_dir.exists():
        dashboard_files = list(dashboard_dir.glob("*.ndjson")) + list(
            dashboard_dir.glob("*.json")
        )

        if dashboard_files:
            print(f"\nFound {len(dashboard_files)} dashboard files:")
            for file in dashboard_files:
                print(f"  - {file.name}")

            success_count = 0
            for file in dashboard_files:
                print(f"\nTrying to import: {file.name}")

                if file.suffix == ".ndjson":
                    if import_ndjson_dashboard(file):
                        success_count += 1
                elif file.suffix == ".json":
                    if import_json_dashboard(file):
                        success_count += 1

            print(
                f"\nSuccessfully imported {success_count}/{len(dashboard_files)} dashboards"
            )

            if success_count == 0:
                print("\nAll imports failed. Creating a simple dashboard instead...")
                create_simple_dashboard()
        else:
            print("No dashboard files found. Creating a simple dashboard...")
            create_simple_dashboard()
    else:
        print("Dashboard directory not found. Creating a simple dashboard...")
        create_simple_dashboard()

    print("\n" + "=" * 40)
    print("Dashboard import completed!")
    print(f"Access Kibana at: {KIBANA_URL}")
    print("Go to Dashboard section to view your dashboards")


if __name__ == "__main__":
    main()
