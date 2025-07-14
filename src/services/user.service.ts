import { apiService } from './api.service';
import { User, CreateUserRequest, UpdateUserRequest } from '../types';

export interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface UserListParams {
  page?: number;
  per_page?: number;
  search?: string;
  role?: string;
  is_active?: boolean;
}

class UserService {
  private static instance: UserService;

  public static getInstance(): UserService {
    if (!UserService.instance) {
      UserService.instance = new UserService();
    }
    return UserService.instance;
  }

  async getUsers(params: UserListParams = {}): Promise<UserListResponse> {
    const searchParams = new URLSearchParams();
    
    if (params.page) searchParams.append('page', params.page.toString());
    if (params.per_page) searchParams.append('per_page', params.per_page.toString());
    if (params.search) searchParams.append('search', params.search);
    if (params.role) searchParams.append('role', params.role);
    if (params.is_active !== undefined) searchParams.append('is_active', params.is_active.toString());

    const queryString = searchParams.toString();
    const url = queryString ? `/api/users/?${queryString}` : '/api/users/';
    
    return await apiService.get<UserListResponse>(url);
  }

  async getUserById(id: string): Promise<User> {
    return await apiService.get<User>(`/api/users/${id}`);
  }

  async createUser(userData: CreateUserRequest): Promise<User> {
    return await apiService.post<User>('/api/users/', userData);
  }

  async updateUser(id: string, userData: UpdateUserRequest): Promise<User> {
    return await apiService.patch<User>(`/api/users/${id}`, userData);
  }

  async deleteUser(id: string): Promise<void> {
    await apiService.delete(`/api/users/${id}`);
  }

  async changePassword(id: string, newPassword: string): Promise<void> {
    await apiService.post(`/api/users/${id}/change-password`, {
      new_password: newPassword
    });
  }

  async resetPassword(id: string): Promise<{ temporary_password: string }> {
    return await apiService.post<{ temporary_password: string }>(`/api/users/${id}/reset-password`, {});
  }

  async updateUserStatus(id: string, isActive: boolean): Promise<User> {
    return await apiService.patch<User>(`/api/users/${id}`, {
      is_active: isActive
    });
  }

  async updateUserPermissions(id: string, permissions: Partial<User['permissions']>): Promise<User> {
    return await apiService.patch<User>(`/api/users/${id}`, {
      permissions
    });
  }

  getDefaultPermissionsByRole(role: 'admin' | 'user' | 'viewer'): User['permissions'] {
    const defaultPermissions = {
      canViewCameras: false,
      canControlCameras: false,
      canViewAlerts: false,
      canManageAlerts: false,
      canViewAnalytics: false,
      canManageUsers: false,
      canManageSystem: false,
      canExportData: false,
    };

    switch (role) {
      case 'admin':
        return {
          ...defaultPermissions,
          canViewCameras: true,
          canControlCameras: true,
          canViewAlerts: true,
          canManageAlerts: true,
          canViewAnalytics: true,
          canManageUsers: true,
          canManageSystem: true,
          canExportData: true,
        };
      case 'user':
        return {
          ...defaultPermissions,
          canViewCameras: true,
          canViewAlerts: true,
          canManageAlerts: true,
          canExportData: true,
        };
      case 'viewer':
        return {
          ...defaultPermissions,
          canViewCameras: true,
          canViewAlerts: true,
        };
      default:
        return defaultPermissions;
    }
  }
}

export const userService = UserService.getInstance();
