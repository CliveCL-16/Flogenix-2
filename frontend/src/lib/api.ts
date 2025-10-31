/**
 * Enterprise API Client for Flogenix
 * Handles authentication, requests, and error handling
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface LoginCredentials {
  email_or_username: string;
  password: string;
  totp_code?: string;
}

export interface UserInfo {
  id: number;
  user_id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  role: 'USER' | 'PROCESSOR' | 'ADMIN' | 'SUPER_ADMIN';
  two_factor_enabled: boolean;
}

export enum ClaimStatus {
  PENDING = 'PENDING',
  PROCESSING = 'PROCESSING',
  APPROVED = 'APPROVED',
  DENIED = 'DENIED',
  PENDING_REVIEW = 'PENDING_REVIEW',
  FRAUD_FLAGGED = 'FRAUD_FLAGGED'
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_info: UserInfo;
}

export interface ClaimSubmission {
  patient_name: string;
  patient_id: string;
  insurance_provider: string;
  policy_number: string;
  diagnosis_code: string;
  procedure_code: string;
  service_date: string;
  claim_amount: number;
  provider_name: string;
  provider_npi?: string;
  notes?: string;
  priority?: number;
}

export interface Claim {
  claim_id: string;
  status: string;
  patient_name: string;
  patient_id: string;
  insurance_provider: string;
  policy_number: string;
  diagnosis_code: string;
  procedure_code: string;
  service_date: string;
  claim_amount: number;
  priority: number;
  provider_name: string;
  provider_npi?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  processed_at?: string;
  confidence_score?: number;
}

export interface ClaimDetails {
  claim: {
    claim_id: string;
    patient_name: string;
    patient_id: string;
    insurance_provider: string;
    policy_number: string;
    diagnosis_code: string;
    procedure_code: string;
    service_date: string;
    claim_amount: number;
    provider_name: string;
    provider_npi?: string;
    notes?: string;
    status: string;
    priority: number;
    created_at: string;
    processed_at?: string;
  };
  decision_log?: {
    decision: string;
    confidence_score: number;
    reasoning_text: string;
    processing_time_seconds: number;
    fraud_score: number;
    created_at: string;
  };
  agent_reports: Array<{
    agent_name: string;
    agent_type: string;
    status: string;
    result: string;
    confidence_score: number;
    duration_seconds: number;
    reasoning_steps: any[];
    tool_usage: any[];
    started_at: string;
    completed_at: string;
  }>;
  fraud_analysis?: {
    fraud_score: number;
    risk_level: string;
    is_flagged: boolean;
    risk_factors: string[];
    created_at: string;
  };
}

export interface DashboardMetrics {
  total_claims: number;
  pending_claims: number;
  processing_claims: number;
  approved_claims: number;
  denied_claims: number;
  fraud_flagged_claims: number;
  approval_rate: number;
  avg_processing_time_seconds: number;
  claims_today: number;
  revenue_approved_today: number;
}

export interface AgentTimeline {
  claim_id: string;
  agents: Array<{
    agent: string;
    agent_type: string;
    status: string;
    duration: number;
    result: string;
    confidence: number;
    started_at: string;
    completed_at: string;
    reasoning_steps: number;
    tools_used: number;
  }>;
  total_processing_time: number;
  final_decision?: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

class ApiClient {
  private baseURL: string;
  private token: string | null = null;

  constructor() {
    this.baseURL = API_BASE_URL;
    this.token = localStorage.getItem('access_token');
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Add authorization header if token is available
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('access_token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  // Authentication
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(credentials),
    });

    const data = await this.handleResponse<AuthResponse>(response);
    this.setToken(data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return data;
  }

  async logout(): Promise<void> {
    try {
      await fetch(`${this.baseURL}/auth/logout`, {
        method: 'POST',
        headers: this.getHeaders(),
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.clearToken();
    }
  }

  async getCurrentUser(): Promise<UserInfo> {
    const response = await fetch(`${this.baseURL}/auth/me`, {
      headers: this.getHeaders(),
    });

    return this.handleResponse<UserInfo>(response);
  }

  // Claims - Updated to use unified API structure
  async submitClaim(claimData: ClaimSubmission): Promise<Claim> {
    const response = await fetch(`${this.baseURL}/api/claims/submit`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(claimData),
    });

    return this.handleResponse<Claim>(response);
  }

  async getClaims(params?: {
    status?: string;
    priority?: number;
    search?: string;
    date_from?: string;
    date_to?: string;
    amount_min?: number;
    amount_max?: number;
    start_date?: string;
    end_date?: string;
    patient_name?: string;
    insurance_provider?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ claims: Claim[]; total: number }> {
    const searchParams = new URLSearchParams();
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString());
        }
      });
    }

    const response = await fetch(`${this.baseURL}/api/claims?${searchParams}`, {
      headers: this.getHeaders(),
    });

    const data = await this.handleResponse<Claim[]>(response);
    
    // If backend returns array directly, wrap it in expected format
    if (Array.isArray(data)) {
      return { claims: data, total: data.length };
    }
    
    return data as { claims: Claim[]; total: number };
  }

  async getClaimDetails(claimId: string): Promise<ClaimDetails> {
    const response = await fetch(`${this.baseURL}/api/claims/${claimId}`, {
      headers: this.getHeaders(),
    });

    return this.handleResponse<ClaimDetails>(response);
  }

  async processClaim(claimId: string, options?: {
    priority?: number;
    async_processing?: boolean;
  }): Promise<{
    claim_id: string;
    status: string;
    confidence_score?: number;
    reasoning?: string;
    fraud_score?: number;
    processing_time?: number;
    async: boolean;
    task_id?: string;
    message?: string;
  }> {
    const response = await fetch(`${this.baseURL}/api/claims/${claimId}/process`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        priority: options?.priority || 1,
        async_processing: options?.async_processing ?? true,
      }),
    });

    return this.handleResponse(response);
  }

  async exportClaims(params?: { claim_ids?: string[] }): Promise<string> {
    const response = await fetch(`${this.baseURL}/api/claims/export`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(params || {}),
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    return response.text();
  }

  // Dashboard
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    const response = await fetch(`${this.baseURL}/api/dashboard/metrics`, {
      headers: this.getHeaders(),
    });

    return this.handleResponse<DashboardMetrics>(response);
  }

  // Agent Processing
  async getAgentTimeline(claimId: string): Promise<AgentTimeline> {
    const response = await fetch(`${this.baseURL}/api/claims/${claimId}/agent-timeline`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return this.handleResponse<AgentTimeline>(response);
  }

  async getAgentReasoning(claimId: string): Promise<{ claim_id: string; agent_reasoning: Record<string, any[]> }> {
    const response = await fetch(`${this.baseURL}/api/claims/${claimId}/agent-reasoning`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return this.handleResponse<{ claim_id: string; agent_reasoning: Record<string, any[]> }>(response);
  }

  async getToolUsage(claimId: string): Promise<{ claim_id: string; tool_usage: any[] }> {
    const response = await fetch(`${this.baseURL}/api/claims/${claimId}/tool-usage`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return this.handleResponse<{ claim_id: string; tool_usage: any[] }>(response);
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await fetch(`${this.baseURL}/api/health`);
    return this.handleResponse<{ status: string; timestamp: string }>(response);
  }

  // Admin endpoints
  async getSystemStats(): Promise<{
    total_users: number;
    active_users: number;
    total_claims: number;
    system_uptime: string;
    ai_agents_active: number;
    queue_size: number;
  }> {
    const response = await fetch(`${this.baseURL}/api/admin/stats`, {
      headers: this.getHeaders(),
    });

    return this.handleResponse<any>(response);
  }

  async getUsers(params?: {
    search?: string;
    role?: string;
    is_active?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<{ users: any[]; total: number }> {
    const searchParams = new URLSearchParams();
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString());
        }
      });
    }

    const response = await fetch(`${this.baseURL}/api/admin/users?${searchParams}`, {
      headers: this.getHeaders(),
    });

    return this.handleResponse<{ users: any[]; total: number }>(response);
  }

  async getQueuedClaims(): Promise<any[]> {
    const response = await fetch(`${this.baseURL}/api/admin/queue`, {
      headers: this.getHeaders(),
    });

    return this.handleResponse<any[]>(response);
  }

  // Notification endpoints
  async getNotifications(params?: {
    unread_only?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<{
    notifications: any[];
    count: number;
    unread_count: number;
  }> {
    const searchParams = new URLSearchParams();
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString());
        }
      });
    }

    const response = await fetch(`${this.baseURL}/api/notifications?${searchParams}`, {
      headers: this.getHeaders(),
    });

    return this.handleResponse<any>(response);
  }

  async markNotificationRead(notificationId: string): Promise<void> {
    const response = await fetch(`${this.baseURL}/api/notifications/${notificationId}/read`, {
      method: 'POST',
      headers: this.getHeaders(),
    });

    await this.handleResponse<void>(response);
  }

  async markAllNotificationsRead(): Promise<{ updated_count: number }> {
    const response = await fetch(`${this.baseURL}/api/notifications/read-all`, {
      method: 'POST',
      headers: this.getHeaders(),
    });

    return this.handleResponse<{ updated_count: number }>(response);
  }

  async deleteNotification(notificationId: string): Promise<void> {
    const response = await fetch(`${this.baseURL}/api/notifications/${notificationId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });

    await this.handleResponse<void>(response);
  }

  async getNotificationStats(): Promise<{
    total_notifications: number;
    unread_notifications: number;
    category_breakdown: Record<string, any>;
    priority_breakdown: Record<string, any>;
  }> {
    const response = await fetch(`${this.baseURL}/api/notifications/stats`, {
      headers: this.getHeaders(),
    });

    return this.handleResponse<any>(response);
  }

  // Enhanced Analytics API
  async getAnalyticsOverview(days: number = 30): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/analytics/overview?days=${days}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async getPerformanceAnalytics(days: number = 30, agentFilter?: string): Promise<any> {
    const url = new URL(`${this.baseURL}/api/analytics/performance`);
    url.searchParams.set('days', days.toString());
    if (agentFilter) url.searchParams.set('agent_filter', agentFilter);
    
    const response = await fetch(url.toString(), {
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async getFraudAnalytics(days: number = 30): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/analytics/fraud?days=${days}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async getFinancialAnalytics(days: number = 30): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/analytics/financial?days=${days}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async getTrendAnalysis(metric: string, period: string = 'daily', days: number = 30): Promise<any> {
    const response = await fetch(
      `${this.baseURL}/api/analytics/trends?metric=${metric}&period=${period}&days=${days}`,
      { headers: this.getHeaders() }
    );
    return this.handleResponse<any>(response);
  }

  // User Dashboard API
  async getUserDashboardMetrics(): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/analytics/dashboard/user/metrics`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async getUserNotifications(limit: number = 10): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/analytics/dashboard/user/notifications?limit=${limit}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  // Claim Tracking API
  async getClaimTimeline(claimId: string): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/claims/${claimId}/agent-timeline`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async getClaimAIAnalysis(claimId: string): Promise<any> {
    // Note: This endpoint currently has database issues, will return gracefully
    try {
      const response = await fetch(`${this.baseURL}/api/claims/${claimId}/ai-analysis`, {
        headers: this.getHeaders(),
      });
      return this.handleResponse<any>(response);
    } catch (error) {
      // Return empty analysis if endpoint is not available
      return {
        decision: '',
        confidence_score: 0,
        risk_level: '',
        reasoning: '',
        next_steps: '',
        fraud_indicators: []
      };
    }
  }

  // Reports API
  async getAutomatedReports(reportType?: string): Promise<any> {
    const url = new URL(`${this.baseURL}/api/analytics/reports/automated`);
    if (reportType) url.searchParams.set('report_type', reportType);
    
    const response = await fetch(url.toString(), {
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async scheduleReport(reportConfig: any): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/analytics/reports/schedule`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(reportConfig),
    });
    return this.handleResponse<any>(response);
  }

  async exportAnalytics(reportType: string, format: string = 'csv', days: number = 30): Promise<any> {
    const url = new URL(`${this.baseURL}/api/analytics/export`);
    url.searchParams.set('report_type', reportType);
    url.searchParams.set('format', format);
    url.searchParams.set('days', days.toString());
    
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  // Admin Dashboard API
  async getAdminKPIs(days: number = 30): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/admin/dashboard/kpis?days=${days}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async getClaimsQueue(statusFilter?: string, priorityFilter?: number, limit: number = 50, offset: number = 0): Promise<any> {
    const url = new URL(`${this.baseURL}/api/admin/dashboard/claims-queue`);
    if (statusFilter) url.searchParams.set('status_filter', statusFilter);
    if (priorityFilter) url.searchParams.set('priority_filter', priorityFilter.toString());
    url.searchParams.set('limit', limit.toString());
    url.searchParams.set('offset', offset.toString());
    
    const response = await fetch(url.toString(), {
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async getSystemHealth(): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/admin/dashboard/system-health`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async getAIDecisionSupport(days: number = 7): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/admin/dashboard/ai-decision-support?days=${days}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  // AI System Monitoring API
  async getAISystemHealth(): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/ai/monitoring/system-health`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async getModelPerformance(): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/ai/monitoring/model-performance`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async getAgentMetrics(agentType?: string, hours: number = 24): Promise<any> {
    const url = new URL(`${this.baseURL}/api/ai/monitoring/agent-metrics`);
    if (agentType) url.searchParams.set('agent_type', agentType);
    url.searchParams.set('hours', hours.toString());
    
    const response = await fetch(url.toString(), {
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  // Document Processing API
  async getDocumentOCRResults(documentId: string): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/documents/${documentId}/ocr-results`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return this.handleResponse<any>(response);
  }

  async getDocumentValidation(documentId: string): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/documents/${documentId}/validation`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return this.handleResponse<any>(response);
  }

  async getClaimDocuments(claimId: string): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/documents/claim/${claimId}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return this.handleResponse<any>(response);
  }

  async reprocessDocument(documentId: string, provider?: string): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/documents/${documentId}/reprocess`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ provider }),
    });
    return this.handleResponse<any>(response);
  }

  // Claims Management API
  async getClaimDetailedReview(claimId: string): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/enterprise/claims/claims/${claimId}/detailed-review`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async getClaimCommunicationHistory(claimId: string): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/enterprise/claims/claims/${claimId}/communication-history`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async submitManualDecision(claimId: string, decision: string, reasoning: string): Promise<any> {
    const response = await fetch(`${this.baseURL}/api/enterprise/claims/claims/${claimId}/manual-decision`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ decision, reasoning }),
    });
    return this.handleResponse<any>(response);
  }

  // WebSocket connection for real-time notifications
  connectNotifications(onMessage: (notification: any) => void): WebSocket | null {
    if (!this.token) {
      console.error('No authentication token available for WebSocket connection');
      return null;
    }

    const wsUrl = this.baseURL.replace('http', 'ws') + `/api/ws/notifications?token=${this.token}`;
    
    try {
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('🔗 WebSocket connected for notifications');
      };
      
      ws.onmessage = (event) => {
        try {
          const notification = JSON.parse(event.data);
          onMessage(notification);
        } catch (error) {
          console.error('Error parsing notification:', error);
        }
      };
      
      ws.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      // Keep connection alive with ping
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        } else {
          clearInterval(pingInterval);
        }
      }, 30000); // Ping every 30 seconds
      
      return ws;
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      return null;
    }
  }
}

export const apiClient = new ApiClient();

// Helper functions
export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount);
};

export const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export const formatDateTime = (dateString: string): string => {
  return new Date(dateString).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const getStatusColor = (status: string): string => {
  switch (status.toUpperCase()) {
    case 'APPROVED':
      return 'bg-green-100 text-green-800';
    case 'DENIED':
      return 'bg-red-100 text-red-800';
    case 'PENDING':
      return 'bg-yellow-100 text-yellow-800';
    case 'PROCESSING':
      return 'bg-blue-100 text-blue-800';
    case 'PENDING_REVIEW':
      return 'bg-orange-100 text-orange-800';
    case 'FRAUD_FLAGGED':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

export const getStatusLabel = (status: string): string => {
  switch (status.toUpperCase()) {
    case 'PENDING':
      return 'Pending';
    case 'PROCESSING':
      return 'Processing';
    case 'APPROVED':
      return 'Approved';
    case 'DENIED':
      return 'Denied';
    case 'PENDING_REVIEW':
      return 'Pending Review';
    case 'FRAUD_FLAGGED':
      return 'Fraud Flagged';
    default:
      return status;
  }
};