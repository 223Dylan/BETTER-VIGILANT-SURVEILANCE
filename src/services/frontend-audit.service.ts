import { apiService } from './api.service';
import { authService } from './auth.service';

interface FrontendAuditEvent {
  action: string;
  resource_type?: string;
  resource_id?: string;
  permission_checked?: string;
  permission_granted?: boolean;
  component?: string;
  url?: string;
  metadata?: Record<string, any>;
}

interface PermissionUsageEvent {
  permission: string;
  granted: boolean;
  component: string;
  action: string;
  timestamp: string;
}

class FrontendAuditService {
  private static instance: FrontendAuditService;
  private eventQueue: FrontendAuditEvent[] = [];
  private permissionUsage: PermissionUsageEvent[] = [];
  private flushInterval: NodeJS.Timeout | null = null;
  private readonly FLUSH_INTERVAL_MS = 30000; // 30 seconds
  private readonly MAX_QUEUE_SIZE = 50;

  private constructor() {
    this.startPeriodicFlush();
    this.setupSessionTracking();
  }

  public static getInstance(): FrontendAuditService {
    if (!FrontendAuditService.instance) {
      FrontendAuditService.instance = new FrontendAuditService();
    }
    return FrontendAuditService.instance;
  }

  /**
   * Log a permission check event
   */
  logPermissionCheck(
    permission: string,
    granted: boolean,
    component: string,
    action: string = 'check',
    metadata?: Record<string, any>
  ): void {
    const event: FrontendAuditEvent = {
      action: granted ? 'permission_granted' : 'permission_denied',
      permission_checked: permission,
      permission_granted: granted,
      component: component,
      url: window.location.pathname,
      metadata: {
        action,
        user_agent: navigator.userAgent,
        screen_resolution: `${window.screen.width}x${window.screen.height}`,
        ...metadata
      }
    };

    this.queueEvent(event);

    // Track permission usage statistics
    this.permissionUsage.push({
      permission,
      granted,
      component,
      action,
      timestamp: new Date().toISOString()
    });

    // Keep only recent usage data (last 100 events)
    if (this.permissionUsage.length > 100) {
      this.permissionUsage = this.permissionUsage.slice(-100);
    }
  }

  /**
   * Log a user action/interaction
   */
  logUserAction(
    action: string,
    resourceType?: string,
    resourceId?: string,
    metadata?: Record<string, any>
  ): void {
    const event: FrontendAuditEvent = {
      action,
      resource_type: resourceType,
      resource_id: resourceId,
      url: window.location.pathname,
      metadata: {
        timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent,
        referrer: document.referrer,
        ...metadata
      }
    };

    this.queueEvent(event);
  }

  /**
   * Log navigation events
   */
  logNavigation(fromPath: string, toPath: string): void {
    this.logUserAction('page_navigation', 'route', toPath, {
      from_path: fromPath,
      to_path: toPath
    });
  }

  /**
   * Log component access
   */
  logComponentAccess(component: string, granted: boolean, requiredPermissions?: string[]): void {
    this.logUserAction(
      granted ? 'component_accessed' : 'component_access_denied',
      'component',
      component,
      {
        granted,
        required_permissions: requiredPermissions,
        timestamp: new Date().toISOString()
      }
    );
  }

  /**
   * Log security events (failed authentication, suspicious activity)
   */
  logSecurityEvent(
    event: string,
    severity: 'low' | 'medium' | 'high' | 'critical' = 'medium',
    metadata?: Record<string, any>
  ): void {
    const securityEvent: FrontendAuditEvent = {
      action: `security_${event}`,
      url: window.location.pathname,
      metadata: {
        severity,
        timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent,
        session_storage_size: this.getSessionStorageSize(),
        local_storage_size: this.getLocalStorageSize(),
        ...metadata
      }
    };

    // Security events are high priority - flush immediately for critical events
    this.queueEvent(securityEvent);
    if (severity === 'critical' || severity === 'high') {
      this.flushEvents();
    }
  }

