import React, { useState } from 'react';
import { User } from '../../types/user';
import { userService } from '../../services/user.service';

interface SimplePermissionManagerProps {
  user: User;
  onUserUpdate: (updatedUser: User) => void;
  onClose: () => void;
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
  admin: {
    canViewCameras: true,
    canControlCameras: true,
    canViewAlerts: true,
    canManageAlerts: true,
    canViewAnalytics: true,
    canManageUsers: true,
    canManageSystem: true,
    canExportData: true
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
  viewer: {
    canViewCameras: true,
    canControlCameras: false,
    canViewAlerts: true,
    canManageAlerts: false,
    canViewAnalytics: false,
    canManageUsers: false,
    canManageSystem: false,
    canExportData: false
  }
};

export const SimplePermissionManager: React.FC<SimplePermissionManagerProps> = ({
  user,
  onUserUpdate,
  onClose
}) => {
  const [selectedRole, setSelectedRole] = useState<User['role']>(user.role);
  const [permissions, setPermissions] = useState<User['permissions']>(user.permissions);
  const [loading, setLoading] = useState(false);
  const [useRoleDefaults, setUseRoleDefaults] = useState(true);

  // Get effective permissions (role defaults or custom)
  const effectivePermissions = useRoleDefaults
    ? ROLE_DEFAULTS[selectedRole]
    : permissions;

  const handleRoleChange = (newRole: User['role']) => {
    setSelectedRole(newRole);
    if (useRoleDefaults) {
      setPermissions(ROLE_DEFAULTS[newRole]);
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
      setPermissions(ROLE_DEFAULTS[selectedRole]);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      // Update user role
      await userService.updateUser(user.id, {
        role: selectedRole
      });

      // Update permissions
      const finalUser = await userService.updateUserPermissions(user.id, effectivePermissions);

      onUserUpdate(finalUser);
      onClose();
    } catch (error) {
      console.error('Failed to update user permissions:', error);
    } finally {
      setLoading(false);
    }
  };

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

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-900">
            Manage Permissions - {user.username}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          {/* Role Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              User Role
            </label>
            <select
              value={selectedRole}
              onChange={(e) => handleRoleChange(e.target.value as User['role'])}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="viewer">Viewer - Read-only access</option>
              <option value="user">User - Standard access with limited controls</option>
              <option value="admin">Admin - Full system access</option>
            </select>
          </div>

          {/* Permission Configuration Options */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
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
                  Use role defaults ({Object.values(ROLE_DEFAULTS[selectedRole]).filter(Boolean).length} permissions)
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
              <h3 className="text-lg font-medium text-gray-900 mb-3">{category}</h3>

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

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
};
