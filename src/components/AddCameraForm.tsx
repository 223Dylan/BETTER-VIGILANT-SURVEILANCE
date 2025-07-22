import React, { useState } from 'react';
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Typography,
  Alert,
  FormControlLabel,
  Switch,
  Divider,
  FormHelperText,
  Stack,
} from '@mui/material';
import { CreateCameraRequest, CAMERA_SOURCE_TYPES, RESOLUTION_PRESETS } from '../types/camera';
import VideoFileUpload from './VideoFileUpload';

interface AddCameraFormProps {
  onSubmit: (cameraData: CreateCameraRequest) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  error?: string;
}

const AddCameraForm: React.FC<AddCameraFormProps> = ({
  onSubmit,
  onCancel,
  isLoading = false,
  error,
}) => {
  const [formData, setFormData] = useState<CreateCameraRequest>({
    id: '',
    name: '',
    description: '',
    source: '',
    source_type: 'webcam',
    fps: 15,
    resolution: {
      width: 1280,
      height: 720,
    },
    detection_enabled: true,
    detection_sensitivity: 0.5,
    recording_enabled: false,
    location: '',
    zone: '',
  });

  const [selectedResolution, setSelectedResolution] = useState('1280x720 (HD)');
  const [customResolution, setCustomResolution] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [uploadedVideoFile, setUploadedVideoFile] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    // Required field validation
    if (!formData.id.trim()) {
      errors.id = 'Camera ID is required';
    } else if (!/^[a-zA-Z0-9-_]+$/.test(formData.id)) {
      errors.id = 'Camera ID can only contain letters, numbers, hyphens, and underscores';
    }

    if (!formData.name.trim()) {
      errors.name = 'Camera name is required';
    }

    if (!formData.source.trim()) {
      errors.source = 'Camera source is required';
    } else {
      // Validate source based on type
      if (formData.source_type === 'webcam') {
        if (!/^\d+$/.test(formData.source)) {
          errors.source = 'USB camera source must be a number (device index, e.g., 0, 1, 2)';
        }
      } else if (formData.source_type === 'rtsp') {
        if (!formData.source.startsWith('rtsp://')) {
          errors.source = 'RTSP source must start with rtsp:// (e.g., rtsp://username:password@ip:port/path)';
        }
      } else if (formData.source_type === 'file') {
        // For file type, source should be set by the upload component
        if (!uploadedVideoFile) {
          errors.source = 'Please upload a video file';
        }
      }
    }

    // FPS validation
    if (formData.fps && (formData.fps < 1 || formData.fps > 60)) {
      errors.fps = 'FPS must be between 1 and 60';
    }

    // Resolution validation
    if (formData.resolution) {
      if (formData.resolution.width < 320 || formData.resolution.width > 4096) {
        errors.resolution_width = 'Width must be between 320 and 4096';
      }
      if (formData.resolution.height < 240 || formData.resolution.height > 2160) {
        errors.resolution_height = 'Height must be between 240 and 2160';
      }
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    await onSubmit(formData);
  };

  const handleInputChange = (field: keyof CreateCameraRequest, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));

    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors(prev => ({
        ...prev,
        [field]: '',
      }));
    }
  };

  const handleResolutionPresetChange = (preset: string) => {
    setSelectedResolution(preset);

    if (preset === 'Custom') {
      setCustomResolution(true);
    } else {
      setCustomResolution(false);
      const resolutionData = RESOLUTION_PRESETS.find(p => p.label === preset);
      if (resolutionData && resolutionData.width > 0) {
        handleInputChange('resolution', {
          width: resolutionData.width,
          height: resolutionData.height,
        });
      }
    }
  };

  const handleResolutionChange = (dimension: 'width' | 'height', value: string) => {
    const numValue = parseInt(value) || 0;
    handleInputChange('resolution', {
      ...formData.resolution,
      [dimension]: numValue,
    });
  };

  const handleVideoFileUploaded = (filePath: string, originalName: string) => {
    setUploadedVideoFile(filePath);
    setUploadError(null);
    handleInputChange('source', filePath);

    // Clear validation error if present
    if (validationErrors.source) {
      setValidationErrors(prev => ({
        ...prev,
        source: '',
      }));
    }
  };

  const handleVideoUploadError = (error: string) => {
    setUploadError(error);
    setUploadedVideoFile(null);
    handleInputChange('source', '');
  };

  const handleSourceTypeChange = (sourceType: string) => {
    handleInputChange('source_type', sourceType);
    // Clear source when changing type
    handleInputChange('source', '');
    setUploadedVideoFile(null);
    setUploadError(null);

    // Clear validation errors
    if (validationErrors.source) {
      setValidationErrors(prev => ({
        ...prev,
        source: '',
      }));
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} noValidate>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Typography variant="h6" gutterBottom>
        Basic Information
      </Typography>

      <Stack spacing={2} sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexDirection: { xs: 'column', sm: 'row' } }}>
          <TextField
            fullWidth
            label="Camera ID"
            value={formData.id}
            onChange={(e) => handleInputChange('id', e.target.value)}
            error={!!validationErrors.id}
            helperText={validationErrors.id || 'Unique identifier (e.g., entrance-cam-01)'}
            required
          />
          <TextField
            fullWidth
            label="Camera Name"
            value={formData.name}
            onChange={(e) => handleInputChange('name', e.target.value)}
            error={!!validationErrors.name}
            helperText={validationErrors.name || 'Display name for the camera'}
            required
          />
        </Box>
        <TextField
          fullWidth
          label="Description"
          value={formData.description}
          onChange={(e) => handleInputChange('description', e.target.value)}
          helperText="Optional description of the camera"
          multiline
          rows={2}
        />
      </Stack>

      <Divider sx={{ my: 2 }} />

      <Typography variant="h6" gutterBottom>
        Camera Source
      </Typography>

      <Stack spacing={2} sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexDirection: { xs: 'column', sm: 'row' } }}>
          <FormControl fullWidth>
            <InputLabel>Camera Type</InputLabel>
            <Select
              value={formData.source_type}
              label="Camera Type"
              onChange={(e) => handleSourceTypeChange(e.target.value)}
            >
              {Object.entries(CAMERA_SOURCE_TYPES).map(([key, value]) => (
                <MenuItem key={key} value={key}>
                  {value.label}
                </MenuItem>
              ))}
            </Select>
            <FormHelperText>
              {CAMERA_SOURCE_TYPES[formData.source_type]?.description}
            </FormHelperText>
          </FormControl>
          {formData.source_type !== 'file' && (
            <TextField
              fullWidth
              label="Source"
              value={formData.source}
              onChange={(e) => handleInputChange('source', e.target.value)}
              error={!!validationErrors.source}
              helperText={
                validationErrors.source ||
                (formData.source_type === 'webcam'
                  ? 'Device index (0, 1, 2...)'
                  : formData.source_type === 'rtsp'
                  ? 'RTSP URL (rtsp://user:pass@ip:port/path)'
                  : 'File path')
              }
              required
            />
          )}
        </Box>

        {formData.source_type === 'file' && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Upload Video File
            </Typography>
            <VideoFileUpload
              onFileUploaded={handleVideoFileUploaded}
              onError={handleVideoUploadError}
              disabled={isLoading}
              maxFileSizeMB={500}
            />
            {uploadError && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {uploadError}
              </Alert>
            )}
            {validationErrors.source && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {validationErrors.source}
              </Alert>
            )}
          </Box>
        )}
      </Stack>

      <Divider sx={{ my: 2 }} />

      <Typography variant="h6" gutterBottom>
        Video Settings
      </Typography>

      <Stack spacing={2} sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexDirection: { xs: 'column', sm: 'row' } }}>
          <FormControl fullWidth>
            <InputLabel>Resolution</InputLabel>
            <Select
              value={selectedResolution}
              label="Resolution"
              onChange={(e) => handleResolutionPresetChange(e.target.value)}
            >
              {RESOLUTION_PRESETS.map((preset) => (
                <MenuItem key={preset.label} value={preset.label}>
                  {preset.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="FPS"
            type="number"
            value={formData.fps}
            onChange={(e) => handleInputChange('fps', parseInt(e.target.value) || 15)}
            error={!!validationErrors.fps}
            helperText={validationErrors.fps || 'Frames per second (1-60)'}
            inputProps={{ min: 1, max: 60 }}
          />
        </Box>
        {customResolution && (
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              fullWidth
              label="Width"
              type="number"
              value={formData.resolution?.width || ''}
              onChange={(e) => handleResolutionChange('width', e.target.value)}
              error={!!validationErrors.resolution_width}
              helperText={validationErrors.resolution_width}
              inputProps={{ min: 320, max: 4096 }}
            />
            <TextField
              fullWidth
              label="Height"
              type="number"
              value={formData.resolution?.height || ''}
              onChange={(e) => handleResolutionChange('height', e.target.value)}
              error={!!validationErrors.resolution_height}
              helperText={validationErrors.resolution_height}
              inputProps={{ min: 240, max: 2160 }}
            />
          </Box>
        )}
      </Stack>

      <Divider sx={{ my: 2 }} />

      <Typography variant="h6" gutterBottom>
        Location & Settings
      </Typography>

      <Stack spacing={2} sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexDirection: { xs: 'column', sm: 'row' } }}>
          <TextField
            fullWidth
            label="Location"
            value={formData.location}
            onChange={(e) => handleInputChange('location', e.target.value)}
            helperText="Physical location (e.g., Main Entrance, Aisle 3)"
          />
          <TextField
            fullWidth
            label="Zone"
            value={formData.zone}
            onChange={(e) => handleInputChange('zone', e.target.value)}
            helperText="Security zone (e.g., public, restricted, warehouse)"
          />
        </Box>

        <Box sx={{ display: 'flex', gap: 2, flexDirection: { xs: 'column', sm: 'row' }, alignItems: 'flex-start' }}>
          <FormControlLabel
            control={
              <Switch
                checked={formData.detection_enabled}
                onChange={(e) => handleInputChange('detection_enabled', e.target.checked)}
              />
            }
            label="Enable Detection"
          />
          <FormControlLabel
            control={
              <Switch
                checked={formData.recording_enabled}
                onChange={(e) => handleInputChange('recording_enabled', e.target.checked)}
              />
            }
            label="Enable Recording"
          />
          <TextField
            label="Detection Sensitivity"
            type="number"
            value={formData.detection_sensitivity}
            onChange={(e) => handleInputChange('detection_sensitivity', parseFloat(e.target.value) || 0.5)}
            helperText="0.0 (low) to 1.0 (high)"
            inputProps={{ min: 0, max: 1, step: 0.1 }}
            disabled={!formData.detection_enabled}
            sx={{ minWidth: 200 }}
          />
        </Box>
      </Stack>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 3 }}>
        <Button
          variant="outlined"
          onClick={onCancel}
          disabled={isLoading}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          variant="contained"
          disabled={isLoading}
        >
          {isLoading ? 'Creating...' : 'Create Camera'}
        </Button>
      </Box>
    </Box>
  );
};

export default AddCameraForm;
