import React from 'react';
import CameraGrid from '../components/CameraGrid';

const CamerasPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Camera Management</h1>
          <p className="mt-2 text-gray-600">
            Monitor and control all cameras in your system
          </p>
        </div>
      </div>

      {/* Camera Management Grid */}
      <CameraGrid />
    </div>
  );
};

export default CamerasPage; 