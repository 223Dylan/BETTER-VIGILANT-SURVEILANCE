# Monitoring and Analytics (ELK Stack)

## Overview

The Monitoring and Analytics system uses the ELK stack (Elasticsearch, Logstash, Kibana) to provide real-time monitoring, log aggregation, performance metrics, and business intelligence dashboards.

## Architecture

### ELK Stack Components

1. **Elasticsearch** - Search and analytics engine
2. **Logstash** - Data processing pipeline
3. **Kibana** - Visualization and dashboard platform
4. **Beats** - Lightweight data shippers
5. **Detection Metrics** - Custom metrics collection
6. **Performance Monitoring** - System health tracking

### Data Flow

```
Application Logs → Logstash → Elasticsearch → Kibana Dashboards
System Metrics  →    ↑            ↑              ↑
Alert Data      →    |            |              |
Performance     →    └────────────┴──────────────┘
```

## Elasticsearch Configuration

### Index Templates

**Detection Metrics Template:**
```json
{
  "index_patterns": ["detection-metrics-*"],
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "index.refresh_interval": "5s"
  },
  "mappings": {
    "properties": {
      "@timestamp": {
        "type": "date"
      },
      "camera_id": {
        "type": "keyword"
      },
      "prediction": {
        "properties": {
          "confidence": {
            "type": "float"
          },
          "is_shoplifting": {
            "type": "boolean"
          },
          "label": {
            "type": "keyword"
          }
        }
      },
      "performance": {
        "properties": {
          "processing_time_ms": {
            "type": "float"
          },
          "fps": {
            "type": "float"
          },
          "memory_usage_mb": {
            "type": "float"
          }
        }
      },
      "location": {
        "type": "geo_point"
      }
    }
  }
}
```

**Alert Metrics Template:**
```json
{
  "index_patterns": ["detection-alerts-*"],
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "properties": {
      "@timestamp": {
        "type": "date"
      },
      "alert_id": {
        "type": "keyword"
      },
      "camera_id": {
        "type": "keyword"
      },
      "severity": {
        "type": "keyword"
      },
      "confidence": {
        "type": "float"
      },
      "status": {
        "type": "keyword"
      },
      "location": {
        "type": "keyword"
      },
      "detection_data": {
        "type": "object",
        "enabled": false
      }
    }
  }
}
```

## Logstash Configuration

### Pipeline Configuration

**Source:** `logstash/pipeline/logstash.conf`

```ruby
input {
  tcp {
    port => 5000
    codec => json_lines
  }
  udp {
    port => 5000
    codec => json_lines
  }
  beats {
    port => 5044
  }
}

filter {
  # Parse detection metrics
  if [type] == "detection_metrics" {
    mutate {
      add_field => {
        "[@metadata][target_index]" => "detection-metrics-%{+YYYY.MM.dd}"
      }
    }

    # Parse confidence levels
    if [prediction][confidence] {
      ruby {
        code => "
          confidence = event.get('[prediction][confidence]')
          if confidence.is_a?(Numeric)
            if confidence >= 0.9
              event.set('confidence_level', 'critical')
            elsif confidence >= 0.7
              event.set('confidence_level', 'high')
            elsif confidence >= 0.5
              event.set('confidence_level', 'medium')
            else
              event.set('confidence_level', 'low')
            end
          end
        "
      }
    }
  }

  # Parse alert events
  if [type] == "alert_event" {
    mutate {
      add_field => {
        "[@metadata][target_index]" => "detection-alerts-%{+YYYY.MM.dd}"
      }
    }

    # Add alert metadata
    if [alert_id] {
      mutate {
        add_field => { "event_category" => "security" }
        add_field => { "event_action" => "alert_triggered" }
      }
    }
  }

  # Parse system performance metrics
  if [type] == "system_performance" {
    mutate {
      add_field => {
        "[@metadata][target_index]" => "system-performance-%{+YYYY.MM.dd}"
      }
    }

    # Calculate performance status
    if [performance][cpu_usage] {
      ruby {
        code => "
          cpu_usage = event.get('[performance][cpu_usage]')
          memory_usage = event.get('[performance][memory_usage]')

          if cpu_usage.to_f > 80 || memory_usage.to_f > 80
            event.set('performance_status', 'critical')
          elsif cpu_usage.to_f > 60 || memory_usage.to_f > 60
            event.set('performance_status', 'warning')
          else
            event.set('performance_status', 'normal')
          end
        "
      }
    }
  }

  # Parse camera events
  if [type] == "camera_event" {
    mutate {
      add_field => {
        "[@metadata][target_index]" => "camera-events-%{+YYYY.MM.dd}"
      }
    }

    # Enrich camera data
    if [camera_id] {
      # Add camera metadata (location, zone, etc.)
      mutate {
        add_field => { "event_source" => "camera_system" }
      }
    }
  }

  # Add common fields
  mutate {
    add_field => { "environment" => "production" }
    add_field => { "service" => "shoplifting_detection" }
  }

  # Parse timestamp if not already set
  if ![timestamp] {
    mutate {
      add_field => { "timestamp" => "%{@timestamp}" }
    }
  }

  # Remove sensitive data
  if [password] {
    mutate {
      remove_field => [ "password" ]
    }
  }

  if [token] {
    mutate {
      remove_field => [ "token" ]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "%{[@metadata][target_index]}"
    template_name => "shoplifting_detection"
    template_pattern => "detection-*,camera-*,system-*"
  }

  # Debug output (remove in production)
  if [loglevel] == "debug" {
    stdout {
      codec => rubydebug
    }
  }
}
```

