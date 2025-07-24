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
  const [selectedTimeRange, setSelectedTimeRange] = useState<TimeRange>(TIME_RANGES[0]);
  const [customDateRange, setCustomDateRange] = useState({
    start: '',
    end: ''
  });
  const [isCustomRange, setIsCustomRange] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    loadAnalyticsData();
    setupWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [selectedTimeRange]);

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
        metricsService.getSystemMetrics(selectedTimeRange.value, 100),
        metricsService.getDetectionMetrics(selectedTimeRange.value),
        metricsService.getMetricsSummary(),
        metricsService.getHealthStatus(),
        metricsService.getRecentAlerts(50)
      ]);

      // Process alert metrics by time
      const alertMetrics = processAlertMetrics(recentAlerts, selectedTimeRange.days);

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
    if (!data.detectionMetrics.length) return [];

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

  const calculateDetectionStats = () => {
    if (!data.detectionMetrics.length) return { totalDetections: 0, avgConfidence: 0, shoplifting: 0 };

    const totalDetections = data.detectionMetrics.length;
    const avgConfidence = data.detectionMetrics.reduce((sum, d) => sum + d.confidence, 0) / totalDetections;
    const shoplifting = data.detectionMetrics.filter(d => d.is_shoplifting).length;

    return { totalDetections, avgConfidence: Math.round(avgConfidence * 100), shoplifting };
  };

  const getConfidenceDistribution = () => {
    if (!data.detectionMetrics.length) return [];

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

  const handleTimeRangeChange = (timeRange: TimeRange) => {
    setSelectedTimeRange(timeRange);
    setIsCustomRange(false);
  };

  const handleCustomDateRange = () => {
    if (customDateRange.start && customDateRange.end) {
      setIsCustomRange(true);
      // Implementation for custom date range would go here
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
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">Comprehensive system and detection analytics</p>
        </div>

        {/* Time Range Selector */}
        <div className="flex items-center space-x-4">
          <div className="flex bg-gray-100 rounded-lg p-1">
            {TIME_RANGES.map((range) => (
              <button
                key={range.value}
                onClick={() => handleTimeRangeChange(range)}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                  selectedTimeRange.value === range.value && !isCustomRange
                    ? 'bg-white shadow text-blue-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>

          {/* Custom Date Range */}
          <div className="flex items-center space-x-2">
            <input
              type="date"
              value={customDateRange.start}
              onChange={(e) => setCustomDateRange(prev => ({ ...prev, start: e.target.value }))}
              className="border border-gray-300 rounded px-2 py-1 text-sm"
            />
            <span className="text-gray-500">-</span>
            <input
              type="date"
              value={customDateRange.end}
              onChange={(e) => setCustomDateRange(prev => ({ ...prev, end: e.target.value }))}
              className="border border-gray-300 rounded px-2 py-1 text-sm"
            />
            <button
              onClick={handleCustomDateRange}
              className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
            >
              Apply
            </button>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Error: {error}
        </div>
      )}

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
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

        <div className="bg-white rounded-lg shadow p-6">
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

        <div className="bg-white rounded-lg shadow p-6">
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

        <div className="bg-white rounded-lg shadow p-6">
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

      {/* Main Content - Two Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* System Metrics Section */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <ServerIcon className="h-6 w-6 mr-2" />
            System Metrics
          </h2>

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

        {/* Detection System Section */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <EyeIcon className="h-6 w-6 mr-2" />
            Detection System Analytics
          </h2>

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
            <h3 className="text-lg font-medium text-gray-900 mb-4">Confidence Score Distribution</h3>
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
            <h3 className="text-lg font-medium text-gray-900 mb-4">Detections by Hour</h3>
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

          {/* Detection Rate by Camera */}
          {data.summary?.cameras && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Detection Rate by Camera</h3>
              <div className="space-y-3">
                {data.summary.cameras.map((camera: any) => (
                  <div key={camera.camera_id} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Camera {camera.camera_id}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${Math.min(camera.fps_actual / camera.fps_target * 100, 100)}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-500">
                        {((camera.fps_actual / camera.fps_target) * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
