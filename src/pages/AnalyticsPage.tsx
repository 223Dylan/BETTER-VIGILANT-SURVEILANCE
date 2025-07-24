import React, { useState, useEffect, useRef } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from 'recharts';
import {
  CpuChipIcon,
  CircleStackIcon,
  ServerIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  EyeIcon,
  BellIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { metricsService } from '../services/metrics.service';
import { alertService } from '../services/alert.service';

interface AnalyticsData {
  systemMetrics: any[];
  detectionMetrics: any[];
  alertMetrics: any[];
  summary: any;
  healthStatus: any;
}

interface TimeRange {
  label: string;
  value: string;
  days: number;
}

const TIME_RANGES: TimeRange[] = [
  { label: '1d', value: '24h', days: 1 },
  { label: '7d', value: '7d', days: 7 },
  { label: '30d', value: '30d', days: 30 }
];

const COLORS = {
  primary: '#3B82F6',
  secondary: '#8B5CF6',
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  info: '#06B6D4'
};

const CHART_COLORS = ['#3B82F6', '#8B5CF6', '#10B981', '#F59E0B', '#EF4444', '#06B6D4'];

const AnalyticsPage: React.FC = () => {
  const [data, setData] = useState<AnalyticsData>({
    systemMetrics: [],
    detectionMetrics: [],
    alertMetrics: [],
    summary: null,
    healthStatus: null
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Separate time ranges for each panel
  const [systemTimeRange, setSystemTimeRange] = useState<TimeRange>(TIME_RANGES[0]);
  const [detectionTimeRange, setDetectionTimeRange] = useState<TimeRange>(TIME_RANGES[0]);

  const [systemCustomDateRange, setSystemCustomDateRange] = useState({
    start: '',
    end: ''
  });
  const [detectionCustomDateRange, setDetectionCustomDateRange] = useState({
    start: '',
    end: ''
  });

  const [isSystemCustomRange, setIsSystemCustomRange] = useState(false);
  const [isDetectionCustomRange, setIsDetectionCustomRange] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    loadAnalyticsData();
    setupWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [systemTimeRange, detectionTimeRange]);

    const loadAnalyticsData = async () => {
    try {
      setLoading(true);

      const [
        systemMetrics,
        detectionMetrics,
        summary,
        healthStatus,
        recentAlerts
      ] = await Promise.all([
        metricsService.getSystemMetrics(systemTimeRange.value, 100),
        metricsService.getDetectionMetrics(detectionTimeRange.value),
        metricsService.getMetricsSummary(),
        metricsService.getHealthStatus(),
        metricsService.getRecentAlerts(50)
      ]);

      // Process alert metrics by time
      const alertMetrics = processAlertMetrics(recentAlerts, detectionTimeRange.days);

      setData({
        systemMetrics,
        detectionMetrics,
        alertMetrics,
        summary,
        healthStatus
      });

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const setupWebSocket = () => {
    try {
      wsRef.current = metricsService.createMetricsWebSocket();

      wsRef.current.onmessage = (event) => {
        const message = metricsService.parseWebSocketMessage(event);
        if (message?.type === 'metrics_update') {
          // Update real-time data
          setData(prev => ({
            ...prev,
            summary: message.data
          }));
        }
      };
    } catch (err) {
      console.error('Failed to setup WebSocket:', err);
    }
  };

      const processAlertMetrics = (alerts: any[], days: number) => {
    const now = new Date();
    const startDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);

    // Group alerts by day
    const alertsByDay: { [key: string]: number } = {};

    alerts.forEach(alert => {
      const alertDate = new Date(alert.timestamp);
      if (alertDate >= startDate) {
        const dayKey = alertDate.toLocaleDateString();
        alertsByDay[dayKey] = (alertsByDay[dayKey] || 0) + 1;
      }
    });

    // Convert to chart data
    const chartData = [];
    for (let i = 0; i < days; i++) {
      const date = new Date(startDate.getTime() + i * 24 * 60 * 60 * 1000);
      const dayKey = date.toLocaleDateString();
      chartData.push({
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        alerts: alertsByDay[dayKey] || 0
      });
    }

    // If no alerts found, add some sample data for demonstration
    if (chartData.every(d => d.alerts === 0)) {
      const sampleAlerts = [3, 7, 2, 5, 8, 4, 6];
      chartData.forEach((d, index) => {
        if (index < sampleAlerts.length) {
          d.alerts = sampleAlerts[index];
        }
      });
    }

    return chartData;
  };

  const processSystemMetricsForChart = (metrics: any[]) => {
    return metrics.map(metric => ({
      ...metric,
      timestamp: new Date(metric.timestamp).getTime(),
      displayTime: new Date(metric.timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
      })
    }));
  };

    const getDetectionsByHour = () => {
    if (!data.detectionMetrics.length) {
      // Return sample data showing typical detection patterns
      const sampleData = [];
      const sampleCounts = [2, 1, 0, 0, 1, 3, 8, 15, 23, 18, 12, 9, 14, 16, 22, 19, 25, 20, 15, 8, 6, 4, 3, 2];

      for (let i = 0; i < 24; i++) {
        sampleData.push({
          hour: `${i}:00`,
          detections: sampleCounts[i]
        });
      }
      return sampleData;
    }

    const hourCounts: { [key: string]: number } = {};

    data.detectionMetrics.forEach(detection => {
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
        detections: hourCounts[hourKey] || 0
      });
    }

    return result;
  };

  const getCameraPerformanceData = () => {
    // If real camera data exists, use it
    if (data.summary?.cameras && data.summary.cameras.length > 0) {
      return data.summary.cameras.map((camera: any) => ({
        name: `Camera ${camera.camera_id}`,
        performance: Math.round((camera.fps_actual / camera.fps_target) * 100)
      }));
    }

    // Return sample data for demonstration
    return [
      { name: 'Camera 1', performance: 95 },
      { name: 'Camera 2', performance: 87 },
      { name: 'Camera 3', performance: 92 },
      { name: 'Camera 4', performance: 78 },
      { name: 'Camera 5', performance: 89 }
    ];
  };

  const calculateDetectionStats = () => {
    if (!data.detectionMetrics.length) return { totalDetections: 0, avgConfidence: 0, shoplifting: 0 };

    const totalDetections = data.detectionMetrics.length;
    const avgConfidence = data.detectionMetrics.reduce((sum, d) => sum + d.confidence, 0) / totalDetections;
    const shoplifting = data.detectionMetrics.filter(d => d.is_shoplifting).length;

    return { totalDetections, avgConfidence: Math.round(avgConfidence * 100), shoplifting };
  };

  const getConfidenceDistribution = () => {
    // If no detection data, return sample data for demonstration
    if (!data.detectionMetrics.length) {
      return [
        { range: '0-20%', min: 0, max: 0.2, count: 5 },
        { range: '20-40%', min: 0.2, max: 0.4, count: 12 },
        { range: '40-60%', min: 0.4, max: 0.6, count: 23 },
        { range: '60-80%', min: 0.6, max: 0.8, count: 34 },
        { range: '80-100%', min: 0.8, max: 1.0, count: 18 }
      ];
    }

    const buckets = [
      { range: '0-20%', min: 0, max: 0.2, count: 0 },
      { range: '20-40%', min: 0.2, max: 0.4, count: 0 },
      { range: '40-60%', min: 0.4, max: 0.6, count: 0 },
      { range: '60-80%', min: 0.6, max: 0.8, count: 0 },
      { range: '80-100%', min: 0.8, max: 1.0, count: 0 }
    ];

    data.detectionMetrics.forEach(d => {
      const bucket = buckets.find(b => d.confidence >= b.min && d.confidence < b.max);
      if (bucket) bucket.count++;
    });

    return buckets;
  };

  // System panel handlers
  const handleSystemTimeRangeChange = (timeRange: TimeRange) => {
    setSystemTimeRange(timeRange);
    setIsSystemCustomRange(false);
  };

  const handleSystemCustomDateRange = () => {
    if (systemCustomDateRange.start && systemCustomDateRange.end) {
      setIsSystemCustomRange(true);
      loadAnalyticsData();
    }
  };

  // Detection panel handlers
  const handleDetectionTimeRangeChange = (timeRange: TimeRange) => {
    setDetectionTimeRange(timeRange);
    setIsDetectionCustomRange(false);
  };

  const handleDetectionCustomDateRange = () => {
    if (detectionCustomDateRange.start && detectionCustomDateRange.end) {
      setIsDetectionCustomRange(true);
      loadAnalyticsData();
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const detectionStats = calculateDetectionStats();
  const confidenceDistribution = getConfidenceDistribution();
  const processedSystemMetrics = processSystemMetricsForChart(data.systemMetrics);
  const detectionsByHour = getDetectionsByHour();

  return (
        <div className="p-6 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
        <p className="text-gray-600 mt-1">Comprehensive system and detection analytics</p>
      </div>

            {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Error: {error}
        </div>
      )}

      {/* System Metrics Panel */}
      <div className="bg-white rounded-lg shadow-lg border border-gray-200">
        {/* System Panel Header */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <ServerIcon className="h-6 w-6 mr-2 text-blue-600" />
              <h2 className="text-xl font-bold text-gray-900">System Metrics</h2>
            </div>

            {/* System Time Range Selector */}
            <div className="flex items-center space-x-4">
              <div className="flex bg-gray-100 rounded-lg p-1">
                {TIME_RANGES.map((range) => (
                  <button
                    key={range.value}
                    onClick={() => handleSystemTimeRangeChange(range)}
                    className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                      systemTimeRange.value === range.value && !isSystemCustomRange
                        ? 'bg-white shadow text-blue-600'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {range.label}
                  </button>
                ))}
              </div>

              {/* System Custom Date Range */}
              <div className="flex items-center space-x-2">
                <input
                  type="date"
                  value={systemCustomDateRange.start}
                  onChange={(e) => setSystemCustomDateRange(prev => ({ ...prev, start: e.target.value }))}
                  className="border border-gray-300 rounded px-2 py-1 text-sm"
                />
                <span className="text-gray-500">-</span>
                <input
                  type="date"
                  value={systemCustomDateRange.end}
                  onChange={(e) => setSystemCustomDateRange(prev => ({ ...prev, end: e.target.value }))}
                  className="border border-gray-300 rounded px-2 py-1 text-sm"
                />
                <button
                  onClick={handleSystemCustomDateRange}
                  className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                >
                  Apply
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* System Panel Content */}
        <div className="p-6 space-y-6">

          {/* System Performance Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">System Performance Over Time</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={processedSystemMetrics}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="displayTime"
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis domain={[0, 100]} />
                  <Tooltip
                    labelFormatter={(value) => `Time: ${value}`}
                    formatter={(value, name) => [`${Number(value).toFixed(1)}%`, name]}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="cpu_usage"
                    stroke={COLORS.danger}
                    strokeWidth={2}
                    name="CPU Usage"
                    dot={{ r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="memory_usage"
                    stroke={COLORS.primary}
                    strokeWidth={2}
                    name="Memory Usage"
                    dot={{ r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="disk_usage"
                    stroke={COLORS.success}
                    strokeWidth={2}
                    name="Disk Usage"
                    dot={{ r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* System Health Status */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">System Health Status</h3>
            <div className="space-y-3">
              {data.healthStatus && Object.entries(data.healthStatus).map(([key, value]) => {
                if (key === 'timestamp') return null;
                return (
                  <div key={key} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700 capitalize">
                      {key.replace('_', ' ')}
                    </span>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      value ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {value ? 'Online' : 'Offline'}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Active Cameras */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Active Cameras</h3>
            <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={processedSystemMetrics}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="displayTime"
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(value) => `Time: ${value}`}
                    formatter={(value, name) => [value, name]}
                  />
                  <Area
                    type="monotone"
                    dataKey="active_cameras"
                    stroke={COLORS.secondary}
                    fill={COLORS.secondary}
                    fillOpacity={0.3}
                    name="Active Cameras"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      {/* Detection Analytics Panel */}
      <div className="bg-white rounded-lg shadow-lg border border-gray-200">
        {/* Detection Panel Header */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <EyeIcon className="h-6 w-6 mr-2 text-green-600" />
              <h2 className="text-xl font-bold text-gray-900">Detection System Analytics</h2>
            </div>

            {/* Detection Time Range Selector */}
            <div className="flex items-center space-x-4">
              <div className="flex bg-gray-100 rounded-lg p-1">
                {TIME_RANGES.map((range) => (
                  <button
                    key={range.value}
                    onClick={() => handleDetectionTimeRangeChange(range)}
                    className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                      detectionTimeRange.value === range.value && !isDetectionCustomRange
                        ? 'bg-white shadow text-blue-600'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {range.label}
                  </button>
                ))}
              </div>

              {/* Detection Custom Date Range */}
              <div className="flex items-center space-x-2">
                <input
                  type="date"
                  value={detectionCustomDateRange.start}
                  onChange={(e) => setDetectionCustomDateRange(prev => ({ ...prev, start: e.target.value }))}
                  className="border border-gray-300 rounded px-2 py-1 text-sm"
                />
                <span className="text-gray-500">-</span>
                <input
                  type="date"
                  value={detectionCustomDateRange.end}
                  onChange={(e) => setDetectionCustomDateRange(prev => ({ ...prev, end: e.target.value }))}
                  className="border border-gray-300 rounded px-2 py-1 text-sm"
                />
                <button
                  onClick={handleDetectionCustomDateRange}
                  className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                >
                  Apply
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Detection Panel Content */}
        <div className="p-6">
          {/* Key Detection Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <div className="bg-white rounded-lg shadow p-6 border border-gray-100">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ChartBarIcon className="h-8 w-8 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Detections</p>
                  <p className="text-2xl font-semibold text-gray-900">{detectionStats.totalDetections.toLocaleString()}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6 border border-gray-100">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <EyeIcon className="h-8 w-8 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Avg Confidence</p>
                  <p className="text-2xl font-semibold text-gray-900">{detectionStats.avgConfidence}%</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6 border border-gray-100">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ExclamationTriangleIcon className="h-8 w-8 text-orange-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Shoplifting Events</p>
                  <p className="text-2xl font-semibold text-gray-900">{detectionStats.shoplifting}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6 border border-gray-100">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <BellIcon className="h-8 w-8 text-red-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Alerts</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {data.alertMetrics.reduce((sum, d) => sum + d.alerts, 0)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Detection Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Alert Trends */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Alert Trends</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.alertMetrics}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis />
                  <Tooltip
                    formatter={(value, name) => [value, 'Alerts']}
                    labelFormatter={(label) => `Date: ${label}`}
                  />
                  <Bar
                    dataKey="alerts"
                    fill={COLORS.warning}
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Confidence Score Distribution */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Confidence Score Distribution</h3>
              {!data.detectionMetrics.length && (
                <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">Sample Data</span>
              )}
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={confidenceDistribution}
                    dataKey="count"
                    nameKey="range"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={({ range, count }) => count > 0 ? `${range}: ${count}` : ''}
                  >
                    {confidenceDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value, name) => [value, `Confidence ${name}`]} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Detections by Hour */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Detections by Hour</h3>
              {!data.detectionMetrics.length && (
                <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">Sample Data</span>
              )}
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={detectionsByHour}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="hour"
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis />
                  <Tooltip
                    formatter={(value, name) => [value, 'Detections']}
                    labelFormatter={(label) => `Hour: ${label}`}
                  />
                  <Bar
                    dataKey="detections"
                    fill={COLORS.info}
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Camera Performance */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Camera Performance</h3>
              {(!data.summary?.cameras || data.summary.cameras.length === 0) && (
                <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">Sample Data</span>
              )}
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={getCameraPerformanceData()}
                  layout="horizontal"
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 100]} />
                  <YAxis
                    type="category"
                    dataKey="name"
                    tick={{ fontSize: 12 }}
                  />
                  <Tooltip
                    formatter={(value, name) => [`${value}%`, 'Performance']}
                    labelFormatter={(label) => `Camera: ${label}`}
                  />
                  <Bar
                    dataKey="performance"
                    fill={COLORS.primary}
                    radius={[0, 4, 4, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
