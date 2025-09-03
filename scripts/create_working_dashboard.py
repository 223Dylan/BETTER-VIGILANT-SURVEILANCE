#!/usr/bin/env python3
"""
Create a working detection dashboard with corrected field formatting
"""

import json
import time

import requests

KIBANA_URL = "http://localhost:5601"


def wait_for_kibana(max_retries=30):
    """Wait for Kibana to be ready."""
    print("Waiting for Kibana to be ready...")

    for i in range(max_retries):
        try:
            response = requests.get(f"{KIBANA_URL}/api/status", timeout=5)
            if response.status_code == 200:
                print("✓ Kibana is ready!")
                return True
        except requests.exceptions.ConnectionError:
            pass

        print(f"Attempt {i+1}/{max_retries} - Kibana not ready yet...")
        time.sleep(2)

    return False


def create_index_pattern(pattern_name, time_field="@timestamp"):
    """Create an index pattern in Kibana."""
    print(f"Creating index pattern: {pattern_name}")

    data = {"attributes": {"title": pattern_name, "timeFieldName": time_field}}

    try:
        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/index-pattern/{pattern_name.replace('*', 'pattern')}",
            json=data,
            headers={"kbn-xsrf": "true", "Content-Type": "application/json"},
            timeout=10,
        )

        if response.status_code in [200, 201]:
            print(f"✓ Created index pattern: {pattern_name}")
            return True
        elif response.status_code == 409:
            print(f"✓ Index pattern already exists: {pattern_name}")
            return True
        else:
            print(
                f"✗ Failed to create index pattern {pattern_name}: {response.status_code}"
            )
            return False

    except Exception as e:
        print(f"✗ Error creating index pattern {pattern_name}: {e}")
        return False


def create_simple_visualization():
    """Create a very simple visualization to test the approach."""
    print("Creating simple detection count visualization...")

    viz_data = {
        "attributes": {
            "title": "Detection Count",
            "visState": json.dumps(
                {
                    "title": "Detection Count",
                    "type": "metric",
                    "params": {
                        "addTooltip": True,
                        "addLegend": False,
                        "type": "metric",
                        "metric": {
                            "percentageMode": False,
                            "useRanges": False,
                            "colorSchema": "Green to Red",
                            "metricColorMode": "None",
                            "colorsRange": [{"from": 0, "to": 10000}],
                            "labels": {"show": True},
                            "invertColors": False,
                            "style": {
                                "bgFill": "#000",
                                "bgColor": False,
                                "labelColor": False,
                                "subText": "",
                                "fontSize": 60,
                            },
                        },
                    },
                    "aggs": [
                        {
                            "id": "1",
                            "enabled": True,
                            "type": "count",
                            "schema": "metric",
                            "params": {},
                        }
                    ],
                }
            ),
            "uiStateJSON": "{}",
            "description": "Simple count of detection events",
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps(
                    {
                        "index": "detection-metrics-*",
                        "query": {"match": {"type": "detection_metrics"}},
                        "filter": [],
                    }
                )
            },
        }
    }

    try:
        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/visualization/simple-detection-count",
            json=viz_data,
            headers={"kbn-xsrf": "true", "Content-Type": "application/json"},
            timeout=15,
        )

        if response.status_code in [200, 201]:
            print("✓ Created simple detection count visualization")
            return True
        else:
            print(f"✗ Failed to create visualization: {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"✗ Error creating visualization: {e}")
        return False


def create_timeline_chart():
    """Create a simple timeline chart."""
    print("Creating detection timeline chart...")

    viz_data = {
        "attributes": {
            "title": "Detection Timeline",
            "visState": json.dumps(
                {
                    "title": "Detection Timeline",
                    "type": "line",
                    "params": {
                        "grid": {"categoryLines": False, "style": {"color": "#eee"}},
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
                                "show": True,
                                "type": "line",
                                "mode": "normal",
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
                            "type": "date_histogram",
                            "schema": "segment",
                            "params": {
                                "field": "@timestamp",
                                "interval": "auto",
                                "customInterval": "2h",
                                "min_doc_count": 1,
                                "extended_bounds": {},
                            },
                        },
                    ],
                }
            ),
            "uiStateJSON": "{}",
            "description": "Timeline of detection events",
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps(
                    {
                        "index": "detection-metrics-*",
                        "query": {"match_all": {}},
                        "filter": [],
                    }
                )
            },
        }
    }

    try:
        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/visualization/detection-timeline-simple",
            json=viz_data,
            headers={"kbn-xsrf": "true", "Content-Type": "application/json"},
            timeout=15,
        )

        if response.status_code in [200, 201]:
            print("✓ Created detection timeline visualization")
            return True
        else:
            print(f"✗ Failed to create timeline: {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ Error creating timeline: {e}")
        return False


