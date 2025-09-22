interface SystemMetrics {
  timestamp: string;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  active_cameras: number;
}

interface CameraMetrics {
  camera_id: string;
  fps_actual: number;
  fps_target: number;
  latency_ms: number;
  status: string;
  last_detection?: string;
}

interface DetectionMetrics {
  camera_id: string;
  confidence: number;
  label: string;
  is_shoplifting: boolean;
  timestamp: string;
  alert_triggered: boolean;
}

interface MetricsSummary {
  system: SystemMetrics;
  cameras: CameraMetrics[];
  recent_detections: DetectionMetrics[];
  total_detections_today: number;
  alert_count_today: number;
}

interface CameraPerformance {
  camera_id: string;
  time_range: string;
  data: Array<{
    timestamp: string;
    fps_actual: number;
    latency_ms: number;
    queue_depth: number;
    dropped_frames: number;
  }>;
}

interface Alert {
  timestamp: string;
  camera_id: string;
  level: string;
  type: string;
  confidence: number;
  label: string;
}

interface HealthStatus {
  elasticsearch: boolean;
  prometheus: boolean;
  system_monitor: boolean;
  timestamp: string;
}

class MetricsService {
  private baseUrl: string;

  constructor(baseUrl: string = '/api/metrics') {
    this.baseUrl = baseUrl;
  }

