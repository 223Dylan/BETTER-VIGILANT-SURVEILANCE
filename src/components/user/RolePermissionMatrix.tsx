import React from 'react';
import { User } from '../../types/user';

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
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Role Permission Matrix
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Overview of default permissions for each user role
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          {/* Role Descriptions */}
          <div className="mb-8">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Role Descriptions</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {roles.map((role) => (
                <div key={role} className="p-4 border rounded-lg bg-gray-50">
                  <h4 className="text-md font-medium text-gray-900 capitalize mb-2">
                    {role}
                  </h4>
                  <p className="text-sm text-gray-600">
                    {ROLE_DESCRIPTIONS[role]}
                  </p>
                  <div className="mt-2 text-xs text-gray-500">
                    {Object.values(ROLE_PERMISSIONS[role]).filter(Boolean).length} permissions enabled
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Permission Matrix */}
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Permission Matrix</h3>

            {Object.entries(permissionsByCategory).map(([category, permissions]) => (
              <div key={category} className="mb-8">
                <h4 className="text-md font-medium text-gray-900 mb-3">{category}</h4>

                <div className="overflow-x-auto">
                  <table className="min-w-full border border-gray-200 rounded-lg">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r">
                          Permission
                        </th>
                        {roles.map((role) => (
                          <th
                            key={role}
                            className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r last:border-r-0"
                          >
                            {role}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {permissions.map((permission) => (
                        <tr key={permission.key} className="hover:bg-gray-50">
                          <td className="px-4 py-3 border-r">
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {permission.label}
                              </div>
                              <div className="text-xs text-gray-500 mt-1">
                                {permission.description}
                              </div>
                            </div>
                          </td>
                          {roles.map((role) => {
                            const hasPermission = ROLE_PERMISSIONS[role][permission.key];
                            return (
                              <td
                                key={role}
                                className="px-4 py-3 text-center border-r last:border-r-0"
                              >
                                <div className="flex justify-center">
                                  {hasPermission ? (
                                    <svg
                                      className="w-5 h-5 text-green-500"
                                      fill="currentColor"
                                      viewBox="0 0 20 20"
                                    >
                                      <path
                                        fillRule="evenodd"
                                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                        clipRule="evenodd"
                                      />
                                    </svg>
                                  ) : (
                                    <svg
                                      className="w-5 h-5 text-red-500"
                                      fill="currentColor"
                                      viewBox="0 0 20 20"
                                    >
                                      <path
                                        fillRule="evenodd"
                                        d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                                        clipRule="evenodd"
                                      />
                                    </svg>
                                  )}
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

          {/* Legend */}
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Legend</h4>
            <div className="flex items-center space-x-6 text-sm">
              <div className="flex items-center">
                <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="text-gray-700">Permission granted by role</span>
              </div>
              <div className="flex items-center">
                <svg className="w-4 h-4 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="text-gray-700">Permission not granted by role</span>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Note: Individual users can have custom permissions that override these defaults
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
