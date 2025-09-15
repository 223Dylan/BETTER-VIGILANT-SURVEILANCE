import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { VideoCameraIcon, BellIcon, ChartBarIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import ActiveCameraGrid from '../components/ActiveCameraGrid';
import DetectionChart from '../components/DetectionChart';
import CameraPerformancePanel from '../components/CameraPerformancePanel';
import AlertsNotificationPanel from '../components/AlertsNotificationPanel';
import RecentSystemEventsPanel from '../components/RecentSystemEventsPanel';
import RealTimeNotificationDisplay from '../components/RealTimeNotificationDisplay';
import { cameraService } from '../services/camera.service';
import { metricsService } from '../services/metrics.service';
import { useThemeClasses } from '../contexts/ThemeContext';

// Material-UI Icons for additional UI elements
import { Videocam as VideocamIcon } from '@mui/icons-material';

const Dashboard: React.FC = () => {
  const [cameraStats, setCameraStats] = useState({
    total: 0,
    active: 0,
    error: 0,
    detections24h: 0
  });
  const [selectedCamera, setSelectedCamera] = useState<string | null>(null);
  const [healthStatus, setHealthStatus] = useState<any>(null);
  const themeClasses = useThemeClasses();

  useEffect(() => {
    loadCameraStats();
    loadHealthStatus();

    // Set up periodic refresh
    const interval = setInterval(() => {
      loadCameraStats();
      loadHealthStatus();
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, []);

  const loadCameraStats = async () => {
    try {
      const cameras = await cameraService.getCameras();
      const active = cameras.filter(c => c.enabled).length;
      const error = cameras.filter(c => c.health?.status === 'error').length;

      // Get detections count for last 24 hours
      let detections24h = 0;
      try {
        const summary = await metricsService.getMetricsSummary();
        detections24h = summary.total_detections_today || 0;
      } catch (metricsErr) {
        console.warn('Could not fetch detections count:', metricsErr);
      }

      setCameraStats({
        total: cameras.length,
        active,
        error,
        detections24h
      });

      // Set first active camera as selected if none selected
      if (!selectedCamera && active > 0) {
        const firstActive = cameras.find(c => c.enabled);
        if (firstActive) {
          setSelectedCamera(firstActive.id.toString());
        }
      }
    } catch (err) {
      console.error('Error loading camera stats:', err);
    }
  };

  const loadHealthStatus = async () => {
    try {
      const health = await metricsService.getHealthStatus();
      setHealthStatus(health);
    } catch (err) {
      console.error('Error loading health status:', err);
    }
  };

  const stats = [
    {
      name: 'Active Cameras',
      value: `${cameraStats.active}/${cameraStats.total}`,
      icon: VideoCameraIcon,
      color: cameraStats.active > 0 ? 'bg-green-500' : 'bg-gray-400'
    },
    {
      name: 'System Alerts',
      value: cameraStats.error.toString(),
      icon: cameraStats.error > 0 ? ExclamationTriangleIcon : BellIcon,
      color: cameraStats.error > 0 ? 'bg-red-500' : 'bg-blue-500'
    },
    {
      name: 'Detections (24h)',
      value: cameraStats.detections24h.toString(),
      icon: ChartBarIcon,
      color: 'bg-purple-500'
    },
  ];

  return (
    <div className="space-y-6">
      {/* Real-time Notifications */}
      <RealTimeNotificationDisplay
        maxNotifications={3}
        autoDismiss={true}
        dismissDelay={8000}
        position="top-right"
      />

      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className={`text-3xl font-bold ${themeClasses.text.primary}`}>
            Better Vigilant Surveillance
          </h1>
          <p className={`mt-1 text-sm ${themeClasses.text.secondary}`}>
            Real-time monitoring and system overview
          </p>
        </div>
        <div className="flex space-x-3">
          <Link
            to="/cameras"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors space-x-2"
          >
            <VideocamIcon className="w-4 h-4" />
            <span>Manage Cameras</span>
          </Link>
          <Link
            to="/alerts"
            className={`inline-flex items-center px-4 py-2 ${themeClasses.border.primary} border text-sm font-medium rounded-md ${themeClasses.text.primary} ${themeClasses.bg.primary} ${themeClasses.hover.bg} transition-colors space-x-2`}
          >
            <BellIcon className="w-4 h-4" />
            <span>View Alerts</span>
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {stats.map(stat => (
          <div
            key={stat.name}
            className={`relative overflow-hidden rounded-lg ${themeClasses.bg.primary} px-4 pt-5 pb-12 shadow-md ${themeClasses.border.primary} border hover:shadow-lg transition-shadow`}
          >
            <dt>
              <div className={`absolute rounded-md ${stat.color} p-3`}>
                <stat.icon className="h-6 w-6 text-white" aria-hidden="true" />
              </div>
              <p className={`ml-16 truncate text-sm font-medium ${themeClasses.text.secondary}`}>{stat.name}</p>
            </dt>
            <dd className="ml-16 flex items-baseline pb-6 sm:pb-7">
              <p className={`text-2xl font-semibold ${themeClasses.text.primary}`}>{stat.value}</p>
            </dd>
          </div>
        ))}
      </div>

      {/* System Status Banner */}
      {cameraStats.error > 0 && (
        <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4 border border-red-200 dark:border-red-800">
          <div className="flex">
            <div className="flex-shrink-0">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800 dark:text-red-400">
                System Alert
              </h3>
              <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                <p>
                  {cameraStats.error} camera{cameraStats.error > 1 ? 's' : ''} {cameraStats.error > 1 ? 'are' : 'is'} experiencing issues.
                  <Link to="/cameras" className="font-medium underline text-red-800 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 ml-1">
                    Check camera status →
                  </Link>
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Camera Grid & Analytics */}
        <div className="lg:col-span-2 space-y-6">
          {/* Active Cameras Section */}
          <div className={`${themeClasses.bg.primary} rounded-lg shadow ${themeClasses.border.primary} border`}>
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className={`text-lg font-medium ${themeClasses.text.primary}`}>Live Camera Feeds</h3>
                <span className={`text-sm ${themeClasses.text.secondary}`}>
                  {cameraStats.active} active
                </span>
              </div>

              {cameraStats.active > 0 ? (
                <ActiveCameraGrid limit={4} />
              ) : (
                <div className={`text-center py-8 ${themeClasses.text.secondary}`}>
                  <div className="flex justify-center mb-2">
                    <VideoCameraIcon className="w-12 h-12" />
                  </div>
                  <p className="text-lg font-medium mb-2">No Active Cameras</p>
                  <p className="mb-4">No cameras are currently running. Start some cameras to see live feeds here.</p>
                  <Link
                    to="/cameras"
                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors space-x-2"
                  >
                    <VideocamIcon className="w-4 h-4" />
                    <span>Manage Cameras</span>
                  </Link>
                </div>
              )}
            </div>
          </div>

          {/* Analytics Section - Detection Chart */}
          <DetectionChart />

          {/* Performance Panel */}
          {selectedCamera && (
            <div className={`${themeClasses.bg.primary} rounded-lg shadow ${themeClasses.border.primary} border p-6`}>
              <div className="flex items-center justify-between mb-4">
                <h3 className={`text-lg font-medium ${themeClasses.text.primary}`}>Camera Performance</h3>
                <select
                  value={selectedCamera}
                  onChange={(e) => setSelectedCamera(e.target.value)}
                  className={`px-3 py-1 ${themeClasses.bg.secondary} ${themeClasses.border.primary} border rounded-md text-sm ${themeClasses.text.primary} focus:outline-none focus:ring-2 focus:ring-blue-500`}
                >
                  <option value="camera-1">Camera 1</option>
                  <option value="camera-2">Camera 2</option>
                  <option value="testing-camera">Testing Camera</option>
                </select>
              </div>
              <CameraPerformancePanel
                cameraId={selectedCamera}
                timeRange="1h"
                realTime={true}
              />
            </div>
          )}

          {/* Recent System Events Panel */}
          <RecentSystemEventsPanel limit={8} refreshInterval={30000} />
        </div>

        {/* Right Column - Alerts & Quick Stats */}
        <div className="space-y-6">
          {/* Real-time Alerts */}
          <AlertsNotificationPanel
            limit={15}
            realTime={true}
            onAlertClick={(alert) => {
              console.log('Alert clicked:', alert);
              // Could navigate to alert detail or camera view
            }}
          />

          {/* Quick Actions */}
          <div className={`${themeClasses.bg.primary} rounded-lg shadow ${themeClasses.border.primary} border p-6`}>
            <h3 className={`text-lg font-medium ${themeClasses.text.primary} mb-4`}>Quick Actions</h3>
            <div className="space-y-3">
              <Link
                to="/cameras"
                className={`w-full flex items-center justify-center px-4 py-2 ${themeClasses.border.primary} border rounded-md text-sm font-medium ${themeClasses.text.primary} ${themeClasses.bg.primary} ${themeClasses.hover.bg}`}
              >
                <VideocamIcon className="w-4 h-4 mr-2" />
                Camera Management
              </Link>
              <Link
                to="/alerts"
                className={`w-full flex items-center justify-center px-4 py-2 ${themeClasses.border.primary} border rounded-md text-sm font-medium ${themeClasses.text.primary} ${themeClasses.bg.primary} ${themeClasses.hover.bg}`}
              >
                <BellIcon className="w-4 h-4 mr-2" />
                Alert History
              </Link>
              <button
                onClick={() => window.open('/api/metrics/health', '_blank')}
                className={`w-full flex items-center justify-center px-4 py-2 ${themeClasses.border.primary} border rounded-md text-sm font-medium ${themeClasses.text.primary} ${themeClasses.bg.primary} ${themeClasses.hover.bg}`}
              >
                <ChartBarIcon className="w-4 h-4 mr-2" />
                System Health
              </button>
            </div>
          </div>

          {/* System Status */}
          {healthStatus && (
            <div className={`${themeClasses.bg.primary} rounded-lg shadow ${themeClasses.border.primary} border p-6`}>
              <h3 className={`text-lg font-medium ${themeClasses.text.primary} mb-4`}>Infrastructure Status</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className={`text-sm ${themeClasses.text.secondary}`}>Elasticsearch</span>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    healthStatus.elasticsearch ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-400' : 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-400'
                  }`}>
                    {healthStatus.elasticsearch ? '● Online' : '● Offline'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className={`text-sm ${themeClasses.text.secondary}`}>Prometheus</span>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    healthStatus.prometheus ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-400' : 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-400'
                  }`}>
                    {healthStatus.prometheus ? '● Online' : '● Offline'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className={`text-sm ${themeClasses.text.secondary}`}>System Monitor</span>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-400">
                    ● Running
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