  /**
   * Get system performance metrics over time
   */
  async getSystemMetrics(timeRange: string = '15m', limit: number = 100): Promise<SystemMetrics[]> {
    const response = await fetch(`${this.baseUrl}/system?time_range=${timeRange}&limit=${limit}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch system metrics: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get current metrics for all cameras
   */
  async getCameraMetrics(): Promise<CameraMetrics[]> {
    const response = await fetch(`${this.baseUrl}/cameras`);
    if (!response.ok) {
      throw new Error(`Failed to fetch camera metrics: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get detailed performance metrics for a specific camera
   */
  async getCameraPerformance(cameraId: string, timeRange: string = '1h'): Promise<CameraPerformance> {
    const response = await fetch(`${this.baseUrl}/cameras/${cameraId}/performance?time_range=${timeRange}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch camera ${cameraId} performance: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get detection metrics with optional filtering
   */
  async getDetectionMetrics(
    timeRange: string = '1h',
    cameraId?: string,
    confidenceThreshold: number = 0.0
  ): Promise<DetectionMetrics[]> {
    const params = new URLSearchParams({
      time_range: timeRange,
      confidence_threshold: confidenceThreshold.toString()
    });

    if (cameraId) {
      params.append('camera_id', cameraId);
    }

    const response = await fetch(`${this.baseUrl}/detections?${params}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch detection metrics: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get comprehensive metrics summary
   */
  async getMetricsSummary(): Promise<MetricsSummary> {
    const response = await fetch(`${this.baseUrl}/summary`);
    if (!response.ok) {
      throw new Error(`Failed to fetch metrics summary: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get health status of metrics infrastructure
   */
  async getHealthStatus(): Promise<HealthStatus> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new Error(`Failed to fetch health status: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get recent alerts from the system
   */
  async getRecentAlerts(limit: number = 50, severity?: string): Promise<Alert[]> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (severity) {
      params.append('severity', severity);
    }

    const response = await fetch(`${this.baseUrl}/alerts/recent?${params}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch recent alerts: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Create WebSocket connection for real-time metrics updates
   */
  createMetricsWebSocket(): WebSocket {
    const { protocol, hostname } = window.location;
    const wsProtocol = protocol === 'https:' ? 'wss' : 'ws';
    const wsPort = process.env.NODE_ENV === 'development' ? '8001' : (window.location.port || '8001');
    return new WebSocket(`${wsProtocol}://${hostname}:${wsPort}/ws/metrics`);
  }

  /**
   * Create WebSocket connection for camera-specific metrics
   */
  createCameraMetricsWebSocket(cameraId: string): WebSocket {
    const { protocol, hostname } = window.location;
    const wsProtocol = protocol === 'https:' ? 'wss' : 'ws';
    const wsPort = process.env.NODE_ENV === 'development' ? '8001' : (window.location.port || '8001');
    return new WebSocket(`${wsProtocol}://${hostname}:${wsPort}/ws/metrics/camera/${cameraId}`);
  }

  /**
   * Create WebSocket connection for real-time alerts
   */
  createAlertsWebSocket(): WebSocket {
    const { protocol, hostname } = window.location;
    const wsProtocol = protocol === 'https:' ? 'wss' : 'ws';
    const wsPort = process.env.NODE_ENV === 'development' ? '8001' : (window.location.port || '8001');
    return new WebSocket(`${wsProtocol}://${hostname}:${wsPort}/ws/alerts`);
  }

  /**
   * Parse WebSocket message and return typed data
   */
  parseWebSocketMessage(message: MessageEvent): any {
    try {
      return JSON.parse(message.data);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
      return null;
    }
  }

  /**
   * Get analytics data for a specific time range
   */
  async getAnalyticsData(timeRange: string = '24h'): Promise<{
    systemMetrics: SystemMetrics[];
    detectionMetrics: DetectionMetrics[];
    summary: MetricsSummary;
  }> {
    const [systemMetrics, detectionMetrics, summary] = await Promise.all([
      this.getSystemMetrics(timeRange, 100),
      this.getDetectionMetrics(timeRange),
      this.getMetricsSummary()
    ]);

    return { systemMetrics, detectionMetrics, summary };
  }

  /**
   * Get detection statistics for analytics
   */
  async getDetectionStatistics(timeRange: string = '24h'): Promise<{
    totalDetections: number;
    shopliflingDetections: number;
    averageConfidence: number;
    detectionsByHour: Array<{ hour: string; count: number }>;
  }> {
    const detections = await this.getDetectionMetrics(timeRange);

    const totalDetections = detections.length;
    const shopliflingDetections = detections.filter(d => d.is_shoplifting).length;
    const averageConfidence = detections.length > 0
      ? detections.reduce((sum, d) => sum + d.confidence, 0) / detections.length
      : 0;

    // Group detections by hour
    const detectionsByHour = this.groupDetectionsByHour(detections);

    return {
      totalDetections,
      shopliflingDetections,
      averageConfidence,
      detectionsByHour
    };
  }

  /**
   * Group detections by hour for time-based analytics
   */
  private groupDetectionsByHour(detections: DetectionMetrics[]): Array<{ hour: string; count: number }> {
    const hourCounts: { [key: string]: number } = {};

    detections.forEach(detection => {
      const hour = new Date(detection.timestamp).getHours();
      const hourKey = `${hour}:00`;
      hourCounts[hourKey] = (hourCounts[hourKey] || 0) + 1;
    });

    // Create array for all 24 hours
    const result = [];
    for (let i = 0; i < 24; i++) {
      const hourKey = `${i}:00`;
      result.push({
        hour: hourKey,
        count: hourCounts[hourKey] || 0
      });
    }

    return result;
  }

  /**
   * Format timestamp for display
   */
  formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleString();
  }

  /**
   * Calculate percentage with proper formatting
   */
  formatPercentage(value: number, decimals: number = 1): string {
    return `${value.toFixed(decimals)}%`;
  }

  /**
   * Get status color for UI elements
   */
  getStatusColor(status: string): string {
    switch (status.toLowerCase()) {
      case 'online':
      case 'active':
      case 'healthy':
        return '#22c55e'; // green-500
      case 'offline':
      case 'inactive':
      case 'error':
        return '#ef4444'; // red-500
      case 'warning':
      case 'degraded':
        return '#f59e0b'; // amber-500
      default:
        return '#6b7280'; // gray-500
    }
  }

  /**
   * Get confidence level label
   */
  getConfidenceLevel(confidence: number): string {
    if (confidence >= 0.9) return 'critical';
    if (confidence >= 0.7) return 'high';
    if (confidence >= 0.5) return 'medium';
    return 'low';
  }

  /**
   * Get confidence level color
   */
  getConfidenceLevelColor(confidence: number): string {
    if (confidence >= 0.9) return '#dc2626'; // red-600
    if (confidence >= 0.7) return '#ea580c'; // orange-600
    if (confidence >= 0.5) return '#d97706'; // amber-600
    return '#65a30d'; // lime-600
  }
}

// Export singleton instance
export const metricsService = new MetricsService();

// Export types for use in components
export type {
  SystemMetrics,
  CameraMetrics,
  DetectionMetrics,
  MetricsSummary,
  CameraPerformance,
  Alert,
  HealthStatus
};
