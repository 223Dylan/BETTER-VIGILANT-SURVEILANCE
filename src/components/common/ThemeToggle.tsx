import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';

interface ThemeToggleProps {
  className?: string;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({
  className = '',
  showLabel = false,
  size = 'md'
}) => {
  const { theme, setTheme, actualTheme } = useTheme();

  const sizeClasses = {
    sm: 'p-1.5 text-sm',
    md: 'p-2 text-base',
    lg: 'p-3 text-lg'
  };

  const iconSizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  };

  const getThemeIcon = () => {
    switch (theme) {
      case 'light':
        return (
          <svg className={iconSizeClasses[size]} fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5H21a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75V21a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM7.758 17.303a.75.75 0 00-1.061-1.06l-1.591 1.59a.75.75 0 001.06 1.061l1.591-1.59zM6 12a.75.75 0 01-.75.75H3a.75.75 0 010-1.5h2.25A.75.75 0 016 12zM6.697 7.757a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 00-1.061 1.06l1.59 1.591z" />
          </svg>
        );
      case 'dark':
        return (
          <svg className={iconSizeClasses[size]} fill="currentColor" viewBox="0 0 24 24">
            <path fillRule="evenodd" d="M9.528 1.718a.75.75 0 01.162.819A8.97 8.97 0 009 6a9 9 0 009 9 8.97 8.97 0 003.463-.69.75.75 0 01.981.98 10.503 10.503 0 01-9.694 6.46c-5.799 0-10.5-4.701-10.5-10.5 0-4.368 2.667-8.112 6.46-9.694a.75.75 0 01.818.162z" clipRule="evenodd" />
          </svg>
        );
      case 'system':
        return (
          <svg className={iconSizeClasses[size]} fill="currentColor" viewBox="0 0 24 24">
            <path fillRule="evenodd" d="M2.25 5.25a3 3 0 013-3h13.5a3 3 0 013 3V15a3 3 0 01-3 3h-3.844l.938 3.75a.75.75 0 01-.728.75H8.834a.75.75 0 01-.728-.75L9.044 18H5.25a3 3 0 01-3-3V5.25zm1.5 0V15a1.5 1.5 0 001.5 1.5h13.5a1.5 1.5 0 001.5-1.5V5.25a1.5 1.5 0 00-1.5-1.5H5.25a1.5 1.5 0 00-1.5 1.5z" clipRule="evenodd" />
          </svg>
        );
      default:
        return null;
    }
  };

  const getThemeLabel = () => {
    switch (theme) {
      case 'light':
        return 'Light';
      case 'dark':
        return 'Dark';
      case 'system':
        return 'System';
      default:
        return '';
    }
  };

  const handleCycleTheme = () => {
    if (theme === 'light') {
      setTheme('dark');
    } else if (theme === 'dark') {
      setTheme('system');
    } else {
      setTheme('light');
    }
  };

  return (
    <div className="flex items-center">
      <button
        onClick={handleCycleTheme}
        className={`${sizeClasses[size]} rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
          actualTheme === 'dark'
            ? 'text-gray-300 hover:text-white hover:bg-gray-700 focus:ring-offset-gray-800'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:ring-offset-white'
        } ${className}`}
        title={`Current theme: ${getThemeLabel()}. Click to cycle themes.`}
        aria-label={`Switch theme. Current: ${getThemeLabel()}`}
      >
        {getThemeIcon()}
      </button>

      {showLabel && (
        <span className={`ml-2 text-sm font-medium ${
          actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
        }`}>
          {getThemeLabel()}
        </span>
      )}
    </div>
  );
};

// Dropdown version for more explicit theme selection
export const ThemeSelector: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { theme, setTheme, actualTheme } = useTheme();

  return (
    <div className={`relative ${className}`}>
      <select
        value={theme}
        onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'system')}
        className={`rounded-lg border px-3 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors ${
          actualTheme === 'dark'
            ? 'bg-gray-800 border-gray-600 text-gray-300 hover:bg-gray-700 focus:ring-offset-gray-800'
            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-offset-white'
        }`}
      >
        <option value="light">Light</option>
        <option value="dark">Dark</option>
        <option value="system">System</option>
      </select>
    </div>
  );
};

export default ThemeToggle;
