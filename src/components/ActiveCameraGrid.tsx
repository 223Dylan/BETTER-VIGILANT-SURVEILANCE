import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Camera } from '../types';
import { cameraService } from '../services/camera.service';
import VideoPlayer from './VideoPlayer';

// Material-UI Icons
import {
  Circle as CircleIcon,
  LocationOn as LocationIcon,
  Videocam as VideocamIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';

// Heroicons
import {
  ChartBarIcon
} from '@heroicons/react/24/outline';

interface ActiveCameraCardProps {
  camera: Camera;
}

const ActiveCameraCard: React.FC<ActiveCameraCardProps> = ({ camera }) => {
  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition-shadow overflow-hidden">
      <div className="p-4 pb-2">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900 truncate">{camera.name}</h3>
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 flex-shrink-0 space-x-1">
            <CircleIcon className="w-3 h-3 text-green-500" />
            <span>Live</span>
          </span>
        </div>

        {camera.zone_name && (
          <div className="text-sm text-gray-500 mb-2 truncate flex items-center space-x-1">
            <LocationIcon className="w-4 h-4" />
            <span>{camera.zone_name}</span>
          </div>
        )}
      </div>

      {/* Video Feed */}
      <div className="px-4 pb-2">
        <VideoPlayer
          cameraId={camera.id}
          camera={camera}
          width="100%"
          height="200px"
          streamType="mjpeg"
        />
      </div>

      <div className="px-4 pb-4">
        <div className="flex items-center justify-between text-sm text-gray-500 mb-2">
          <span className="flex items-center space-x-1">
            <VideocamIcon className="w-4 h-4" />
            <span>{camera.resolutionWidth}x{camera.resolutionHeight}</span>
          </span>
          <span className="flex items-center space-x-1">
            <ChartBarIcon className="w-4 h-4" />
            <span>{camera.fps} FPS</span>
          </span>
        </div>

        {camera.health && camera.health.status !== 'healthy' && (
          <div className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded flex items-center space-x-1">
            <WarningIcon className="w-3 h-3" />
            <span>{camera.health.message}</span>
          </div>
        )}
      </div>
    </div>
  );
};

interface ActiveCameraGridProps {
  limit?: number;
}

const ActiveCameraGrid: React.FC<ActiveCameraGridProps> = ({ limit }) => {
  const [activeCameras, setActiveCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadActiveCameras();

    // Refresh active cameras every 10 seconds
          const interval = setInterval(loadActiveCameras, 20000); // Reduced frequency: 20s instead of 10s

    return () => clearInterval(interval);
  }, []);

  const loadActiveCameras = async () => {
    try {
      const allCameras = await cameraService.getCameras();
      // Only show cameras that are actually running (enabled)
      const activeOnly = allCameras.filter(camera => camera.enabled);
      setActiveCameras(activeOnly);
      setError(null);
    } catch (err) {
      console.error('Error loading active cameras:', err);
      setError('Failed to load active cameras');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Loading active cameras...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 bg-red-50 rounded-lg border border-red-200">
        <div className="text-red-500 mb-2 flex items-center justify-center space-x-2">
          <WarningIcon className="w-5 h-5" />
          <span>{error}</span>
        </div>
        <button
          onClick={loadActiveCameras}
          className="text-blue-500 hover:text-blue-700 font-medium flex items-center justify-center space-x-1"
        >
          <RefreshIcon className="w-4 h-4" />
          <span>Try again</span>
        </button>
      </div>
    );
  }

  if (activeCameras.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="flex justify-center mb-4">
          <VideocamIcon className="w-16 h-16 text-gray-400" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Cameras</h3>
        <p className="text-gray-500 mb-4">
          No cameras are currently running. Start some cameras to see live feeds here.
        </p>
        <Link
          to="/cameras"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 transition-colors space-x-2"
        >
          <VideocamIcon className="w-4 h-4" />
          <span>Manage Cameras</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800 flex items-center space-x-2">
          <VideocamIcon className="w-6 h-6" />
          <span>Active Cameras ({activeCameras.length})</span>
        </h2>
        <Link
          to="/cameras"
          className="inline-flex items-center px-3 py-1 text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors border border-blue-200 rounded-md hover:bg-blue-50 space-x-1"
        >
          <SettingsIcon className="w-4 h-4" />
          <span>Manage All Cameras →</span>
        </Link>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {activeCameras
          .slice(0, limit)
          .map(camera => (
            <ActiveCameraCard key={camera.id} camera={camera} />
          ))}
      </div>

      {/* Real-time status indicator */}
      <div className="text-center text-sm text-gray-500">
        <span className="inline-flex items-center">
          <span className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></span>
          Live monitoring • Updated every 10 seconds
        </span>
      </div>
    </div>
  );
};

export default ActiveCameraGrid;
