import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { ChartBarIcon } from '@heroicons/react/24/outline';
import { metricsService } from '../services/metrics.service';

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
  info: '#06B6D4'
};

const DetectionsByHourDashboard: React.FC = () => {
  const [detectionMetrics, setDetectionMetrics] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTimeRange] = useState<TimeRange>(TIME_RANGES[0]); // Fixed to 24h

  useEffect(() => {
    loadDetectionData();

    // Set up hourly updates instead of WebSocket
    const interval = setInterval(loadDetectionData, 60 * 60 * 1000); // 1 hour

    return () => {
      clearInterval(interval);
    };
  }, [selectedTimeRange]);

  const loadDetectionData = async () => {
    try {
      setLoading(true);
      const metrics = await metricsService.getDetectionMetrics(selectedTimeRange.value);
      setDetectionMetrics(metrics);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load detection data');
    } finally {
      setLoading(false);
    }
  };



  const getDetectionsByHour = () => {
    if (!detectionMetrics.length) {
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

    detectionMetrics.forEach(detection => {
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



  const detectionsByHour = getDetectionsByHour();

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header */}
      <div className="flex items-center mb-6">
        <ChartBarIcon className="h-6 w-6 mr-2 text-blue-600" />
        <div>
          <h3 className="text-lg font-medium text-gray-900">Detections by Hour</h3>
          <p className="text-sm text-gray-500">Detection patterns throughout the day • Updates every hour</p>
        </div>
        {!detectionMetrics.length && (
          <span className="ml-3 text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">Sample Data</span>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Error: {error}
        </div>
      )}

      {/* Chart */}
      <div className="h-80">
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

      {/* Summary Stats */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-semibold text-gray-900">
              {detectionsByHour.reduce((sum, d) => sum + d.detections, 0)}
            </p>
            <p className="text-sm text-gray-500">Total Detections</p>
          </div>
          <div>
            <p className="text-2xl font-semibold text-gray-900">
              {Math.max(...detectionsByHour.map(d => d.detections))}
            </p>
            <p className="text-sm text-gray-500">Peak Hour</p>
          </div>
          <div>
            <p className="text-2xl font-semibold text-gray-900">
              {Math.round(detectionsByHour.reduce((sum, d) => sum + d.detections, 0) / 24)}
            </p>
            <p className="text-sm text-gray-500">Avg/Hour</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DetectionsByHourDashboard;
