import React, { useState, useEffect } from 'react';
import { Alert, AlertStats as AlertStatsType } from '../types';
import { 
  AlertStats, 
  AlertFilters, 
  AlertList, 
  AlertDetailModal 
} from '../components/alerts';
import { apiService } from '../services/api.service';
import { authService } from '../services/auth.service';
import { alertService } from '../services/alert.service';

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
      const activeData = await apiService.get<any>(`/api/alerts/active?${filterParams}`);
      setActiveAlerts(activeData.data.alerts);

      // Fetch all alerts (for "all" view)
      const allData = await apiService.get<any>(`/api/alerts/history?limit=200&${filterParams}`);
      setAllAlerts([...activeData.data.alerts, ...allData.data.alerts]);

      // Fetch statistics
      const statsData = await apiService.get<any>('/api/alerts/stats');
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
      const currentUser = authService.getCurrentUser();
      if (!currentUser) {
        setError('Please log in to acknowledge alerts');
        return;
      }

      await apiService.post(`/api/alerts/${alertId}/acknowledge`, { 
        userId: currentUser.id,
        notes 
      });
      
      fetchData(); // Refresh data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to acknowledge alert');
    }
  };

  const resolveAlert = async (alertId: string, notes?: string) => {
    try {
      const currentUser = authService.getCurrentUser();
      if (!currentUser) {
        setError('Please log in to resolve alerts');
        return;
      }

      await apiService.post(`/api/alerts/${alertId}/resolve`, { 
        userId: currentUser.id,
        notes 
      });
      
      fetchData(); // Refresh data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resolve alert');
    }
  };

  const handleBulkAcknowledge = async (alertIds: string[], notes?: string) => {
    try {
      const result = await alertService.bulkAcknowledge(alertIds, notes);
      
      if (result.successful > 0) {
        // Show success message
        setError(null);
        console.log(`Successfully acknowledged ${result.successful} alerts`);
      }
      
      if (result.failed > 0) {
        console.warn(`Failed to acknowledge ${result.failed} alerts`);
        // You might want to show a more detailed error message here
      }
      
      fetchData(); // Refresh data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to bulk acknowledge alerts');
    }
  };

  const handleBulkResolve = async (alertIds: string[], notes?: string) => {
    try {
      const result = await alertService.bulkResolve(alertIds, notes);
      
      if (result.successful > 0) {
        // Show success message
        setError(null);
        console.log(`Successfully resolved ${result.successful} alerts`);
      }
      
      if (result.failed > 0) {
        console.warn(`Failed to resolve ${result.failed} alerts`);
        // You might want to show a more detailed error message here
      }
      
      fetchData(); // Refresh data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to bulk resolve alerts');
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
          onBulkAcknowledge={handleBulkAcknowledge}
          onBulkResolve={handleBulkResolve}
          showBulkActions={view === 'active'}
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