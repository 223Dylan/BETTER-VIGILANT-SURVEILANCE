import React, { useRef, useEffect, useState } from 'react';
import { Box, Typography } from '@mui/material';
import { Camera } from '../types/camera';
import LoadingOverlay from './LoadingOverlay';

interface VideoPlayerProps {
  cameraId: string;
  camera: Camera;
  width?: string;
  height?: string;
  streamType?: 'mjpeg' | 'mjpeg-ws' | 'hls' | 'webrtc';
  onError?: (error: string) => void;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({
  cameraId,
  camera,
  width = '100%',
  height = 'auto',
  streamType = 'mjpeg',
  onError,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const hlsRef = useRef<any>(null); // HLS.js instance
  const currentBlobUrl = useRef<string | null>(null);
  const shouldStayConnected = useRef<boolean>(true);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [frameCount, setFrameCount] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [lastEvent, setLastEvent] = useState<string | null>(null);

  // Initialize HLS if available
  const initializeHLS = async () => {
    if (streamType !== 'hls') return;

    try {
      // Load HLS.js dynamically
      let Hls;

      if (typeof window !== 'undefined') {
        // Check if HLS is already loaded
        if ((window as any).Hls) {
          Hls = (window as any).Hls;
        } else {
          // Import HLS.js dynamically
          const HlsModule = await import('hls.js');
          Hls = HlsModule.default;
          (window as any).Hls = Hls; // Cache for future use
        }

        if (Hls.isSupported() && videoRef.current) {
          // Clean up any existing HLS instance
          if (hlsRef.current) {
            hlsRef.current.destroy();
          }

          const hls = new Hls({
            enableWorker: true,
            lowLatencyMode: true,
            liveDurationInfinity: true,
          });

          // Store HLS instance in ref for cleanup
          hlsRef.current = hls;

          // Try simple HLS first, fallback to complex HLS
          const simpleHlsUrl = `http://localhost:8001/api/simple/hls/${cameraId}/playlist.m3u8`;
          const complexHlsUrl = `http://localhost:8001/api/video/hls/${cameraId}/playlist.m3u8`;

          console.log(`Trying Simple HLS for camera ${cameraId}`);
          hls.loadSource(simpleHlsUrl);
          hls.attachMedia(videoRef.current);

          hls.on(Hls.Events.MANIFEST_PARSED, () => {
            console.log('HLS manifest loaded, starting playback');
            setIsLoading(false);
            setError(null);
            videoRef.current?.play();
          });

          hls.on(Hls.Events.FRAG_LOADED, () => {
            // Clear any previous errors when segments load successfully
            setError(null);
          });

          // Clear errors when playback actually starts
          videoRef.current.addEventListener('playing', () => {
            setError(null);
            setIsPlaying(true);
          });

          videoRef.current.addEventListener('timeupdate', () => {
            // Clear errors when video is actively playing
            if (!videoRef.current?.paused) {
              setError(null);
              setIsPlaying(true);
            }
          });

          hls.on(Hls.Events.ERROR, (event: any, data: any) => {
            console.error('HLS Error:', data);
            if (data.details === 'manifestLoadError' && data.url === simpleHlsUrl) {
              console.log('Simple HLS failed, trying complex HLS...');
              hls.loadSource(complexHlsUrl);
            } else if (data.fatal) {
              // Only show error for fatal errors
              setError(`HLS Error: ${data.details}`);
              setIsLoading(false);
            } else {
              // Non-fatal errors (like buffer stalls) - just log them
              console.warn('Non-fatal HLS issue:', data.details);
            }
          });

          return () => {
            if (hlsRef.current) {
              hlsRef.current.destroy();
              hlsRef.current = null;
            }
          };
        } else if (videoRef.current?.canPlayType('application/vnd.apple.mpegurl')) {
          // Native HLS support (Safari) - try simple HLS first
          const simpleHlsUrl = `http://localhost:8001/api/simple/hls/${cameraId}/playlist.m3u8`;
          videoRef.current.src = simpleHlsUrl;
          videoRef.current.addEventListener('loadedmetadata', () => {
            setIsLoading(false);
            setError(null);
          });
          videoRef.current.addEventListener('error', () => {
            setError('Failed to load HLS stream');
            setIsLoading(false);
          });
        } else {
          setError('HLS not supported on this browser');
          setIsLoading(false);
        }
      }
    } catch (error) {
      console.error('Failed to initialize HLS:', error);
      setError('Failed to initialize HLS player');
      setIsLoading(false);
    }
  };

  // MJPEG over HTTP (multipart stream)
  const initializeMJPEGHttp = () => {
    if (streamType !== 'mjpeg') return;

    try {
      if (imgRef.current) {
        const mjpegUrl = `http://localhost:8001/api/video/mjpeg/${cameraId}`;

        console.log(`MJPEG HTTP stream loading for camera ${cameraId}`);
        setIsLoading(true);

        imgRef.current.onload = () => {
          console.log(`MJPEG HTTP stream ready for camera ${cameraId}`);
          setIsLoading(false);
          setError(null);
          setIsPlaying(true);
          setLastEvent('Frame loaded');
        };

        imgRef.current.onerror = () => {
          console.error(`MJPEG HTTP stream failed for camera ${cameraId}`);
          setError('Failed to load MJPEG stream');
          setIsLoading(false);
          setIsPlaying(false);
          setRetryCount((c) => c + 1);
          setLastEvent('HTTP image error');
          // Clear the image source to remove any lingering frame
          if (imgRef.current) {
            imgRef.current.src = '';
          }
        };

        // Set the src last to trigger loading
        imgRef.current.src = mjpegUrl;
      }
    } catch (error) {
      console.error('Failed to initialize MJPEG HTTP stream:', error);
      setError('Failed to initialize MJPEG stream');
      setIsLoading(false);
    }
  };

  // MJPEG over WebSocket implementation (legacy)
  const connectMJPEGWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const ws = new WebSocket(`ws://localhost:8001/api/video/stream/${cameraId}`);

      ws.onopen = () => {
        console.log(`Video WebSocket connected for camera ${cameraId}`);
        setError(null);
        setIsLoading(false);
        setRetryCount(0);
        setLastEvent('WebSocket connected');
      };

      ws.onmessage = (event) => {
        try {
          if (event.data instanceof Blob) {
            // Handle JPEG frame data
            const url = URL.createObjectURL(new Blob([event.data], { type: 'image/jpeg' }));

            // Clean up previous blob URL
            if (currentBlobUrl.current) {
              URL.revokeObjectURL(currentBlobUrl.current);
            }
            currentBlobUrl.current = url;

            // Method 1: Use img element for MJPEG-WS (frame-by-frame)
            if (imgRef.current && streamType === 'mjpeg-ws') {
              imgRef.current.src = url;
              setError(null);
              setFrameCount(prev => prev + 1);
              setIsPlaying(true);
              setLastEvent('Frame received');
            }

            // Method 2: Use canvas for more control (alternative approach)
            if (canvasRef.current && streamType === 'mjpeg-ws') {
              const canvas = canvasRef.current;
              const ctx = canvas.getContext('2d');
              const img = new Image();

              img.onload = () => {
                canvas.width = img.width;
                canvas.height = img.height;
                ctx?.drawImage(img, 0, 0);
                URL.revokeObjectURL(url);
              };

              img.src = url;
            }
          } else {
            // Handle JSON error messages
            try {
              const data = JSON.parse(event.data);
              if (data.error) {
                if (data.error === "Camera stopped") {
                  shouldStayConnected.current = false;
                  wsRef.current?.close();
                  return;
                }
                // For "No frame available", keep loading overlay with details instead of showing placeholder
                if (data.error !== "No frame available") {
                  setError(data.error);
                  setLastEvent(`Error: ${data.error}`);
                } else {
                  setLastEvent('Waiting for frames...');
                  setIsLoading(true);
                }
              }
            } catch (e) {
              console.error(`Failed to parse message for camera ${cameraId}:`, e);
            }
          }
        } catch (error) {
          console.error(`Error handling video message for camera ${cameraId}:`, error);
        }
      };

      ws.onerror = (error) => {
        console.error(`Video WebSocket error for camera ${cameraId}:`, error);
        setError('Failed to connect to video stream');
        setIsLoading(false);
        setRetryCount((c) => c + 1);
        setLastEvent('WebSocket error');
      };

      ws.onclose = (event) => {
        console.log(`Video WebSocket closed for camera ${cameraId}:`, event.code, event.reason);
        setError('Video stream disconnected');
        setIsLoading(false);
        setIsPlaying(false);
        setRetryCount((c) => c + 1);
        setLastEvent('WebSocket closed');

        // Only attempt to reconnect if we should stay connected
        if (shouldStayConnected.current && camera.enabled) {
          setTimeout(connectMJPEGWebSocket, 3000);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      setError('Failed to connect to video stream');
      setIsLoading(false);
    }
  };

  // WebRTC implementation (placeholder for future)
  const initializeWebRTC = async () => {
    if (streamType !== 'webrtc') return;

    console.log('WebRTC streaming not yet implemented');
    setError('WebRTC streaming coming soon');
    setIsLoading(false);
  };

  useEffect(() => {
    if (!camera.enabled) {
      shouldStayConnected.current = false;
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      // Clean up HLS player when camera is disabled
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
      if (videoRef.current) {
        videoRef.current.src = '';
        videoRef.current.load();
      }
      // Clear MJPEG image source when camera is disabled
      if (imgRef.current) {
        imgRef.current.src = '';
      }
      setIsPlaying(false);
      setError(null);
      return;
    }

    shouldStayConnected.current = true;
    setIsLoading(true);

    // Initialize based on stream type
    switch (streamType) {
      case 'hls':
        initializeHLS();
        break;
      case 'mjpeg':
        initializeMJPEGHttp();
        break;
      case 'mjpeg-ws':
        connectMJPEGWebSocket();
        break;
      case 'webrtc':
        initializeWebRTC();
        break;
      default:
        connectMJPEGWebSocket();
    }

    return () => {
      shouldStayConnected.current = false;
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
      if (currentBlobUrl.current) {
        URL.revokeObjectURL(currentBlobUrl.current);
        currentBlobUrl.current = null;
      }
    };
  }, [cameraId, camera.enabled, streamType]);

  // Show placeholder if camera is disabled
  if (!camera.enabled) {
    return (
      <Box
        sx={{
          position: 'relative',
          width,
          height: height === 'auto' ? '200px' : height,
          backgroundColor: '#f3f4f6',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          overflow: 'hidden',
          borderRadius: '4px',
          border: '1px solid #e5e7eb',
        }}
      >
        <Typography variant="body2" color="text.secondary">
          Camera Disabled
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        position: 'relative',
        width,
        height: height === 'auto' ? '200px' : height,
        backgroundColor: 'black',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        overflow: 'hidden',
        borderRadius: '4px',
      }}
    >
      {/* Video Element for HLS only */}
      <video
        ref={videoRef}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          display: streamType === 'hls' ? 'block' : 'none',
        }}
        autoPlay
        muted
        playsInline
        controls={streamType === 'hls'} // Show controls for HLS only
      />

