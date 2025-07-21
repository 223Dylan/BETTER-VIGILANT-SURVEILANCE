import json
import os

json_path = os.path.join(os.path.dirname(__file__), "camera-system.json")
ndjson_path = os.path.join(os.path.dirname(__file__), "camera-system.ndjson")

with open(json_path, "r") as f:
    data = json.load(f)

with open(ndjson_path, "w") as f:
    for obj in data["objects"]:
        f.write(json.dumps(obj) + "\n")

print(f"Exported {len(data['objects'])} objects to {ndjson_path}")
