import { Alert } from '../types';
import { apiService } from './api.service';

interface AlertActionResponse {
  success: boolean;
  message: string;
  data?: any;
}

interface BulkActionRequest {
  alert_ids: string[];
  action: 'acknowledge' | 'resolve';
  user_id: string;
  notes?: string;
}

interface BulkActionResult {
  action: string;
  total_requested: number;
  successful: number;
  failed: number;
  success_rate: number;
  successful_alert_ids: string[];
  failed_actions: Array<{ alert_id: string; error: string }>;
  performed_by: string;
  timestamp: number;
}

class AlertService {
  private static instance: AlertService;

  private constructor() {}

  public static getInstance(): AlertService {
    if (!AlertService.instance) {
      AlertService.instance = new AlertService();
    }
    return AlertService.instance;
  }

  /**
   * Get all active alerts
   */
  async getActiveAlerts(): Promise<Alert[]> {
    try {
      const response = await apiService.get<AlertActionResponse>('/api/alerts/active');
      return response.data || [];
    } catch (error) {
      console.error('Error fetching active alerts:', error);
      throw error;
    }
  }

  /**
   * Get alert history
   */
  async getAlertHistory(limit?: number): Promise<Alert[]> {
    try {
      const url = limit ? `/api/alerts/history?limit=${limit}` : '/api/alerts/history';
      const response = await apiService.get<AlertActionResponse>(url);
      return response.data || [];
    } catch (error) {
      console.error('Error fetching alert history:', error);
      throw error;
    }
  }

  /**
   * Acknowledge a single alert
   */
  async acknowledgeAlert(alertId: string, notes?: string): Promise<boolean> {
    try {
      const response = await apiService.post<AlertActionResponse>(`/api/alerts/${alertId}/acknowledge`, {
        userId: this.getCurrentUserId(),
        notes
      });
      return response.success;
    } catch (error) {
      console.error('Error acknowledging alert:', error);
      throw error;
    }
  }

  /**
   * Resolve a single alert
   */
  async resolveAlert(alertId: string, notes?: string): Promise<boolean> {
    try {
      const response = await apiService.post<AlertActionResponse>(`/api/alerts/${alertId}/resolve`, {
        userId: this.getCurrentUserId(),
        notes
      });
      return response.success;
    } catch (error) {
      console.error('Error resolving alert:', error);
      throw error;
    }
  }

  /**
   * Perform bulk action on multiple alerts
   */
  async bulkAction(
    alertIds: string[], 
    action: 'acknowledge' | 'resolve', 
    notes?: string
  ): Promise<BulkActionResult> {
    try {
      const requestData: BulkActionRequest = {
        alert_ids: alertIds,
        action,
        user_id: this.getCurrentUserId(),
        notes
      };

      const response = await apiService.post<AlertActionResponse>('/api/alerts/bulk-action', requestData);
      
      if (!response.success) {
        throw new Error(response.message || 'Bulk action failed');
      }

      return response.data as BulkActionResult;
    } catch (error) {
      console.error('Error performing bulk action:', error);
      throw error;
    }
  }

  /**
   * Bulk acknowledge multiple alerts
   */
  async bulkAcknowledge(alertIds: string[], notes?: string): Promise<BulkActionResult> {
    return this.bulkAction(alertIds, 'acknowledge', notes);
  }

  /**
   * Bulk resolve multiple alerts
   */
  async bulkResolve(alertIds: string[], notes?: string): Promise<BulkActionResult> {
    return this.bulkAction(alertIds, 'resolve', notes);
  }

  /**
   * Get alert statistics
   */
  async getAlertStats(days?: number): Promise<any> {
    try {
      const url = days ? `/api/alerts/stats?days=${days}` : '/api/alerts/stats';
      const response = await apiService.get<AlertActionResponse>(url);
      return response.data;
    } catch (error) {
      console.error('Error fetching alert stats:', error);
      throw error;
    }
  }

  /**
   * Search alerts with filters
   */
  async searchAlerts(filters: any, limit?: number): Promise<Alert[]> {
    try {
      const url = limit ? `/api/alerts/search?limit=${limit}` : '/api/alerts/search';
      const response = await apiService.post<AlertActionResponse>(url, filters);
      return response.data || [];
    } catch (error) {
      console.error('Error searching alerts:', error);
      throw error;
    }
  }

  /**
   * Get current user ID from auth service or localStorage
   */
  private getCurrentUserId(): string {
    // Try to get user from localStorage first
    const userData = localStorage.getItem('user_data');
    if (userData) {
      try {
        const user = JSON.parse(userData);
        return user.username || user.id || 'unknown';
      } catch (e) {
        console.warn('Could not parse user data from localStorage');
      }
    }

    // Fallback to 'admin' for now - in production this should be properly handled
    return 'admin';
  }
}

export const alertService = AlertService.getInstance();
export default alertService; 