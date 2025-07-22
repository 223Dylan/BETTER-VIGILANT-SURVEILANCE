# Simple Detection Metrics Dashboard Creation

## Quick Dashboard Setup (5 minutes)

### 1. Detection Confidence Chart
1. Go to Kibana → **Visualize** → **Create visualization**
2. Select **Vertical bar chart**
3. Choose index: `detection-metrics-*`
4. **Y-axis**: Count (default)
5. **X-axis**:
   - Aggregation: Terms
   - Field: `confidence_level`
6. Click **Update** → **Save** as "Detection Confidence"

### 2. Detection Timeline
1. **Visualize** → **Create visualization** → **Line**
2. Index: `detection-metrics-*`
3. **Add filter**: `type:detection_metrics`
4. **Y-axis**: Count
5. **X-axis**:
   - Aggregation: Date Histogram
   - Field: `@timestamp`
   - Interval: 1 minute
6. **Save** as "Detection Timeline"

### 3. System Performance Table
1. **Visualize** → **Create visualization** → **Data table**
2. Index: `system-performance-*`
3. **Split rows**:
   - Aggregation: Terms
   - Field: `camera_id`
4. **Add metric**:
   - Aggregation: Average
   - Field: `performance.fps_actual`
5. **Save** as "Camera Performance"

### 4. Create Dashboard
1. **Dashboard** → **Create new dashboard**
2. **Add** → Select your 3 visualizations
3. **Save** as "Enhanced Detection Dashboard"

## Key Queries to Use

### Detection Events Filter:
```
type:detection_metrics AND detection_outcome:shoplifting
```

### System Performance Filter:
```
type:system_performance
```

### Camera Health Filter:
```
type:camera_health
```

## You're All Set!

Your enhanced detection metrics system is now working with:
- Proper index templates
- Data flowing into Elasticsearch
- Index patterns configured
- Ready for dashboard creation
