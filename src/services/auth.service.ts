import { User } from '../types';
import { apiService } from './api.service';

const TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const TOKEN_EXPIRY_KEY = 'token_expiry';
const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes in milliseconds

interface LoginCredentials {
  username: string;
  password: string;
}

interface RegisterCredentials extends LoginCredentials {
  email: string;
}

interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user?: User;
}

class AuthService {
  private static instance: AuthService;
  private currentUser: User | null = null;
  private refreshTimeout: NodeJS.Timeout | null = null;

  private constructor() {
    this.initializeSession();
    
    // Make debug function available globally for testing
    if (typeof window !== 'undefined') {
      (window as any).debugAuth = () => this.debugLocalStorage();
    }
  }

  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  private initializeSession(): void {
    const token = this.getToken();
    if (token) {
      apiService.setAuthToken(token);
      try {
        const userData = this.parseJwt(token);
        this.currentUser = userData;
        this.setupRefreshTimeout();
      } catch (error) {
        this.clearSession();
      }
    }
  }

  private setupRefreshTimeout(): void {
    if (this.refreshTimeout) {
      clearTimeout(this.refreshTimeout);
    }

    const expiryTime = this.getTokenExpiry();
    if (expiryTime) {
      const timeUntilExpiry = expiryTime - Date.now();
      if (timeUntilExpiry > 0) {
        this.refreshTimeout = setTimeout(
          () => this.refreshToken(),
          timeUntilExpiry - 5 * 60 * 1000
        );
      } else {
        this.clearSession();
      }
    }
  }

  private parseJwt(token: string): User {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      const payload = JSON.parse(jsonPayload);
      
      // Extract user data from JWT payload
      // Handle case where JWT contains minimal info (sub = username, role)
      const username = payload.sub || payload.username || 'unknown';
      const role = payload.role || 'viewer';
      
      return {
        id: payload.user_id || payload.sub || username,
        username: username,
        email: payload.email || `${username}@localhost`,
        first_name: payload.first_name || undefined,
        last_name: payload.last_name || undefined,
        role: role,
        is_active: payload.is_active !== false,
        is_verified: payload.is_verified !== false,
        permissions: payload.permissions || this.getDefaultPermissions(role),
        created_at: payload.created_at || new Date().toISOString(),
        updated_at: payload.updated_at || new Date().toISOString(),
        last_login_at: payload.last_login_at || undefined,
        last_activity_at: payload.last_activity_at || undefined,
        avatar_url: payload.avatar_url || undefined,
      };
    } catch (error) {
      throw new Error('Invalid token');
    }
  }

  public async login(credentials: LoginCredentials): Promise<User | null> {
    try {
      const response = await apiService.post<AuthResponse>('/api/auth/login', credentials);
      
      // Store refresh token if provided
      if (response.refresh_token) {
        localStorage.setItem(REFRESH_TOKEN_KEY, response.refresh_token);
      }
      
      this.setSessionFromToken(response.access_token);
      
      return this.currentUser;
    } catch (error) {
      console.error('Login failed:', error);
      this.clearSession();
      throw error;
    }
  }

  public async register(credentials: RegisterCredentials): Promise<User | null> {
    try {
      const response = await apiService.post<AuthResponse>('/auth/register', credentials);
      this.setSessionFromToken(response.access_token);
      return this.currentUser;
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  public async refreshToken(): Promise<void> {
    try {
      const refreshToken = this.getRefreshToken();
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await apiService.post<AuthResponse>('/api/auth/refresh', {
        refreshToken,
      });
      this.setSessionFromToken(response.access_token);
    } catch (error) {
      this.clearSession();
      throw error;
    }
  }

  public async requestPasswordReset(email: string): Promise<void> {
    try {
      await apiService.post('/auth/password-reset-request', { email });
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  public async resetPassword(token: string, newPassword: string): Promise<void> {
    try {
      await apiService.post('/auth/password-reset-confirm', {
        token,
        new_password: newPassword,
      });
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  public async updateProfile(userData: Partial<User>): Promise<User> {
    try {
      const response = await apiService.put<{ user: User }>('/auth/profile', userData);
      return response.user;
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  public async updatePassword(currentPassword: string, newPassword: string): Promise<void> {
    try {
      await apiService.put('/auth/password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
    } catch (error) {
      throw this.handleAuthError(error);
    }
  }

  public logout(): void {
    this.clearSession();
    window.location.href = '/login';
  }

  public getCurrentUser(): User | null {
    return this.currentUser;
  }

  public isAuthenticated(): boolean {
    const token = this.getToken();
    const expiryTime = this.getTokenExpiry();
    return !!token && !!expiryTime && expiryTime > Date.now();
  }

  private getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  private getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  private getTokenExpiry(): number | null {
    const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
    return expiry ? parseInt(expiry, 10) : null;
  }

  private setSessionFromToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
    const expiryTime = Date.now() + SESSION_TIMEOUT;
    localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
    
    try {
      const userData = this.parseJwt(token);
      this.currentUser = userData;
      
      apiService.setAuthToken(token);
      
      this.setupRefreshTimeout();
    } catch (error) {
      console.error('Error setting session:', error);
      this.clearSession();
      throw error;
    }
  }

  private clearSession(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
    if (this.refreshTimeout) {
      clearTimeout(this.refreshTimeout);
      this.refreshTimeout = null;
    }
    this.currentUser = null;
    apiService.removeAuthToken();
  }

  private getDefaultPermissions(role: string) {
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

  private handleAuthError(error: unknown): Error {
    if (error && typeof error === 'object' && 'response' in error) {
      const response = (error as { response?: { data?: { message?: string } } }).response;
      if (response?.data?.message) {
        return new Error(response.data.message);
      }
    }
    return new Error('An unexpected error occurred');
  }

  public debugLocalStorage(): void {
    console.log('🔍 LocalStorage Debug:');
    console.log('  - auth_token:', localStorage.getItem('auth_token') ? 'EXISTS' : 'NOT FOUND');
    console.log('  - refresh_token:', localStorage.getItem('refresh_token') ? 'EXISTS' : 'NOT FOUND');
    console.log('  - token_expiry:', localStorage.getItem('token_expiry'));
    console.log('  - All localStorage keys:', Object.keys(localStorage));
    
    // Check if auth_token exists and is valid
    const token = localStorage.getItem('auth_token');
    if (token) {
      console.log('  - Token preview:', token.substring(0, 50) + '...');
      try {
        // Parse raw JWT payload
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
          atob(base64)
            .split('')
            .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
            .join('')
        );
        const payload = JSON.parse(jsonPayload);
        console.log('  - Token payload:', { 
          username: payload.sub, 
          role: payload.role, 
          exp: new Date(payload.exp * 1000),
          type: payload.type 
        });
      } catch (error) {
        console.log('  - Token parse error:', error);
      }
    }
  }
}

export const authService = AuthService.getInstance();
