import React, { useState, useEffect, useRef, useCallback } from 'react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { Progress } from './ui/progress';
import { Camera, Cpu, MemoryStick, AlertTriangle, Eye, Server, Bell, Shield, Activity, BarChart3 } from 'lucide-react';
import { useThemeClasses, useTheme } from '../contexts/ThemeContext';

// VERIFIED REAL DATA TYPES ONLY
interface LiveSystemPerformance {
  id: string;
  hostname: string;
  timestamp: string;
  cpu_usage_percent: number;
  memory_usage_percent: number;
  memory_total_gb: number;
  memory_used_gb: number;
  disk_usage_percent: number;
  disk_total_gb: number;
  disk_used_gb: number;
  network_sent_mb: number;
  network_recv_mb: number;
  uptime_hours: number;
  process_count: number;
  data_source: string;
}

interface AlertAnalytics {
  id: string;
  timestamp: string;
  alerts_last_24h: number;
  alerts_last_week: number;
  alerts_last_30d: number;
  active_alerts_total: number;
  alerts_by_severity: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };

  avg_confidence_7d: number;
  recent_alerts: Array<{
    id: string;
    type: string;
    severity: string;
    confidence: number;
    camera_id: string;
    timestamp: string;
    status: string;
    message: string;
  }>;
  chart_data: {
    hourly: Record<string, number>;
    daily: Record<string, number>;
    weekly: Record<string, number>;
    raw_alerts: Array<{
      timestamp: string;
      type: string;
      severity: string;
      confidence: number;
    }>;
  };
  data_source: string;
}

interface CameraAnalytics {
  id: string;
  timestamp: string;
  total_cameras: number;
  enabled_cameras: number;
  active_cameras: number;
  camera_status_breakdown: Record<string, number>;
  camera_details: Array<{
    id: string;
    name: string;
    enabled: boolean;
    status: string;
    location: string;
    zone: string;
    fps: number;
    resolution: string;
    source_type: string;
    detection_enabled: boolean;
  }>;
  data_source: string;
}

interface NotificationAnalytics {
  id: string;
  timestamp: string;
  notifications_last_24h: number;
  notifications_last_week: number;
  notification_status_breakdown: Record<string, number>;
  notification_type_breakdown: Record<string, number>;
  data_source: string;
}

interface VerifiedDashboardData {
  live_system_performance: LiveSystemPerformance | null;
  alert_analytics: AlertAnalytics | null;
  camera_analytics: CameraAnalytics | null;
  notification_analytics: NotificationAnalytics | null;
  last_updated: string;
  data_sources: string[];
  verification_status: string;
}

