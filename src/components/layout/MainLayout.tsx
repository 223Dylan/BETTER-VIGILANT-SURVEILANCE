import React, { useState, useRef, useEffect } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../../services/auth.service';
import { User } from '../../types';

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
  ExitToApp as LogoutIcon
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
        className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 transition-colors"
      >
        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
          <span className="text-white text-sm font-medium">
            {user.username?.charAt(0).toUpperCase() || 'U'}
          </span>
        </div>
        <span className="text-sm text-gray-700 hidden sm:block">{user.username}</span>
        <svg
          className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50 max-w-[calc(100vw-2rem)] sm:max-w-none">
          <div className="p-4">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white text-lg font-medium">
                  {user.username?.charAt(0).toUpperCase() || 'U'}
                </span>
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="font-semibold text-gray-900 truncate">{user.first_name || user.username}</h3>
                <p className="text-sm text-gray-500 truncate">{user.email}</p>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full mt-1 ${
                  user.role === 'admin' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'
                }`}>
                  {user.role}
                </span>
              </div>
            </div>

            {!isEditing ? (
              // Profile Display Mode
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <label className="text-gray-500">First Name</label>
                    <p className="font-medium">{user.first_name || 'Not set'}</p>
                  </div>
                  <div>
                    <label className="text-gray-500">Last Name</label>
                    <p className="font-medium">{user.last_name || 'Not set'}</p>
                  </div>
                </div>

                <div className="text-sm">
                  <label className="text-gray-500">Member Since</label>
                  <p className="font-medium">{new Date(user.created_at).toLocaleDateString()}</p>
                </div>

                <div className="flex space-x-2 pt-3 border-t">
                  <button
                    onClick={() => setIsEditing(true)}
                    className="flex-1 bg-blue-600 text-white px-3 py-2 rounded-md text-sm hover:bg-blue-700 transition-colors flex items-center justify-center space-x-1"
                  >
                    <EditIcon className="w-4 h-4" />
                    <span>Edit Profile</span>
                  </button>
                  <button
                    onClick={onLogout}
                    className="flex-1 bg-gray-100 text-gray-700 px-3 py-2 rounded-md text-sm hover:bg-gray-200 transition-colors flex items-center justify-center space-x-1"
                  >
                    <LogoutIcon className="w-4 h-4" />
                    <span>Logout</span>
                  </button>
                </div>
              </div>
            ) : (
              // Profile Edit Mode
              <form onSubmit={handleSubmit} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">First Name</label>
                    <input
                      type="text"
                      name="first_name"
                      value={formData.first_name}
                      onChange={handleChange}
                      className="w-full p-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Last Name</label>
                    <input
                      type="text"
                      name="last_name"
                      value={formData.last_name}
                      onChange={handleChange}
                      className="w-full p-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Username</label>
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    className="w-full p-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Email</label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className="w-full p-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {error && (
                  <div className="p-2 bg-red-50 text-red-700 text-sm rounded-md">{error}</div>
                )}

                {success && (
                  <div className="p-2 bg-green-50 text-green-700 text-sm rounded-md">{success}</div>
                )}

                <div className="flex space-x-2 pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditing(false);
                      setError(null);
                      setSuccess(null);
                    }}
                    className="flex-1 bg-gray-100 text-gray-700 px-3 py-2 rounded-md text-sm hover:bg-gray-200 transition-colors"
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

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  // Helper function to determine if a link is active
  const isActiveLink = (path: string) => {
    return location.pathname === path;
  };

  // Navigation link styling
  const getLinkClassName = (path: string) => {
    const baseClasses = "inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors";
    const activeClasses = "border-blue-500 text-blue-600";
    const inactiveClasses = "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700";

    return `${baseClasses} ${isActiveLink(path) ? activeClasses : inactiveClasses}`;
  };

  if (!currentUser) {
    return null; // or redirect to login
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <span className="text-xl font-bold text-blue-600 flex items-center space-x-2">
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
            <div className="flex sm:ml-6 sm:items-center">
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
