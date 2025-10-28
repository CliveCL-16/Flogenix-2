// API client for Flogenix backend integration

const API_BASE_URL = 'http://localhost:8000/api';

// Types matching backend models
export interface ClaimSubmission {
  patient_name: string;
  patient_id: string;
  insurance_provider: string;
  policy_number: string;
  diagnosis_code: string;
  procedure_code: string;
  claim_amount: number;
  service_date: string;
  provider_name: string;
  provider_npi?: string;
  notes?: string;
}

export interface Claim extends ClaimSubmission {
  claim_id: string;
  status: ClaimStatus;
  created_at: string;
  processed_at?: string;
}

export enum ClaimStatus {
  PENDING = "PENDING",
  APPROVED = "APPROVED",
  DENIED = "DENIED",
  PENDING_REVIEW = "PENDING_REVIEW",
  FRAUD_FLAGGED = "FRAUD_FLAGGED"
}

export enum DecisionType {
  APPROVE = "APPROVE",
  DENY = "DENY",
  REVIEW = "REVIEW"
}

export interface DecisionLog {
  claim_id: string;
  decision: DecisionType;
  confidence_score: number;
  reasoning_text: string;
  fraud_score?: number;
  created_at: string;
}

export interface ExceptionLog {
  claim_id: string;
  exception_type: string;
  resolution_action: string;
  learned_from_case_id?: string;
  created_at: string;
}

export interface DashboardMetrics {
  total_claims: number;
  approved_count: number;
  denied_count: number;
  pending_review_count: number;
  fraud_flagged_count: number;
  approval_rate: number;
  avg_processing_time_seconds: number;
}

export interface FraudAnalysis {
  claim_id: string;
  fraud_score: number;
  risk_factors: string[];
  is_flagged: boolean;
  analysis_details: Record<string, any>;
}

export interface ClaimDetail extends Claim {
  decision_log?: DecisionLog;
  fraud_analysis?: FraudAnalysis;
  exception_logs: ExceptionLog[];
  agent_reports: any[];
  claim_state?: any;
}

export interface ProcessClaimResponse {
  claim_id: string;
  status: ClaimStatus;
  decision: DecisionType;
  confidence_score: number;
  reasoning_text: string;
  fraud_score: number;
  processing_time_seconds: number;
  agent_reports: any[];
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred');
    }
  }

  // Claims API methods
  async submitClaim(claimData: ClaimSubmission): Promise<Claim> {
    return this.request<Claim>('/claims/submit', {
      method: 'POST',
      body: JSON.stringify(claimData),
    });
  }

  async getClaims(status?: ClaimStatus): Promise<Claim[]> {
    const query = status ? `?status=${status}` : '';
    return this.request<Claim[]>(`/claims${query}`);
  }

  async getClaimDetails(claimId: string): Promise<ClaimDetail> {
    return this.request<ClaimDetail>(`/claims/${claimId}`);
  }

  async processClaim(claimId: string): Promise<ProcessClaimResponse> {
    return this.request<ProcessClaimResponse>(`/claims/${claimId}/process`, {
      method: 'POST',
    });
  }

  async getFraudAnalysis(claimId: string): Promise<FraudAnalysis> {
    return this.request<FraudAnalysis>(`/claims/${claimId}/fraud-analysis`);
  }

  async handleException(
    claimId: string,
    exceptionType: string,
    exceptionDetails: string = ''
  ): Promise<any> {
    return this.request(`/claims/${claimId}/handle-exception`, {
      method: 'POST',
      body: JSON.stringify({
        exception_type: exceptionType,
        exception_details: exceptionDetails,
      }),
    });
  }

  async getAgentTimeline(claimId: string): Promise<any> {
    return this.request(`/claims/${claimId}/agent-timeline`);
  }

  async getAgentReasoning(claimId: string): Promise<any> {
    return this.request(`/claims/${claimId}/agent-reasoning`);
  }

  async getToolUsage(claimId: string): Promise<any> {
    return this.request(`/claims/${claimId}/tool-usage`);
  }

  // Dashboard API methods
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    return this.request<DashboardMetrics>('/dashboard/metrics');
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request('/health');
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export helper functions
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

export const getStatusColor = (status: ClaimStatus): string => {
  switch (status) {
    case ClaimStatus.APPROVED:
      return 'success';
    case ClaimStatus.DENIED:
      return 'destructive';
    case ClaimStatus.PENDING:
      return 'warning';
    case ClaimStatus.PENDING_REVIEW:
      return 'info';
    case ClaimStatus.FRAUD_FLAGGED:
      return 'destructive';
    default:
      return 'default';
  }
};

export const getStatusLabel = (status: ClaimStatus): string => {
  switch (status) {
    case ClaimStatus.PENDING:
      return 'Pending';
    case ClaimStatus.APPROVED:
      return 'Approved';
    case ClaimStatus.DENIED:
      return 'Denied';
    case ClaimStatus.PENDING_REVIEW:
      return 'Pending Review';
    case ClaimStatus.FRAUD_FLAGGED:
      return 'Fraud Flagged';
    default:
      return status;
  }
};