## Detection Metrics System

### Metrics Collection

**Source:** `src/detection_metrics.py`

```python
import json
import logging
import socket
import time
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class DetectionMetrics:
    """Structure for detection-related metrics."""
    timestamp: str
    camera_id: str
    prediction: Dict[str, Any]
    performance: Dict[str, float]
    type: str = "detection_metrics"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

@dataclass
class AlertMetrics:
    """Structure for alert-related metrics."""
    timestamp: str
    alert_id: str
    camera_id: str
    severity: str
    confidence: float
    status: str
    type: str = "alert_event"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class PerformanceMetrics:
    """Structure for system performance metrics."""
    timestamp: str
    performance: Dict[str, float]
    system_info: Dict[str, Any]
    type: str = "system_performance"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class MetricsLogger:
    """Centralized metrics logging to ELK stack."""

    def __init__(self, logstash_host: str = "localhost", logstash_port: int = 5000):
        self.logstash_host = logstash_host
        self.logstash_port = logstash_port
        self.logger = logging.getLogger("metrics")

        # Setup logger to send to Logstash
        self._setup_logstash_handler()

    def _setup_logstash_handler(self):
        """Setup handler to send logs to Logstash."""
        try:
            # Create socket handler for Logstash
            socket_handler = logging.handlers.SocketHandler(
                self.logstash_host,
                self.logstash_port
            )
            socket_handler.setLevel(logging.INFO)

            # JSON formatter
            formatter = logging.Formatter('%(message)s')
            socket_handler.setFormatter(formatter)

            self.logger.addHandler(socket_handler)
            self.logger.setLevel(logging.INFO)

        except Exception as e:
            print(f"Failed to setup Logstash handler: {e}")

    def log_detection_metrics(self, camera_id: str, prediction: Dict[str, Any],
                            performance: Dict[str, float]):
        """Log detection prediction metrics."""
        metrics = DetectionMetrics(
            timestamp=datetime.utcnow().isoformat(),
            camera_id=camera_id,
            prediction=prediction,
            performance=performance
        )

        try:
            self.logger.info(json.dumps(metrics.to_dict()))
        except Exception as e:
            print(f"Failed to log detection metrics: {e}")

    def log_alert_metrics(self, alert_id: str, camera_id: str, severity: str,
                         confidence: float, status: str):
        """Log alert-related metrics."""
        metrics = AlertMetrics(
            timestamp=datetime.utcnow().isoformat(),
            alert_id=alert_id,
            camera_id=camera_id,
            severity=severity,
            confidence=confidence,
            status=status
        )

        try:
            self.logger.info(json.dumps(metrics.to_dict()))
        except Exception as e:
            print(f"Failed to log alert metrics: {e}")

    def log_performance_metrics(self, performance: Dict[str, float],
                              system_info: Dict[str, Any]):
        """Log system performance metrics."""
        metrics = PerformanceMetrics(
            timestamp=datetime.utcnow().isoformat(),
            performance=performance,
            system_info=system_info
        )

        try:
            self.logger.info(json.dumps(metrics.to_dict()))
        except Exception as e:
            print(f"Failed to log performance metrics: {e}")

# Global metrics logger instance
metrics_logger = MetricsLogger()
```

### System Monitoring

**Source:** `src/utils/system_monitor.py`

