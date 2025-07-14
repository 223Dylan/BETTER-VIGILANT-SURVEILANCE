import React from 'react';
import { Camera } from '../types';
import VideoPlayer from './VideoPlayer';

interface VideoFeedProps {
  cameraId: string;
  camera: Camera;
  width?: string;
  height?: string;
  streamType?: 'mjpeg' | 'mjpeg-ws' | 'hls' | 'webrtc';
  onError?: (error: string) => void;
}

const VideoFeed: React.FC<VideoFeedProps> = ({
  cameraId,
  camera,
  width = '100%',
  height = 'auto',
  streamType = 'mjpeg',
  onError,
}) => {
  // Use the new VideoPlayer component for better video handling
  return (
    <VideoPlayer
      cameraId={cameraId}
      camera={camera}
      width={width}
      height={height}
      streamType={streamType}
      onError={onError}
    />
  );
};

export default VideoFeed;
