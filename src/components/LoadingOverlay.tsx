import React from 'react';
import { CircularProgress, Box, Typography } from '@mui/material';

interface LoadingOverlayProps {
  isVisible: boolean;
  message?: string;
  subMessage?: string;
  size?: number;
  className?: string;
}

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  isVisible,
  message = 'Loading...',
  subMessage,
  size = 40,
  className = '',
}) => {
  if (!isVisible) return null;

  return (
    <div className={`absolute inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 backdrop-blur-sm ${className}`}>
      <Box className="text-center text-white animate-pulse">
        <div className="relative mb-3">
          <CircularProgress
            size={size}
            sx={{ color: 'white' }}
          />
          <div className="absolute inset-0 rounded-full border-2 border-white opacity-20 animate-ping"></div>
        </div>
        <Typography variant="body2" className="font-medium mb-1 text-white">
          {message}
        </Typography>
        {subMessage && (
          <Typography variant="caption" className="opacity-75 text-white">
            {subMessage}
          </Typography>
        )}
      </Box>
    </div>
  );
};

export default LoadingOverlay;
