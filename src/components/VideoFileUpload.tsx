import React, { useState, useCallback, useRef } from 'react';
import {
  Box,
  Typography,
  Button,
  LinearProgress,
  Alert,
  IconButton,
  Chip,
  Stack,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Delete as DeleteIcon,
  VideoFile as VideoFileIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

interface VideoFileUploadProps {
  onFileUploaded: (filePath: string, originalName: string) => void;
  onError: (error: string) => void;
  disabled?: boolean;
  maxFileSizeMB?: number;
}

interface UploadedFile {
  file: File;
  filePath: string;
  originalName: string;
  sizeBytes: number;
}

const DropZone = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isDragActive' && prop !== 'hasFile',
})<{ isDragActive: boolean; hasFile: boolean }>(({ theme, isDragActive, hasFile }) => ({
  border: `2px dashed ${
    isDragActive
      ? theme.palette.primary.main
      : hasFile
      ? theme.palette.success.main
      : theme.palette.divider
  }`,
  borderRadius: theme.shape.borderRadius,
  padding: theme.spacing(3),
  textAlign: 'center',
  cursor: 'pointer',
  backgroundColor: isDragActive
    ? theme.palette.action.hover
    : hasFile
    ? theme.palette.action.selected
    : 'transparent',
  transition: 'all 0.2s ease-in-out',
  '&:hover': {
    backgroundColor: theme.palette.action.hover,
    borderColor: theme.palette.primary.main,
  },
}));

const VideoFileUpload: React.FC<VideoFileUploadProps> = ({
  onFileUploaded,
  onError,
  disabled = false,
  maxFileSizeMB = 500,
}) => {
  const [isDragActive, setIsDragActive] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const allowedTypes = [
    'video/mp4',
    'video/avi',
    'video/quicktime',
    'video/x-msvideo',
    'video/webm',
    'video/x-flv',
    'video/x-ms-wmv',
    'video/x-matroska',
  ];

  const allowedExtensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'];

  const validateFile = (file: File): string | null => {
    // Check file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
      return `Invalid file type. Allowed: ${allowedExtensions.join(', ')}`;
    }

    // Check file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxFileSizeMB) {
      return `File too large. Maximum size: ${maxFileSizeMB}MB`;
    }

    return null;
  };

  const uploadFile = async (file: File) => {
    setIsUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8001/cameras/upload-video', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const result = await response.json();
      const uploadedFileInfo: UploadedFile = {
        file,
        filePath: result.file_path,
        originalName: result.original_filename,
        sizeBytes: result.size_bytes,
      };

      setUploadedFile(uploadedFileInfo);
      onFileUploaded(result.file_path, result.original_filename);
      setUploadProgress(100);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      onError(errorMessage);
    } finally {
      setIsUploading(false);
    }
  };

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;

      const file = files[0];
      const validationError = validateFile(file);

      if (validationError) {
        onError(validationError);
        return;
      }

      await uploadFile(file);
    },
    [maxFileSizeMB, onError]
  );

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragActive(false);

      if (disabled || isUploading) return;

      const files = e.dataTransfer.files;
      handleFiles(files);
    },
    [disabled, isUploading, handleFiles]
  );

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      handleFiles(e.target.files);
    },
    [handleFiles]
  );

  const handleBrowseClick = () => {
    if (!disabled && !isUploading) {
      fileInputRef.current?.click();
    }
  };

  const handleRemoveFile = () => {
    setUploadedFile(null);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes: number): string => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  return (
    <Box>
      <input
        ref={fileInputRef}
        type="file"
        accept={allowedExtensions.join(',')}
        onChange={handleFileInputChange}
        style={{ display: 'none' }}
      />

      {!uploadedFile ? (
        <DropZone
          isDragActive={isDragActive}
          hasFile={false}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={handleBrowseClick}
          sx={{
            opacity: disabled ? 0.5 : 1,
            cursor: disabled ? 'not-allowed' : 'pointer',
          }}
        >
          <CloudUploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {isDragActive ? 'Drop video file here' : 'Drag & drop a video file'}
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            or click to browse
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Supported: {allowedExtensions.join(', ')} • Max: {maxFileSizeMB}MB
          </Typography>
        </DropZone>
      ) : (
        <DropZone hasFile={true} isDragActive={false}>
          <Stack direction="row" alignItems="center" spacing={2} justifyContent="center">
            <VideoFileIcon sx={{ fontSize: 32, color: 'success.main' }} />
            <Box sx={{ flexGrow: 1, textAlign: 'left' }}>
              <Typography variant="body1" fontWeight="medium">
                {uploadedFile.originalName}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {formatFileSize(uploadedFile.sizeBytes)}
              </Typography>
            </Box>
            <IconButton
              onClick={handleRemoveFile}
              color="error"
              size="small"
              disabled={disabled}
            >
              <DeleteIcon />
            </IconButton>
          </Stack>
        </DropZone>
      )}

      {isUploading && (
        <Box sx={{ mt: 2 }}>
          <LinearProgress variant="indeterminate" />
          <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 1 }}>
            Uploading video file...
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default VideoFileUpload;
