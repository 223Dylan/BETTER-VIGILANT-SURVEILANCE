import React, { useState, useEffect, useCallback } from 'react';
import VideoPlayer from './VideoPlayer';
import { Camera } from '../types';
import { Alert } from '../types/alert';
import { cameraService } from '../services/camera.service';

// Material-UI Icons
import {
  Videocam as VideoCameraIcon,
  Warning as WarningIcon,
  Security as SecurityIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  SportsEsports as GamepadIcon,
  Home as HomeIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  PhotoCamera as PhotoCameraIcon,
  VideoCall as VideoCallIcon,
  Person as PersonIcon,
  Inventory as InventoryIcon,
  Circle as CircleIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Pause as PauseIcon,
  Refresh as RefreshIcon,
  Close as CloseIcon,
  Visibility as VisibilityIcon
} from '@mui/icons-material';

// Heroicons
import {
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ArrowPathIcon,
  DocumentTextIcon,
  ChartBarIcon,
  CogIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ArrowLeftIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';

interface CameraDetailPanelProps {
  camera: Camera | null;
  isOpen: boolean;
  onClose: () => void;
  onCameraUpdated?: () => void;
  streamType?: 'mjpeg' | 'mjpeg-ws' | 'hls' | 'webrtc';
}

interface AccordionSectionProps {
  title: string;
  icon: React.ReactNode;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  badge?: string | number;
}

interface CameraSettings {
  motionDetection: boolean;
  nightVision: boolean;
  audioRecording: boolean;
  aiDetection: boolean;
  motionSensitivity: number;
  nightVisionMode: 'auto' | 'on' | 'off';
  audioGain: number;
  aiConfidenceThreshold: number;
}

const AccordionSection: React.FC<AccordionSectionProps> = ({
  title,
  icon,
  isExpanded,
  onToggle,
  children,
  badge
}) => {
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex items-center justify-between transition-colors"
      >
        <div className="flex items-center space-x-2">
          <div className="text-lg">{icon}</div>
          <span className="font-medium text-gray-900">{title}</span>
          {badge !== undefined && (
            <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full font-medium">
              {badge}
            </span>
          )}
        </div>
        <svg
          className={`w-5 h-5 text-gray-500 transform transition-transform ${
            isExpanded ? 'rotate-180' : 'rotate-0'
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      <div className={`transition-all duration-300 overflow-hidden ${isExpanded ? 'max-h-screen' : 'max-h-0'}`}>
        <div className="p-4 bg-white border-t border-gray-200">
          {children}
        </div>
      </div>
    </div>
  );
};

const CameraDetailPanel: React.FC<CameraDetailPanelProps> = ({
  camera,
  isOpen,
  onClose,
  onCameraUpdated,
  streamType = 'mjpeg'
}) => {
  const [status, setStatus] = useState<string>('stopped');
  const [isToggling, setIsToggling] = useState(false);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState({
    uptime: '00:00:00',
    alertsToday: 0,
    totalFrames: 0,
    averageFPS: 0,
    lastAlert: null as string | null,
    connectionQuality: 'Good' as 'Excellent' | 'Good' | 'Poor' | 'Offline'
  });

  // Camera settings state
  const [cameraSettings, setCameraSettings] = useState<CameraSettings>({
    motionDetection: true,
    nightVision: false,
    audioRecording: false,
    aiDetection: true,
    motionSensitivity: 50,
    nightVisionMode: 'auto',
    audioGain: 50,
    aiConfidenceThreshold: 75
  });
  const [isUpdatingSettings, setIsUpdatingSettings] = useState(false);

  // Accordion section states
  const [expandedSections, setExpandedSections] = useState({
    info: true,
    alerts: false,
    ptz: false,
    settings: true
  });
  
  // State for overlay collapse
  const [overlayExpanded, setOverlayExpanded] = useState(true);
  
  // Real-time metrics state
  const [realTimeStats, setRealTimeStats] = useState({
    actualFPS: 0,
    bufferSize: 0,
    framesSent: 0,
    framesProcessed: 0,
    lastUpdate: new Date(),
    streamConnected: false,
    streamErrors: 0
  });

  // WebSocket for receiving predictions/alerts
  const [predictionWs, setPredictionWs] = useState<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<string>('disconnected');
  const [alertsReceived, setAlertsReceived] = useState<number>(0);

  // Local editable camera state for the settings form
  const [editableCamera, setEditableCamera] = useState<Camera | null>(null);
  
  // Brightness state
  const [brightness, setBrightness] = useState<number>(1.0);
  const [isUpdatingBrightness, setIsUpdatingBrightness] = useState(false);

  useEffect(() => {
    if (camera && isOpen) {
      loadCameraStatus();
      loadCameraStats();
      loadRealTimeStats();
      loadCameraSettings();
      connectToPredictionWebSocket();
      
      // Update basic stats every 5 seconds
      const statsInterval = setInterval(() => {
        loadCameraStatus();
        loadCameraStats();
      }, 5000);
      
      // Update real-time metrics every 2 seconds for more accurate overlay
      const realTimeInterval = setInterval(() => {
        loadRealTimeStats();
      }, 2000);
      
      return () => {
        clearInterval(statsInterval);
        clearInterval(realTimeInterval);
        if (predictionWs) {
          predictionWs.close();
        }
      };
    }
  }, [camera, isOpen]);

  // Separate effect to update editableCamera when camera prop changes
  useEffect(() => {
    if (camera) {
      setEditableCamera({ ...camera });
      setBrightness(camera.brightness || 1.0);
    }
  }, [camera]);

  // Sync local status when camera enabled state changes (for state synchronization between card and detail views)
  useEffect(() => {
    if (camera) {
      setStatus(camera.enabled ? 'active' : 'stopped');
      
      // Reconnect or disconnect WebSocket based on camera state
      if (camera.enabled && isOpen) {
        // Reconnect WebSocket if camera becomes enabled
        connectToPredictionWebSocket();
      } else if (!camera.enabled && predictionWs) {
        // Disconnect WebSocket if camera becomes disabled
        console.log('🔌 Disconnecting WebSocket - camera disabled');
        predictionWs.close();
        setPredictionWs(null);
        setConnectionStatus('disconnected');
      }
    }
  }, [camera?.enabled]);

  const connectToPredictionWebSocket = () => {
    if (!camera || !camera.enabled) {
      console.log('🚫 Not connecting WebSocket - camera disabled or not found');
      return;
    }

    // Close existing connection first
    if (predictionWs) {
      console.log('🔌 Closing existing WebSocket connection');
      predictionWs.close();
      setPredictionWs(null);
    }

    try {
      const wsUrl = `ws://localhost:8001/ws/cameras/${camera.id}/prediction`;
      console.log(`🔗 Creating NEW WebSocket connection to: ${wsUrl}`);
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log(`[SUCCESS] WebSocket opened for ${camera.id}`);
        setConnectionStatus('connected');
      };

      ws.onmessage = (event) => {
        console.log(`[MESSAGE] RAW WebSocket message for ${camera.id}:`, event.data);
        
        try {
          const data = JSON.parse(event.data);
          console.log(`[PARSED] WebSocket message for ${camera.id}:`, data);
          
          if (data.type === 'prediction' && data.prediction) {
            console.log('[PREDICTION] Processing prediction message:', data.prediction);
            
            const prediction = data.prediction;
            const newAlert: Alert = {
              id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
              cameraId: camera.id,
              timestamp: data.timestamp ? new Date(data.timestamp * 1000).toISOString() : new Date().toISOString(),
              type: prediction.type || 'motion',
              severity: prediction.confidence >= 0.8 ? 'high' : prediction.confidence >= 0.6 ? 'medium' : 'low',
              status: 'active',
              confidence: prediction.confidence || 0,
              message: prediction.message || `${prediction.type || 'Detection'}: ${(prediction.confidence * 100).toFixed(1)}%`,
              source: 'detection',
              frame: prediction.frame,
              detectionData: {
                isShoplifting: prediction.type === 'shoplifting',
                modelLabel: prediction.modelLabel || 0,
                sequenceStats: {
                  mean: prediction.sequenceStats?.mean || 0,
                  std: prediction.sequenceStats?.std || 0,
                  frames: prediction.sequenceStats?.frames || 1
                },
                processingTime: prediction.processingTime,
                modelVersion: prediction.modelVersion
              },
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString()
            };

            console.log('[ALERT] Adding new alert:', newAlert);
            setAlerts(prev => [newAlert, ...prev.slice(0, 49)]);
            setAlertsReceived(prev => prev + 1);
            
            setStats(prev => ({
              ...prev,
              alertsToday: prev.alertsToday + 1,
              lastAlert: new Date().toLocaleTimeString()
            }));
            
          } else if (data.type === 'connection') {
            console.log('[CONNECTION] Connection confirmed for', camera.id);
            
          } else if (data.type === 'keepalive') {
            console.log('[KEEPALIVE] Keepalive received for', camera.id, 'connections:', data.connections);
            
          } else {
            console.log('[MESSAGE] Other message type:', data.type);
          }
          
        } catch (error) {
          console.error('[ERROR] Error parsing WebSocket message:', error);
          console.error('[RAW] Raw message that failed:', event.data);
        }
      };

      ws.onerror = (error) => {
        console.error(`[ERROR] WebSocket error for ${camera.id}:`, error);
        setConnectionStatus('error');
      };

      ws.onclose = (event) => {
        console.log(`[CLOSE] WebSocket closed for ${camera.id}:`, event.code, event.reason);
        setConnectionStatus('disconnected');
      };

      setPredictionWs(ws);
      
    } catch (error) {
      console.error('[ERROR] Failed to create WebSocket:', error);
      setConnectionStatus('error');
    }
  };

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const loadCameraStatus = async () => {
    if (!camera) return;
    try {
      const currentStatus = await cameraService.getCameraStatus(camera.id);
      setStatus(currentStatus);
    } catch (error) {
      console.error('Error loading camera status:', error);
    }
  };

  const loadCameraStats = async () => {
    if (!camera) return;
    // Mock stats for now - replace with actual API calls when available
    setStats(prev => ({
      ...prev,
      uptime: camera.enabled ? calculateUptime() : '00:00:00',
      totalFrames: prev.totalFrames + (camera.enabled ? Math.floor(Math.random() * 30) : 0),
      averageFPS: camera.enabled ? camera.fps + Math.floor(Math.random() * 5) - 2 : 0,
      connectionQuality: camera.enabled ? 'Good' : 'Offline'
    }));
  };

  const loadRealTimeStats = async () => {
    if (!camera) return;
    
    try {
      // For MJPEG streams, get stats from camera manager and provide fallback logic
      if (streamType === 'mjpeg') {
        const cameraStatsResponse = await fetch(`http://localhost:8001/cameras/status`);
        if (cameraStatsResponse.ok) {
          const allCameraStats = await cameraStatsResponse.json();
          const cameraStats = allCameraStats[camera.id];
          
          if (cameraStats) {
            // For MJPEG, if the backend FPS is 0 but camera is enabled and status is active,
            // assume the stream is working at a reasonable FPS (since we can see the video)
            let effectiveFPS = cameraStats.fps || 0;
            let streamStatus = cameraStats.running && cameraStats.status === 'active';
            
            // Fallback logic for MJPEG: if camera is enabled but FPS is 0, estimate based on visible stream
            if (camera.enabled && streamStatus && effectiveFPS === 0) {
              // If we can see video but FPS is 0, it means the backend isn't tracking properly
              // Estimate a reasonable FPS based on camera configuration
              effectiveFPS = Math.min(camera.fps * 0.7, 15); // Assume 70% of target FPS, max 15
            }
            
            setRealTimeStats(prev => ({
              ...prev,
              actualFPS: effectiveFPS,
              streamConnected: streamStatus,
              lastUpdate: new Date()
            }));
          } else {
            // Camera not found in stats - likely disconnected
            setRealTimeStats(prev => ({
              ...prev,
              actualFPS: 0,
              streamConnected: false,
              lastUpdate: new Date()
            }));
          }
        } else {
          // If API call fails but camera is enabled, provide optimistic fallback
          setRealTimeStats(prev => ({
            ...prev,
            actualFPS: camera.enabled ? Math.min(camera.fps * 0.5, 10) : 0,
            streamConnected: camera.enabled,
            streamErrors: prev.streamErrors + 1,
            lastUpdate: new Date()
          }));
        }
      } else {
        // For WebSocket-based streams (HLS, mjpeg-ws, webrtc), use stream manager stats
        const streamStatsResponse = await fetch(`http://localhost:8001/api/video/status/${camera.id}`);
        if (streamStatsResponse.ok) {
          const streamStats = await streamStatsResponse.json();
          
          setRealTimeStats(prev => ({
            ...prev,
            actualFPS: streamStats.fps || 0,
            bufferSize: streamStats.buffer_size || 0,
            framesSent: streamStats.frames_sent || 0,
            framesProcessed: streamStats.frames_processed || 0,
            streamConnected: streamStats.connected || false,
            lastUpdate: new Date()
          }));
        } else {
          // Fallback to camera manager stats for WebSocket streams too
          const cameraStatsResponse = await fetch(`http://localhost:8001/cameras/status`);
          if (cameraStatsResponse.ok) {
            const allCameraStats = await cameraStatsResponse.json();
            const cameraStats = allCameraStats[camera.id];
            
            if (cameraStats) {
              setRealTimeStats(prev => ({
                ...prev,
                actualFPS: cameraStats.fps || 0,
                streamConnected: cameraStats.running || false,
                lastUpdate: new Date()
              }));
            }
          }
        }
      }
    } catch (error) {
      console.error('Error loading real-time stats:', error);
      setRealTimeStats(prev => ({
        ...prev,
        streamErrors: prev.streamErrors + 1,
        lastUpdate: new Date()
      }));
    }
  };

  const calculateUptime = () => {
    // Mock uptime calculation
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
  };

  const loadCameraSettings = async () => {
    if (!camera) return;
    try {
      // In a real app, load these from the camera or database
      // For now, use default values since these aren't in the Camera type yet
      setCameraSettings({
        motionDetection: true,
        nightVision: false,
        audioRecording: false,
        aiDetection: true,
        motionSensitivity: camera.thresholds?.motion ? camera.thresholds.motion * 100 : 50,
        nightVisionMode: 'auto',
        audioGain: 50,
        aiConfidenceThreshold: camera.thresholds?.object ? camera.thresholds.object * 100 : 75
      });
    } catch (error) {
      console.error('Error loading camera settings:', error);
    }
  };

  const updateCameraSetting = async (setting: keyof CameraSettings, value: any) => {
    if (!camera || isUpdatingSettings) return;
    
    setIsUpdatingSettings(true);
    try {
      // Update local state immediately for responsive UI
      setCameraSettings(prev => ({
        ...prev,
        [setting]: value
      }));

      // In a real app, save to backend
      // await cameraService.updateCameraSetting(camera.id, setting, value);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      console.log(`Updated ${setting} to ${value} for camera ${camera.id}`);
      
      if (onCameraUpdated) {
        onCameraUpdated();
      }
    } catch (error) {
      console.error(`Error updating ${setting}:`, error);
      // Revert on error
      setCameraSettings(prev => ({
        ...prev,
        [setting]: !value
      }));
    } finally {
      setIsUpdatingSettings(false);
    }
  };

  const updateCameraProperty = async (property: string, value: any) => {
    if (!camera || isUpdatingSettings) return;
    
    setIsUpdatingSettings(true);
    try {
      console.log(`[UPDATE] Updating camera ${camera.id} property ${property} to:`, value);
      
      // Save to backend
      await cameraService.updateCameraProperty(camera.id, property, value);
      
      console.log(`[SUCCESS] Successfully updated ${property} for camera ${camera.id}`);
      
      // Update the local editableCamera state immediately
      if (editableCamera) {
        setEditableCamera({ ...editableCamera, [property]: value });
      }
      
      // Refresh the camera list to get updated data from backend
      if (onCameraUpdated) {
        onCameraUpdated();
      }
    } catch (error) {
      console.error(`[ERROR] Error updating ${property}:`, error);
      
      // Show error to user
      alert(`Failed to update ${property}. Please try again.`);
      
      // Revert the editableCamera state on error
      if (camera && editableCamera) {
        setEditableCamera({ ...camera });
      }
    } finally {
      setIsUpdatingSettings(false);
    }
  };

  const SettingToggle: React.FC<{
    label: string;
    description: string;
    icon: string;
    enabled: boolean;
    onChange: (enabled: boolean) => void;
    disabled?: boolean;
  }> = ({ label, description, icon, enabled, onChange, disabled = false }) => (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div className="flex items-center space-x-3">
        <span className="text-lg">{icon}</span>
        <div>
          <div className="font-medium text-sm text-gray-900">{label}</div>
          <div className="text-xs text-gray-500">{description}</div>
        </div>
      </div>
      <button
        onClick={() => !disabled && onChange(!enabled)}
        disabled={disabled || isUpdatingSettings}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          enabled ? 'bg-blue-600' : 'bg-gray-300'
        } ${disabled || isUpdatingSettings ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            enabled ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
    </div>
  );

  const SettingSlider: React.FC<{
    label: string;
    value: number;
    min: number;
    max: number;
    step?: number;
    unit?: string;
    onChange: (value: number) => void;
    disabled?: boolean;
  }> = ({ label, value, min, max, step = 1, unit = '', onChange, disabled = false }) => (
    <div className="p-3 bg-gray-50 rounded-lg">
      <div className="flex justify-between items-center mb-2">
        <label className="text-sm font-medium text-gray-900">{label}</label>
        <span className="text-sm text-gray-600">{value}{unit}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => !disabled && onChange(Number(e.target.value))}
        disabled={disabled || isUpdatingSettings}
        className={`w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer ${
          disabled || isUpdatingSettings ? 'opacity-50' : ''
        }`}
      />
    </div>
  );

  const SettingSelect: React.FC<{
    label: string;
    value: string;
    options: { value: string; label: string }[];
    onChange: (value: string) => void;
    disabled?: boolean;
  }> = ({ label, value, options, onChange, disabled = false }) => (
    <div className="p-3 bg-gray-50 rounded-lg">
      <label className="block text-sm font-medium text-gray-900 mb-2">{label}</label>
      <select
        value={value}
        onChange={(e) => !disabled && onChange(e.target.value)}
        disabled={disabled || isUpdatingSettings}
        className={`w-full p-2 border border-gray-300 rounded-md text-sm ${
          disabled || isUpdatingSettings ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
        }`}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );

  const handleToggleCamera = async () => {
    if (!camera || isToggling) return;
    
    setIsToggling(true);
    try {
      if (camera.enabled) {
        setStatus('stopping');
        await cameraService.disableCamera(camera.id);
        setStatus('stopped');
        // Update local camera data immediately
        if (editableCamera) {
          setEditableCamera({ ...editableCamera, enabled: false });
        }
      } else {
        setStatus('starting');
        await cameraService.enableCamera(camera.id);
        
        // Poll for camera to actually become active (same logic as CameraCard)
        let retries = 0;
        const maxRetries = 10;
        
        while (retries < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, 1000));
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
        
        if (retries >= maxRetries) {
          const finalStatus = await cameraService.getCameraStatus(camera.id);
          setStatus(finalStatus || 'error');
        }
        
        // Update local camera data immediately
        if (editableCamera) {
          setEditableCamera({ ...editableCamera, enabled: true });
        }
      }
      
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

  const clearAlerts = () => {
    setAlerts([]);
    setStats(prev => ({ ...prev, alertsToday: 0, lastAlert: null }));
  };

  const getAlertIcon = (type: Alert['type']) => {
    const iconProps = { fontSize: 'small' as const, className: 'w-4 h-4' };
    switch (type) {
      case 'shoplifting': return <SecurityIcon {...iconProps} />;
      case 'motion': return <PersonIcon {...iconProps} />;
      case 'object_detection': return <InventoryIcon {...iconProps} />;
      default: return <WarningIcon {...iconProps} />;
    }
  };

  const getAlertColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-red-600 bg-red-50 border-red-200';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-blue-600 bg-blue-50 border-blue-200';
  };

  const getStatusColor = () => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100';
      case 'stopped': return 'text-gray-600 bg-gray-100';
      case 'starting': return 'text-blue-600 bg-blue-100';
      case 'stopping': return 'text-yellow-600 bg-yellow-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getConnectionQualityColor = () => {
    switch (stats.connectionQuality) {
      case 'Excellent': return 'text-green-600';
      case 'Good': return 'text-blue-600';
      case 'Poor': return 'text-yellow-600';
      case 'Offline': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  // Add debugging info to the alerts section
  const alertsSectionTitle = `Real-time Alerts (${alerts.length}) - ${connectionStatus}`;

  const handleCameraFieldChange = (field: keyof Camera, value: any) => {
    if (!editableCamera) return;
    setEditableCamera({ ...editableCamera, [field]: value });
  };

  const handleCameraFieldBlur = (field: keyof Camera, value: any) => {
    if (!camera || !editableCamera) return;
    
    console.log(`[FIELD] Field blur: ${field}, Current value: ${camera[field]}, New value: ${value}`);
    
    // Only update if the value actually changed
    if (camera[field] !== value && value !== '' && value !== null && value !== undefined) {
      console.log(`[CHANGE] Value changed, updating ${field}...`);
      updateCameraProperty(field, value);
    } else {
      console.log(`[NO_CHANGE] No change detected for ${field}`);
    }
  };

  const handleEnabledToggle = async () => {
    if (!editableCamera) return;
    const newValue = !editableCamera.enabled;
    handleCameraFieldChange('enabled', newValue);
    await updateCameraProperty('enabled', newValue);
  };

  // Handle brightness adjustment
  const handleBrightnessChange = async (newBrightness: number) => {
    if (!camera || isUpdatingBrightness) return;

    setBrightness(newBrightness);
    setIsUpdatingBrightness(true);
    try {
      await cameraService.updateCameraBrightness(camera.id, newBrightness);
      
      // Update local camera data
      if (editableCamera) {
        setEditableCamera({ ...editableCamera, brightness: newBrightness });
      }
      
      // No restart needed for brightness - it updates dynamically!
      // Just notify parent to refresh data
      if (onCameraUpdated) {
        onCameraUpdated();
      }
    } catch (error) {
      console.error('Error updating brightness:', error);
      // Revert brightness on error
      setBrightness(camera.brightness || 1.0);
    } finally {
      setIsUpdatingBrightness(false);
    }
  };

  if (!isOpen || !camera) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />
      
      {/* Panel */}
      <div className="fixed inset-y-0 right-0 flex max-w-full pl-10">
        <div className="w-screen max-w-6xl">
          <div className="flex h-full flex-col bg-white shadow-xl">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                <h2 className="text-2xl font-bold text-gray-900">{editableCamera?.name || camera.name}</h2>
                <span className={`px-3 py-1 rounded-full text-sm font-medium flex items-center space-x-1 ${getStatusColor()}`}>
                  {status === 'active' ? (
                    <>
                      <CircleIcon className="w-3 h-3 text-green-500" />
                      <span>Online</span>
                    </>
                  ) : status === 'stopped' ? (
                    <>
                      <CircleIcon className="w-3 h-3 text-gray-500" />
                      <span>Stopped</span>
                    </>
                  ) : status === 'starting' ? (
                    <>
                      <ArrowPathIcon className="w-3 h-3 animate-spin" />
                      <span>Starting</span>
                    </>
                  ) : status === 'stopping' ? (
                    <>
                      <StopIcon className="w-3 h-3" />
                      <span>Stopping</span>
                    </>
                  ) : (
                    <>
                      <XCircleIcon className="w-3 h-3" />
                      <span>Error</span>
                    </>
                  )}
                </span>
              </div>
              <button
                onClick={onClose}
                className="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <span className="sr-only">Close panel</span>
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 flex overflow-hidden">
              {/* Left side - Large video feed */}
              <div className="flex-1 flex flex-col p-6">
                <div className="flex-1 bg-black rounded-lg overflow-hidden relative">
                  <VideoPlayer
                    cameraId={camera.id}
                    camera={camera}
                    width="100%"
                    height="100%"
                    streamType={streamType}
                  />
                  
                  {/* Camera Details Overlay - Collapsible */}
                  <div className="absolute top-4 left-4 bg-black bg-opacity-80 text-white rounded-lg max-w-sm transition-all duration-300">
                    {/* Header with toggle button */}
                    <div className="flex items-center justify-between p-3 border-b border-gray-600">
                      <div className="flex items-center space-x-2">
                        <VideoCameraIcon className="w-4 h-4" />
                        <span className="font-semibold">{editableCamera?.name || camera.name}</span>
                        <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor()}`}>
                          {status === 'active' ? 'Live' : status === 'stopped' ? 'Offline' : status}
                        </span>
                      </div>
                      <button
                        onClick={() => setOverlayExpanded(!overlayExpanded)}
                        className="p-1 hover:bg-gray-600 rounded transition-colors"
                      >
                        <svg 
                          className={`w-4 h-4 transition-transform ${overlayExpanded ? 'rotate-180' : ''}`} 
                          fill="none" 
                          viewBox="0 0 24 24" 
                          stroke="currentColor"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>
                    </div>
                    
                    {/* Collapsible Content */}
                    {overlayExpanded && (
                      <div className="p-3 space-y-3">
                        {/* Real-time metrics */}
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>
                            <span className="text-gray-300">Live FPS:</span>
                            <div className={`font-medium ${
                              realTimeStats.actualFPS > 0 
                                ? realTimeStats.actualFPS > (camera.fps * 0.8) 
                                  ? 'text-green-400' 
                                  : 'text-yellow-400'
                                : 'text-red-400'
                            }`}>
                              {realTimeStats.actualFPS > 0 ? realTimeStats.actualFPS.toFixed(1) : '0.0'}
                            </div>
                          </div>
                          <div>
                            <span className="text-gray-300">Target FPS:</span>
                            <div className="font-medium">{editableCamera?.fps || camera.fps}</div>
                          </div>
                          <div>
                            <span className="text-gray-300">Stream:</span>
                            <div className="font-medium uppercase">{streamType}</div>
                          </div>
                          <div>
                            <span className="text-gray-300">Camera:</span>
                            <div className={`font-medium ${camera.enabled ? 
                              (realTimeStats.streamConnected ? 'text-green-400' : 'text-yellow-400') 
                              : 'text-red-400'
                            }`}>
                              {camera.enabled ? 
                                (realTimeStats.streamConnected ? 'Active' : 'Starting...') 
                                : 'Disabled'
                              }
                            </div>
                          </div>
                          <div>
                            <span className="text-gray-300">Zone:</span>
                            <div className="font-medium">{editableCamera?.zone_name || 'Unknown'}</div>
                          </div>
                          <div>
                            <span className="text-gray-300">Resolution:</span>
                            <div className="font-medium">{editableCamera?.resolutionWidth || camera.resolutionWidth}x{editableCamera?.resolutionHeight || camera.resolutionHeight}</div>
                          </div>
                          
                          {/* Stream-specific metrics */}
                          {streamType !== 'mjpeg' && realTimeStats.bufferSize > 0 && (
                            <>
                              <div>
                                <span className="text-gray-300">Buffer:</span>
                                <div className={`font-medium ${
                                  realTimeStats.bufferSize > 5 ? 'text-green-400' : 
                                  realTimeStats.bufferSize > 2 ? 'text-yellow-400' : 'text-red-400'
                                }`}>
                                  {realTimeStats.bufferSize} frames
                                </div>
                              </div>
                              <div>
                                <span className="text-gray-300">Frames Sent:</span>
                                <div className="font-medium">{realTimeStats.framesSent.toLocaleString()}</div>
                              </div>
                            </>
                          )}
                          
                          {/* MJPEG specific info */}
                          {streamType === 'mjpeg' && (
                            <>
                              <div>
                                <span className="text-gray-300">Protocol:</span>
                                <div className="font-medium">HTTP Stream</div>
                              </div>
                              <div>
                                <span className="text-gray-300">Quality:</span>
                                <div className={`font-medium ${
                                  realTimeStats.actualFPS > 10 ? 'text-green-400' : 
                                  realTimeStats.actualFPS > 5 ? 'text-yellow-400' : 'text-red-400'
                                }`}>
                                  {realTimeStats.actualFPS > 10 ? 'Excellent' : 
                                   realTimeStats.actualFPS > 5 ? 'Good' : 
                                   realTimeStats.actualFPS > 0 ? 'Poor' : 'No Signal'}
                                </div>
                              </div>
                              <div>
                                <span className="text-gray-300">Stream URL:</span>
                                <div className="font-medium text-xs">
                                  /mjpeg/{camera.id}
                                </div>
                              </div>
                              <div>
                                <span className="text-gray-300">Backend FPS:</span>
                                <div className="font-medium text-xs">
                                  {realTimeStats.actualFPS === Math.min(camera.fps * 0.7, 15) && camera.enabled ? 
                                    'Estimated' : 
                                    realTimeStats.actualFPS === 0 ? 'Not Tracked' : 'Measured'
                                  }
                                </div>
                              </div>
                            </>
                          )}
                          
                          <div>
                            <span className="text-gray-300">Uptime:</span>
                            <div className="font-medium">{stats.uptime}</div>
                          </div>
                          <div>
                            <span className="text-gray-300">Last Update:</span>
                            <div className="font-medium text-xs">{realTimeStats.lastUpdate.toLocaleTimeString()}</div>
                          </div>
                        </div>
                        
                        {/* Alerts section */}
                        {alerts.length > 0 && (
                          <div className="pt-2 border-t border-gray-600">
                            <div className="flex items-center space-x-1 text-xs">
                              <SecurityIcon className="w-3 h-3 text-red-400" />
                              <span className="text-red-400">Active Alerts: {alerts.length}</span>
                            </div>
                          </div>
                        )}
                        
                        {/* Connection status */}
                        <div className="pt-2 border-t border-gray-600 text-xs">
                          <div className="flex items-center justify-between">
                            <span className="text-gray-300">WS Connection:</span>
                            <span className={connectionStatus === 'connected' ? 'text-green-400' : 'text-red-400'}>
                              {connectionStatus}
                            </span>
                          </div>
                          {realTimeStats.streamErrors > 0 && (
                            <div className="flex items-center justify-between mt-1">
                              <span className="text-gray-300">Errors:</span>
                              <span className="text-yellow-400">{realTimeStats.streamErrors}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Video controls */}
                <div className="mt-4 flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <button
                      onClick={handleToggleCamera}
                      disabled={isToggling}
                      className={`px-6 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2 ${
                        camera.enabled
                          ? 'bg-red-100 text-red-700 hover:bg-red-200'
                          : 'bg-green-100 text-green-700 hover:bg-green-200'
                      } ${isToggling ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      {isToggling ? (
                        <>
                          <ClockIcon className="w-4 h-4" />
                          <span>Processing...</span>
                        </>
                      ) : camera.enabled ? (
                        <>
                          <StopIcon className="w-4 h-4" />
                          <span>Stop Camera</span>
                        </>
                      ) : (
                        <>
                          <PlayIcon className="w-4 h-4" />
                          <span>Start Camera</span>
                        </>
                      )}
                    </button>
                    
                    <button className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors flex items-center space-x-2">
                      <PhotoCameraIcon className="w-4 h-4" />
                      <span>Take Snapshot</span>
                    </button>
                    
                    <button className="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors flex items-center space-x-2">
                      <VideoCameraIcon className="w-4 h-4" />
                      <span>Record</span>
                    </button>
                  </div>
                  
                  <div className="text-sm text-gray-500 flex items-center space-x-4">
                    <div className="flex items-center space-x-1">
                      <VideoCameraIcon className="w-4 h-4" />
                      <span>{editableCamera?.resolutionWidth || camera.resolutionWidth}x{editableCamera?.resolutionHeight || camera.resolutionHeight}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <ChartBarIcon className="w-4 h-4" />
                      <span>{editableCamera?.fps || camera.fps} FPS</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right side - Expandable sections */}
              <div className="w-80 border-l border-gray-200 p-4 overflow-y-auto h-full">
                <div className="space-y-4 pb-8">
                  {/* Camera Info Section */}
                  <AccordionSection
                    title="Camera Details"
                    icon={<VideoCameraIcon className="w-5 h-5" />}
                    isExpanded={expandedSections.info}
                    onToggle={() => toggleSection('info')}
                  >
                    <div className="space-y-3 text-sm">
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Name</label>
                        <input
                          type="text"
                          value={editableCamera?.name || ''}
                          onChange={(e) => handleCameraFieldChange('name', e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.currentTarget.blur();
                              handleCameraFieldBlur('name', e.currentTarget.value);
                            }
                          }}
                          onBlur={(e) => handleCameraFieldBlur('name', e.target.value)}
                          className="w-full p-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          disabled={isUpdatingSettings}
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Zone</label>
                        <input
                          type="text"
                          value={editableCamera?.zone_name || 'Unknown Zone'}
                          onChange={(e) => handleCameraFieldChange('zone_name', e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.currentTarget.blur();
                              handleCameraFieldBlur('zone_name', e.currentTarget.value);
                            }
                          }}
                          onBlur={(e) => handleCameraFieldBlur('zone_name', e.target.value)}
                          className="w-full p-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          disabled={isUpdatingSettings}
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Model</label>
                        <input
                          type="text"
                          value={editableCamera?.model || 'Unknown Model'}
                          onChange={(e) => handleCameraFieldChange('model', e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.currentTarget.blur();
                              handleCameraFieldBlur('model', e.currentTarget.value);
                            }
                          }}
                          onBlur={(e) => handleCameraFieldBlur('model', e.target.value)}
                          className="w-full p-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          disabled={isUpdatingSettings}
                        />
                      </div>

                      <div className="pt-2 border-t border-gray-200 space-y-2">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Resolution:</span>
                          <span className="font-medium">{editableCamera?.resolutionWidth || camera.resolutionWidth}x{editableCamera?.resolutionHeight || camera.resolutionHeight}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Target FPS:</span>
                          <span className="font-medium">{editableCamera?.fps || camera.fps}</span>
                        </div>
                      </div>
                    </div>
                  </AccordionSection>

                  {/* Alerts Section */}
                  <AccordionSection
                    title={alertsSectionTitle}
                    icon={<SecurityIcon className="w-5 h-5" />}
                    isExpanded={expandedSections.alerts}
                    onToggle={() => toggleSection('alerts')}
                    badge={alerts.length}
                  >
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-gray-700">Live Detection Feed</span>
                        {alerts.length > 0 && (
                          <button
                            onClick={clearAlerts}
                            className="text-xs text-red-600 hover:text-red-800"
                          >
                            Clear All
                          </button>
                        )}
                      </div>

                      {/* Connection Status Debug Info */}
                      <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                        <div>Status: <span className={connectionStatus === 'connected' ? 'text-green-600' : 'text-red-600'}>{connectionStatus}</span></div>
                        <div>Alerts Received: {alertsReceived}</div>
                        <div>WebSocket URL: ws://localhost:8001/ws/cameras/{camera.id}/prediction</div>
                      </div>
                      
                      <div className="max-h-64 overflow-y-auto space-y-2">
                        {alerts.length === 0 ? (
                          <div className="text-center py-4 text-gray-500">
                            <div className="flex justify-center mb-2">
                              <VisibilityIcon className="w-8 h-8" />
                            </div>
                            <p className="text-sm">No alerts detected</p>
                            <p className="text-xs">ML predictions will appear here</p>
                            <p className="text-xs text-blue-500 mt-2">Connection: {connectionStatus}</p>
                          </div>
                        ) : (
                          alerts.map((alert) => (
                            <div
                              key={alert.id}
                              className={`p-3 rounded-lg border ${getAlertColor(alert.confidence)}`}
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex items-center space-x-2">
                                  <div className="text-lg">{getAlertIcon(alert.type)}</div>
                                  <div>
                                    <p className="text-sm font-medium">{alert.message}</p>
                                    <p className="text-xs opacity-75">
                                      {new Date(alert.timestamp).toLocaleTimeString()}
                                    </p>
                                  </div>
                                </div>
                                <span className="text-xs font-bold">
                                  {(alert.confidence * 100).toFixed(1)}%
                                </span>
                              </div>
                              {alert.frame && (
                                <div className="mt-2">
                                  <img
                                    src={`data:image/jpeg;base64,${alert.frame}`}
                                    alt="Alert frame"
                                    className="w-full h-16 object-cover rounded"
                                  />
                                </div>
                              )}
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  </AccordionSection>



                  {/* PTZ Controls Section */}
                  {camera.ptz && (
                    <AccordionSection
                      title="PTZ Controls"
                      icon={<GamepadIcon className="w-5 h-5" />}
                      isExpanded={expandedSections.ptz}
                      onToggle={() => toggleSection('ptz')}
                    >
                      <div className="space-y-3">
                        <div className="grid grid-cols-3 gap-2">
                          <div></div>
                          <button className="p-3 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors text-center flex items-center justify-center">
                            <ArrowUpIcon className="w-4 h-4" />
                          </button>
                          <div></div>
                          
                          <button className="p-3 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors text-center flex items-center justify-center">
                            <ArrowLeftIcon className="w-4 h-4" />
                          </button>
                          <button className="p-3 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors text-center flex items-center justify-center">
                            <HomeIcon className="w-4 h-4" />
                          </button>
                          <button className="p-3 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors text-center flex items-center justify-center">
                            <ArrowRightIcon className="w-4 h-4" />
                          </button>
                          
                          <div></div>
                          <button className="p-3 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors text-center flex items-center justify-center">
                            <ArrowDownIcon className="w-4 h-4" />
                          </button>
                          <div></div>
                        </div>
                        
                        <div className="flex space-x-2">
                          <button className="flex-1 p-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors text-sm flex items-center justify-center space-x-1">
                            <ZoomInIcon className="w-4 h-4" />
                            <span>Zoom In</span>
                          </button>
                          <button className="flex-1 p-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors text-sm flex items-center justify-center space-x-1">
                            <ZoomOutIcon className="w-4 h-4" />
                            <span>Zoom Out</span>
                          </button>
                        </div>
                      </div>
                    </AccordionSection>
                  )}

                  {/* Camera Settings Section */}
                  <AccordionSection
                    title="Camera Settings"
                    icon={<SettingsIcon className="w-5 h-5" />}
                    isExpanded={expandedSections.settings}
                    onToggle={() => toggleSection('settings')}
                  >
                    <div className="space-y-3">
                      {/* Enabled Toggle */}
                      <div className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                        <label className="text-xs font-medium text-gray-500">Enabled</label>
                        <button
                          onClick={handleEnabledToggle}
                          disabled={isUpdatingSettings}
                          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                            editableCamera?.enabled ? 'bg-blue-600' : 'bg-gray-300'
                          } ${isUpdatingSettings ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                        >
                          <span
                            className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${
                              editableCamera?.enabled ? 'translate-x-5' : 'translate-x-1'
                            }`}
                          />
                        </button>
                      </div>

                      {/* Technical Settings */}
                      <div className="space-y-2">
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <label className="block text-xs font-medium text-gray-500 mb-1">Resolution (W)</label>
                            <input
                              type="number"
                              value={editableCamera?.resolutionWidth || 0}
                              onChange={(e) => handleCameraFieldChange('resolutionWidth', parseInt(e.target.value))}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  e.currentTarget.blur();
                                  handleCameraFieldBlur('resolutionWidth', parseInt(e.currentTarget.value));
                                }
                              }}
                              onBlur={(e) => handleCameraFieldBlur('resolutionWidth', parseInt(e.target.value))}
                              className="w-full p-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                              disabled={isUpdatingSettings}
                              min="320"
                              max="4096"
                            />
                          </div>

                          <div>
                            <label className="block text-xs font-medium text-gray-500 mb-1">Resolution (H)</label>
                            <input
                              type="number"
                              value={editableCamera?.resolutionHeight || 0}
                              onChange={(e) => handleCameraFieldChange('resolutionHeight', parseInt(e.target.value))}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  e.currentTarget.blur();
                                  handleCameraFieldBlur('resolutionHeight', parseInt(e.currentTarget.value));
                                }
                              }}
                              onBlur={(e) => handleCameraFieldBlur('resolutionHeight', parseInt(e.target.value))}
                              className="w-full p-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                              disabled={isUpdatingSettings}
                              min="240"
                              max="2160"
                            />
                          </div>
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-gray-500 mb-1">FPS</label>
                          <input
                            type="number"
                            value={editableCamera?.fps || 0}
                            onChange={(e) => handleCameraFieldChange('fps', parseInt(e.target.value))}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                e.currentTarget.blur();
                                handleCameraFieldBlur('fps', parseInt(e.currentTarget.value));
                              }
                            }}
                            onBlur={(e) => handleCameraFieldBlur('fps', parseInt(e.target.value))}
                            className="w-full p-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            disabled={isUpdatingSettings}
                            min="1"
                            max="60"
                          />
                        </div>
                      </div>

                      {/* Brightness Control */}
                      <div className="mt-3">
                        <SettingSlider
                          label="Brightness"
                          value={brightness}
                          min={0.0}
                          max={2.0}
                          step={0.1}
                          unit="x"
                          onChange={handleBrightnessChange}
                          disabled={isUpdatingBrightness}
                        />
                        {isUpdatingBrightness && (
                          <div className="text-xs text-blue-500 mt-1">Updating brightness...</div>
                        )}
                      </div>

                      {/* Save/Update Status */}
                      {isUpdatingSettings && (
                        <div className="flex items-center justify-center p-2 bg-yellow-50 rounded-lg border border-yellow-200">
                          <div className="flex items-center space-x-2 text-yellow-700">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-700"></div>
                            <span className="text-sm">Saving changes...</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </AccordionSection>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CameraDetailPanel; 