```python
import psutil
import time
import threading
from datetime import datetime
from typing import Dict, Any

class SystemMonitor:
    """Monitor system performance and resources."""

    def __init__(self, interval: int = 60):
        self.interval = interval
        self.monitoring = False
        self.monitor_thread = None

    def start_monitoring(self):
        """Start system monitoring."""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop system monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                metrics = self.collect_system_metrics()

                # Log metrics to ELK stack
                from src.detection_metrics import metrics_logger
                metrics_logger.log_performance_metrics(
                    performance=metrics['performance'],
                    system_info=metrics['system_info']
                )

                time.sleep(self.interval)

            except Exception as e:
                print(f"System monitoring error: {e}")
                time.sleep(self.interval)

    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics."""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()

        # Network metrics
        network_io = psutil.net_io_counters()

        # Process metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        process_cpu = process.cpu_percent()

        return {
            'performance': {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_usage': disk.percent,
                'disk_free_gb': disk.free / (1024**3),
                'process_memory_mb': process_memory.rss / (1024**2),
                'process_cpu': process_cpu,
                'network_bytes_sent': network_io.bytes_sent,
                'network_bytes_recv': network_io.bytes_recv
            },
            'system_info': {
                'cpu_count': cpu_count,
                'cpu_freq_mhz': cpu_freq.current if cpu_freq else 0,
                'total_memory_gb': memory.total / (1024**3),
                'total_disk_gb': disk.total / (1024**3),
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                'python_version': psutil.version_info,
                'platform': psutil.platform.system()
            }
        }

# Global system monitor
system_monitor = SystemMonitor()
```

## Kibana Dashboards

### Detection System Dashboard

**Dashboard Configuration:**
```json
{
  "version": "8.12.1",
  "objects": [
    {
      "id": "detection-overview",
      "type": "dashboard",
      "attributes": {
        "title": "Shoplifting Detection Overview",
        "description": "Main dashboard for monitoring detection system performance",
        "panelsJSON": "[
          {
            \"version\":\"8.12.1\",
            \"gridData\":{\"x\":0,\"y\":0,\"w\":24,\"h\":15},
            \"panelIndex\":\"1\",
            \"embeddableConfig\":{},
            \"panelRefName\":\"panel_1\"
          },
          {
            \"version\":\"8.12.1\",
            \"gridData\":{\"x\":24,\"y\":0,\"w\":24,\"h\":15},
            \"panelIndex\":\"2\",
            \"embeddableConfig\":{},
            \"panelRefName\":\"panel_2\"
          }
        ]",
        "timeRestore": true,
        "timeTo": "now",
        "timeFrom": "now-24h"
      }
    }
  ]
}
```

### Key Performance Indicators

**Detection Rate Visualization:**
```json
{
  "id": "detection-rate-viz",
  "type": "visualization",
  "attributes": {
    "title": "Detection Rate Over Time",
    "visState": {
      "type": "line",
      "params": {
        "seriesParams": [
          {
            "data": {
              "label": "Detections per Hour"
            },
            "type": "line",
            "mode": "normal"
          }
        ]
      }
    }
  }
}
```

**Confidence Distribution:**
```json
{
  "id": "confidence-distribution",
  "type": "visualization",
  "attributes": {
    "title": "Confidence Score Distribution",
    "visState": {
      "type": "histogram",
      "params": {
        "shareYAxis": true,
        "addTooltip": true,
        "addLegend": true,
        "scale": "linear",
        "mode": "stacked",
        "times": [],
        "addTimeMarker": false
      }
    }
  }
}
```

### Alert Analytics

**Alert Severity Breakdown:**
```json
{
  "id": "alert-severity-pie",
  "type": "visualization",
  "attributes": {
    "title": "Alert Severity Distribution",
    "visState": {
      "type": "pie",
      "params": {
        "addTooltip": true,
        "addLegend": true,
        "legendPosition": "right",
        "isDonut": false
      }
    }
  }
}
```

## Alerting and Notifications

### Kibana Watcher Configuration