  /**
   * Get permission usage statistics
   */
  getPermissionUsageStats(): Record<string, any> {
    const stats: Record<string, any> = {};

    this.permissionUsage.forEach(event => {
      const key = event.permission;
      if (!stats[key]) {
        stats[key] = {
          permission: event.permission,
          total_checks: 0,
          granted: 0,
          denied: 0,
          components: new Set(),
          actions: new Set()
        };
      }

      stats[key].total_checks++;
      if (event.granted) {
        stats[key].granted++;
      } else {
        stats[key].denied++;
      }
      stats[key].components.add(event.component);
      stats[key].actions.add(event.action);
    });

    // Convert Sets to arrays for JSON serialization
    Object.values(stats).forEach((stat: any) => {
      stat.components = Array.from(stat.components);
      stat.actions = Array.from(stat.actions);
      stat.success_rate = stat.total_checks > 0 ? (stat.granted / stat.total_checks * 100).toFixed(2) : 0;
    });

    return stats;
  }

  /**
   * Queue an event for batched sending
   */
  private queueEvent(event: FrontendAuditEvent): void {
    this.eventQueue.push(event);

    // Flush if queue is getting full
    if (this.eventQueue.length >= this.MAX_QUEUE_SIZE) {
      this.flushEvents();
    }
  }

  /**
   * Send queued events to backend
   */
  private async flushEvents(): Promise<void> {
    if (this.eventQueue.length === 0) {
      return;
    }

    const events = [...this.eventQueue];
    this.eventQueue = []; // Clear the queue

    try {
      // Only send if user is authenticated
      if (!authService.isAuthenticated()) {
        return;
      }

      await apiService.post('/api/audit/frontend-events', {
        events,
        client_info: {
          user_agent: navigator.userAgent,
          screen_resolution: `${window.screen.width}x${window.screen.height}`,
          viewport_size: `${window.innerWidth}x${window.innerHeight}`,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          language: navigator.language,
          online: navigator.onLine
        }
      });

    } catch (error) {
      console.warn('Failed to send audit events:', error);
      // Re-queue events if they failed to send (up to a limit)
      if (events.length < this.MAX_QUEUE_SIZE) {
        this.eventQueue.unshift(...events);
      }
    }
  }

  /**
   * Start periodic flushing of events
   */
  private startPeriodicFlush(): void {
    this.flushInterval = setInterval(() => {
      this.flushEvents();
    }, this.FLUSH_INTERVAL_MS);
  }

  /**
   * Setup session tracking
   */
  private setupSessionTracking(): void {
    // Track page visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.logUserAction('page_hidden');
        this.flushEvents(); // Flush before page becomes hidden
      } else {
        this.logUserAction('page_visible');
      }
    });

    // Track page unload
    window.addEventListener('beforeunload', () => {
      this.logUserAction('page_unload');
      this.flushEvents();
    });

    // Track initial page load
    window.addEventListener('load', () => {
      this.logUserAction('page_loaded', 'page', window.location.pathname);
    });

    // Track errors
    window.addEventListener('error', (event) => {
      this.logSecurityEvent('javascript_error', 'medium', {
        message: event.message,
        filename: event.filename,
        line: event.lineno,
        column: event.colno,
        stack: event.error?.stack
      });
    });

    // Track unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.logSecurityEvent('unhandled_promise_rejection', 'medium', {
        reason: event.reason?.toString(),
        stack: event.reason?.stack
      });
    });
  }

  /**
   * Get session storage size
   */
  private getSessionStorageSize(): number {
    try {
      return JSON.stringify(sessionStorage).length;
    } catch {
      return 0;
    }
  }

  /**
   * Get local storage size
   */
  private getLocalStorageSize(): number {
    try {
      return JSON.stringify(localStorage).length;
    } catch {
      return 0;
    }
  }

  /**
   * Clean up resources
   */
  destroy(): void {
    if (this.flushInterval) {
      clearInterval(this.flushInterval);
      this.flushInterval = null;
    }
    this.flushEvents(); // Final flush
  }
}

// Export singleton instance
export const frontendAuditService = FrontendAuditService.getInstance();

// Global error boundary logging
export const logComponentError = (
  componentName: string,
  error: Error,
  errorInfo?: any
) => {
  frontendAuditService.logSecurityEvent('component_error', 'medium', {
    component: componentName,
    error_message: error.message,
    error_stack: error.stack,
    error_info: errorInfo
  });
};
