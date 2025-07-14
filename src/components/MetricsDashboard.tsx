import React, { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface SystemMetrics {
  timestamp: string;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
}

const MetricsDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<SystemMetrics[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('http://localhost:9200/system_metrics/_search', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            size: 100,
            sort: [{ '@timestamp': 'desc' }],
            query: {
              range: {
                '@timestamp': {
                  gte: 'now-15m',
                  lte: 'now'
                }
              }
            }
          })
        });

        if (!response.ok) {
          throw new Error('Failed to fetch metrics');
        }

        const data = await response.json();
        const formattedMetrics = data.hits.hits.map((hit: any) => ({
          timestamp: new Date(hit._source['@timestamp']).toLocaleTimeString(),
          cpu_usage: hit._source.cpu_usage,
          memory_usage: hit._source.memory_usage,
          disk_usage: hit._source.disk_usage
        }));

        setMetrics(formattedMetrics.reverse());
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
        setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="text-center p-4">Loading metrics...</div>;
  }

  if (error) {
    return <div className="text-center p-4 text-red-500">Error: {error}</div>;
  }

  return (
    <div className="bg-white shadow rounded-lg p-4">
      <h3 className="text-lg font-medium text-gray-900 mb-4">System Metrics (Last 15 minutes)</h3>
      <div className="h-[400px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={metrics}
            margin={{
              top: 5,
              right: 30,
              left: 20,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="cpu_usage"
              name="CPU Usage (%)"
              stroke="#ff6384"
              activeDot={{ r: 8 }}
            />
            <Line
              type="monotone"
              dataKey="memory_usage"
              name="Memory Usage (%)"
              stroke="#35a2eb"
            />
            <Line
              type="monotone"
              dataKey="disk_usage"
              name="Disk Usage (%)"
              stroke="#4bc0c0"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default MetricsDashboard; 