**High Detection Rate Alert:**
```json
{
  "trigger": {
    "schedule": {
      "interval": "5m"
    }
  },
  "input": {
    "search": {
      "request": {
        "search_type": "query_then_fetch",
        "indices": ["detection-metrics-*"],
        "body": {
          "query": {
            "bool": {
              "must": [
                {
                  "range": {
                    "@timestamp": {
                      "gte": "now-5m"
                    }
                  }
                },
                {
                  "term": {
                    "prediction.is_shoplifting": true
                  }
                }
              ]
            }
          },
          "aggs": {
            "detection_count": {
              "value_count": {
                "field": "prediction.is_shoplifting"
              }
            }
          }
        }
      }
    }
  },
  "condition": {
    "compare": {
      "ctx.payload.aggregations.detection_count.value": {
        "gt": 5
      }
    }
  },
  "actions": {
    "send_email": {
      "email": {
        "to": ["security@company.com"],
        "subject": "High Detection Rate Alert",
        "body": "Detected {{ctx.payload.aggregations.detection_count.value}} potential shoplifting events in the last 5 minutes."
      }
    }
  }
}
```

**System Performance Alert:**
```json
{
  "trigger": {
    "schedule": {
      "interval": "1m"
    }
  },
  "input": {
    "search": {
      "request": {
        "indices": ["system-performance-*"],
        "body": {
          "query": {
            "range": {
              "@timestamp": {
                "gte": "now-1m"
              }
            }
          },
          "sort": [
            {
              "@timestamp": {
                "order": "desc"
              }
            }
          ],
          "size": 1
        }
      }
    }
  },
  "condition": {
    "compare": {
      "ctx.payload.hits.hits.0._source.performance.cpu_usage": {
        "gt": 80
      }
    }
  },
  "actions": {
    "webhook": {
      "webhook": {
        "scheme": "https",
        "host": "hooks.slack.com",
        "port": 443,
        "method": "post",
        "path": "/services/YOUR/SLACK/WEBHOOK",
                        "body": "{\"text\": \"Warning: High CPU usage detected: {{ctx.payload.hits.hits.0._source.performance.cpu_usage}}%\"}"
      }
    }
  }
}
```

## Metrics Collection Scripts

### Setup Detection Metrics

**Source:** `scripts/setup_detection_metrics.py`

```python
#!/usr/bin/env python3
"""Setup detection metrics collection and Elasticsearch templates."""

import requests
import json
import sys
from datetime import datetime

ELASTICSEARCH_URL = "http://localhost:9200"

def create_index_template(name: str, template: dict) -> bool:
    """Create Elasticsearch index template."""
    url = f"{ELASTICSEARCH_URL}/_index_template/{name}"

    try:
        response = requests.put(url, json=template)
        if response.status_code in [200, 201]:
            print(f"Created index template: {name}")
            return True
        else:
            print(f"Failed to create template {name}: {response.text}")
            return False
    except Exception as e:
        print(f"Error creating template {name}: {e}")
        return False

def main():
    """Main setup function."""
    print("Setting up Elasticsearch templates for detection metrics...")

    # Detection metrics template
    detection_template = {
        "index_patterns": ["detection-metrics-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index.refresh_interval": "5s"
            },
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "camera_id": {"type": "keyword"},
                    "prediction": {
                        "properties": {
                            "confidence": {"type": "float"},
                            "is_shoplifting": {"type": "boolean"},
                            "label": {"type": "keyword"}
                        }
                    },
                    "performance": {
                        "properties": {
                            "processing_time_ms": {"type": "float"},
                            "fps": {"type": "float"},
                            "memory_usage_mb": {"type": "float"}
                        }
                    }
                }
            }
        }
    }

    # Alert metrics template
    alert_template = {
        "index_patterns": ["detection-alerts-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "alert_id": {"type": "keyword"},
                    "camera_id": {"type": "keyword"},
                    "severity": {"type": "keyword"},
                    "confidence": {"type": "float"},
                    "status": {"type": "keyword"}
                }
            }
        }
    }

    # Create templates
    success = True
    success &= create_index_template("detection-metrics", detection_template)
    success &= create_index_template("detection-alerts", alert_template)

    if success:
        print("All templates created successfully")
        return 0
    else:
        print("Some templates failed to create")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## Best Practices

1. **Index Management**
   - Use time-based indices for logs
   - Implement index lifecycle policies
   - Monitor index sizes and performance
   - Regular cleanup of old indices

2. **Performance Optimization**
   - Use appropriate shard sizes
   - Optimize mapping field types
   - Enable compression for stored fields
   - Monitor cluster health

3. **Alerting Strategy**
   - Set appropriate thresholds
   - Avoid alert fatigue
   - Use escalation policies
   - Test alert configurations

4. **Data Retention**
   - Define retention policies
   - Archive historical data
   - Monitor storage usage
   - Implement automated cleanup
