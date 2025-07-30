import React, { useState, useEffect } from 'react';
import { User, CreateUserRequest, UpdateUserRequest } from '../../types/user';
import { userService } from '../../services/user.service';

interface UnifiedUserModalProps {
  isOpen: boolean;
  onClose: () => void;
  user?: User;
  onUserSaved: () => void;
}

interface PermissionSetting {
  key: keyof User['permissions'];
  label: string;
  description: string;
  category: string;
}

const PERMISSION_SETTINGS: PermissionSetting[] = [
  {
    key: 'canViewCameras',
    label: 'View Cameras',
    description: 'Access camera feeds and status',
    category: 'Camera Management'
  },
  {
    key: 'canControlCameras',
    label: 'Control Cameras',
    description: 'Start, stop, and configure cameras',
    category: 'Camera Management'
  },
  {
    key: 'canViewAlerts',
    label: 'View Alerts',
    description: 'Access alert notifications and history',
    category: 'Alert Management'
  },
  {
    key: 'canManageAlerts',
    label: 'Manage Alerts',
    description: 'Acknowledge, resolve, and dismiss alerts',
    category: 'Alert Management'
  },
  {
    key: 'canViewAnalytics',
    label: 'View Analytics',
    description: 'Access analytics dashboards and reports',
    category: 'Analytics'
  },
  {
    key: 'canManageUsers',
    label: 'Manage Users',
    description: 'Create, update, and delete user accounts',
    category: 'User Management'
  },
  {
    key: 'canManageSystem',
    label: 'Manage System',
    description: 'Configure system settings and maintenance',
    category: 'System Administration'
  },
  {
    key: 'canExportData',
    label: 'Export Data',
    description: 'Export alerts, analytics, and system data',
    category: 'Data Access'
  }
];

const ROLE_DEFAULTS: Record<User['role'], User['permissions']> = {
  viewer: {
    canViewCameras: true,
    canControlCameras: false,
    canViewAlerts: true,
    canManageAlerts: false,
    canViewAnalytics: false,
    canManageUsers: false,
    canManageSystem: false,
    canExportData: false
  },
  user: {
    canViewCameras: true,
    canControlCameras: false,
    canViewAlerts: true,
    canManageAlerts: true,
    canViewAnalytics: true,
    canManageUsers: false,
    canManageSystem: false,
    canExportData: false
  },
  admin: {
    canViewCameras: true,
    canControlCameras: true,
    canViewAlerts: true,
    canManageAlerts: true,
    canViewAnalytics: true,
    canManageUsers: true,
    canManageSystem: true,
    canExportData: true
  }
};

