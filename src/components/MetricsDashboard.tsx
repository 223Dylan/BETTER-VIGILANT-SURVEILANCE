import React, { useEffect, useState, useRef } from 'react';
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
  Cell
} from 'recharts';

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

const MetricsDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<SystemMetrics[]>([]);
  const [summary, setSummary] = useState<MetricsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRealTime, setIsRealTime] = useState(true);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Initial load
    fetchInitialData();
    
    // Setup WebSocket for real-time updates
    if (isRealTime) {
      setupWebSocket();
    } else {
      // Fallback to polling if real-time is disabled
      const interval = setInterval(fetchSummary, 30000);
      return () => clearInterval(interval);
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [isRealTime]);

  const fetchInitialData = async () => {
    try {
      await Promise.all([
        fetchSystemMetrics(),
        fetchSummary()
      ]);
        setLoading(false);
      } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load metrics');
        setLoading(false);
      }
    };

  const fetchSystemMetrics = async () => {
    try {
      const response = await fetch('/api/metrics/system?time_range=15m&limit=50');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      
      const formattedMetrics = data.map((item: any) => ({
        timestamp: new Date(item.timestamp).toLocaleTimeString(),
        cpu_usage: item.cpu_usage,
        memory_usage: item.memory_usage,
        disk_usage: item.disk_usage,
        active_cameras: item.active_cameras
      }));

      setMetrics(formattedMetrics);
    } catch (err) {
      console.error('Error fetching system metrics:', err);
      throw err;
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await fetch('/api/metrics/summary');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setSummary(data);
    } catch (err) {
      console.error('Error fetching metrics summary:', err);
      throw err;
    }
  };

  const setupWebSocket = () => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/metrics`;
      
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('Metrics WebSocket connected');
        setError(null);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          if (message.type === 'metrics_update') {
            const data = message.data as MetricsSummary;
            setSummary(data);
            
            // Update system metrics chart with latest data point
            if (data.system) {
              const newPoint = {
                timestamp: new Date(data.system.timestamp).toLocaleTimeString(),
                cpu_usage: data.system.cpu_usage,
                memory_usage: data.system.memory_usage,
                disk_usage: data.system.disk_usage,
                active_cameras: data.system.active_cameras
              };
              
              setMetrics(prev => {
                const updated = [...prev, newPoint];
                // Keep last 50 data points
                return updated.slice(-50);
              });
            }
          } else if (message.type === 'error') {
            console.error('WebSocket error:', message.message);
            setError(`Real-time update error: ${message.message}`);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
      };

      wsRef.current.onclose = () => {
        console.log('Metrics WebSocket disconnected');
        // Try to reconnect after 5 seconds
        setTimeout(() => {
          if (isRealTime) {
            setupWebSocket();
          }
        }, 5000);
      };
    } catch (err) {
      console.error('Failed to setup WebSocket:', err);
      setError('Failed to establish real-time connection');
    }
  };



  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'online': return '#4ade80';
      case 'offline': return '#f87171';
      case 'error': return '#fbbf24';
      default: return '#6b7280';
    }
  };

  const getCameraStatusData = () => {
    if (!summary?.cameras) return [];
    
    const statusCounts = summary.cameras.reduce((acc, camera) => {
      const status = camera.status || 'unknown';
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(statusCounts).map(([status, count]) => ({
      name: status,
      value: count,
      color: getStatusColor(status)
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading metrics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error loading metrics</h3>
            <p className="mt-1 text-sm text-red-700">{error}</p>
            <div className="mt-3">
              <button
                onClick={fetchInitialData}
                className="bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded text-sm"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">System Metrics Dashboard</h2>
        <div className="flex items-center space-x-4">
          <span className="text-sm font-medium text-gray-700">
            Real-time updates <span className="text-green-500">●</span>
          </span>
          <span className="text-sm text-gray-500">
            Last updated: {summary?.system ? new Date(summary.system.timestamp).toLocaleTimeString() : 'Never'}
          </span>
        </div>
      </div>



      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Metrics Chart */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">System Performance (Last 15 minutes)</h3>
          <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="cpu_usage"
                  name="CPU (%)"
              stroke="#ff6384"
                  strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="memory_usage"
                  name="Memory (%)"
              stroke="#35a2eb"
                  strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="disk_usage"
                  name="Disk (%)"
              stroke="#4bc0c0"
                  strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
        </div>

        {/* Camera Status Chart */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Camera Status Distribution</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={getCameraStatusData()}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {getCameraStatusData().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Detections */}
      {summary?.recent_detections && summary.recent_detections.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Detections</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Camera</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Label</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Confidence</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Alert</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {summary.recent_detections.map((detection, index) => (
                  <tr key={index} className={detection.is_shoplifting ? 'bg-red-50' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {detection.camera_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        detection.is_shoplifting ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                      }`}>
                        {detection.label}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {(detection.confidence * 100).toFixed(1)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {detection.alert_triggered ? (
                        <span className="text-red-600">[ALERT] Yes</span>
                      ) : (
                        <span className="text-gray-400">No</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(detection.timestamp).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default MetricsDashboard; 