import React from 'react';
import { usePermissions, Permission } from '../../hooks/usePermissions';

interface PermissionGateProps {
  permission?: Permission;
  permissions?: Permission[];
  requireAll?: boolean; // Whether to require all permissions (default: false, requires any)
  role?: string;
  fallback?: React.ReactNode;
  children: React.ReactNode;
  showFallback?: boolean; // Whether to show fallback or nothing when access denied
}

export const PermissionGate: React.FC<PermissionGateProps> = ({
  permission,
  permissions = [],
  requireAll = false,
  role,
  fallback = null,
  children,
  showFallback = false,
}) => {
  const { hasPermission, hasAnyPermission, hasAllPermissions, isAdmin } = usePermissions();

  // Admin bypass
  if (isAdmin) {
    return <>{children}</>;
  }

  // Role-based check
  if (role) {
    // This is a simple role check - you might want to get user role from auth service
    // For now, we'll skip this as it requires more auth integration
  }

  // Permission-based checks
  let hasAccess = false;

  if (permission) {
    hasAccess = hasPermission(permission);
  } else if (permissions.length > 0) {
    hasAccess = requireAll
      ? hasAllPermissions(permissions)
      : hasAnyPermission(permissions);
  } else {
    // No permissions specified, allow access
    hasAccess = true;
  }

  if (hasAccess) {
    return <>{children}</>;
  }

  return showFallback ? <>{fallback}</> : null;
};

// Convenience components for common use cases
export const AdminOnly: React.FC<{
  children: React.ReactNode;
  fallback?: React.ReactNode;
}> = ({ children, fallback = null }) => {
  const { isAdmin } = usePermissions();
  return isAdmin ? <>{children}</> : <>{fallback}</>;
};

export const CameraViewGate: React.FC<{
  children: React.ReactNode;
  fallback?: React.ReactNode;
}> = ({ children, fallback = null }) => (
  <PermissionGate
    permission={Permission.CAMERA_VIEW}
    fallback={fallback}
    showFallback={!!fallback}
  >
    {children}
  </PermissionGate>
);

export const CameraControlGate: React.FC<{
  children: React.ReactNode;
  fallback?: React.ReactNode;
}> = ({ children, fallback = null }) => (
  <PermissionGate
    permission={Permission.CAMERA_CONTROL}
    fallback={fallback}
    showFallback={!!fallback}
  >
    {children}
  </PermissionGate>
);

export const UserManagementGate: React.FC<{
  children: React.ReactNode;
  fallback?: React.ReactNode;
}> = ({ children, fallback = null }) => (
  <PermissionGate
    permissions={[Permission.USER_VIEW, Permission.USER_CREATE, Permission.USER_UPDATE]}
    fallback={fallback}
    showFallback={!!fallback}
  >
    {children}
  </PermissionGate>
);

export const AlertManagementGate: React.FC<{
  children: React.ReactNode;
  fallback?: React.ReactNode;
}> = ({ children, fallback = null }) => (
  <PermissionGate
    permissions={[Permission.ALERT_VIEW, Permission.ALERT_ACKNOWLEDGE]}
    fallback={fallback}
    showFallback={!!fallback}
  >
    {children}
  </PermissionGate>
);

// Higher-order component version
export const withPermission = <P extends object>(
  Component: React.ComponentType<P>,
  permission: Permission,
  fallback?: React.ReactNode
) => {
  return (props: P) => (
    <PermissionGate permission={permission} fallback={fallback} showFallback={!!fallback}>
      <Component {...props} />
    </PermissionGate>
  );
};

export default PermissionGate;
