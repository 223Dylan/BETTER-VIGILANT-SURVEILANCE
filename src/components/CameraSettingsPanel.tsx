import React, { useState } from 'react';
import { Camera } from '../types';

interface CameraSettingsPanelProps {
  camera: Camera;
  onClose: () => void;
  onSave?: (updatedCamera: Camera) => void;
}

const CameraSettingsPanel: React.FC<CameraSettingsPanelProps> = ({ camera, onClose, onSave }) => {
  const [name, setName] = useState(camera.name);
  const [zone, setZone] = useState(camera.zone_name || '');
  const [model, setModel] = useState(camera.model || '');
  const [enabled, setEnabled] = useState(camera.enabled);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [resolutionWidth, setResolutionWidth] = useState(camera.resolutionWidth || 1280);
  const [resolutionHeight, setResolutionHeight] = useState(camera.resolutionHeight || 720);
  const [fps, setFps] = useState(camera.fps || 30);
  const [brightness, setBrightness] = useState(camera.brightness || 1.0);
  const [motionThreshold, setMotionThreshold] = useState(camera.thresholds?.motion ?? 0.7);
  const [objectThreshold, setObjectThreshold] = useState(camera.thresholds?.object ?? 0.5);

  const handleSave = () => {
    // Validation: require name
    if (!name.trim()) {
      setError('Camera name is required.');
      setSuccess(null);
      return;
    }
    setError(null);
    if (onSave) {
      onSave({
        ...camera,
        name,
        zone_name: zone,
        model,
        enabled,
        resolutionWidth,
        resolutionHeight,
        fps,
        brightness,
        thresholds: {
          motion: motionThreshold,
          object: objectThreshold,
        },
      });
      setSuccess('Camera updated successfully!');
    }
    // Optionally, close after a delay
    // setTimeout(onClose, 1000);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-semibold mb-4">Camera Settings</h2>
        {error && <div className="mb-2 text-red-600">{error}</div>}
        {success && <div className="mb-2 text-green-600">{success}</div>}
        <div className="mb-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
          <input
            className="w-full border border-gray-300 rounded px-2 py-1"
            value={name}
            onChange={e => setName(e.target.value)}
          />
        </div>
        <div className="mb-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">Zone</label>
          <input
            className="w-full border border-gray-300 rounded px-2 py-1"
            value={zone}
            onChange={e => setZone(e.target.value)}
          />
        </div>
        <div className="mb-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
          <input
            className="w-full border border-gray-300 rounded px-2 py-1"
            value={model}
            onChange={e => setModel(e.target.value)}
          />
        </div>
        <div className="mb-2 flex items-center">
          <label className="block text-sm font-medium text-gray-700 mr-2">Enabled</label>
          <input type="checkbox" checked={enabled} onChange={e => setEnabled(e.target.checked)} />
        </div>
        <div className="mb-2 flex gap-2">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Resolution (W)</label>
            <input
              type="number"
              className="w-full border border-gray-300 rounded px-2 py-1"
              value={resolutionWidth}
              onChange={e => setResolutionWidth(Number(e.target.value))}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Resolution (H)</label>
            <input
              type="number"
              className="w-full border border-gray-300 rounded px-2 py-1"
              value={resolutionHeight}
              onChange={e => setResolutionHeight(Number(e.target.value))}
            />
          </div>
        </div>
        <div className="mb-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">FPS</label>
          <input
            type="number"
            className="w-full border border-gray-300 rounded px-2 py-1"
            value={fps}
            onChange={e => setFps(Number(e.target.value))}
          />
        </div>
        <div className="mb-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Brightness ({brightness.toFixed(1)}x)
          </label>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-400">0</span>
            <input
              type="range"
              min="0.0"
              max="2.0"
              step="0.1"
              value={brightness}
              onChange={e => setBrightness(Number(e.target.value))}
              className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <span className="text-xs text-gray-400">2</span>
          </div>
        </div>
        <div className="mb-2">
          <label className="block text-sm font-medium text-gray-700">Motion Threshold</label>
          <input
            type="number"
            min="0"
            max="1"
            step="0.1"
            value={motionThreshold}
            onChange={e => setMotionThreshold(Number(e.target.value))}
            className="w-full border border-gray-300 rounded px-2 py-1"
          />
        </div>
        <div className="mb-2">
          <label className="block text-sm font-medium text-gray-700">Object Threshold</label>
          <input
            type="number"
            min="0"
            max="1"
            step="0.1"
            value={objectThreshold}
            onChange={e => setObjectThreshold(Number(e.target.value))}
            className="w-full border border-gray-300 rounded px-2 py-1"
          />
        </div>
        <div className="flex justify-end gap-2 mt-4">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default CameraSettingsPanel;
