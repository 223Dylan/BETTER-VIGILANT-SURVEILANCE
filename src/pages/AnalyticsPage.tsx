import React from 'react';
import { useThemeClasses } from '../contexts/ThemeContext';
import AnalyticsDashboard from '../components/AnalyticsDashboard';

const AnalyticsPage: React.FC = () => {
  const themeClasses = useThemeClasses();

  return (
    <div className={`min-h-screen ${themeClasses.bg} ${themeClasses.text}`}>
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Analytics Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Real-time monitoring and analytics for your surveillance system
          </p>
        </div>

        <AnalyticsDashboard />
      </div>
    </div>
  );
};

export default AnalyticsPage;
