#!/usr/bin/env python3
"""
Create a simple detection dashboard using Kibana API
This bypasses the complex import issues by creating dashboards piece by piece
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

    print("✗ Kibana is not ready after maximum retries")
    return False


def create_index_pattern(pattern_name, time_field="@timestamp"):
    """Create an index pattern in Kibana."""
    print(f"Creating index pattern: {pattern_name}")

    data = {"attributes": {"title": pattern_name, "timeFieldName": time_field}}

    try:
        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/index-pattern/{pattern_name}",
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


def create_detection_confidence_viz():
    """Create detection confidence distribution visualization."""
    print("Creating Detection Confidence Distribution visualization...")

    viz_data = {
        "attributes": {
            "title": "Detection Confidence Distribution",
            "visState": json.dumps(
                {
                    "title": "Detection Confidence Distribution",
                    "type": "histogram",
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
                                "title": {"text": "Confidence Level"},
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
            "description": "Shows distribution of detection confidence levels",
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

    try:
        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/visualization/detection-confidence-dist",
            json=viz_data,
            headers={"kbn-xsrf": "true", "Content-Type": "application/json"},
            timeout=15,
        )

        if response.status_code in [200, 201]:
            print("✓ Created Detection Confidence Distribution visualization")
            return True
        else:
            print(f"✗ Failed to create visualization: {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"✗ Error creating visualization: {e}")
        return False


def create_detection_timeline_viz():
    """Create detection events timeline visualization."""
    print("Creating Detection Events Timeline visualization...")

    viz_data = {
        "attributes": {
            "title": "Shoplifting Detection Timeline",
            "visState": json.dumps(
                {
                    "title": "Shoplifting Detection Timeline",
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
                                "title": {"text": "Time"},
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
                                "title": {"text": "Detections per Minute"},
                            }
                        ],
                        "seriesParams": [
                            {
                                "show": True,
                                "type": "line",
                                "mode": "normal",
                                "data": {"label": "Shoplifting Detections", "id": "1"},
                                "valueAxis": "ValueAxis-1",
                                "drawLinesBetweenPoints": True,
                                "lineWidth": 2,
                                "interpolate": "linear",
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
                                "timeRange": {"from": "now-1h", "to": "now"},
                                "useNormalizedEsInterval": True,
                                "scaleMetricValues": False,
                                "interval": "1m",
                                "drop_partials": False,
                                "min_doc_count": 1,
                                "extended_bounds": {},
                            },
                        },
                    ],
                }
            ),
            "uiStateJSON": "{}",
            "description": "Shows shoplifting detections over time",
            "kibanaSavedObjectMeta": json.dumps(
                {
                    "searchSourceJSON": json.dumps(
                        {
                            "index": "detection-metrics-*",
                            "query": {
                                "bool": {
                                    "must": [
                                        {"match": {"type": "detection_metrics"}},
                                        {"match": {"detection_outcome": "shoplifting"}},
                                    ]
                                }
                            },
                            "filter": [],
                        }
                    )
                }
            ),
        }
    }

    try:
        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/visualization/detection-timeline",
            json=viz_data,
            headers={"kbn-xsrf": "true", "Content-Type": "application/json"},
            timeout=15,
        )

        if response.status_code in [200, 201]:
            print("✓ Created Shoplifting Detection Timeline visualization")
            return True
        else:
            print(f"✗ Failed to create visualization: {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ Error creating visualization: {e}")
        return False


def create_system_performance_gauge():
    """Create system performance gauge."""
    print("Creating System Performance Gauge...")

    viz_data = {
        "attributes": {
            "title": "System Performance",
            "visState": json.dumps(
                {
                    "title": "System Performance",
                    "type": "gauge",
                    "params": {
                        "type": "gauge",
                        "addTooltip": True,
                        "addLegend": True,
                        "gauge": {
                            "verticalSplit": False,
                            "extendRange": True,
                            "percentageMode": False,
                            "gaugeType": "Arc",
                            "gaugeStyle": "Full",
                            "backStyle": "Full",
                            "colorSchema": "Green to Red",
                            "gaugeColorMode": "Labels",
                            "colorsRange": [
                                {"from": 0, "to": 15},
                                {"from": 15, "to": 25},
                                {"from": 25, "to": 30},
                            ],
                            "invertColors": False,
                            "labels": {"show": True, "color": "black"},
                            "scale": {
                                "show": True,
                                "labels": False,
                                "color": "rgba(105,112,125,0.2)",
                            },
                            "type": "meter",
                            "style": {
                                "bgWidth": 0.9,
                                "width": 0.9,
                                "mask": False,
                                "bgMask": False,
                                "maskBars": 50,
                                "bgFill": "rgba(105,112,125,0.2)",
                                "bgColor": False,
                                "subText": "",
                                "fontSize": 60,
                                "labelColor": True,
                            },
                        },
                    },
                    "aggs": [
                        {
                            "id": "1",
                            "enabled": True,
                            "type": "avg",
                            "schema": "metric",
                            "params": {"field": "performance.fps_actual"},
                        }
                    ],
                }
            ),
            "uiStateJSON": "{}",
            "description": "Shows current system performance (FPS)",
            "kibanaSavedObjectMeta": json.dumps(
                {
                    "searchSourceJSON": json.dumps(
                        {
                            "index": "system-performance-*",
                            "query": {"match": {"type": "system_performance"}},
                            "filter": [],
                        }
                    )
                }
            ),
        }
    }

    try:
        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/visualization/system-performance-gauge",
            json=viz_data,
            headers={"kbn-xsrf": "true", "Content-Type": "application/json"},
            timeout=15,
        )

        if response.status_code in [200, 201]:
            print("✓ Created System Performance Gauge")
            return True
        else:
            print(f"✗ Failed to create gauge: {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ Error creating gauge: {e}")
        return False


def create_detection_dashboard():
    """Create the main detection dashboard."""
    print("Creating Detection Dashboard...")

    dashboard_data = {
        "attributes": {
            "title": "Detection System Dashboard",
            "hits": 0,
            "description": "Main dashboard for monitoring detection system",
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
                    {
                        "version": "8.12.1",
                        "gridData": {"x": 0, "y": 15, "w": 48, "h": 15, "i": "3"},
                        "panelIndex": "3",
                        "embeddableConfig": {},
                        "panelRefName": "panel_3",
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
            "kibanaSavedObjectMeta": json.dumps(
                {
                    "searchSourceJSON": json.dumps(
                        {"query": {"query": "", "language": "kuery"}, "filter": []}
                    )
                }
            ),
        },
        "references": [
            {
                "name": "panel_1",
                "type": "visualization",
                "id": "detection-confidence-dist",
            },
            {"name": "panel_2", "type": "visualization", "id": "detection-timeline"},
            {
                "name": "panel_3",
                "type": "visualization",
                "id": "system-performance-gauge",
            },
        ],
    }

    try:
        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/dashboard/detection-system-dashboard",
            json=dashboard_data,
            headers={"kbn-xsrf": "true", "Content-Type": "application/json"},
            timeout=15,
        )

        if response.status_code in [200, 201]:
            print("✓ Created Detection System Dashboard")
            return True
        else:
            print(f"✗ Failed to create dashboard: {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"✗ Error creating dashboard: {e}")
        return False


def main():
    """Main function to create detection dashboard."""
    print("Creating Simple Detection Dashboard")
    print("=" * 50)

    # Wait for Kibana
    if not wait_for_kibana():
        return

    success_count = 0
    total_steps = 6

    # Step 1: Create index patterns
    if create_index_pattern("detection-metrics-*"):
        success_count += 1
    if create_index_pattern("system-performance-*"):
        success_count += 1

    # Step 2: Create visualizations
    if create_detection_confidence_viz():
        success_count += 1
    if create_detection_timeline_viz():
        success_count += 1
    if create_system_performance_gauge():
        success_count += 1

    # Step 3: Create dashboard
    if create_detection_dashboard():
        success_count += 1

    print("\n" + "=" * 50)
    print(f"Completed {success_count}/{total_steps} steps successfully")

    if success_count >= 4:  # Index patterns + at least 2 visualizations + dashboard
        print("✓ Detection dashboard created successfully!")
        print(f"\nAccess your dashboard at:")
        print(f"{KIBANA_URL}/app/dashboards#/view/detection-system-dashboard")
        print(f"\nOr browse all dashboards at:")
        print(f"{KIBANA_URL}/app/dashboards")
    else:
        print("✗ Dashboard creation had some issues")
        print("Check the error messages above and try creating visualizations manually")


if __name__ == "__main__":
    main()
