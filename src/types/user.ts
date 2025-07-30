export interface User {
  id: string;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role: 'admin' | 'user' | 'viewer';
  is_active: boolean;
  is_verified: boolean;
  permissions: {
    canViewCameras: boolean;
    canControlCameras: boolean;
    canViewAlerts: boolean;
    canManageAlerts: boolean;
    canViewAnalytics: boolean;
    canManageUsers: boolean;
    canManageSystem: boolean;
    canExportData: boolean;
  };
  created_at: string;
  updated_at: string;
  last_login_at?: string;
  last_activity_at?: string;
  avatar_url?: string;
}

export interface UserSettings {
  notifications: {
    email: boolean;
    push: boolean;
    alerts: boolean;
  };
  theme: 'light' | 'dark';
  language: 'en' | 'es' | 'fr';
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  role: 'admin' | 'user' | 'viewer';
  permissions?: Partial<User['permissions']>;
}

export interface UpdateUserRequest {
  username?: string;
  email?: string;
  password?: string;
  first_name?: string;
  last_name?: string;
  role?: 'admin' | 'user' | 'viewer';
  is_active?: boolean;
  permissions?: Partial<User['permissions']>;
}
