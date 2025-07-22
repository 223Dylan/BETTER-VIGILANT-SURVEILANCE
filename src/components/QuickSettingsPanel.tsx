import React, { useState } from 'react';
import { Camera } from '../types';
import CameraSettingsPanel from './CameraSettingsPanel';

// Material-UI Icons
import {
  Settings as SettingsIcon,
  Videocam as VideocamIcon
} from '@mui/icons-material';

interface QuickSettingsPanelProps {
  cameras: Camera[];
  onCameraUpdated: () => void;
}

const QuickSettingsPanel: React.FC<QuickSettingsPanelProps> = ({
  cameras,
  onCameraUpdated
}) => {
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);

  const handleCameraClick = (camera: Camera) => {
    setSelectedCamera(camera);
  };

  const activeCameras = cameras.filter(c => c.enabled);
  const inactiveCameras = cameras.filter(c => !c.enabled);

  return (
    <>
      <div className="bg-white rounded-lg shadow-md border border-gray-200 mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <SettingsIcon className="text-blue-600 w-6 h-6" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Quick Settings</h2>
                <p className="text-sm text-gray-600">
                  Click on any camera below to configure its settings
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                {activeCameras.length} active • {inactiveCameras.length} inactive
              </div>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {cameras.map(camera => (
              <div
                key={camera.id}
                className="p-4 rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md cursor-pointer transition-all bg-white hover:bg-blue-50"
                onClick={() => handleCameraClick(camera)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900 truncate flex items-center space-x-1">
                      <VideocamIcon className="w-4 h-4" />
                      <span>{camera.name}</span>
                    </div>
                    <div className="text-xs text-gray-500 truncate">
                      {camera.zone_name || 'No zone'}
                    </div>
                  </div>
                  <div className={`w-3 h-3 rounded-full flex-shrink-0 ml-2 ${
                    camera.enabled ? 'bg-green-400' : 'bg-gray-300'
                  }`} />
                </div>
                <div className="text-xs text-gray-400">
                  Click to configure settings
                </div>
              </div>
            ))}
          </div>

          {cameras.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <div className="flex justify-center mb-2">
                <VideocamIcon className="w-12 h-12" />
              </div>
              <p>No cameras available for configuration</p>
            </div>
          )}
        </div>
      </div>

      {/* Camera Settings Panel */}
      {selectedCamera && (
        <CameraSettingsPanel
          camera={selectedCamera}
          onClose={() => setSelectedCamera(null)}
          onSave={async (updatedCamera) => {
            setSelectedCamera(null);
            await onCameraUpdated();
          }}
        />
      )}
    </>
  );
};

export default QuickSettingsPanel;
