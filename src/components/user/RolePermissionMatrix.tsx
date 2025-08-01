import React from 'react';
import { User } from '../../types/user';
import { useThemeClasses } from '../../contexts/ThemeContext';

interface RolePermissionMatrixProps {
  onClose: () => void;
}

interface PermissionDefinition {
  key: keyof User['permissions'];
  label: string;
  description: string;
  category: string;
}

const PERMISSION_DEFINITIONS: PermissionDefinition[] = [
  {
    key: 'canViewCameras',
    label: 'View Cameras',
    description: 'Access camera feeds and status information',
    category: 'Camera Management'
  },
  {
    key: 'canControlCameras',
    label: 'Control Cameras',
    description: 'Start, stop, and configure camera operations',
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

const ROLE_PERMISSIONS: Record<User['role'], User['permissions']> = {
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

const ROLE_DESCRIPTIONS: Record<User['role'], string> = {
  viewer: 'Read-only access to cameras and alerts. Limited system visibility.',
  user: 'Standard user with camera viewing, alert management, and analytics access.',
  admin: 'Full system access including user management and system configuration.'
};

export const RolePermissionMatrix: React.FC<RolePermissionMatrixProps> = ({ onClose }) => {
  const themeClasses = useThemeClasses();
  const roles: User['role'][] = ['viewer', 'user', 'admin'];

  // Group permissions by category
  const permissionsByCategory = PERMISSION_DEFINITIONS.reduce((acc, permission) => {
    if (!acc[permission.category]) {
      acc[permission.category] = [];
    }
    acc[permission.category].push(permission);
    return acc;
  }, {} as Record<string, PermissionDefinition[]>);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className={`${themeClasses.bg.primary} rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden`}>
        <div className={`px-6 py-4 border-b ${themeClasses.border.primary} flex justify-between items-center`}>
          <div>
            <h2 className={`text-xl font-semibold ${themeClasses.text.primary}`}>
              Role Permission Matrix
            </h2>
            <p className={`text-sm ${themeClasses.text.secondary} mt-1`}>
              Overview of default permissions for each user role
            </p>
          </div>
          <button
            onClick={onClose}
            className={`${themeClasses.text.secondary} hover:${themeClasses.text.primary} text-2xl font-bold`}
          >
            ×
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          {/* Role Descriptions */}
          <div className="mb-8">
            <h3 className={`text-lg font-medium ${themeClasses.text.primary} mb-4`}>Role Descriptions</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {roles.map((role) => (
                <div key={role} className={`p-4 border rounded-lg ${themeClasses.bg.secondary} ${themeClasses.border.primary}`}>
                  <h4 className={`text-md font-medium ${themeClasses.text.primary} capitalize mb-2`}>
                    {role}
                  </h4>
                  <p className={`text-sm ${themeClasses.text.secondary}`}>
                    {ROLE_DESCRIPTIONS[role]}
                  </p>
                  <div className={`mt-2 text-xs ${themeClasses.text.tertiary}`}>
                    {Object.values(ROLE_PERMISSIONS[role]).filter(Boolean).length} permissions enabled
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Permission Matrix */}
          <div className="mb-6">
            <h3 className={`text-lg font-medium ${themeClasses.text.primary} mb-4`}>Permission Matrix</h3>

            {Object.entries(permissionsByCategory).map(([category, permissions]) => (
              <div key={category} className="mb-8">
                <h4 className={`text-md font-medium ${themeClasses.text.primary} mb-3`}>{category}</h4>

                <div className="overflow-x-auto">
                  <table className={`min-w-full border ${themeClasses.border.primary} rounded-lg`}>
                    <thead className={themeClasses.bg.secondary}>
                      <tr>
                        <th className={`px-4 py-3 text-left text-xs font-medium ${themeClasses.text.secondary} uppercase tracking-wider border-r ${themeClasses.border.primary}`}>
                          Permission
                        </th>
                        {roles.map((role) => (
                          <th
                            key={role}
                            className={`px-4 py-3 text-center text-xs font-medium ${themeClasses.text.secondary} uppercase tracking-wider border-r ${themeClasses.border.primary} last:border-r-0`}
                          >
                            {role}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className={`${themeClasses.bg.primary} divide-y ${themeClasses.border.primary}`}>
                      {permissions.map((permission) => (
                        <tr key={permission.key} className={`hover:${themeClasses.bg.secondary}`}>
                          <td className={`px-4 py-3 border-r ${themeClasses.border.primary}`}>
                            <div>
                              <div className={`text-sm font-medium ${themeClasses.text.primary}`}>
                                {permission.label}
                              </div>
                              <div className={`text-xs ${themeClasses.text.secondary} mt-1`}>
                                {permission.description}
                              </div>
                            </div>
                          </td>
                          {roles.map((role) => {
                            const hasPermission = ROLE_PERMISSIONS[role][permission.key];
                            return (
                              <td
                                key={role}
                                className={`px-4 py-3 text-center border-r ${themeClasses.border.primary} last:border-r-0`}
                              >
                                <div className={`inline-flex items-center justify-center w-6 h-6 rounded-full ${
                                  hasPermission
                                    ? 'bg-green-100 dark:bg-green-900/20 text-green-600 dark:text-green-400'
                                    : 'bg-red-100 dark:bg-red-900/20 text-red-600 dark:text-red-400'
                                }`}>
                                  {hasPermission ? '✓' : '✗'}
                                </div>
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className={`px-6 py-4 border-t ${themeClasses.border.primary} flex justify-end`}>
          <button
            onClick={onClose}
            className={`px-4 py-2 border ${themeClasses.border.primary} rounded-md text-sm font-medium ${themeClasses.text.secondary} ${themeClasses.bg.primary} hover:${themeClasses.bg.secondary} focus:outline-none focus:ring-2 focus:ring-blue-500`}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
