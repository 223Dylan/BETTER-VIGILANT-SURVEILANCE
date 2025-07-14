import { Camera, CameraApiResponse, CameraStatusResponse, CreateCameraRequest, CreateCameraResponse } from '../types/camera'
import { apiService } from './api.service'

const API_BASE_URL = 'http://localhost:8001/api'

// Default camera configurations from config.json
const DEFAULT_CAMERAS = [
  {
    id: 'local-webcam',
    name: 'Laptop Webcam',
    location_id: 'desktop',
    source: 0,
    camera_type: 'usb',
    resolution: { width: 1280, height: 720 },
    fps: 30,
    status: 'active'
  },
  {
    id: 'entrance-cam',
    name: 'Entrance Camera',
    location_id: 'entrance',
    source: 'rtsp://user:pass@ip/stream',
    camera_type: 'ip',
    resolution: { width: 1920, height: 1080 },
    fps: 25,
    status: 'inactive'
  },
  {
    id: 'aisle-cam',
    name: 'Aisle Camera',
    location_id: 'aisle-3',
    source: 'rtsp://user:pass@ip2/stream',
    camera_type: 'ip',
    resolution: { width: 1280, height: 720 },
    fps: 20,
    status: 'active'
  }
];

class CameraService {
  async getCameras(): Promise<Camera[]> {
    try {
      // Get available cameras from config
      const availableCameras = await apiService.get<CameraApiResponse[]>('/cameras/available')
      
      // Get current camera status
      const cameraStatus = await apiService.get<CameraStatusResponse>('/cameras/status')
      
      const cameras = availableCameras.map((camera: CameraApiResponse) => {
        const status = cameraStatus[camera.id] || 'stopped'
        const isActive = status === 'active'
        
        // Determine health status with proper typing
        let healthStatus: 'healthy' | 'error' | 'warning' = 'warning'
        if (isActive) {
          healthStatus = 'healthy'
        } else if (status === 'error') {
          healthStatus = 'error'
        }
        
        return {
          id: camera.id,
          name: camera.name,
          enabled: camera.enabled, // Use database enabled field directly
          zone_name: camera.zone || camera.location || 'Unknown Zone',
          model: camera.description || camera.source_type || 'Unknown Model',
          streamUrl: camera.source,
          ptz: false, // PTZ info can be added to advanced_settings if needed
          lastActive: camera.last_online || new Date().toISOString(),
          health: {
            status: healthStatus,
            message: isActive 
              ? 'Camera is running normally' 
              : status === 'error' 
              ? 'Camera encountered an error'
              : 'Camera is stopped',
          },
          resolutionWidth: camera.resolution.width,
          resolutionHeight: camera.resolution.height,
          fps: camera.fps,
          brightness: camera.brightness || 1.0, // Default to 1.0 if not set
          thresholds: {
            motion: 0.7,
            object: 0.5,
          },
        }
      })
      
      return cameras
    } catch (error) {
      console.error('Error fetching cameras from API:', error)
      throw error
    }
  }

  async enableCamera(cameraId: string): Promise<void> {
    try {
      await apiService.post(`/cameras/${cameraId}/start`)
    } catch (error) {
      console.error('Error starting camera:', error)
      throw error
    }
  }

  async disableCamera(cameraId: string): Promise<void> {
    try {
      await apiService.post(`/cameras/${cameraId}/stop`)
    } catch (error) {
      console.error('Error stopping camera:', error)
      throw error
    }
  }

  async getCameraStatus(cameraId: string): Promise<string> {
    try {
      const statusData = await apiService.get<CameraStatusResponse>('/cameras/status')
      return statusData[cameraId] || 'unknown'
    } catch (error) {
      console.error('Error getting camera status:', error)
      throw error
    }
  }

  async updateCameraProperty(cameraId: string, property: string, value: any): Promise<void> {
    try {
      // Map frontend property names to backend field names
      const propertyMap: { [key: string]: string } = {
        'name': 'name',
        'zone_name': 'zone',
        'model': 'description', // Using description field for model
        'enabled': 'enabled',
        'resolutionWidth': 'resolution_width',
        'resolutionHeight': 'resolution_height',
        'fps': 'fps',
        'brightness': 'brightness'
      }

      const backendProperty = propertyMap[property] || property
      const updateData = { [backendProperty]: value }

      await apiService.put(`/cameras/${cameraId}`, updateData)
    } catch (error) {
      console.error('Error updating camera property:', error)
      throw error
    }
  }

  async updateCameraBrightness(cameraId: string, brightness: number): Promise<void> {
    try {
      // Validate brightness range on frontend
      if (brightness < 0.0 || brightness > 2.0) {
        throw new Error('Brightness must be between 0.0 and 2.0')
      }

      await apiService.put(`/cameras/${cameraId}/brightness`, { brightness })
    } catch (error) {
      console.error('Error updating camera brightness:', error)
      throw error
    }
  }

  async createCamera(cameraData: CreateCameraRequest): Promise<CreateCameraResponse> {
    try {
      const response = await apiService.post<CreateCameraResponse>('/cameras', cameraData)
      return response
    } catch (error: any) {
      console.error('Error creating camera:', error)
      
      // Extract error message from API response
      let errorMessage = 'Failed to create camera'
      if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error?.message) {
        errorMessage = error.message
      }
      
      return {
        status: 'error',
        message: errorMessage
      }
    }
  }

  async deleteCamera(cameraId: string): Promise<boolean> {
    try {
      await apiService.delete(`/cameras/${cameraId}`)
      return true
    } catch (error) {
      console.error('Error deleting camera:', error)
      return false
    }
  }
}

export const cameraService = new CameraService()