      {/* Image Element for MJPEG streams (both HTTP and WebSocket) */}
      <img
        ref={imgRef}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          display: streamType === 'mjpeg' || streamType === 'mjpeg-ws' ? 'block' : 'none',
        }}
        alt={`Camera feed for ${camera.name || cameraId}`}
      />

      {/* Canvas Element for Custom Rendering */}
      <canvas
        ref={canvasRef}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          display: 'none', // Hidden by default, can be enabled for custom rendering
        }}
      />

      {/* Loading Overlay */}
      <LoadingOverlay
        isVisible={isLoading}
        message={`Connecting to ${streamType.toUpperCase()} stream`}
        subMessage={`Camera ${camera.name || cameraId}`}
        attemptText={retryCount > 0 ? `Retry attempts: ${retryCount}` : undefined}
        details={[
          lastEvent ? `Last event: ${lastEvent}` : undefined,
          error ? `Last error: ${error}` : undefined,
        ].filter(Boolean) as string[]}
      />

      {/* Error Display */}
      {error && !isLoading && (
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center',
            padding: 2,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            borderRadius: '4px',
            color: 'white',
          }}
        >
          <Typography variant="body2" color="error">
            {error}
          </Typography>
          {retryCount > 0 && (
            <Typography variant="caption" color="inherit">
              Retry attempts: {retryCount}
            </Typography>
          )}
        </Box>
      )}


    </Box>
  );
};

export default VideoPlayer;