const AnalyticsDashboard: React.FC = () => {
  const themeClasses = useThemeClasses();
  const { actualTheme } = useTheme();

  // VERIFIED DATA STATE
  const [dashboardData, setDashboardData] = useState<VerifiedDashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting');

  // Chart state
  const [chartTimeFilter, setChartTimeFilter] = useState<'24h' | '7d' | '30d'>('7d');
  const [chartData, setChartData] = useState<any[]>([]);
  const [isLoadingChart, setIsLoadingChart] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);

  // WebSocket connection for real-time updates
  useEffect(() => {
    connectWebSocket();

    // Fetch initial data
    fetchDashboardData();

    // Cleanup
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = useCallback(() => {
    try {
      const wsHost = process.env.NODE_ENV === 'development' ? 'localhost:8001' : window.location.host;
      const ws = new WebSocket(`ws://${wsHost}/ws/analytics`);

      ws.onopen = () => {
        console.log('✅ WebSocket connected for VERIFIED analytics');
        setConnectionStatus('connected');

        // Subscribe to VERIFIED data topics only
        ws.send(JSON.stringify([
          'live_system',
          'alert_analytics',
          'camera_analytics',
          'notification_analytics'
        ]));
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('📡 Received VERIFIED analytics update:', message.type);

          // Update dashboard data based on message type
          if (message.type === 'live_system_update') {
            setDashboardData(prev => prev ? {
              ...prev,
              live_system_performance: message.data
            } : null);
          } else if (message.type === 'alert_analytics_update') {
            setDashboardData(prev => prev ? {
              ...prev,
              alert_analytics: message.data
            } : null);
          } else if (message.type === 'camera_analytics_update') {
            setDashboardData(prev => prev ? {
              ...prev,
              camera_analytics: message.data
            } : null);
          } else if (message.type === 'notification_analytics_update') {
            setDashboardData(prev => prev ? {
              ...prev,
              notification_analytics: message.data
            } : null);
          }

          setLastUpdate(new Date().toLocaleTimeString());

        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('disconnected');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionStatus('disconnected');

        // Reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };

      wsRef.current = ws;

    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setConnectionStatus('disconnected');
    }
  }, []);

  const fetchDashboardData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch('/api/analytics/dashboard');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: VerifiedDashboardData = await response.json();
      console.log('✅ Fetched VERIFIED dashboard data:', data);

      setDashboardData(data);
      setLastUpdate(new Date().toLocaleTimeString());

    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data');
    } finally {
      setIsLoading(false);
    }
  };

  const refreshData = useCallback(() => {
    fetchDashboardData();
  }, []);

  const fetchChartData = useCallback(async (timePeriod: string) => {
    try {
      setIsLoadingChart(true);

      // Use the existing dashboard data if available, otherwise fetch from API
      let alertData = null;
      if (dashboardData?.alert_analytics) {
        alertData = dashboardData.alert_analytics;
      } else {
        const response = await fetch('/api/analytics/alerts');
        if (response.ok) {
          alertData = await response.json();
        }
      }

      if (!alertData || !alertData.chart_data) {
        setChartData([]);
        return;
      }

      // Use real chart data from the backend
      let chartDataPoints: any[] = [];
      const chartData = alertData.chart_data;

      if (timePeriod === '24h') {
        // Use hourly data from the last 24 hours
        const now = new Date();
        const hourlyData = chartData.hourly || {};

        // Generate 24 hourly data points
        for (let i = 23; i >= 0; i--) {
          const time = new Date(now.getTime() - (i * 60 * 60 * 1000));
          const hourKey = time.toISOString().slice(0, 13) + ':00';
          const alerts = hourlyData[hourKey] || 0;

          chartDataPoints.push({
            time: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
            alerts: alerts,
            timestamp: time.toISOString()
          });
        }
      } else if (timePeriod === '7d') {
        // Use daily data from the last 7 days
        const now = new Date();
        const dailyData = chartData.daily || {};

        // Generate 7 daily data points
        for (let i = 6; i >= 0; i--) {
          const time = new Date(now.getTime() - (i * 24 * 60 * 60 * 1000));
          const dayKey = time.toISOString().slice(0, 10);
          const alerts = dailyData[dayKey] || 0;

          chartDataPoints.push({
            time: time.toLocaleDateString('en-US', { weekday: 'short' }),
            alerts: alerts,
            timestamp: time.toISOString()
          });
        }
      } else if (timePeriod === '30d') {
        // Use daily data from the last 30 days
        const now = new Date();
        const dailyData = chartData.daily || {};

        // Generate 30 daily data points
        for (let i = 29; i >= 0; i--) {
          const time = new Date(now.getTime() - (i * 24 * 60 * 60 * 1000));
          const dayKey = time.toISOString().slice(0, 10);
          const alerts = dailyData[dayKey] || 0;

          chartDataPoints.push({
            time: time.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
            alerts: alerts,
            timestamp: time.toISOString()
          });
        }
      }

      setChartData(chartDataPoints);
    } catch (err) {
      console.error('Error fetching chart data:', err);
      setChartData([]);
    } finally {
      setIsLoadingChart(false);
    }
  }, [dashboardData]);

  // Load chart data when time filter changes or dashboard data updates
  useEffect(() => {
    if (dashboardData?.alert_analytics) {
      fetchChartData(chartTimeFilter);
    }
  }, [chartTimeFilter, fetchChartData, dashboardData]);

  if (isLoading) {
    return (
      <div className={`min-h-screen ${themeClasses.bg} ${themeClasses.text} p-8`}>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Activity className="h-8 w-8 animate-spin mx-auto mb-4 text-gray-600 dark:text-gray-400" />
            <p className="text-gray-600 dark:text-gray-400">Loading analytics data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`min-h-screen ${themeClasses.bg} ${themeClasses.text} p-8`}>
        <Alert className="max-w-lg mx-auto">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Error loading analytics: {error}
            <Button onClick={refreshData} className="ml-4" size="sm">
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className={`min-h-screen ${themeClasses.bg} ${themeClasses.text} p-8`}>
        <div className="text-center">
          <p className="text-gray-600 dark:text-gray-400">No analytics data available</p>
          <Button onClick={refreshData} className="mt-4">
            Load Data
          </Button>
        </div>
      </div>
    );
  }

  const { live_system_performance, alert_analytics, camera_analytics, notification_analytics } = dashboardData;

  return (
    <div className={`min-h-screen ${themeClasses.bg} ${themeClasses.text}`}>
      <div className="container mx-auto px-4 py-8">

        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2 text-gray-900 dark:text-white">Analytics Dashboard</h1>
            <p className="text-gray-600 dark:text-gray-300">
              Real-time monitoring and system analytics
            </p>
            <div className="flex items-center gap-4 mt-2">
              <Badge variant={connectionStatus === 'connected' ? 'default' : 'destructive'} className={connectionStatus === 'connected' ? 'bg-green-500 hover:bg-green-600 text-white dark:bg-green-600 dark:hover:bg-green-700' : 'bg-red-500 hover:bg-red-600 text-white dark:bg-red-600 dark:hover:bg-red-700'}>
                {connectionStatus === 'connected' ? '🟢 Live' : '🔴 Offline'}
              </Badge>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Last updated: {lastUpdate}
              </span>
            </div>
          </div>
          <Button onClick={refreshData} variant="outline" className="border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800">
            Refresh Data
          </Button>
        </div>

        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">

          {/* System Performance */}
          {live_system_performance && (
            <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-900 dark:text-white">System Performance</CardTitle>
                <Server className="h-4 w-4 text-gray-500 dark:text-gray-400" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {live_system_performance.cpu_usage_percent?.toFixed(1) || 0}% CPU
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-300">
                  {live_system_performance.memory_usage_percent?.toFixed(1) || 0}% Memory
                </p>
                <div className="mt-2">
                  <Progress value={live_system_performance.cpu_usage_percent || 0} className="h-2" />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Active Alerts */}
          {alert_analytics && (
            <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-900 dark:text-white">Active Alerts</CardTitle>
                <AlertTriangle className="h-4 w-4 text-gray-500 dark:text-gray-400" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {alert_analytics.active_alerts_total || 0}
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-300">
                  {alert_analytics.alerts_last_24h || 0} in last 24h
                </p>
                <div className="flex gap-1 mt-2">
                  <Badge variant="destructive" className="text-xs bg-red-500 hover:bg-red-600 text-white dark:bg-red-600 dark:hover:bg-red-700">
                    {alert_analytics.alerts_by_severity?.critical || 0} Critical
                  </Badge>
                  <Badge variant="secondary" className="text-xs bg-gray-200 hover:bg-gray-300 text-gray-800 dark:bg-gray-600 dark:hover:bg-gray-500 dark:text-gray-200">
                    {alert_analytics.alerts_by_severity?.high || 0} High
                  </Badge>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Camera Status */}
          {camera_analytics && (
            <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-900 dark:text-white">Camera Status</CardTitle>
                <Camera className="h-4 w-4 text-gray-500 dark:text-gray-400" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {camera_analytics.active_cameras || 0}/{camera_analytics.total_cameras || 0}
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-300">
                  Active cameras
                </p>
                <div className="mt-2">
                  <Progress
                    value={camera_analytics.total_cameras > 0 ?
                      (camera_analytics.active_cameras / camera_analytics.total_cameras) * 100 : 0
                    }
                    className="h-2"
                  />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Notifications */}
          {notification_analytics && (
            <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-900 dark:text-white">Notifications</CardTitle>
                <Bell className="h-4 w-4 text-gray-500 dark:text-gray-400" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {notification_analytics.notifications_last_24h || 0}
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-300">
                  Sent in last 24h
                </p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Detailed Analytics Tabs */}
        <Tabs defaultValue="alerts" className="w-full">
          <TabsList className="grid w-full grid-cols-4 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
            <TabsTrigger value="alerts" className="text-gray-700 dark:text-gray-300 data-[state=active]:bg-white dark:data-[state=active]:bg-gray-700 data-[state=active]:text-gray-900 dark:data-[state=active]:text-white">Alert Analytics</TabsTrigger>
            <TabsTrigger value="cameras" className="text-gray-700 dark:text-gray-300 data-[state=active]:bg-white dark:data-[state=active]:bg-gray-700 data-[state=active]:text-gray-900 dark:data-[state=active]:text-white">Camera Analytics</TabsTrigger>
            <TabsTrigger value="system" className="text-gray-700 dark:text-gray-300 data-[state=active]:bg-white dark:data-[state=active]:bg-gray-700 data-[state=active]:text-gray-900 dark:data-[state=active]:text-white">System Performance</TabsTrigger>
            <TabsTrigger value="notifications" className="text-gray-700 dark:text-gray-300 data-[state=active]:bg-white dark:data-[state=active]:bg-gray-700 data-[state=active]:text-gray-900 dark:data-[state=active]:text-white">Notifications</TabsTrigger>
          </TabsList>

          {/* Alert Analytics Tab */}
          <TabsContent value="alerts" className="space-y-6">
            {alert_analytics ? (
              <>
                {/* Alert Statistics */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-gray-900 dark:text-white">Last 24 Hours</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">{alert_analytics.alerts_last_24h}</div>
                    </CardContent>
                  </Card>
                  <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-gray-900 dark:text-white">Last 7 Days</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">{alert_analytics.alerts_last_week}</div>
                    </CardContent>
                  </Card>
                  <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-gray-900 dark:text-white">Last 30 Days</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">{alert_analytics.alerts_last_30d || 0}</div>
                    </CardContent>
                  </Card>
                  <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-gray-900 dark:text-white">Avg Confidence (7d)</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {((alert_analytics.avg_confidence_7d || 0) * 100).toFixed(1)}%
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Alerts Chart */}
                <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-gray-900 dark:text-white flex items-center gap-2">
                          <BarChart3 className="h-5 w-5" />
                          Alert Trends
                        </CardTitle>
                        <CardDescription className="text-gray-600 dark:text-gray-400">
                          Track alert patterns over time
                        </CardDescription>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant={chartTimeFilter === '24h' ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setChartTimeFilter('24h')}
                          className={chartTimeFilter === '24h' ? 'bg-blue-500 hover:bg-blue-600 text-white dark:bg-blue-600 dark:hover:bg-blue-700' : 'border-gray-300 text-gray-700 dark:border-gray-600 dark:text-gray-300'}
                        >
                          Last 24 Hours
                        </Button>
                        <Button
                          variant={chartTimeFilter === '7d' ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setChartTimeFilter('7d')}
                          className={chartTimeFilter === '7d' ? 'bg-blue-500 hover:bg-blue-600 text-white dark:bg-blue-600 dark:hover:bg-blue-700' : 'border-gray-300 text-gray-700 dark:border-gray-600 dark:text-gray-300'}
                        >
                          Last 7 Days
                        </Button>
                        <Button
                          variant={chartTimeFilter === '30d' ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setChartTimeFilter('30d')}
                          className={chartTimeFilter === '30d' ? 'bg-blue-500 hover:bg-blue-600 text-white dark:bg-blue-600 dark:hover:bg-blue-700' : 'border-gray-300 text-gray-700 dark:border-gray-600 dark:text-gray-300'}
                        >
                          Last 30 Days
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {isLoadingChart ? (
                      <div className="flex items-center justify-center h-64">
                        <div className="text-center">
                          <Activity className="h-8 w-8 animate-spin mx-auto mb-4 text-gray-600 dark:text-gray-400" />
                          <p className="text-gray-600 dark:text-gray-400">Loading chart data...</p>
                        </div>
                      </div>
                    ) : chartData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={chartTimeFilter === '30d' ? 400 : chartTimeFilter === '24h' ? 350 : 300}>
                        <AreaChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: chartTimeFilter === '24h' ? 20 : 5 }}>
                          <defs>
                            <linearGradient id="alertsGradient" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                              <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke={actualTheme === 'light' ? '#e5e7eb' : '#374151'} opacity={0.3} />
                          <XAxis
                            dataKey="time"
                            stroke={actualTheme === 'light' ? '#6b7280' : '#9ca3af'}
                            fontSize={12}
                            tick={{ fill: actualTheme === 'light' ? '#6b7280' : '#9ca3af' }}
                            interval={chartTimeFilter === '30d' ? 'preserveStartEnd' : chartTimeFilter === '24h' ? 2 : 0}
                            angle={chartTimeFilter === '30d' ? -45 : 0}
                            textAnchor={chartTimeFilter === '30d' ? 'end' : 'middle'}
                            height={chartTimeFilter === '30d' ? 60 : 30}
                          />
                          <YAxis
                            stroke={actualTheme === 'light' ? '#6b7280' : '#9ca3af'}
                            fontSize={12}
                            tick={{ fill: actualTheme === 'light' ? '#6b7280' : '#9ca3af' }}
                          />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: actualTheme === 'light' ? '#ffffff' : '#1f2937',
                              border: actualTheme === 'light' ? '1px solid #e5e7eb' : '1px solid #374151',
                              borderRadius: '8px',
                              color: actualTheme === 'light' ? '#111827' : '#f9fafb'
                            }}
                            labelStyle={{
                              color: actualTheme === 'light' ? '#111827' : '#f9fafb'
                            }}
                          />
                          <Area
                            type="monotone"
                            dataKey="alerts"
                            stroke="#ef4444"
                            strokeWidth={2}
                            fill="url(#alertsGradient)"
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="flex items-center justify-center h-64">
                        <div className="text-center">
                          <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-400 dark:text-gray-500" />
                          <p className="text-gray-600 dark:text-gray-400">No chart data available</p>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Alert Type Breakdown */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                    <CardHeader>
                      <CardTitle className="text-gray-900 dark:text-white">Alerts by Severity</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {Object.entries(alert_analytics.alerts_by_severity).map(([severity, count]) => (
                          <div key={severity} className="flex justify-between items-center">
                            <span className="capitalize text-gray-700 dark:text-gray-300">{severity}</span>
                            <Badge variant={
                              severity === 'critical' ? 'destructive' :
                              severity === 'high' ? 'secondary' : 'outline'
                            } className={
                              severity === 'critical' ? 'bg-red-500 hover:bg-red-600 text-white dark:bg-red-600 dark:hover:bg-red-700' :
                              severity === 'high' ? 'bg-orange-500 hover:bg-orange-600 text-white dark:bg-orange-600 dark:hover:bg-orange-700' :
                              severity === 'medium' ? 'bg-yellow-500 hover:bg-yellow-600 text-white dark:bg-yellow-600 dark:hover:bg-yellow-700' :
                              'border-gray-300 text-gray-700 dark:border-gray-600 dark:text-gray-300'
                            }>
                              {count}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                    <CardHeader>
                      <CardTitle className="text-gray-900 dark:text-white">Severity Distribution</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={[
                                { name: 'Critical', value: alert_analytics.alerts_by_severity.critical, color: '#dc2626' },
                                { name: 'High', value: alert_analytics.alerts_by_severity.high, color: '#ea580c' },
                                { name: 'Medium', value: alert_analytics.alerts_by_severity.medium, color: '#d97706' },
                                { name: 'Low', value: alert_analytics.alerts_by_severity.low, color: '#65a30d' }
                              ]}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
                              outerRadius={80}
                              fill="#8884d8"
                              dataKey="value"
                            >
                              {[
                                { name: 'Critical', value: alert_analytics.alerts_by_severity.critical, color: '#dc2626' },
                                { name: 'High', value: alert_analytics.alerts_by_severity.high, color: '#ea580c' },
                                { name: 'Medium', value: alert_analytics.alerts_by_severity.medium, color: '#d97706' },
                                { name: 'Low', value: alert_analytics.alerts_by_severity.low, color: '#65a30d' }
                              ].map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                              ))}
                            </Pie>
                            <Tooltip
                              contentStyle={{
                                backgroundColor: actualTheme === 'light' ? '#ffffff' : '#1f2937',
                                border: actualTheme === 'light' ? '1px solid #e5e7eb' : '1px solid #374151',
                                borderRadius: '8px',
                                color: actualTheme === 'light' ? '#111827' : '#f9fafb'
                              }}
                              labelStyle={{
                                color: actualTheme === 'light' ? '#111827' : '#f9fafb'
                              }}
                            />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Recent Alerts */}
                <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                  <CardHeader>
                    <CardTitle className="text-gray-900 dark:text-white">Recent Alerts</CardTitle>
                    <CardDescription className="text-gray-600 dark:text-gray-400">Latest alerts from your surveillance system</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {alert_analytics.recent_alerts.length > 0 ? (
                        alert_analytics.recent_alerts.map((alert) => (
                          <div key={alert.id} className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700">
                            <div className="flex items-center gap-3">
                              <Badge variant={
                                alert.severity === 'critical' ? 'destructive' :
                                alert.severity === 'high' ? 'secondary' : 'outline'
                              } className={
                                alert.severity === 'critical' ? 'bg-red-500 hover:bg-red-600 text-white dark:bg-red-600 dark:hover:bg-red-700' :
                                alert.severity === 'high' ? 'bg-orange-500 hover:bg-orange-600 text-white dark:bg-orange-600 dark:hover:bg-orange-700' :
                                'border-gray-300 text-gray-700 dark:border-gray-600 dark:text-gray-300'
                              }>
                                {alert.severity}
                              </Badge>
                              <div>
                                <p className="font-medium text-gray-900 dark:text-white">{alert.type.replace('_', ' ')}</p>
                                <p className="text-sm text-gray-600 dark:text-gray-300">
                                  Camera {alert.camera_id} • {alert.confidence * 100}% confidence
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-sm text-gray-600 dark:text-gray-300">{new Date(alert.timestamp).toLocaleTimeString()}</p>
                              <Badge variant="outline" className="text-xs border-gray-300 text-gray-700 dark:border-gray-600 dark:text-gray-300">
                                {alert.status}
                              </Badge>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                          <Shield className="h-12 w-12 mx-auto mb-4 opacity-50" />
                          <p className="text-gray-600 dark:text-gray-400">No recent alerts</p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">Your system is secure</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-600 dark:text-gray-400">Alert analytics data not available</p>
              </div>
            )}
          </TabsContent>

          {/* Camera Analytics Tab */}
          <TabsContent value="cameras" className="space-y-6">
            {camera_analytics ? (
              <>
                {/* Camera Overview */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-gray-900 dark:text-white">Total Cameras</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">{camera_analytics.total_cameras}</div>
                    </CardContent>
                  </Card>
                  <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-gray-900 dark:text-white">Enabled</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">{camera_analytics.enabled_cameras}</div>
                    </CardContent>
                  </Card>
                  <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-gray-900 dark:text-white">Active</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">{camera_analytics.active_cameras}</div>
                    </CardContent>
                  </Card>
                </div>

                {/* Camera Details */}
                <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                  <CardHeader>
                    <CardTitle className="text-gray-900 dark:text-white">Camera Details</CardTitle>
                    <CardDescription className="text-gray-600 dark:text-gray-400">Status and configuration of all cameras</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {camera_analytics.camera_details.map((camera) => (
                        <div key={camera.id} className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700">
                          <div className="flex items-center gap-3">
                            <Camera className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                            <div>
                              <p className="font-medium text-gray-900 dark:text-white">{camera.name}</p>
                              <p className="text-sm text-gray-500 dark:text-gray-400">
                                {camera.location} • {camera.resolution} • {camera.fps} FPS
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant={camera.enabled ? 'default' : 'secondary'} className={camera.enabled ? 'bg-green-500 hover:bg-green-600 text-white dark:bg-green-600 dark:hover:bg-green-700' : 'bg-gray-200 hover:bg-gray-300 text-gray-800 dark:bg-gray-600 dark:hover:bg-gray-500 dark:text-gray-200'}>
                              {camera.enabled ? 'Enabled' : 'Disabled'}
                            </Badge>
                            <Badge variant={
                              camera.status === 'active' ? 'default' :
                              camera.status === 'starting' ? 'secondary' : 'destructive'
                            } className={
                              camera.status === 'active' ? 'bg-green-500 hover:bg-green-600 text-white dark:bg-green-600 dark:hover:bg-green-700' :
                              camera.status === 'starting' ? 'bg-yellow-500 hover:bg-yellow-600 text-white dark:bg-yellow-600 dark:hover:bg-yellow-700' :
                              'bg-red-500 hover:bg-red-600 text-white dark:bg-red-600 dark:hover:bg-red-700'
                            }>
                              {camera.status}
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-600 dark:text-gray-400">Camera analytics data not available</p>
              </div>
            )}
          </TabsContent>

          {/* System Performance Tab */}
          <TabsContent value="system" className="space-y-6">
            {live_system_performance ? (
              <>
                {/* System Overview */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-gray-900 dark:text-white">CPU Usage</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {live_system_performance.cpu_usage_percent.toFixed(1)}%
                      </div>
                      <Progress value={live_system_performance.cpu_usage_percent} className="mt-2" />
                    </CardContent>
                  </Card>
                  <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-gray-900 dark:text-white">Memory Usage</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {live_system_performance.memory_usage_percent.toFixed(1)}%
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {live_system_performance.memory_used_gb.toFixed(1)} / {live_system_performance.memory_total_gb.toFixed(1)} GB
                      </p>
                      <Progress value={live_system_performance.memory_usage_percent} className="mt-2" />
                    </CardContent>
                  </Card>
                  <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-gray-900 dark:text-white">Disk Usage</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {live_system_performance.disk_usage_percent.toFixed(1)}%
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {live_system_performance.disk_used_gb.toFixed(1)} / {live_system_performance.disk_total_gb.toFixed(1)} GB
                      </p>
                      <Progress value={live_system_performance.disk_usage_percent} className="mt-2" />
                    </CardContent>
                  </Card>
                  <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-gray-900 dark:text-white">Uptime</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {(live_system_performance.uptime_hours / 24).toFixed(1)}d
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {live_system_performance.process_count} processes
                      </p>
                    </CardContent>
                  </Card>
                </div>

                {/* System Info */}
                <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                  <CardHeader>
                    <CardTitle className="text-gray-900 dark:text-white">System Information</CardTitle>
                    <CardDescription className="text-gray-600 dark:text-gray-400">Live system performance metrics via psutil</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium mb-2 text-gray-900 dark:text-white">Hostname</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">{live_system_performance.hostname}</p>
                      </div>
                      <div>
                        <h4 className="font-medium mb-2 text-gray-900 dark:text-white">Network</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Sent: {live_system_performance.network_sent_mb.toFixed(1)} MB
                          <br />
                          Received: {live_system_performance.network_recv_mb.toFixed(1)} MB
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-600 dark:text-gray-400">System performance data not available</p>
              </div>
            )}
          </TabsContent>

          {/* Notifications Tab */}
          <TabsContent value="notifications" className="space-y-6">
            {notification_analytics ? (
              <>
                {/* Notification Overview */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-gray-900 dark:text-white">Last 24 Hours</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">{notification_analytics.notifications_last_24h}</div>
                    </CardContent>
                  </Card>
                  <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-gray-900 dark:text-white">Last Week</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">{notification_analytics.notifications_last_week}</div>
                    </CardContent>
                  </Card>
                </div>

                {/* Notification Breakdowns */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                    <CardHeader>
                      <CardTitle className="text-gray-900 dark:text-white">By Status</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {Object.entries(notification_analytics.notification_status_breakdown).map(([status, count]) => (
                          <div key={status} className="flex justify-between items-center">
                            <span className="capitalize text-gray-700 dark:text-gray-300">{status}</span>
                            <Badge variant="outline" className="bg-white dark:bg-gray-700 text-gray-900 dark:text-white border-gray-300 dark:border-gray-600">{count}</Badge>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                    <CardHeader>
                      <CardTitle className="text-gray-900 dark:text-white">By Type</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {Object.entries(notification_analytics.notification_type_breakdown).map(([type, count]) => (
                          <div key={type} className="flex justify-between items-center">
                            <span className="capitalize text-gray-700 dark:text-gray-300">{type}</span>
                            <Badge variant="outline" className="bg-white dark:bg-gray-700 text-gray-900 dark:text-white border-gray-300 dark:border-gray-600">{count}</Badge>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-600 dark:text-gray-400">Notification analytics data not available</p>
              </div>
            )}
          </TabsContent>
        </Tabs>


      </div>
    </div>
  );
};

export default AnalyticsDashboard;
