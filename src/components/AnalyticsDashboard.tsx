import React, { useState, useEffect, useRef, useCallback } from 'react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { Progress } from './ui/progress';
import { Camera, Cpu, MemoryStick, AlertTriangle, Eye } from 'lucide-react';

// Type definitions
interface SystemMetrics {
  id: string;
  timestamp: string;
  cpu_usage_percent: number;
  memory_usage_percent: number;
  disk_usage_percent: number;
  network_io_mbps: number;
  created_at: string;
}

interface CameraMetrics {
  id: string;
  camera_id: string;
  timestamp: string;
  fps: number;
  resolution: string;
  bitrate_kbps: number;
  is_active: boolean;
  created_at: string;
}

interface DetectionMetrics {
  id: string;
  camera_id: string;
  timestamp: string;
  prediction_label: string;
  confidence_score: number;
  processing_time_ms: number;
  created_at: string;
}

interface AnalyticsAggregates {
  id: string;
  aggregation_type: string;
  time_period: string;
  total_detections: number;
  avg_confidence: number;
  total_cameras: number;
  avg_fps: number;
  created_at: string;
}

interface WebSocketMessage {
  type: string;
  topic: string;
  data: unknown;
  timestamp: string;
}

const AnalyticsDashboard: React.FC = () => {
  // State management
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics[]>([]);
  const [cameraMetrics, setCameraMetrics] = useState<CameraMetrics[]>([]);
  const [detectionMetrics, setDetectionMetrics] = useState<DetectionMetrics[]>([]);
  const [analyticsAggregates, setAnalyticsAggregates] = useState<AnalyticsAggregates[]>([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // WebSocket connection
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setConnectionStatus('connecting');
    const ws = new WebSocket(`ws://${window.location.host}/ws/analytics`);

    ws.onopen = () => {
      setIsConnected(true);
      setConnectionStatus('connected');
      setError(null);
      console.log('WebSocket connected');

      // Subscribe to all topics
      ws.send(JSON.stringify({
        type: 'subscribe',
        topic: 'system_metrics'
      }));
      ws.send(JSON.stringify({
        type: 'subscribe',
        topic: 'camera_metrics'
      }));
      ws.send(JSON.stringify({
        type: 'subscribe',
        topic: 'detection_metrics'
      }));
      ws.send(JSON.stringify({
        type: 'subscribe',
        topic: 'analytics_aggregates'
      }));
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        handleWebSocketMessage(message);
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      setConnectionStatus('disconnected');
      console.log('WebSocket disconnected');

      // Attempt to reconnect
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket connection error');
    };

    wsRef.current = ws;
  }, []);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    setLastUpdate(new Date());

    switch (message.topic) {
      case 'system_metrics':
        if (message.data && typeof message.data === 'object' && 'cpu_usage_percent' in message.data) {
          setSystemMetrics(prev => {
            const newMetrics = [...prev, message.data as SystemMetrics];
            return newMetrics.slice(-50); // Keep last 50 entries
          });
        }
        break;
      case 'camera_metrics':
        if (message.data && typeof message.data === 'object' && 'camera_id' in message.data) {
          setCameraMetrics(prev => {
            const newMetrics = [...prev, message.data as CameraMetrics];
            return newMetrics.slice(-100); // Keep last 100 entries
          });
        }
        break;
      case 'detection_metrics':
        if (message.data && typeof message.data === 'object' && 'prediction_label' in message.data) {
          setDetectionMetrics(prev => {
            const newMetrics = [...prev, message.data as DetectionMetrics];
            return newMetrics.slice(-200); // Keep last 200 entries
          });
        }
        break;
      case 'analytics_aggregates':
        if (message.data && typeof message.data === 'object' && 'aggregation_type' in message.data) {
          setAnalyticsAggregates(prev => {
            const newAggregates = [...prev, message.data as AnalyticsAggregates];
            return newAggregates.slice(-24); // Keep last 24 entries
          });
        }
        break;
    }
  }, []);

  // Disconnect WebSocket
  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  // Connect on component mount
  useEffect(() => {
    connectWebSocket();
    return () => disconnectWebSocket();
  }, [connectWebSocket, disconnectWebSocket]);

  // Calculate current system status
  const currentSystemMetrics = systemMetrics[systemMetrics.length - 1];
  const activeCameras = cameraMetrics.filter(cm => cm.is_active).length;
  const totalDetections = detectionMetrics.length;
  const recentDetections = detectionMetrics.slice(-10);

  // Chart data preparation
  const systemChartData = systemMetrics.slice(-20).map(metric => ({
    time: new Date(metric.timestamp).toLocaleTimeString(),
    cpu: metric.cpu_usage_percent,
    memory: metric.memory_usage_percent,
    disk: metric.disk_usage_percent
  }));

  const detectionChartData = detectionMetrics.slice(-20).map(metric => ({
    time: new Date(metric.timestamp).toLocaleTimeString(),
    confidence: metric.confidence_score,
    processingTime: metric.processing_time_ms
  }));

  const cameraStatusData = [
    { name: 'Active', value: activeCameras, color: '#10b981' },
    { name: 'Inactive', value: Math.max(0, cameraMetrics.length - activeCameras), color: '#6b7280' }
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
        <p className="text-gray-600 mt-2">Real-time surveillance system monitoring and analytics</p>

        {/* Connection Status */}
        <div className="mt-4 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${
              connectionStatus === 'connected' ? 'bg-green-500' :
              connectionStatus === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'
            }`} />
            <span className="text-sm text-gray-600">
              {connectionStatus === 'connected' ? 'Connected' :
               connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}
            </span>
          </div>

          {lastUpdate && (
            <span className="text-sm text-gray-500">
              Last update: {lastUpdate.toLocaleTimeString()}
            </span>
          )}

          <Button
            onClick={isConnected ? disconnectWebSocket : connectWebSocket}
            variant={isConnected ? 'outline' : 'default'}
            size="sm"
          >
            {isConnected ? 'Disconnect' : 'Connect'}
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {currentSystemMetrics ? `${currentSystemMetrics.cpu_usage_percent.toFixed(1)}%` : 'N/A'}
            </div>
            <Progress
              value={currentSystemMetrics?.cpu_usage_percent || 0}
              className="mt-2"
              size="sm"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
            <MemoryStick className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {currentSystemMetrics ? `${currentSystemMetrics.memory_usage_percent.toFixed(1)}%` : 'N/A'}
            </div>
            <Progress
              value={currentSystemMetrics?.memory_usage_percent || 0}
              className="mt-2"
              size="sm"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Cameras</CardTitle>
            <Camera className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeCameras}</div>
            <p className="text-xs text-muted-foreground">
              Total: {cameraMetrics.length}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Detections</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalDetections}</div>
            <p className="text-xs text-muted-foreground">
              Recent: {recentDetections.length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
          <TabsTrigger value="cameras">Cameras</TabsTrigger>
          <TabsTrigger value="detections">Detections</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* System Performance Chart */}
            <Card>
              <CardHeader>
                <CardTitle>System Performance</CardTitle>
                <CardDescription>CPU, Memory, and Disk usage over time</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={systemChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="cpu" stroke="#ef4444" name="CPU %" />
                    <Line type="monotone" dataKey="memory" stroke="#3b82f6" name="Memory %" />
                    <Line type="monotone" dataKey="disk" stroke="#10b981" name="Disk %" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Camera Status Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Camera Status</CardTitle>
                <CardDescription>Active vs Inactive cameras</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={cameraStatusData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                    >
                      {cameraStatusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="mt-4 flex justify-center gap-4">
                  {cameraStatusData.map((item) => (
                    <div key={item.name} className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                      <span className="text-sm">{item.name}: {item.value}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>Latest system events and detections</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentDetections.slice(-5).map((detection, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Eye className="h-4 w-4 text-blue-500" />
                      <div>
                        <p className="font-medium">Camera {detection.camera_id}</p>
                        <p className="text-sm text-gray-600">
                          {detection.prediction_label} ({detection.confidence_score.toFixed(2)}%)
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-500">
                        {new Date(detection.timestamp).toLocaleTimeString()}
                      </p>
                      <Badge variant="outline">
                        {detection.processing_time_ms}ms
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Tab */}
        <TabsContent value="system" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>System Metrics</CardTitle>
              <CardDescription>Detailed system performance monitoring</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={systemChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="cpu" stackId="1" stroke="#ef4444" fill="#ef4444" fillOpacity={0.3} />
                  <Area type="monotone" dataKey="memory" stackId="1" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
                  <Area type="monotone" dataKey="disk" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Cameras Tab */}
        <TabsContent value="cameras" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Camera Metrics</CardTitle>
              <CardDescription>Real-time camera performance and status</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {cameraMetrics.slice(-10).map((camera, index) => (
                  <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <Camera className={`h-5 w-5 ${camera.is_active ? 'text-green-500' : 'text-gray-400'}`} />
                      <div>
                        <p className="font-medium">Camera {camera.camera_id}</p>
                        <p className="text-sm text-gray-600">
                          {camera.resolution} • {camera.fps} FPS
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <Badge variant={camera.is_active ? 'default' : 'secondary'}>
                        {camera.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                      <div className="text-right">
                        <p className="text-sm font-medium">{camera.bitrate_kbps} kbps</p>
                        <p className="text-xs text-gray-500">
                          {new Date(camera.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Detections Tab */}
        <TabsContent value="detections" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Detection Metrics</CardTitle>
              <CardDescription>ML model performance and detection accuracy</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={detectionChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="confidence" fill="#3b82f6" name="Confidence %" />
                  <Bar dataKey="processingTime" fill="#10b981" name="Processing Time (ms)" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Analytics Aggregates</CardTitle>
              <CardDescription>Time-based analytics and trends</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analyticsAggregates.slice(-10).map((aggregate, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium">{aggregate.aggregation_type} - {aggregate.time_period}</h4>
                      <Badge variant="outline">
                        {new Date(aggregate.created_at).toLocaleDateString()}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <p className="text-2xl font-bold text-blue-600">{aggregate.total_detections}</p>
                        <p className="text-sm text-gray-600">Detections</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-green-600">{aggregate.avg_confidence.toFixed(1)}%</p>
                        <p className="text-sm text-gray-600">Avg Confidence</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-purple-600">{aggregate.total_cameras}</p>
                        <p className="text-sm text-gray-600">Cameras</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-orange-600">{aggregate.avg_fps.toFixed(1)}</p>
                        <p className="text-sm text-gray-600">Avg FPS</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AnalyticsDashboard;
