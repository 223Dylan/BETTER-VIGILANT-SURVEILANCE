import { useState, useEffect } from 'react';
import { authService } from '../services/auth.service';
import { User } from '../types';

// Permission enumeration matching backend
export enum Permission {
  // Camera permissions
  CAMERA_VIEW = 'camera:view',
  CAMERA_CREATE = 'camera:create',
  CAMERA_UPDATE = 'camera:update',
  CAMERA_DELETE = 'camera:delete',
  CAMERA_CONTROL = 'camera:control',
  CAMERA_STREAM = 'camera:stream',
  CAMERA_CONFIG = 'camera:config',

  // Alert permissions
  ALERT_VIEW = 'alert:view',
  ALERT_CREATE = 'alert:create',
  ALERT_ACKNOWLEDGE = 'alert:acknowledge',
  ALERT_RESOLVE = 'alert:resolve',
  ALERT_DELETE = 'alert:delete',
  ALERT_EXPORT = 'alert:export',

  // User permissions
  USER_VIEW = 'user:view',
  USER_CREATE = 'user:create',
  USER_UPDATE = 'user:update',
  USER_DELETE = 'user:delete',
  USER_MANAGE_ROLES = 'user:manage_roles',
  USER_MANAGE_PERMISSIONS = 'user:manage_permissions',

  // System permissions
  SYSTEM_CONFIG = 'system:config',
  SYSTEM_LOGS = 'system:logs',
  SYSTEM_METRICS = 'system:metrics',
  SYSTEM_BACKUP = 'system:backup',
  SYSTEM_MAINTENANCE = 'system:maintenance',

  // Analytics permissions
  ANALYTICS_VIEW = 'analytics:view',
  ANALYTICS_EXPORT = 'analytics:export',
  ANALYTICS_REPORTS = 'analytics:reports',

  // Security permissions
  SECURITY_AUDIT = 'security:audit',
  SECURITY_CONFIG = 'security:config',
}

// Role-based permission mappings
export const ROLE_PERMISSIONS: Record<string, Permission[]> = {
  admin: Object.values(Permission), // Admin has all permissions
  operator: [
    Permission.CAMERA_VIEW,
    Permission.CAMERA_UPDATE,
    Permission.CAMERA_CONTROL,
    Permission.CAMERA_STREAM,
    Permission.CAMERA_CONFIG,
    Permission.ALERT_VIEW,
    Permission.ALERT_ACKNOWLEDGE,
    Permission.ALERT_RESOLVE,
    Permission.ALERT_EXPORT,
    Permission.USER_VIEW,
    Permission.SYSTEM_METRICS,
    Permission.ANALYTICS_VIEW,
    Permission.ANALYTICS_EXPORT,
  ],
  user: [
    Permission.CAMERA_VIEW,
    Permission.CAMERA_STREAM,
    Permission.ALERT_VIEW,
    Permission.ALERT_ACKNOWLEDGE,
    Permission.USER_VIEW,
    Permission.SYSTEM_METRICS,
    Permission.ANALYTICS_VIEW,
  ],
  viewer: [
    Permission.CAMERA_VIEW,
    Permission.CAMERA_STREAM,
    Permission.ALERT_VIEW,
    Permission.USER_VIEW,
    Permission.ANALYTICS_VIEW,
  ],
};

export interface PermissionHook {
  hasPermission: (permission: Permission) => boolean;
  hasAnyPermission: (permissions: Permission[]) => boolean;
  hasAllPermissions: (permissions: Permission[]) => boolean;
  userPermissions: Permission[];
  isAdmin: boolean;
  canAccessRoute: (requiredPermissions: Permission[]) => boolean;
}

export const usePermissions = (): PermissionHook => {
  const [user, setUser] = useState<User | null>(authService.getCurrentUser());

  useEffect(() => {
    const currentUser = authService.getCurrentUser();
    setUser(currentUser);
  }, []);

  const getUserPermissions = (user: User | null): Permission[] => {
    if (!user) return [];

    // Admin has all permissions
    if (user.role === 'admin') {
      return Object.values(Permission);
    }

    // Get role-based permissions
    const rolePermissions = ROLE_PERMISSIONS[user.role] || [];

    // Merge with custom user permissions
    const customPermissions: Permission[] = [];
    if (user.permissions) {
      Object.entries(user.permissions).forEach(([key, value]) => {
        if (value && Object.values(Permission).includes(key as Permission)) {
          customPermissions.push(key as Permission);
        }
      });
    }

    // Combine role and custom permissions (remove duplicates)
    const allPermissions = [...rolePermissions, ...customPermissions];
    return Array.from(new Set(allPermissions));
  };

  const userPermissions = getUserPermissions(user);

  const hasPermission = (permission: Permission): boolean => {
    if (!user) return false;
    return userPermissions.includes(permission);
  };

  const hasAnyPermission = (permissions: Permission[]): boolean => {
    if (!user) return false;
    return permissions.some(permission => hasPermission(permission));
  };

  const hasAllPermissions = (permissions: Permission[]): boolean => {
    if (!user) return false;
    return permissions.every(permission => hasPermission(permission));
  };

  const isAdmin = user?.role === 'admin';

  const canAccessRoute = (requiredPermissions: Permission[]): boolean => {
    if (requiredPermissions.length === 0) return true;
    return hasAnyPermission(requiredPermissions);
  };

  return {
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    userPermissions,
    isAdmin,
    canAccessRoute,
  };
};
