# Elasticsearch Index Mapping Setup Guide

This guide shows you how to add index mappings for your surveillance system's Kibana dashboards.

## Quick Answer: How to Add Index Mappings

You have **3 options** to add index mappings:

### Option 1: Automated Script (Recommended)
```bash
python scripts/setup_elasticsearch_mappings.py
```

### Option 2: Use Existing Script
```bash
python scripts/fix_index_templates.py
```

### Option 3: Manual Console Commands
```bash
python scripts/quick_mapping_setup.py
# Then copy and paste the curl commands it shows
```

## Detailed Setup Methods

### Method 1: Automated Setup (Recommended)

The automated script handles everything for you:

```bash
# Make sure Elasticsearch is running
docker-compose up -d elasticsearch

# Run the setup script
python scripts/setup_elasticsearch_mappings.py
```

**What this script does:**
- Waits for Elasticsearch to be ready
- Creates 6 index templates with proper mappings
- Verifies the setup
- Provides next steps

### Method 2: Console Commands

If you prefer manual control, run:

```bash
python scripts/quick_mapping_setup.py
```

This will show you the exact curl commands to run. For example:

```bash
# Detection Metrics Template
curl -X PUT "localhost:9200/_index_template/detection-metrics" \
  -H "Content-Type: application/json" \
  -d '{
    "index_patterns": ["detection-metrics-*"],
    "template": {
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
          "confidence_level": {"type": "keyword"},
          "detection_outcome": {"type": "keyword"}
        }
      }
    }
  }'
```

### Method 3: Kibana Dev Tools

You can also use Kibana's Dev Tools console:

1. Open Kibana: http://localhost:5601
2. Go to **Dev Tools** → **Console**
3. Paste the template JSON and execute

## Index Templates Created

The setup creates these 6 index templates:

### 1. Detection Metrics (`detection-metrics-*`)
**Purpose**: Shoplifting detection predictions and confidence scores

**Key Fields**:
- `@timestamp` - Detection timestamp
- `camera_id` - Source camera identifier
- `prediction.confidence` - Model confidence (0-1)
- `prediction.is_shoplifting` - Boolean detection result
- `confidence_level` - Categorized confidence (critical/high/medium/low)
- `detection_outcome` - Simplified result (shoplifting/normal)

### 2. System Performance (`system-performance-*`)
**Purpose**: System and camera performance metrics

**Key Fields**:
- `@timestamp` - Performance measurement time
- `performance.fps_actual` - Actual frames per second
- `performance.fps_target` - Target FPS
- `fps_status` - Performance status (optimal/good/degraded/poor)
- `performance.cpu_usage` - CPU utilization
- `performance.memory_usage` - Memory utilization

### 3. Camera Health (`camera-health-*`)
**Purpose**: Camera connectivity and health status

**Key Fields**:
- `@timestamp` - Health check time
- `camera_id` - Camera identifier
- `health.is_connected` - Connection status
- `health.status` - Health status
- `health.error_count` - Error frequency
- `health.current_fps` - Current FPS

### 4. Detection Analytics (`detection-analytics-*`)
**Purpose**: Aggregated detection statistics and trends

**Key Fields**:
- `@timestamp` - Analytics calculation time
- `camera_id` - Source camera
- `analytics.detection_count` - Number of detections
- `analytics.false_positive_rate` - Accuracy metrics
- `analytics.average_confidence` - Mean confidence scores

### 5. Camera System (`camera-system-*`)
**Purpose**: General camera system logs

**Key Fields**:
- `@timestamp` - Log timestamp
- `camera_id` - Camera identifier
- `level` - Log level (INFO, WARNING, ERROR)
- `message` - Log message content
- `module` - Source module
- `function` - Function name

### 6. System Metrics (`system-metrics-*`)
**Purpose**: General system performance metrics

**Key Fields**:
- `@timestamp` - Metric timestamp
- `cpu_usage` - CPU utilization
- `memory_usage` - Memory utilization
- `disk_usage` - Disk space usage
- `process_count` - Active processes

## Verification

After running the setup, verify everything is working:

### 1. Check Templates
```bash
curl -X GET "localhost:9200/_index_template"
```

### 2. Check Indices
```bash
curl -X GET "localhost:9200/_cat/indices?v"
```

### 3. Check Sample Data
```bash
# Check if data is flowing (after starting your app)
curl -X GET "localhost:9200/detection-metrics-*/_search?size=1&pretty"
```

## Troubleshooting

### Common Issues

**1. "Connection refused" error:**
```bash
# Make sure Elasticsearch is running
docker-compose up -d elasticsearch

# Wait for it to be ready
curl http://localhost:9200/_cluster/health
```

**2. "Template already exists" error:**
```bash
# Delete existing template first
curl -X DELETE "localhost:9200/_index_template/template-name"

# Then recreate it
```

**3. "Field mapping conflict" error:**
```bash
# Check existing mappings
curl -X GET "localhost:9200/index-name/_mapping"

# Delete the index if it has wrong mappings
curl -X DELETE "localhost:9200/index-name"
```

### Field Type Conflicts

If you get field mapping conflicts, it means:
- Data was already indexed with different field types
- You need to delete the existing indices
- Let the application recreate them with correct mappings

**Solution:**
```bash
# Delete all existing indices
curl -X DELETE "localhost:9200/detection-metrics-*"
curl -X DELETE "localhost:9200/system-performance-*"
curl -X DELETE "localhost:9200/camera-health-*"
curl -X DELETE "localhost:9200/detection-analytics-*"
curl -X DELETE "localhost:9200/camera-system-*"
curl -X DELETE "localhost:9200/system-metrics-*"

# Recreate templates
python scripts/setup_elasticsearch_mappings.py
```

## Next Steps

After setting up mappings:

1. **Start your application** to begin sending data
2. **Create index patterns in Kibana**:
   - Go to Stack Management → Index Patterns
   - Create patterns for each template (e.g., `detection-metrics-*`)
3. **Import dashboards**:
   ```bash
   python kibana/import_dashboard.py
   ```
4. **Access your dashboards** at http://localhost:5601

## Why Index Mappings Matter

Index mappings tell Elasticsearch:
- **Field types** (date, keyword, float, boolean, etc.)
- **How to index** the data for fast searching
- **What aggregations** are possible in Kibana
- **How to display** fields in visualizations

Without proper mappings:
- Kibana visualizations won't work correctly
- Aggregations will fail
- Date fields won't be recognized
- Numeric fields might be treated as text

## Best Practices

1. **Set up mappings before data ingestion** to avoid conflicts
2. **Use appropriate field types** for your data
3. **Test with sample data** before production
4. **Monitor index sizes** and performance
5. **Regular backup** of template configurations

This setup ensures your Kibana dashboards will work correctly with proper field types and aggregations.