export const UnifiedUserModal: React.FC<UnifiedUserModalProps> = ({
  isOpen,
  onClose,
  user,
  onUserSaved
}) => {
  const [activeTab, setActiveTab] = useState<'details' | 'permissions'>('details');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // User details form state
  const [formData, setFormData] = useState<CreateUserRequest>({
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'user',
  });

  // Permission management state
  const [permissions, setPermissions] = useState<User['permissions']>(ROLE_DEFAULTS.user);
  const [useRoleDefaults, setUseRoleDefaults] = useState(true);

  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username,
        email: user.email,
        password: '',
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        role: user.role,
      });
      setPermissions(user.permissions);
      const defaultPerms = ROLE_DEFAULTS[user.role];
      setUseRoleDefaults(JSON.stringify(user.permissions) === JSON.stringify(defaultPerms));
    } else {
      setFormData({
        username: '',
        email: '',
        password: '',
        first_name: '',
        last_name: '',
        role: 'user',
      });
      setPermissions(ROLE_DEFAULTS.user);
      setUseRoleDefaults(true);
    }
    setError(null);
  }, [user, isOpen]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // If role changes, update permissions if using defaults
    if (name === 'role' && useRoleDefaults) {
      setPermissions(ROLE_DEFAULTS[value as User['role']]);
    }
  };

  const handlePermissionToggle = (permissionKey: keyof User['permissions']) => {
    const newPermissions = {
      ...permissions,
      [permissionKey]: !permissions[permissionKey]
    };
    setPermissions(newPermissions);
    setUseRoleDefaults(false);
  };

  const handleUseDefaultsToggle = (useDefaults: boolean) => {
    setUseRoleDefaults(useDefaults);
    if (useDefaults) {
      setPermissions(ROLE_DEFAULTS[formData.role]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      let savedUser: User;

      if (user) {
        // Update existing user - prepare update data without password if empty
        const updateData: UpdateUserRequest = {
          username: formData.username,
          email: formData.email,
          first_name: formData.first_name,
          last_name: formData.last_name,
          role: formData.role
        };

        // Only include password if it's provided
        if (formData.password) {
          updateData.password = formData.password;
        }

        savedUser = await userService.updateUser(user.id, updateData);
        // Update permissions separately
        savedUser = await userService.updateUserPermissions(user.id, permissions);
      } else {
        // Create new user
        savedUser = await userService.createUser({
          ...formData,
          permissions: useRoleDefaults ? undefined : permissions
        } as CreateUserRequest);
      }

      onUserSaved();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Get effective permissions for display
  const effectivePermissions = useRoleDefaults ? ROLE_DEFAULTS[formData.role] : permissions;

  // Group permissions by category
  const permissionsByCategory = PERMISSION_SETTINGS.reduce((acc, setting) => {
    if (!acc[setting.category]) {
      acc[setting.category] = [];
    }
    acc[setting.category].push(setting);
    return acc;
  }, {} as Record<string, PermissionSetting[]>);

  const activePermissions = Object.values(effectivePermissions).filter(Boolean).length;
  const totalPermissions = Object.keys(effectivePermissions).length;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            {user ? `Edit User - ${user.username}` : 'Create New User'}
          </h2>

          {/* Tab Navigation */}
          <div className="mt-4 border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('details')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'details'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                User Details
              </button>
              <button
                onClick={() => setActiveTab('permissions')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'permissions'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Permissions ({activePermissions}/{totalPermissions})
              </button>
            </nav>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-240px)]">
            {error && (
              <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            {/* User Details Tab */}
            {activeTab === 'details' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Username *
                    </label>
                    <input
                      type="text"
                      name="username"
                      value={formData.username}
                      onChange={handleInputChange}
                      required
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email *
                    </label>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleInputChange}
                      required
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      First Name
                    </label>
                    <input
                      type="text"
                      name="first_name"
                      value={formData.first_name}
                      onChange={handleInputChange}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Last Name
                    </label>
                    <input
                      type="text"
                      name="last_name"
                      value={formData.last_name}
                      onChange={handleInputChange}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Role *
                    </label>
                    <select
                      name="role"
                      value={formData.role}
                      onChange={handleInputChange}
                      required
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="viewer">Viewer - Read-only access</option>
                      <option value="user">User - Standard access</option>
                      <option value="admin">Admin - Full access</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {user ? 'New Password (leave blank to keep current)' : 'Password *'}
                    </label>
                    <input
                      type="password"
                      name="password"
                      value={formData.password}
                      onChange={handleInputChange}
                      required={!user}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>

                {/* Role Description */}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Role Description</h4>
                  <p className="text-sm text-gray-600">
                    {formData.role === 'admin' && 'Full system access including user management and system configuration.'}
                    {formData.role === 'user' && 'Standard user with camera viewing, alert management, and analytics access.'}
                    {formData.role === 'viewer' && 'Read-only access to cameras and alerts. Limited system visibility.'}
                  </p>
                </div>
              </div>
            )}

            {/* Permissions Tab */}
            {activeTab === 'permissions' && (
              <div className="space-y-6">
                {/* Permission Configuration Options */}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Permission Configuration</h3>

                  <div className="space-y-3">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="permissionMode"
                        checked={useRoleDefaults}
                        onChange={() => handleUseDefaultsToggle(true)}
                        className="text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">
                        Use role defaults ({Object.values(ROLE_DEFAULTS[formData.role]).filter(Boolean).length} permissions)
                      </span>
                    </label>

                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="permissionMode"
                        checked={!useRoleDefaults}
                        onChange={() => handleUseDefaultsToggle(false)}
                        className="text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">
                        Custom permissions ({activePermissions} of {totalPermissions} enabled)
                      </span>
                    </label>
                  </div>
                </div>

                {/* Permission Categories */}
                {Object.entries(permissionsByCategory).map(([category, settings]) => (
                  <div key={category} className="mb-6">
                    <h4 className="text-md font-medium text-gray-900 mb-3">{category}</h4>

                    <div className="space-y-2">
                      {settings.map((setting) => {
                        const isEnabled = effectivePermissions[setting.key];
                        const isFromRole = useRoleDefaults;

                        return (
                          <div
                            key={setting.key}
                            className={`flex items-center justify-between p-3 border rounded-lg ${
                              isEnabled
                                ? isFromRole
                                  ? 'bg-blue-50 border-blue-200'
                                  : 'bg-green-50 border-green-200'
                                : 'bg-gray-50 border-gray-200'
                            }`}
                          >
                            <div className="flex items-center">
                              <input
                                type="checkbox"
                                checked={isEnabled}
                                onChange={() => handlePermissionToggle(setting.key)}
                                disabled={useRoleDefaults}
                                className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                              />
                              <div className="ml-3">
                                <div className={`text-sm font-medium ${
                                  isEnabled ? 'text-gray-900' : 'text-gray-500'
                                }`}>
                                  {setting.label}
                                </div>
                                <div className="text-xs text-gray-500 mt-1">
                                  {setting.description}
                                </div>
                              </div>
                            </div>

                            <div className="flex items-center space-x-2">
                              {isFromRole && (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                  Role Default
                                </span>
                              )}
                              {!isFromRole && isEnabled && (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  Custom
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Saving...' : (user ? 'Update User' : 'Create User')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
