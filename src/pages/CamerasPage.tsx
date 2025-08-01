import React from 'react';
import CameraGrid from '../components/CameraGrid';
import { useThemeClasses } from '../contexts/ThemeContext';

const CamerasPage: React.FC = () => {
  const themeClasses = useThemeClasses();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className={`text-3xl font-bold ${themeClasses.text.primary}`}>Camera Management</h1>
          <p className={`mt-2 ${themeClasses.text.secondary}`}>
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
