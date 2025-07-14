// Barrel exports for convenient type imports
export * from './camera';
export * from './user';
export * from './alert';

// Re-export commonly used types for easy access
export type { Camera, CreateCameraRequest, CreateCameraResponse, CameraValidationError, CameraApiResponse, CameraStatusResponse } from './camera';
export type { User, CreateUserRequest, UpdateUserRequest, UserSettings } from './user';
export type { Alert, AlertFilter, AlertStats, AlertAction } from './alert';

// Re-export constants
export { CAMERA_SOURCE_TYPES, RESOLUTION_PRESETS } from './camera';
