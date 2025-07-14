export interface Alert {
  id: string;
  cameraId: string;
  timestamp: string;
  type: 'shoplifting' | 'suspicious_activity' | 'object_detection' | 'motion' | 'system_alert';
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'active' | 'acknowledged' | 'resolved' | 'dismissed';
  confidence: number;
  message: string;
  source: 'detection' | 'system' | 'manual';
  
  // Optional frame data for visual alerts (base64 encoded)
  frame?: string;
  
  // Detection-specific data from Celery worker
  detectionData: {
    isShoplifting: boolean;
    modelLabel: number;
    sequenceStats: {
      mean: number;
      std: number;
      frames: number;
    };
    processingTime?: number;
    modelVersion?: string;
  };
  
  // Alert management
  acknowledgedBy?: string;
  acknowledgedAt?: string;
  resolvedBy?: string;
  resolvedAt?: string;
  notes?: string;
  
  // Auto-generated metadata
  createdAt: string;
  updatedAt: string;
}

export interface AlertFilter {
  severity?: ('low' | 'medium' | 'high' | 'critical')[];
  status?: ('active' | 'acknowledged' | 'resolved' | 'dismissed')[];
  type?: ('shoplifting' | 'suspicious_activity' | 'object_detection' | 'motion' | 'system_alert')[];
  cameraId?: string[];
  confidenceMin?: number;
  confidenceMax?: number;
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface AlertStats {
  totalActive: number;
  totalToday: number;
  totalWeek: number;
  bySeverity: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  byCamera: Record<string, number>;
  byType: Record<string, number>;
  avgConfidence: number;
  avgResponseTime: number; // in minutes
}

export interface AlertAction {
  alertId: string;
  action: 'acknowledge' | 'resolve' | 'dismiss' | 'add_note';
  userId: string;
  notes?: string;
  timestamp: string;
}

// API Response Types
export interface AlertApiResponse {
  success: boolean;
  message: string;
  data: {
    alerts: Alert[];
    total: number;
  };
}

export interface AlertStatsApiResponse {
  success: boolean;
  message: string;
  data: AlertStats;
}

export interface AlertActionRequest {
  userId: string;
  notes?: string;
}

export interface AlertActionResponse {
  success: boolean;
  message: string;
  data: {
    alert_id: string;
    acknowledged_by?: string;
    resolved_by?: string;
  };
}
