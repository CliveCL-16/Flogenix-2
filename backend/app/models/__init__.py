from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ClaimStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    PENDING_REVIEW = "PENDING_REVIEW"
    FRAUD_FLAGGED = "FRAUD_FLAGGED"


class DecisionType(str, Enum):
    APPROVE = "APPROVE"
    DENY = "DENY"
    REVIEW = "REVIEW"


class AgentStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ReasoningStep(BaseModel):
    step: int
    type: str  # "REASON", "ACT", "OBSERVE", "COMPLETE"
    text: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ToolUsage(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    result: str
    success: bool
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentReport(BaseModel):
    agent_name: str
    status: AgentStatus
    duration_seconds: float
    tools_used: List[ToolUsage] = []
    reasoning_steps: List[ReasoningStep] = []
    result: str
    confidence_score: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ClaimState(BaseModel):
    """Shared state that flows through all agents"""
    claim_id: str
    claim_data: Dict[str, Any]
    
    # Agent processing status
    intake_completed: bool = False
    eligibility_verified: bool = False
    codes_validated: bool = False
    fraud_checked: bool = False
    adjudication_completed: bool = False
    
    # Results from each agent
    eligibility_result: Optional[Dict[str, Any]] = None
    clinical_result: Optional[Dict[str, Any]] = None
    fraud_result: Optional[Dict[str, Any]] = None
    
    # Agent reports
    agent_reports: List[AgentReport] = []
    
    # Final decision
    final_decision: Optional[DecisionType] = None
    reasoning: str = ""
    confidence_score: float = 0.0


class ClaimSubmission(BaseModel):
    patient_name: str = Field(..., min_length=1, max_length=100)
    patient_id: str = Field(..., min_length=1, max_length=50)
    insurance_provider: str = Field(..., min_length=1, max_length=100)
    policy_number: str = Field(..., min_length=1, max_length=50)
    diagnosis_code: str = Field(..., description="ICD-10 diagnosis code")
    procedure_code: str = Field(..., description="CPT procedure code")
    claim_amount: float = Field(..., gt=0, description="Claim amount in USD")
    service_date: date = Field(..., description="Date when service was provided")
    provider_name: str = Field(..., min_length=1, max_length=100)
    provider_npi: Optional[str] = Field(None, max_length=10, description="National Provider Identifier")
    notes: Optional[str] = Field(None, max_length=500)


class Claim(ClaimSubmission):
    claim_id: str
    status: ClaimStatus = ClaimStatus.PENDING
    created_at: datetime
    processed_at: Optional[datetime] = None


class DecisionLog(BaseModel):
    claim_id: str
    decision: DecisionType
    confidence_score: float = Field(..., ge=0, le=100)
    reasoning_text: str
    fraud_score: Optional[float] = Field(None, ge=0, le=100)
    created_at: datetime


class ExceptionLog(BaseModel):
    claim_id: str
    exception_type: str
    resolution_action: str
    learned_from_case_id: Optional[str] = None
    created_at: datetime


class DashboardMetrics(BaseModel):
    total_claims: int
    approved_count: int
    denied_count: int
    pending_review_count: int
    fraud_flagged_count: int
    approval_rate: float
    avg_processing_time_seconds: float


class FraudAnalysis(BaseModel):
    claim_id: str
    fraud_score: float = Field(..., ge=0, le=100)
    risk_factors: list[str]
    is_flagged: bool
    analysis_details: dict


class ClaimDetail(Claim):
    decision_log: Optional[DecisionLog] = None
    fraud_analysis: Optional[FraudAnalysis] = None
    exception_logs: list[ExceptionLog] = []
    agent_reports: List[AgentReport] = []
    claim_state: Optional[ClaimState] = None


class ProcessClaimResponse(BaseModel):
    claim_id: str
    status: ClaimStatus
    decision: DecisionType
    confidence_score: float
    reasoning_text: str
    fraud_score: float
    processing_time_seconds: float
    agent_reports: List[AgentReport] = []


class AgentTimelineResponse(BaseModel):
    claim_id: str
    agents: List[Dict[str, Any]]


class AgentReasoningResponse(BaseModel):
    claim_id: str
    agent_reasoning: Dict[str, List[ReasoningStep]]


class ToolUsageResponse(BaseModel):
    claim_id: str
    tool_usage: List[Dict[str, Any]]