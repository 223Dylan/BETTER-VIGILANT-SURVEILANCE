import React, { useState, useEffect } from 'react';
import CameraCard from './CameraCard';
import { Camera } from '../types';
import CameraDetailPanel from './CameraDetailPanel';
import AddCameraModal from './AddCameraModal';
// import QuickSettingsPanel from './QuickSettingsPanel';
import { cameraService } from '../services/camera.service';

// Material-UI Icons
import {
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  Videocam as VideocamIcon,
  Add as AddIcon
} from '@mui/icons-material';

const CameraGrid: React.FC = () => {
  const [cameraList, setCameraList] = useState<Camera[]>([]);
  const [detailCamera, setDetailCamera] = useState<Camera | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [addCameraModalOpen, setAddCameraModalOpen] = useState(false);

  // Track stream types for each camera
  const [cameraStreamTypes, setCameraStreamTypes] = useState<{ [cameraId: string]: 'mjpeg' | 'mjpeg-ws' | 'hls' | 'webrtc' }>({});

  useEffect(() => {
    loadCameras();
  }, []);

  const loadCameras = async () => {
    try {
      setLoading(true);
      const cameras = await cameraService.getCameras();
      setCameraList(cameras);

      // Update the detail camera if it's currently open
      if (detailCamera) {
        const updatedDetailCamera = cameras.find(c => c.id === detailCamera.id);
        if (updatedDetailCamera) {
          setDetailCamera(updatedDetailCamera);
        }
      }

      setError(null);
    } catch (err) {
      console.error('Error loading cameras:', err);
      setError('Failed to load cameras. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const refreshCameras = async () => {
    try {
      setRefreshing(true);
      const cameras = await cameraService.getCameras();
      setCameraList(cameras);

      // Update the detail camera if it's currently open
      if (detailCamera) {
        const updatedDetailCamera = cameras.find(c => c.id === detailCamera.id);
        if (updatedDetailCamera) {
          setDetailCamera(updatedDetailCamera);
        }
      }

      setError(null);
    } catch (err) {
      console.error('Error refreshing cameras:', err);
      setError('Failed to refresh cameras');
    } finally {
      setRefreshing(false);
    }
  };

  const handleToggleEnabled = async (camera: Camera) => {
    // Camera card handles the actual API calls
    // This is just for legacy compatibility
  };

  const handleStreamTypeChange = (cameraId: string, streamType: 'mjpeg' | 'mjpeg-ws' | 'hls' | 'webrtc') => {
    setCameraStreamTypes(prev => ({
      ...prev,
      [cameraId]: streamType
    }));
  };

  const handleCardClick = (camera: Camera) => {
    setDetailCamera(camera);
  };

  const handleCloseDetailPanel = () => {
    setDetailCamera(null);
  };

  const handleOpenAddCameraModal = () => {
    setAddCameraModalOpen(true);
  };

  const handleCloseAddCameraModal = () => {
    setAddCameraModalOpen(false);
  };

  const handleCameraAdded = () => {
    refreshCameras(); // Refresh the camera list when a new camera is added
  };

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
        <p className="text-gray-600">Loading cameras...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center p-8">
        <div className="text-red-500 mb-4 text-lg flex items-center justify-center space-x-2">
          <WarningIcon className="w-6 h-6" />
          <span>{error}</span>
        </div>
        <div className="flex justify-center gap-4">
          <button
            onClick={loadCameras}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center space-x-2"
          >
            <RefreshIcon className="w-4 h-4" />
            <span>Retry</span>
          </button>
        </div>
      </div>
    );
  }

  if (cameraList.length === 0) {
    return (
      <>
        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
            <VideocamIcon className="w-6 h-6" />
            <span>Camera System (0 cameras)</span>
          </h1>
          <button
            onClick={handleOpenAddCameraModal}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium flex items-center space-x-2"
          >
            <AddIcon className="w-4 h-4" />
            <span>Add Camera</span>
          </button>
        </div>

        <div className="text-center p-8">
          <div className="text-gray-500 mb-4 text-lg flex items-center justify-center space-x-2">
            <VideocamIcon className="w-6 h-6" />
            <span>No cameras configured</span>
          </div>
          <p className="text-gray-400 mb-4">Add your first camera to get started</p>
          <button
            onClick={handleOpenAddCameraModal}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center space-x-2 mx-auto"
          >
            <AddIcon className="w-5 h-5" />
            <span>Add Your First Camera</span>
          </button>
        </div>

        <AddCameraModal
          open={addCameraModalOpen}
          onClose={handleCloseAddCameraModal}
          onCameraAdded={handleCameraAdded}
        />
      </>
    );
  }



  return (
    <>
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
          <VideocamIcon className="w-6 h-6" />
          <span>Camera System ({cameraList.length} cameras)</span>
        </h1>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleOpenAddCameraModal}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium flex items-center space-x-2"
          >
            <AddIcon className="w-4 h-4" />
            <span>Add Camera</span>
          </button>
          <button
            onClick={refreshCameras}
            disabled={refreshing}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              refreshing
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
            }`}
          >
            <div className="flex items-center space-x-1">
              <RefreshIcon className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              <span>{refreshing ? 'Refreshing...' : 'Refresh Status'}</span>
            </div>
          </button>
        </div>
      </div>

      {/* Quick Settings Panel */}
      {/* <QuickSettingsPanel
        cameras={cameraList}
        onCameraUpdated={refreshCameras}
      /> */}

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {cameraList.map(camera => (
          <CameraCard
            key={camera.id}
            camera={camera}
            onToggleEnabled={() => handleToggleEnabled(camera)}
            onCameraUpdated={refreshCameras}
            onCardClick={handleCardClick}
            onStreamTypeChange={handleStreamTypeChange}
            streamType={cameraStreamTypes[camera.id] || 'mjpeg'}
          />
        ))}
      </div>

      {/* Detail Panel */}
      <CameraDetailPanel
        camera={detailCamera}
        isOpen={!!detailCamera}
        onClose={handleCloseDetailPanel}
        onCameraUpdated={refreshCameras}
        streamType={detailCamera?.id ? cameraStreamTypes[detailCamera.id] || 'mjpeg' : 'mjpeg'}
      />

      {/* Add Camera Modal */}
      <AddCameraModal
        open={addCameraModalOpen}
        onClose={handleCloseAddCameraModal}
        onCameraAdded={handleCameraAdded}
      />
    </>
  );
};

export default CameraGrid;
