from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any, Annotated
from pydantic import BaseModel, Field
import operator


class UserInfo(BaseModel):
    """User information model for API responses"""
    id: int
    user_id: str
    email: str
    username: str
    first_name: str
    last_name: str
    role: str
    two_factor_enabled: bool


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


class DocumentType(str, Enum):
    MEDICAL_BILL = "MEDICAL_BILL"
    INSURANCE_CARD = "INSURANCE_CARD"
    PRESCRIPTION = "PRESCRIPTION"
    MEDICAL_REPORT = "MEDICAL_REPORT"
    REFERRAL = "REFERRAL"
    LAB_RESULT = "LAB_RESULT"
    IMAGING = "IMAGING"
    AUTHORIZATION = "AUTHORIZATION"
    OTHER = "OTHER"


class DocumentStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


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
    
    # Agent reports - use Annotated for concurrent updates
    agent_reports: Annotated[List[AgentReport], operator.add] = []
    
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


# Document Management Models
class DocumentInfo(BaseModel):
    """Document information model"""
    document_id: str
    filename: str
    file_size: int
    content_type: str
    document_type: DocumentType
    status: DocumentStatus
    uploaded_at: datetime
    uploaded_by: str
    claim_id: Optional[str] = None


class DocumentOCRResult(BaseModel):
    """OCR processing result"""
    processed: bool
    provider: Optional[str] = None
    confidence: Optional[float] = None
    processing_time: Optional[float] = None
    extracted_text: Optional[str] = None
    extracted_fields: Dict[str, Any] = {}
    error: Optional[str] = None


class DocumentDetail(DocumentInfo):
    """Detailed document information including OCR results"""
    ocr_result: Optional[DocumentOCRResult] = None
    file_hash: Optional[str] = None
    last_accessed: Optional[datetime] = None
    processing_history: List[Dict[str, Any]] = []


class DocumentUploadRequest(BaseModel):
    """Request model for document upload"""
    claim_id: Optional[str] = None
    document_type: DocumentType = DocumentType.OTHER
    process_ocr: bool = True
    ocr_provider: Optional[str] = None


class DocumentSearchRequest(BaseModel):
    """Request model for document search"""
    claim_id: Optional[str] = None
    document_type: Optional[DocumentType] = None
    status: Optional[DocumentStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    has_ocr: Optional[bool] = None
    filename_pattern: Optional[str] = None


class DocumentProcessingRequest(BaseModel):
    """Request model for document processing"""
    document_id: str
    ocr_provider: Optional[str] = Field(None, description="Specific OCR provider to use")
    extract_fields: bool = Field(True, description="Whether to extract medical fields")
    template_id: Optional[str] = Field(None, description="Document template to use")


class DocumentBatchProcessingRequest(BaseModel):
    """Request model for batch document processing"""
    document_ids: List[str]
    ocr_provider: Optional[str] = None
    extract_fields: bool = True
    priority: int = Field(1, ge=1, le=3)


class DocumentTemplate(BaseModel):
    """Document template model"""
    template_id: str
    name: str
    description: Optional[str] = None
    document_type: DocumentType
    field_extraction_rules: Dict[str, Any]
    validation_rules: Dict[str, Any] = {}
    confidence_threshold: float = 0.8
    version: str = "1.0"
    is_active: bool = True


class DocumentStats(BaseModel):
    """Document processing statistics"""
    total_documents: int
    processed_documents: int
    pending_documents: int
    failed_documents: int
    total_size_bytes: int
    avg_confidence: float
    processing_stats: Dict[str, int]
    provider_stats: Dict[str, int]


class ClaimWithDocuments(Claim):
    """Claim model with attached documents"""
    documents: List[DocumentInfo] = []