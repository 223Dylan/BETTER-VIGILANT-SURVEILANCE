import requests
import json
import os
import time

def wait_for_kibana():
    """Wait for Kibana to be ready."""
    kibana_url = "http://localhost:5601"
    while True:
        try:
            response = requests.get(f"{kibana_url}/api/status")
            if response.status_code == 200:
                print("Kibana is ready!")
                break
        except requests.exceptions.ConnectionError:
            print("Waiting for Kibana to start...")
            time.sleep(5)

def import_dashboard():
    """Import the dashboard into Kibana."""
    kibana_url = "http://localhost:5601"
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboards", "camera-system.ndjson")
    
    # Read dashboard configuration
    with open(dashboard_path, 'r') as f:
        dashboard_config = json.load(f)
    
    # Import dashboard
    import_url = f"{kibana_url}/api/saved_objects/_import"
    files = {
        'file': ('dashboard.ndjson', json.dumps(dashboard_config))
    }
    
    try:
        response = requests.post(import_url, files=files)
        response.raise_for_status()
        print("Dashboard imported successfully!")
        print(f"Access your dashboard at: {kibana_url}/app/dashboards#/view/camera-system-overview")
    except requests.exceptions.RequestException as e:
        print(f"Error importing dashboard: {e}")

if __name__ == "__main__":
    wait_for_kibana()
    import_dashboard() 