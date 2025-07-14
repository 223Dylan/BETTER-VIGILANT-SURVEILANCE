export interface Camera {
  id: string;
  name: string;
  enabled: boolean;
  zone_name: string;
  model: string;
  streamUrl: string;
  ptz: boolean;
  lastActive: string;
  health: {
    status: 'healthy' | 'warning' | 'error';
    message: string;
  };
  resolutionWidth: number;
  resolutionHeight: number;
  fps: number;
  brightness: number; // Individual camera brightness (0.0 to 2.0)
  thresholds: {
    motion: number;
    object: number;
  };
}

// API Response Types
export interface CameraApiResponse {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  source: string;
  source_type: string;
  fps: number;
  resolution: {
    width: number;
    height: number;
  };
  brightness: number;
  detection_enabled: boolean;
  detection_sensitivity: number;
  recording_enabled: boolean;
  location: string;
  zone: string;
  advanced_settings: Record<string, any>;
  created_at: string | null;
  updated_at: string | null;
  last_online: string | null;
  status: string;
  error_message: string | null;
  uptime_hours: number;
}

export interface CameraStatusResponse {
  [cameraId: string]: string;
}

export interface CameraUpdateRequest {
  name?: string;
  zone?: string;
  description?: string;
  enabled?: boolean;
  resolution_width?: number;
  resolution_height?: number;
  fps?: number;
}

export interface CreateCameraRequest {
  id: string;
  name: string;
  description?: string;
  source: string; // Can be number (USB index) or string (RTSP URL)
  source_type: 'webcam' | 'rtsp' | 'file';
  fps?: number;
  resolution?: {
    width: number;
    height: number;
  };
  detection_enabled?: boolean;
  detection_sensitivity?: number;
  recording_enabled?: boolean;
  location?: string;
  zone?: string;
  advanced_settings?: Record<string, any>;
}

export interface CreateCameraResponse {
  status: 'success' | 'error';
  message: string;
  camera?: CameraApiResponse;
}

export interface CameraValidationError {
  field: string;
  message: string;
}

// Camera source type options for UI
export const CAMERA_SOURCE_TYPES = {
  webcam: { label: 'USB/Webcam', description: 'Local USB camera or built-in webcam' },
  rtsp: { label: 'IP Camera (RTSP)', description: 'Network camera with RTSP stream' },
  file: { label: 'Video File', description: 'Pre-recorded video file' }
} as const;

// Common resolution presets
export const RESOLUTION_PRESETS = [
  { label: '640x480 (VGA)', width: 640, height: 480 },
  { label: '1280x720 (HD)', width: 1280, height: 720 },
  { label: '1920x1080 (Full HD)', width: 1920, height: 1080 },
  { label: '2560x1440 (QHD)', width: 2560, height: 1440 },
  { label: 'Custom', width: 0, height: 0 }
] as const;
