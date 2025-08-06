import React, { useState, useRef, useEffect } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../../services/auth.service';
import { User } from '../../types';
import { useTheme, useThemeClasses } from '../../contexts/ThemeContext';
import { useNotifications } from '../../contexts/NotificationContext';
import { ThemeToggle } from '../common/ThemeToggle';

// Material-UI Icons
import {
  Security as SecurityIcon,
  Dashboard as DashboardIcon,
  Videocam as VideocamIcon,
  Security as AlertIcon,
  Analytics as AnalyticsIcon,
  People as PeopleIcon,
  Settings as SettingsIcon,
  Edit as EditIcon,
  ExitToApp as LogoutIcon,
  Notifications as BellIcon
} from '@mui/icons-material';

const UserProfileDropdown: React.FC<{
  user: User;
  onLogout: () => void;
}> = ({ user, onLogout }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    username: user.username,
    email: user.email,
    first_name: user.first_name || '',
    last_name: user.last_name || '',
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const themeClasses = useThemeClasses();

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setIsEditing(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setIsLoading(true);

    try {
      await authService.updateProfile(formData);
      setSuccess('Profile updated successfully');
      setIsEditing(false);
      // Auto-close success message after 2 seconds
      setTimeout(() => setSuccess(null), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* User Avatar Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center space-x-2 p-2 rounded-lg ${themeClasses.hover.bg} transition-colors`}
      >
        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
          <span className="text-white text-sm font-medium">
            {user.username.charAt(0).toUpperCase()}
          </span>
        </div>
        <span className={`hidden sm:block text-sm font-medium ${themeClasses.text.primary}`}>
          {user.first_name && user.last_name
            ? `${user.first_name} ${user.last_name}`
            : user.username}
        </span>
        <svg className={`w-4 h-4 ${themeClasses.text.secondary}`} fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className={`absolute right-0 mt-2 w-80 ${themeClasses.bg.primary} rounded-lg shadow-lg ${themeClasses.border.primary} border z-50`}>
          <div className="p-4">
            {!isEditing ? (
              // Profile Display
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                    <span className="text-white font-medium">
                      {user.username.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <div className={`font-medium ${themeClasses.text.primary}`}>
                      {user.first_name && user.last_name
                        ? `${user.first_name} ${user.last_name}`
                        : user.username}
                    </div>
                    <div className={`text-sm ${themeClasses.text.secondary}`}>{user.email}</div>
                    <div className={`text-xs ${themeClasses.text.tertiary} capitalize`}>
                      {user.role}
                    </div>
                  </div>
                </div>

                <div className="flex space-x-2">
                  <button
                    onClick={() => setIsEditing(true)}
                    className="flex items-center space-x-1 flex-1 bg-blue-600 text-white px-3 py-2 rounded-md text-sm hover:bg-blue-700 transition-colors justify-center"
                  >
                    <EditIcon className="w-4 h-4" />
                    <span>Edit Profile</span>
                  </button>
                  <button
                    onClick={onLogout}
                    className={`flex items-center space-x-1 flex-1 ${themeClasses.bg.tertiary} ${themeClasses.text.primary} px-3 py-2 rounded-md text-sm ${themeClasses.hover.bg} transition-colors justify-center`}
                  >
                    <LogoutIcon className="w-4 h-4" />
                    <span>Logout</span>
                  </button>
                </div>
              </div>
            ) : (
              // Profile Edit Form
              <form onSubmit={handleSubmit} className="space-y-3">
                <h3 className={`text-lg font-medium ${themeClasses.text.primary} mb-3`}>Edit Profile</h3>

                <div className="space-y-2">
                  <div>
                    <label className={`block text-sm font-medium ${themeClasses.text.primary} mb-1`}>
                      First Name
                    </label>
                    <input
                      type="text"
                      name="first_name"
                      value={formData.first_name}
                      onChange={handleChange}
                      className={`w-full px-3 py-2 ${themeClasses.bg.secondary} ${themeClasses.border.primary} border rounded-md text-sm ${themeClasses.text.primary} focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
                    />
                  </div>

                  <div>
                    <label className={`block text-sm font-medium ${themeClasses.text.primary} mb-1`}>
                      Last Name
                    </label>
                    <input
                      type="text"
                      name="last_name"
                      value={formData.last_name}
                      onChange={handleChange}
                      className={`w-full px-3 py-2 ${themeClasses.bg.secondary} ${themeClasses.border.primary} border rounded-md text-sm ${themeClasses.text.primary} focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
                    />
                </div>

                <div>
                    <label className={`block text-sm font-medium ${themeClasses.text.primary} mb-1`}>
                      Username
                    </label>
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                      className={`w-full px-3 py-2 ${themeClasses.bg.secondary} ${themeClasses.border.primary} border rounded-md text-sm ${themeClasses.text.primary} focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
                  />
                </div>

                <div>
                    <label className={`block text-sm font-medium ${themeClasses.text.primary} mb-1`}>
                      Email
                    </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                      className={`w-full px-3 py-2 ${themeClasses.bg.secondary} ${themeClasses.border.primary} border rounded-md text-sm ${themeClasses.text.primary} focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
                  />
                  </div>
                </div>

                {error && (
                  <div className="p-2 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm rounded-md">{error}</div>
                )}

                {success && (
                  <div className="p-2 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 text-sm rounded-md">{success}</div>
                )}

                <div className="flex space-x-2 pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditing(false);
                      setError(null);
                      setSuccess(null);
                    }}
                    className={`flex-1 ${themeClasses.bg.tertiary} ${themeClasses.text.primary} px-3 py-2 rounded-md text-sm ${themeClasses.hover.bg} transition-colors`}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="flex-1 bg-blue-600 text-white px-3 py-2 rounded-md text-sm hover:bg-blue-700 transition-colors disabled:opacity-50"
                  >
                    {isLoading ? 'Saving...' : 'Save'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const currentUser = authService.getCurrentUser();
  const { actualTheme } = useTheme();
  const { unreadCount } = useNotifications();
  const themeClasses = useThemeClasses();

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  // Helper function to determine if a link is active
  const isActiveLink = (path: string) => {
    return location.pathname === path;
  };

  // Navigation link styling with dark mode support
  const getLinkClassName = (path: string) => {
    const baseClasses = "inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors";
    const activeClasses = "border-blue-500 text-blue-600 dark:text-blue-400";
    const inactiveClasses = `border-transparent ${themeClasses.text.secondary} hover:border-gray-300 dark:hover:border-gray-600 hover:text-gray-700 dark:hover:text-gray-300`;

    return `${baseClasses} ${isActiveLink(path) ? activeClasses : inactiveClasses}`;
  };

  if (!currentUser) {
    return null; // or redirect to login
  }

  return (
    <div className={`min-h-screen ${themeClasses.bg.secondary}`}>
      <nav className={`${themeClasses.bg.primary} shadow-sm ${themeClasses.border.primary} border-b`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <span className="text-xl font-bold text-blue-600 dark:text-blue-400 flex items-center space-x-2">
                  <SecurityIcon className="w-6 h-6" />
                  <span>Better Vigilant Surveilance</span>
                </span>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <Link
                  to="/dashboard"
                  className={`${getLinkClassName("/dashboard")} space-x-1`}
                >
                  <DashboardIcon className="w-4 h-4" />
                  <span>Dashboard</span>
                </Link>
                <Link
                  to="/cameras"
                  className={`${getLinkClassName("/cameras")} space-x-1`}
                >
                  <VideocamIcon className="w-4 h-4" />
                  <span>Cameras</span>
                </Link>
                <Link
                  to="/alerts"
                  className={`${getLinkClassName("/alerts")} space-x-1`}
                >
                  <AlertIcon className="w-4 h-4" />
                  <span>Alerts</span>
                </Link>
                <Link
                  to="/analytics"
                  className={`${getLinkClassName("/analytics")} space-x-1`}
                >
                  <AnalyticsIcon className="w-4 h-4" />
                  <span>Analytics</span>
                </Link>
                {currentUser?.role === 'admin' && (
                  <Link
                    to="/users"
                    className={`${getLinkClassName("/users")} space-x-1`}
                  >
                    <PeopleIcon className="w-4 h-4" />
                    <span>Users</span>
                  </Link>
                )}
                <Link
                  to="/settings"
                  className={`${getLinkClassName("/settings")} space-x-1`}
                >
                  <SettingsIcon className="w-4 h-4" />
                  <span>Settings</span>
                </Link>
              </div>
            </div>
            <div className="flex sm:ml-6 sm:items-center space-x-4">
              <Link
                to="/notifications"
                className={`p-2 rounded-md ${themeClasses.text.secondary} hover:${themeClasses.text.primary} hover:${themeClasses.bg.secondary} transition-colors relative`}
              >
                <BellIcon className="w-5 h-5" />
                {/* Notification badge */}
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </Link>
              <ThemeToggle size="md" />
              <UserProfileDropdown user={currentUser} onLogout={handleLogout} />
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  );
};

export default MainLayout;