def create_simple_dashboard():
    """Create a simple dashboard with the visualizations."""
    print("Creating simple dashboard...")

    dashboard_data = {
        "attributes": {
            "title": "Simple Detection Dashboard",
            "hits": 0,
            "description": "Basic detection monitoring dashboard",
            "panelsJSON": json.dumps(
                [
                    {
                        "version": "8.12.1",
                        "gridData": {"x": 0, "y": 0, "w": 24, "h": 15, "i": "1"},
                        "panelIndex": "1",
                        "embeddableConfig": {},
                        "panelRefName": "panel_1",
                    },
                    {
                        "version": "8.12.1",
                        "gridData": {"x": 24, "y": 0, "w": 24, "h": 15, "i": "2"},
                        "panelIndex": "2",
                        "embeddableConfig": {},
                        "panelRefName": "panel_2",
                    },
                ]
            ),
            "optionsJSON": json.dumps(
                {"useMargins": True, "syncColors": False, "hidePanelTitles": False}
            ),
            "version": 1,
            "timeRestore": False,
            "timeTo": "now",
            "timeFrom": "now-24h",
            "refreshInterval": {"pause": True, "value": 0},
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps(
                    {"query": {"query": "", "language": "kuery"}, "filter": []}
                )
            },
        },
        "references": [
            {
                "name": "panel_1",
                "type": "visualization",
                "id": "simple-detection-count",
            },
            {
                "name": "panel_2",
                "type": "visualization",
                "id": "detection-timeline-simple",
            },
        ],
    }

    try:
        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/dashboard/simple-detection-dashboard",
            json=dashboard_data,
            headers={"kbn-xsrf": "true", "Content-Type": "application/json"},
            timeout=15,
        )

        if response.status_code in [200, 201]:
            print("✓ Created Simple Detection Dashboard")
            return True
        else:
            print(f"✗ Failed to create dashboard: {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"✗ Error creating dashboard: {e}")
        return False


def main():
    """Main function to create working dashboard."""
    print("Creating Working Detection Dashboard")
    print("=" * 50)

    # Wait for Kibana
    if not wait_for_kibana():
        print("Cannot proceed - Kibana not ready")
        return

    success_count = 0
    total_steps = 5

    # Step 1: Create index patterns
    if create_index_pattern("detection-metrics-*"):
        success_count += 1
    if create_index_pattern("system-performance-*"):
        success_count += 1

    # Step 2: Create simple visualizations
    if create_simple_visualization():
        success_count += 1
    if create_timeline_chart():
        success_count += 1

    # Step 3: Create dashboard
    if create_simple_dashboard():
        success_count += 1

    print("\n" + "=" * 50)
    print(f"Completed {success_count}/{total_steps} steps successfully")

    if success_count >= 3:
        print("✓ Basic detection dashboard created successfully!")
        print(f"\nAccess your dashboard at:")
        print(f"{KIBANA_URL}/app/dashboards#/view/simple-detection-dashboard")
        print(f"\nTo add more visualizations:")
        print(f"1. Go to {KIBANA_URL}/app/visualize")
        print(f"2. Create new visualizations using your index patterns")
        print(f"3. Add them to the dashboard")
    else:
        print("✗ Dashboard creation failed")
        print("\nTry creating dashboards manually:")
        print(f"1. Go to {KIBANA_URL}")
        print(f"2. Create visualizations in Visualize section")
        print(f"3. Create dashboard and add visualizations")


if __name__ == "__main__":
    main()
