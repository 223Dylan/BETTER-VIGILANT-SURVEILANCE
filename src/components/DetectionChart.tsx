import React, { useState, useEffect, useRef, useCallback } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Activity, BarChart3 } from 'lucide-react';
import { useThemeClasses, useTheme } from '../contexts/ThemeContext';

interface VerifiedDashboardData {
  alert_analytics: {
    chart_data: {
      hourly: Record<string, number>;
      daily: Record<string, number>;
    };
  } | null;
  last_updated: string;
}

const DetectionChart: React.FC = () => {
  const themeClasses = useThemeClasses();
  const { actualTheme } = useTheme();

  // State management
  const [dashboardData, setDashboardData] = useState<VerifiedDashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [isLoadingChart, setIsLoadingChart] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  const wsRef = useRef<WebSocket | null>(null);

  // Fallback data loading function
  const loadDashboardData = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/analytics/dashboard');
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      } else {
        throw new Error('Failed to fetch dashboard data');
      }
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // WebSocket connection for real-time updates
  const connectWebSocket = useCallback(() => {
    try {
      wsRef.current = new WebSocket('ws://localhost:8000/ws/analytics');

      wsRef.current.onopen = () => {
        console.log('WebSocket connected for detection chart');
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'analytics_update') {
            setDashboardData(data.data);
            setLastUpdate(new Date().toLocaleTimeString());
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected for detection chart');
        // Attempt to reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error for detection chart:', error);
      };
    } catch (err) {
      console.error('Failed to connect WebSocket for detection chart:', err);
      // Fallback to polling if WebSocket fails
      loadDashboardData();
    }
  }, [loadDashboardData]);

  // Chart data processing function (restricted to hourly)
  const fetchChartData = useCallback(async () => {
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

      // Use real chart data from the backend - RESTRICTED TO HOURLY ONLY
      let chartDataPoints: any[] = [];
      const chartData = alertData.chart_data;

      // Always use hourly data (24h view)
      const now = new Date();
      const hourlyData = chartData.hourly || {};

      // Generate 24 hourly data points using UTC time to match backend
      for (let i = 23; i >= 0; i--) {
        // Create UTC time for the hour key to match backend
        const utcTime = new Date(Date.UTC(
          now.getUTCFullYear(),
          now.getUTCMonth(),
          now.getUTCDate(),
          now.getUTCHours() - i,
          0, 0, 0
        ));

        // Generate the hour key in the same format as backend: "YYYY-MM-DD HH:00"
        const year = utcTime.getUTCFullYear();
        const month = String(utcTime.getUTCMonth() + 1).padStart(2, '0');
        const day = String(utcTime.getUTCDate()).padStart(2, '0');
        const hour = String(utcTime.getUTCHours()).padStart(2, '0');
        const hourKey = `${year}-${month}-${day} ${hour}:00`;

        const detections = hourlyData[hourKey] || 0;

        // Convert UTC time to local time for display
        const localTime = new Date(utcTime);

        chartDataPoints.push({
          time: localTime.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
          }),
          detections: detections,
          timestamp: utcTime.toISOString()
        });
      }

      setChartData(chartDataPoints);
    } catch (err) {
      console.error('Error fetching chart data:', err);
      setChartData([]);
    } finally {
      setIsLoadingChart(false);
    }
  }, [dashboardData]);

  // Initialize WebSocket and fallback data loading
  useEffect(() => {
    connectWebSocket();
    loadDashboardData();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connectWebSocket, loadDashboardData]);

  // Load chart data when dashboard data updates
  useEffect(() => {
    if (dashboardData?.alert_analytics) {
      fetchChartData();
    }
  }, [dashboardData, fetchChartData]);

  if (isLoading) {
    return (
      <div className={`${themeClasses.bg.primary} rounded-lg shadow ${themeClasses.border.primary} border p-6`}>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Activity className="h-8 w-8 animate-spin mx-auto mb-4 text-gray-600 dark:text-gray-400" />
            <p className="text-gray-600 dark:text-gray-400">Loading detection chart...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${themeClasses.bg.primary} rounded-lg shadow ${themeClasses.border.primary} border p-6`}>
      <CardHeader>
        <CardTitle className="text-gray-900 dark:text-white flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Detection Trends (Last 24 Hours)
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoadingChart ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <Activity className="h-8 w-8 animate-spin mx-auto mb-4 text-gray-600 dark:text-gray-400" />
              <p className="text-gray-600 dark:text-gray-400">Loading chart data...</p>
            </div>
          </div>
        ) : chartData && chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={350}>
            <AreaChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 20 }}>
              <defs>
                <linearGradient id="detectionsGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={actualTheme === 'light' ? '#e5e7eb' : '#374151'} opacity={0.3} />
              <XAxis
                dataKey="time"
                stroke={actualTheme === 'light' ? '#6b7280' : '#9ca3af'}
                fontSize={12}
                tick={{ fill: actualTheme === 'light' ? '#6b7280' : '#9ca3af' }}
                interval={2}
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
                formatter={(value, name) => [value, 'Detections']}
                labelFormatter={(label) => `Time: ${label}`}
              />
              <Area
                type="monotone"
                dataKey="detections"
                stroke="#3B82F6"
                strokeWidth={2}
                fill="url(#detectionsGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-400 dark:text-gray-500" />
              <p className="text-gray-600 dark:text-gray-400">No detection data available</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Check your camera connections</p>
            </div>
          </div>
        )}
      </CardContent>
    </div>
  );
};

export default DetectionChart;
