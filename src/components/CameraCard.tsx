import React, { useEffect, useState, useRef } from 'react';
import { Camera } from '../types';
import VideoFeed from './VideoFeed';
import LoadingOverlay from './LoadingOverlay';
import { cameraService } from '../services/camera.service';

// Material-UI Icons
import {
  LocationOn as LocationIcon,
  Videocam as VideocamIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon
} from '@mui/icons-material';

// Heroicons
import {
  ArrowUpIcon,
  ArrowDownIcon,
  ArrowLeftIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';

interface CameraCardProps {
  camera: Camera;
  onToggleEnabled: () => void;
  onCameraUpdated?: () => void;
  onCardClick?: (camera: Camera) => void;
  streamType?: 'mjpeg' | 'mjpeg-ws' | 'hls' | 'webrtc';
  onStreamTypeChange?: (cameraId: string, streamType: 'mjpeg' | 'mjpeg-ws' | 'hls' | 'webrtc') => void;
}

const CameraCard: React.FC<CameraCardProps> = ({ 
  camera, 
  onToggleEnabled,
  onCameraUpdated,
  onCardClick,
  streamType = 'mjpeg',
  onStreamTypeChange
}) => {
  const [status, setStatus] = useState<string>(camera.enabled ? 'active' : 'stopped');
  const [isToggling, setIsToggling] = useState(false);
  const [currentStreamType, setCurrentStreamType] = useState<'mjpeg' | 'mjpeg-ws' | 'hls' | 'webrtc'>(streamType);
  const statusCheckInterval = useRef<NodeJS.Timeout>();

  const handleCardClick = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('button')) {
      return;
    }
    
    if (onCardClick) {
      onCardClick(camera);
    }
  };

  // Status checking function
  const checkCameraStatus = async () => {
    try {
      const currentStatus = await cameraService.getCameraStatus(camera.id);
      setStatus(currentStatus);
    } catch (error) {
      console.error('Error checking camera status:', error);
    }
  };

  // Enhanced toggle functionality with better loading feedback
  const handleToggle = async () => {
    if (isToggling) return;
    
    setIsToggling(true);
    try {
      if (camera.enabled) {
        setStatus('stopping');
        await cameraService.disableCamera(camera.id);
        setStatus('stopped');
      } else {
        setStatus('starting');
        await cameraService.enableCamera(camera.id);
        
        // Poll for camera to actually become active
        let retries = 0;
        const maxRetries = 10; // 10 seconds max wait time
        
        while (retries < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second
          const currentStatus = await cameraService.getCameraStatus(camera.id);
          
          if (currentStatus === 'active') {
            setStatus('active');
            break;
          } else if (currentStatus === 'error') {
            setStatus('error');
            break;
          }
          
          retries++;
        }
        
        // If we've exceeded retries and still not active, check one more time
        if (retries >= maxRetries) {
          const finalStatus = await cameraService.getCameraStatus(camera.id);
          setStatus(finalStatus || 'error');
        }
      }
      
      // Call parent's toggle handler
      onToggleEnabled();
      
      // Notify parent to refresh data
      if (onCameraUpdated) {
        onCameraUpdated();
      }
    } catch (error) {
      console.error('Error toggling camera:', error);
      setStatus('error');
    } finally {
      setIsToggling(false);
    }
  };

  useEffect(() => {
    // Remove: connectWebSocket();
    
    // Keep only status checking
            statusCheckInterval.current = setInterval(checkCameraStatus, 15000); // Reduced frequency: 15s instead of 5s

    return () => {
      if (statusCheckInterval.current) {
        clearInterval(statusCheckInterval.current);
      }
      // Remove WebSocket cleanup
    };
  }, [camera.id]);

  // Status badge styling
  const getStatusBadge = () => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'stopped':
        return 'bg-gray-100 text-gray-700 border-gray-200';
      case 'starting':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'stopping':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'restarting':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'error':
        return 'bg-red-100 text-red-700 border-red-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'active': return 'Online';
      case 'stopped': return 'Stopped';
      case 'starting': return 'Starting...';
      case 'stopping': return 'Stopping...';
      case 'restarting': return 'Restarting...';
      case 'error': return 'Error';
      default: return 'Unknown';
    }
  };

  const handleStreamTypeChange = (newStreamType: 'mjpeg' | 'mjpeg-ws' | 'hls' | 'webrtc') => {
    setCurrentStreamType(newStreamType);
    if (onStreamTypeChange) {
      onStreamTypeChange(camera.id, newStreamType);
    }
  };



  return (
    <div 
      className="bg-white rounded-lg shadow-md p-4 flex flex-col border border-gray-200 hover:shadow-lg transition-shadow cursor-pointer"
      onClick={handleCardClick}
    >
      <div className="flex items-center mb-3 w-full justify-between">
        <h2 className="text-lg font-semibold text-gray-900">{camera.name}</h2>
        <span
          className={`px-3 py-1 rounded-full text-xs font-semibold border ${getStatusBadge()}`}
        >
          {getStatusText()}
        </span>
      </div>
      
      {camera.zone_name && (
        <div className="text-sm text-gray-500 mb-1">
          <span className="inline-flex items-center space-x-1">
            <LocationIcon className="w-4 h-4" />
            <span>Zone: {camera.zone_name}</span>
          </span>
        </div>
      )}
      
      {camera.model && (
        <div className="text-sm text-gray-500 mb-2">
          <span className="inline-flex items-center space-x-1">
            <VideocamIcon className="w-4 h-4" />
            <span>Model: {camera.model}</span>
          </span>
        </div>
      )}
      
      <div className="mb-3 rounded-lg overflow-hidden bg-gray-100 relative">
        <VideoFeed 
          cameraId={camera.id} 
          camera={camera} 
          width="100%" 
          height="auto" 
          streamType={currentStreamType}
        />
        
        {/* Loading Overlay */}
        <LoadingOverlay
          isVisible={status === 'starting' || status === 'stopping' || status === 'restarting'}
          message={
            status === 'starting' ? 'Starting Camera...' : 
            status === 'stopping' ? 'Stopping Camera...' : 
            status === 'restarting' ? 'Applying Settings...' : ''
          }
          subMessage={
            status === 'starting' ? 'Initializing video stream' : 
            status === 'stopping' ? 'Closing video stream' :
            status === 'restarting' ? 'Restarting with new brightness' : ''
          }
          size={40}
        />
      </div>

      {/* Stream Type Selector */}
      <div className="mb-2">
        <div className="text-xs text-gray-500 mb-1">Stream Type:</div>
        <div className="flex gap-1 flex-wrap">
          {([
            { value: 'mjpeg', label: 'MJPEG' },
            { value: 'mjpeg-ws', label: 'MJPEG-WS' },
            { value: 'hls', label: 'HLS' },
            { value: 'webrtc', label: 'WebRTC' }
          ] as const).map((type) => (
            <button
              key={type.value}
              onClick={() => handleStreamTypeChange(type.value)}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                currentStreamType === type.value
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
              title={
                type.value === 'mjpeg' ? 'Motion JPEG over HTTP (recommended)' :
                type.value === 'mjpeg-ws' ? 'Motion JPEG over WebSocket (legacy)' :
                type.value === 'hls' ? 'HTTP Live Streaming (best quality)' :
                'WebRTC (coming soon)'
              }
            >
              {type.label}
            </button>
          ))}
        </div>
      </div>
      
      {camera.ptz && (
        <div className="flex flex-wrap gap-2 mb-3">
          <div className="text-xs text-gray-500 w-full mb-1">PTZ Controls:</div>
          <button onClick={() => alert('PTZ: Up')} className="px-2 py-1 bg-gray-200 rounded text-xs hover:bg-gray-300 flex items-center justify-center">
            <ArrowUpIcon className="w-3 h-3" />
          </button>
          <button onClick={() => alert('PTZ: Down')} className="px-2 py-1 bg-gray-200 rounded text-xs hover:bg-gray-300 flex items-center justify-center">
            <ArrowDownIcon className="w-3 h-3" />
          </button>
          <button onClick={() => alert('PTZ: Left')} className="px-2 py-1 bg-gray-200 rounded text-xs hover:bg-gray-300 flex items-center justify-center">
            <ArrowLeftIcon className="w-3 h-3" />
          </button>
          <button onClick={() => alert('PTZ: Right')} className="px-2 py-1 bg-gray-200 rounded text-xs hover:bg-gray-300 flex items-center justify-center">
            <ArrowRightIcon className="w-3 h-3" />
          </button>
          <button onClick={() => alert('PTZ: Zoom In')} className="px-2 py-1 bg-gray-200 rounded text-xs hover:bg-gray-300 flex items-center justify-center">
            <ZoomInIcon className="w-3 h-3" />
          </button>
          <button onClick={() => alert('PTZ: Zoom Out')} className="px-2 py-1 bg-gray-200 rounded text-xs hover:bg-gray-300 flex items-center justify-center">
            <ZoomOutIcon className="w-3 h-3" />
          </button>
        </div>
      )}
      
      <div className="flex gap-2 mt-auto">
        <button
          onClick={handleToggle}
          disabled={isToggling}
          className={`w-full px-4 py-2 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
            isToggling
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : status === 'active'
              ? 'bg-red-100 text-red-700 hover:bg-red-200 focus:ring-red-500'
              : 'bg-green-100 text-green-700 hover:bg-green-200 focus:ring-green-500'
          }`}
        >
          <div className="flex items-center justify-center space-x-1">
            {isToggling ? (
              <span>Processing...</span>
            ) : status === 'active' ? (
              <>
                <StopIcon className="w-4 h-4" />
                <span>Stop</span>
              </>
            ) : (
              <>
                <PlayIcon className="w-4 h-4" />
                <span>Start</span>
              </>
            )}
          </div>
        </button>
      </div>
      
      <div className="text-xs text-gray-400 text-center mt-2">
        Click card for detailed view
      </div>
    </div>
  );
};

export default CameraCard;
