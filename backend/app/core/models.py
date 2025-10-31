"""
Enterprise Database Models
SQLAlchemy models for the Flogenix enterprise backend
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum, JSON, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, Dict, Any
import uuid

Base = declarative_base()

class ClaimStatus(PyEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    PENDING_REVIEW = "PENDING_REVIEW"
    FRAUD_FLAGGED = "FRAUD_FLAGGED"
    CANCELLED = "CANCELLED"

class UserRole(PyEnum):
    USER = "USER"
    PROCESSOR = "PROCESSOR"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"

class AgentStatus(PyEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"

class AuditAction(PyEnum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    PROCESS = "PROCESS"
    APPROVE = "APPROVE"
    DENY = "DENY"

class DocumentType(PyEnum):
    MEDICAL_BILL = "MEDICAL_BILL"
    INSURANCE_CARD = "INSURANCE_CARD"
    PRESCRIPTION = "PRESCRIPTION"
    MEDICAL_REPORT = "MEDICAL_REPORT"
    REFERRAL = "REFERRAL"
    LAB_RESULT = "LAB_RESULT"
    IMAGING = "IMAGING"
    AUTHORIZATION = "AUTHORIZATION"
    OTHER = "OTHER"

class DocumentStatus(PyEnum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"

# User Management Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True, default=lambda: f"USR-{uuid.uuid4().hex[:8].upper()}")
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(20))
    
    # Role and Permissions
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Security Settings
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(String(255))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    
    # Audit Fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime)
    
    # Relationships
    claims = relationship("Claim", back_populates="user", foreign_keys=lambda: [Claim.user_id])
    assigned_claims = relationship("Claim", foreign_keys=lambda: [Claim.assigned_processor_id])
    audit_logs = relationship("AuditLog", back_populates="user")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    user = relationship("User")

# Claims Models
class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # Patient Information
    patient_name = Column(String(255), nullable=False)
    patient_id = Column(String(100), nullable=False)
    insurance_provider = Column(String(255), nullable=False)
    policy_number = Column(String(100), nullable=False)
    
    # Medical Information
    diagnosis_code = Column(String(20), nullable=False)
    procedure_code = Column(String(20), nullable=False)
    service_date = Column(DateTime, nullable=False)
    claim_amount = Column(Float, nullable=False)
    
    # Provider Information
    provider_name = Column(String(255), nullable=False)
    provider_npi = Column(String(10))
    
    # Processing Information
    status = Column(Enum(ClaimStatus), default=ClaimStatus.PENDING, nullable=False)
    priority = Column(Integer, default=1)  # 1=Normal, 2=High, 3=Urgent
    assigned_processor_id = Column(Integer, ForeignKey("users.id"))
    
    # Additional Information
    notes = Column(Text)
    supporting_documents = Column(JSON)  # Store file paths/metadata
    
    # Audit Fields
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="claims", foreign_keys=[user_id])
    assigned_processor = relationship("User", foreign_keys=[assigned_processor_id], overlaps="assigned_claims")
    decision_logs = relationship("DecisionLog", back_populates="claim")
    agent_reports = relationship("AgentReport", back_populates="claim")
    fraud_analyses = relationship("FraudAnalysis", back_populates="claim")
    exceptions = relationship("Exception", back_populates="claim")
    documents = relationship("ClaimDocument", back_populates="claim")

class DecisionLog(Base):
    __tablename__ = "decision_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String(50), ForeignKey("claims.claim_id"), nullable=False)
    
    decision = Column(String(20), nullable=False)  # APPROVE, DENY, REVIEW
    confidence_score = Column(Float, nullable=False)
    reasoning_text = Column(Text, nullable=False)
    
    # Processing Information
    processing_time_seconds = Column(Float)
    model_version = Column(String(50))
    fraud_score = Column(Float)
    
    # Audit Fields
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    claim = relationship("Claim", back_populates="decision_logs")
    created_by = relationship("User")

# Multi-Agent System Models
class AgentReport(Base):
    __tablename__ = "agent_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String(50), ForeignKey("claims.claim_id"), nullable=False)
    
    agent_name = Column(String(100), nullable=False)
    agent_type = Column(String(50), nullable=False)  # intake, eligibility, clinical, fraud, adjudication
    status = Column(Enum(AgentStatus), nullable=False)
    
    # Processing Details
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Results
    result = Column(String(100))
    confidence_score = Column(Float)
    reasoning_steps = Column(JSON)  # ReAct pattern steps
    tool_usage = Column(JSON)  # Tools used by the agent
    
    # Error Handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Relationships
    claim = relationship("Claim", back_populates="agent_reports")

class FraudAnalysis(Base):
    __tablename__ = "fraud_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String(50), ForeignKey("claims.claim_id"), nullable=False)
    
    fraud_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    is_flagged = Column(Boolean, default=False, nullable=False)
    
    # Risk Factors
    risk_factors = Column(JSON)  # List of detected risk factors
    duplicate_claims = Column(JSON)  # Similar/duplicate claims found
    provider_history = Column(JSON)  # Provider risk history
    
    # Analysis Details
    analysis_model = Column(String(50))
    processing_time_seconds = Column(Float)
    
    # Audit Fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    claim = relationship("Claim", back_populates="fraud_analyses")

class Exception(Base):
    __tablename__ = "exceptions"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String(50), ForeignKey("claims.claim_id"), nullable=False)
    
    exception_type = Column(String(100), nullable=False)
    exception_details = Column(Text, nullable=False)
    severity = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Resolution
    resolution_action = Column(String(200))
    resolved_at = Column(DateTime)
    resolved_by_id = Column(Integer, ForeignKey("users.id"))
    
    # Learning
    learned_from_case_id = Column(String(50))  # Reference to similar resolved case
    
    # Audit Fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    claim = relationship("Claim", back_populates="exceptions")
    resolved_by = relationship("User")

# Document Management Models
class ClaimDocument(Base):
    __tablename__ = "claim_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # Document Information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    file_hash = Column(String(64))  # SHA-256 hash for integrity
    
    # Classification
    document_type = Column(Enum(DocumentType), default=DocumentType.OTHER, nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False)
    
    # Relationships
    claim_id = Column(String(50), ForeignKey("claims.claim_id"))
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # OCR Processing
    ocr_processed = Column(Boolean, default=False, nullable=False)
    ocr_provider = Column(String(50))  # tesseract, google, azure, openai
    ocr_confidence = Column(Float)
    ocr_processing_time = Column(Float)
    extracted_text = Column(Text)
    extracted_fields = Column(JSON)
    ocr_raw_data = Column(JSON)
    ocr_error = Column(Text)
    
    # Processing Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime)
    last_accessed = Column(DateTime)
    
    # Security and Compliance
    encryption_key_id = Column(String(100))  # For encrypted storage
    retention_until = Column(DateTime)  # Data retention policy
    is_archived = Column(Boolean, default=False, nullable=False)
    
    # Audit Fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    claim = relationship("Claim", back_populates="documents")
    uploaded_by = relationship("User")
    processing_logs = relationship("DocumentProcessingLog", back_populates="document")

class DocumentProcessingLog(Base):
    __tablename__ = "document_processing_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(50), ForeignKey("claim_documents.document_id"), nullable=False)
    
    # Processing Information
    processing_type = Column(String(50), nullable=False)  # ocr, validation, extraction
    processor = Column(String(100), nullable=False)  # Provider or service name
    status = Column(String(20), nullable=False)  # started, completed, failed
    
    # Results
    processing_time_seconds = Column(Float)
    result_data = Column(JSON)
    error_message = Column(Text)
    
    # Configuration
    processing_config = Column(JSON)  # Provider settings, parameters
    
    # Audit Fields
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("ClaimDocument", back_populates="processing_logs")

class DocumentTemplate(Base):
    __tablename__ = "document_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # Template Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    document_type = Column(Enum(DocumentType), nullable=False)
    
    # Field Extraction Rules
    field_extraction_rules = Column(JSON, nullable=False)  # Regex patterns, coordinates
    validation_rules = Column(JSON)  # Field validation rules
    
    # Template Matching
    template_patterns = Column(JSON)  # OCR patterns to identify this template
    confidence_threshold = Column(Float, default=0.8)
    
    # Usage Statistics
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    # Version Control
    version = Column(String(20), default="1.0")
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Audit Fields
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    created_by = relationship("User")

# Audit and Compliance Models
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(String(50), unique=True, index=True, default=lambda: f"AUD-{uuid.uuid4().hex[:8].upper()}")
    
    # Action Information
    action = Column(Enum(AuditAction), nullable=False)
    resource_type = Column(String(50), nullable=False)  # claim, user, decision, etc.
    resource_id = Column(String(50), nullable=False)
    
    # User Information
    user_id = Column(Integer, ForeignKey("users.id"))
    user_email = Column(String(255))
    user_role = Column(String(20))
    
    # Request Information
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(500))
    request_method = Column(String(10))
    request_path = Column(String(500))
    
    # Data Changes
    old_values = Column(JSON)
    new_values = Column(JSON)
    
    # Additional Context
    description = Column(Text)
    extra_data = Column(JSON)  # Renamed from metadata to avoid SQLAlchemy conflict
    
    # Audit Fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")

class SystemMetrics(Base):
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram
    labels = Column(JSON)  # Additional labels for the metric
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(String(50), unique=True, index=True, default=lambda: f"NOT-{uuid.uuid4().hex[:8].upper()}")
    
    # Recipient Information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Notification Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # claim_update, system_alert, etc.
    priority = Column(String(20), default="NORMAL")  # LOW, NORMAL, HIGH, URGENT
    
    # Related Resources
    related_resource_type = Column(String(50))  # claim, user, etc.
    related_resource_id = Column(String(50))
    
    # Status
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime)
    
    # Delivery
    delivery_channels = Column(JSON)  # email, sms, push, in_app
    delivered_at = Column(DateTime)
    
    # Audit Fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime)
    
    # Relationships
    user = relationship("User")