import React, { useState, useEffect } from 'react';
import { Alert, AlertStats as AlertStatsType } from '../types';
import { 
  AlertStats, 
  AlertFilters, 
  AlertList, 
  AlertDetailModal 
} from '../components/alerts';

interface AlertsPageProps {}

const AlertsPage: React.FC<AlertsPageProps> = () => {
  const [activeAlerts, setActiveAlerts] = useState<Alert[]>([]);
  const [allAlerts, setAllAlerts] = useState<Alert[]>([]);
  const [alertStats, setAlertStats] = useState<AlertStatsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<'active' | 'all' | 'stats'>('active');
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  
  // Filters
  const [severityFilter, setSeverityFilter] = useState<string[]>([]);
  const [cameraFilter, setCameraFilter] = useState<string>('');

  useEffect(() => {
    fetchData();
    
    // Set up real-time updates via WebSocket
    const ws = new WebSocket(`ws://localhost:8000/ws/predictions/all`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'alert_created' || data.type === 'alert_updated') {
        fetchData(); // Refresh data when alerts are updated
      }
    };
    
    return () => {
      ws.close();
    };
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Build filter query
      const filterParams = new URLSearchParams();
      if (severityFilter.length > 0) {
        filterParams.set('severity', severityFilter.join(','));
      }
      if (cameraFilter) {
        filterParams.set('camera_id', cameraFilter);
      }

      // Fetch active alerts
      const activeResponse = await fetch(`/api/alerts/active?${filterParams}`);
      if (!activeResponse.ok) throw new Error('Failed to fetch active alerts');
      const activeData = await activeResponse.json();
      setActiveAlerts(activeData.data.alerts);

      // Fetch all alerts (for "all" view)
      const allResponse = await fetch(`/api/alerts/history?limit=200&${filterParams}`);
      if (!allResponse.ok) throw new Error('Failed to fetch alert history');
      const allData = await allResponse.json();
      setAllAlerts([...activeData.data.alerts, ...allData.data.alerts]);

      // Fetch statistics
      const statsResponse = await fetch('/api/alerts/stats');
      if (!statsResponse.ok) throw new Error('Failed to fetch alert stats');
      const statsData = await statsResponse.json();
      setAlertStats(statsData.data);

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const acknowledgeAlert = async (alertId: string, notes?: string) => {
    try {
      const response = await fetch(`/api/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          userId: 'current-user', // Replace with actual user ID
          notes 
        })
      });
      
      if (!response.ok) throw new Error('Failed to acknowledge alert');
      
      fetchData(); // Refresh data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to acknowledge alert');
    }
  };

  const resolveAlert = async (alertId: string, notes?: string) => {
    try {
      const response = await fetch(`/api/alerts/${alertId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          userId: 'current-user', // Replace with actual user ID
          notes 
        })
      });
      
      if (!response.ok) throw new Error('Failed to resolve alert');
      
      fetchData(); // Refresh data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resolve alert');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const currentAlerts = view === 'active' ? activeAlerts : allAlerts;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Security Alerts</h1>
        <p className="text-gray-600">Monitor and manage security alerts from your camera system</p>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Error: {error}
        </div>
      )}

      {/* Filters */}
      <AlertFilters
        view={view}
        onViewChange={setView}
        severityFilter={severityFilter}
        onSeverityFilterChange={setSeverityFilter}
        cameraFilter={cameraFilter}
        onCameraFilterChange={setCameraFilter}
        onRefresh={fetchData}
        activeCount={activeAlerts.length}
      />

      {/* Statistics View */}
      {view === 'stats' && alertStats && (
        <AlertStats stats={alertStats} />
      )}

      {/* Alerts List */}
      {view !== 'stats' && (
        <AlertList
          alerts={currentAlerts}
          loading={loading}
          title={view === 'active' ? 'Active Alerts' : 'All Alerts'}
          emptyMessage={view === 'active' ? 'No active alerts' : 'No alerts found'}
          onAcknowledge={acknowledgeAlert}
          onResolve={resolveAlert}
          onViewDetails={setSelectedAlert}
        />
      )}

      {/* Alert Detail Modal */}
      <AlertDetailModal
        alert={selectedAlert}
        isOpen={!!selectedAlert}
        onClose={() => setSelectedAlert(null)}
        onAcknowledge={acknowledgeAlert}
        onResolve={resolveAlert}
      />
    </div>
  );
};

export default AlertsPage; 