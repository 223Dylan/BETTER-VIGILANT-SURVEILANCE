import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { VideoCameraIcon, BellIcon, ChartBarIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import ActiveCameraGrid from '../components/ActiveCameraGrid';
import MetricsDashboard from '../components/MetricsDashboard';
import { cameraService } from '../services/camera.service';

// Material-UI Icons
import {
  Videocam as VideocamIcon,
  Security as SecurityIcon,
  DoNotDisturb as OfflineIcon
} from '@mui/icons-material';

const Dashboard: React.FC = () => {
  const [cameraStats, setCameraStats] = useState({
    total: 0,
    active: 0,
    error: 0,
    detectionRate: '0%'
  });

  useEffect(() => {
    loadCameraStats();
    
    // Update stats every 30 seconds
    const interval = setInterval(loadCameraStats, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const loadCameraStats = async () => {
    try {
      const cameras = await cameraService.getCameras();
      const active = cameras.filter(c => c.enabled).length;
      const error = cameras.filter(c => c.health?.status === 'error').length;
      
      setCameraStats({
        total: cameras.length,
        active,
        error,
        detectionRate: active > 0 ? '98%' : '0%' // Mock detection rate
      });
    } catch (err) {
      console.error('Error loading camera stats:', err);
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
      name: 'Detection Rate', 
      value: cameraStats.detectionRate, 
      icon: ChartBarIcon,
      color: 'bg-purple-500'
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Security Dashboard</h1>
          <p className="mt-2 text-gray-600">
            Real-time monitoring and system overview
          </p>
        </div>
        <div className="flex space-x-3">
          <Link
            to="/cameras"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 transition-colors space-x-2"
          >
            <VideocamIcon className="w-4 h-4" />
            <span>Manage Cameras</span>
          </Link>
          <Link
            to="/alerts"
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 transition-colors space-x-2"
          >
            <SecurityIcon className="w-4 h-4" />
            <span>View Alerts</span>
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {stats.map(stat => (
          <div
            key={stat.name}
            className="relative overflow-hidden rounded-lg bg-white px-4 pt-5 pb-12 shadow-md border border-gray-200 hover:shadow-lg transition-shadow"
          >
            <dt>
              <div className={`absolute rounded-md ${stat.color} p-3`}>
                <stat.icon className="h-6 w-6 text-white" aria-hidden="true" />
              </div>
              <p className="ml-16 truncate text-sm font-medium text-gray-500">{stat.name}</p>
            </dt>
            <dd className="ml-16 flex items-baseline pb-6 sm:pb-7">
              <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
            </dd>
          </div>
        ))}
      </div>

      {/* System Status Banner */}
      {cameraStats.error > 0 && (
        <div className="rounded-md bg-red-50 p-4 border border-red-200">
          <div className="flex">
            <div className="flex-shrink-0">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                System Alert
              </h3>
              <div className="mt-2 text-sm text-red-700">
                <p>
                  {cameraStats.error} camera{cameraStats.error > 1 ? 's' : ''} {cameraStats.error > 1 ? 'are' : 'is'} experiencing issues. 
                  <Link to="/cameras" className="font-medium underline text-red-800 hover:text-red-900 ml-1">
                    Check camera status →
                  </Link>
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Active Cameras */}
      <ActiveCameraGrid />

      {/* System Metrics */}
      <div className="bg-white rounded-lg shadow-md border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800">System Performance</h2>
        </div>
        <div className="p-6">
          <MetricsDashboard />
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white shadow-md rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
        </div>
        <div className="p-6">
          <div className="space-y-3">
            <div className="flex items-center space-x-3 text-sm">
              <span className="flex-shrink-0 w-2 h-2 bg-green-400 rounded-full"></span>
              <span className="text-gray-500">
                {new Date().toLocaleTimeString()} - System monitoring active
              </span>
            </div>
            {cameraStats.active > 0 && (
              <div className="flex items-center space-x-3 text-sm">
                <span className="flex-shrink-0 w-2 h-2 bg-blue-400 rounded-full"></span>
                <span className="text-gray-500">
                  {new Date().toLocaleTimeString()} - {cameraStats.active} camera{cameraStats.active > 1 ? 's' : ''} streaming
                </span>
              </div>
            )}
            {cameraStats.active === 0 && (
              <div className="text-center py-8 text-gray-500">
                <div className="flex justify-center mb-2">
                  <OfflineIcon className="w-12 h-12" />
                </div>
                <p>No recent activity - all cameras are offline</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
