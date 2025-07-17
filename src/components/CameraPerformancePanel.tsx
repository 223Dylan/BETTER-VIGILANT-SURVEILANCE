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
  AreaChart,
  Area
} from 'recharts';
import { metricsService, CameraMetrics, CameraPerformance } from '../services/metrics.service';

interface CameraPerformancePanelProps {
  cameraId: string;
  timeRange?: string;
  realTime?: boolean;
}

const CameraPerformancePanel: React.FC<CameraPerformancePanelProps> = ({
  cameraId,
  timeRange = '1h',
  realTime = false
}) => {
  const [performance, setPerformance] = useState<CameraPerformance | null>(null);
  const [currentMetrics, setCurrentMetrics] = useState<CameraMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    loadPerformanceData();
    
    if (realTime) {
      setupWebSocket();
    } else {
      const interval = setInterval(loadPerformanceData, 30000);
      return () => clearInterval(interval);
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [cameraId, timeRange, realTime]);

  const loadPerformanceData = async () => {
    try {
      const [performanceData, camerasData] = await Promise.all([
        metricsService.getCameraPerformance(cameraId, timeRange),
        metricsService.getCameraMetrics()
      ]);
      
      setPerformance(performanceData);
      const camera = camerasData.find(c => c.camera_id === cameraId);
      setCurrentMetrics(camera || null);
      setLoading(false);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load performance data');
      setLoading(false);
    }
  };

  const setupWebSocket = () => {
    try {
      wsRef.current = metricsService.createCameraMetricsWebSocket(cameraId);

      wsRef.current.onopen = () => {
        console.log(`Camera metrics WebSocket connected for ${cameraId}`);
        setError(null);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = metricsService.parseWebSocketMessage(event);
          
          if (message?.type === 'camera_metrics_update' && message.camera_id === cameraId) {
            if (message.performance) {
              setPerformance(message.performance);
            }
            
            // Update current metrics with latest data point if available
            if (message.performance?.data && message.performance.data.length > 0) {
              const latest = message.performance.data[message.performance.data.length - 1];
              setCurrentMetrics(prev => prev ? {
                ...prev,
                fps_actual: latest.fps_actual,
                latency_ms: latest.latency_ms
              } : null);
            }
          }
        } catch (err) {
          console.error('Error parsing camera metrics WebSocket message:', err);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('Camera metrics WebSocket error:', error);
        setError('WebSocket connection error');
      };

      wsRef.current.onclose = () => {
        console.log(`Camera metrics WebSocket disconnected for ${cameraId}`);
        if (realTime) {
          setTimeout(() => setupWebSocket(), 5000);
        }
      };
    } catch (err) {
      console.error('Failed to setup camera metrics WebSocket:', err);
      setError('Failed to establish real-time connection');
    }
  };

  const getStatusBadge = (status: string) => {
    const baseClasses = "px-2 py-1 rounded-full text-xs font-medium";
    switch (status?.toLowerCase()) {
      case 'online':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'offline':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'error':
        return `${baseClasses} bg-red-100 text-red-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  const formatLatency = (latency: number) => {
    if (latency < 1000) {
      return `${latency.toFixed(0)}ms`;
    }
    return `${(latency / 1000).toFixed(1)}s`;
  };

  const getPerformanceColor = (actual: number, target: number) => {
    const percentage = (actual / target) * 100;
    if (percentage >= 90) return '#22c55e'; // green
    if (percentage >= 70) return '#eab308'; // yellow
    return '#ef4444'; // red
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-48 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center">
          <div className="text-red-500 mb-2 font-bold">ERROR</div>
          <p className="text-red-600 text-sm">{error}</p>
          <button
            onClick={loadPerformanceData}
            className="mt-2 px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200 text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">
            Camera {cameraId} Performance
          </h3>
          <div className="flex items-center space-x-3">
            {currentMetrics && (
              <span className={getStatusBadge(currentMetrics.status)}>
                {currentMetrics.status}
              </span>
            )}
            {realTime && (
              <span className="flex items-center text-sm text-green-600">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></span>
                Live
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Current Metrics */}
      {currentMetrics && (
        <div className="px-6 py-4 bg-gray-50">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold" style={{ 
                color: getPerformanceColor(currentMetrics.fps_actual, currentMetrics.fps_target) 
              }}>
                {currentMetrics.fps_actual.toFixed(1)}
              </div>
              <div className="text-xs text-gray-500">
                FPS (Target: {currentMetrics.fps_target})
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {formatLatency(currentMetrics.latency_ms)}
              </div>
              <div className="text-xs text-gray-500">Latency</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {performance?.data?.length || 0}
              </div>
              <div className="text-xs text-gray-500">Data Points</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {currentMetrics.last_detection ? 'ACTIVE' : 'MONITOR'}
              </div>
              <div className="text-xs text-gray-500">
                {currentMetrics.last_detection ? 'Detecting' : 'Watching'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Performance Charts */}
      {performance?.data && performance.data.length > 0 && (
        <div className="p-6 space-y-6">
          {/* FPS Chart */}
          <div>
            <h4 className="text-md font-medium text-gray-700 mb-3">FPS Performance</h4>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={performance.data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                    formatter={(value: number) => [value.toFixed(1), 'FPS']}
                  />
                  <Area
                    type="monotone"
                    dataKey="fps_actual"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Latency Chart */}
          <div>
            <h4 className="text-md font-medium text-gray-700 mb-3">Processing Latency</h4>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={performance.data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis tickFormatter={(value) => `${value}ms`} />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                    formatter={(value: number) => [formatLatency(value), 'Latency']}
                  />
                  <Line
                    type="monotone"
                    dataKey="latency_ms"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Queue Depth & Dropped Frames */}
          <div>
            <h4 className="text-md font-medium text-gray-700 mb-3">Queue Performance</h4>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={performance.data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="queue_depth"
                    name="Queue Depth"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="dropped_frames"
                    name="Dropped Frames"
                    stroke="#ef4444"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {(!performance?.data || performance.data.length === 0) && (
        <div className="p-6 text-center text-gray-500">
          <div className="text-4xl mb-2 text-gray-400">NO DATA</div>
          <p>No performance data available for the selected time range.</p>
          <p className="text-sm mt-1">Data will appear once the camera starts processing frames.</p>
        </div>
      )}
    </div>
  );
};

export default CameraPerformancePanel; 