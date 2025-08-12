export interface SystemEvent {
  id: string;
  timestamp: string;
  action: string;
  username: string;
  user_role: string;
  success: boolean;
  severity: string;
  resource_type?: string;
  error_message?: string;
}

class AuditService {
  private readonly baseUrl = '/api/audit';

  async getRecentEvents(limit: number = 10, hours: number = 24): Promise<SystemEvent[]> {
    const response = await fetch(`${this.baseUrl}/recent-events?limit=${limit}&hours=${hours}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch recent events: ${response.statusText}`);
    }
    const data = await response.json();
    return data.logs || [];
  }

  createAuditWebSocket(): WebSocket {
    // Note: In production, derive host from window.location
    const wsUrl = 'ws://localhost:8001/ws/audit';
    return new WebSocket(wsUrl);
  }

  parseWebSocketMessage(event: MessageEvent): any {
    try {
      return JSON.parse(event.data);
    } catch {
      return null;
    }
  }
}

export const auditService = new AuditService();
