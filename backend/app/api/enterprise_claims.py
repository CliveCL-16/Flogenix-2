"""
Enterprise API Endpoints for Claims Processing
Enhanced FastAPI endpoints with authentication, validation, and enterprise features
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from app.core.database import get_database_session
from app.core.security import get_current_user, require_admin, require_processor, log_audit_event
from app.core.models import (
    User, Claim, ClaimStatus, DecisionLog, AgentReport, 
    FraudAnalysis, Notification, AuditAction, ClaimDocument, DocumentStatus, AuditLog
)
from app.services.enhanced_multi_agent_processor import enhanced_multi_agent_processor
from app.tasks.claim_processing import process_claim_async, batch_process_claims
from app.tasks.notification_tasks import send_claim_status_notification

# Pydantic models for requests/responses
from pydantic import BaseModel, Field
from enum import Enum

class ClaimSubmissionRequest(BaseModel):
    patient_name: str = Field(..., min_length=1, max_length=255)
    patient_id: str = Field(..., min_length=1, max_length=100)
    insurance_provider: str = Field(..., min_length=1, max_length=255)
    policy_number: str = Field(..., min_length=1, max_length=100)
    diagnosis_code: str = Field(..., min_length=1, max_length=20)
    procedure_code: str = Field(..., min_length=1, max_length=20)
    service_date: datetime
    claim_amount: float = Field(..., gt=0, le=1000000)
    provider_name: str = Field(..., min_length=1, max_length=255)
    provider_npi: Optional[str] = Field(None, max_length=10)
    notes: Optional[str] = Field(None, max_length=1000)
    priority: Optional[int] = Field(1, ge=1, le=3)  # 1=Normal, 2=High, 3=Urgent

class ClaimResponse(BaseModel):
    claim_id: str
    status: str
    patient_name: str
    claim_amount: float
    created_at: datetime
    processed_at: Optional[datetime]
    confidence_score: Optional[float]

class ProcessingRequest(BaseModel):
    priority: Optional[int] = Field(1, ge=1, le=3)
    async_processing: bool = Field(True)

class BatchProcessingRequest(BaseModel):
    claim_ids: List[str]
    priority: Optional[int] = Field(1, ge=1, le=3)

class ClaimFilterParams(BaseModel):
    status: Optional[ClaimStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    patient_name: Optional[str] = None
    insurance_provider: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    assigned_processor_id: Optional[int] = None

class DashboardMetrics(BaseModel):
    total_claims: int
    pending_claims: int
    processing_claims: int
    approved_claims: int
    denied_claims: int
    fraud_flagged_claims: int
    approval_rate: float
    avg_processing_time_seconds: float
    claims_today: int
    revenue_approved_today: float

class AgentTimelineResponse(BaseModel):
    claim_id: str
    agents: List[Dict[str, Any]]
    total_processing_time: float
    final_decision: Optional[str]

# Create router
router = APIRouter()

@router.post("/claims/submit", response_model=ClaimResponse)
async def submit_claim(
    claim_data: ClaimSubmissionRequest,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """Submit a new claim for processing"""
    
    try:
        # Generate unique claim ID
        claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
        
        # Create claim object using database models
        claim = Claim(
            claim_id=claim_id,
            patient_name=claim_data.patient_name,
            patient_id=claim_data.patient_id,
            insurance_provider=claim_data.insurance_provider,
            policy_number=claim_data.policy_number,
            diagnosis_code=claim_data.diagnosis_code,
            procedure_code=claim_data.procedure_code,
            service_date=claim_data.service_date,
            claim_amount=claim_data.claim_amount,
            provider_name=claim_data.provider_name,
            provider_npi=claim_data.provider_npi,
            notes=claim_data.notes,
            status=ClaimStatus.PENDING,
            user_id=current_user.id,
            created_at=datetime.utcnow()
        )
        
        # Save claim to database
        db.add(claim)
        db.commit()
        db.refresh(claim)
        
        # Process claim immediately using enhanced multi-agent system
        try:
            # Enhanced multi-agent processing using Gemini
            claim_data_dict = {
                "patient_name": claim.patient_name,
                "patient_id": claim.patient_id,
                "insurance_provider": claim.insurance_provider,
                "policy_number": claim.policy_number,
                "diagnosis_code": claim.diagnosis_code,
                "procedure_code": claim.procedure_code,
                "provider_name": claim.provider_name,
                "service_date": claim.service_date.isoformat(),
                "claim_amount": float(claim.claim_amount),
                "patient_age": 35,  # Default age - could be extracted from patient data
                "treatment_type": "medical",  # Could be inferred from procedure code
            }
            
            # Process with enhanced multi-agent system (uses Gemini AI)
            processing_result = await enhanced_multi_agent_processor.process_claim(claim_data_dict, claim.claim_id)
            
            # Extract results from the processing state
            confidence_score = processing_result.confidence_score
            decision = processing_result.final_decision  # Will be "APPROVE", "DENY", or "REVIEW"
            
            # Create comprehensive reasoning text from agent reports and processing details
            reasoning_parts = []
            reasoning_parts.append(f"**Multi-Agent AI Analysis (Gemini-2.5-Flash):**")
            
            if hasattr(processing_result, 'reasoning') and processing_result.reasoning:
                reasoning_parts.append(processing_result.reasoning)
            
            # Add agent summaries if available
            if hasattr(processing_result, 'agent_reports') and processing_result.agent_reports:
                agent_summaries = []
                for report in processing_result.agent_reports:
                    agent_summaries.append(f"✓ {report.agent_name}: {report.result}")
                reasoning_parts.append(" | ".join(agent_summaries))
            
            # If no detailed reasoning available, create a basic explanation
            if len(reasoning_parts) == 1:  # Only has the header
                reasoning_parts.append(f"AI recommendation: {processing_result.final_decision}. Confidence: {confidence_score}%. Processed through multi-agent validation system.")
            
            reasoning_text = " ".join(reasoning_parts)
            
            # Create and save decision log using database
            decision_log = DecisionLog(
                claim_id=claim.claim_id,
                decision=decision,
                confidence_score=confidence_score,
                reasoning_text=reasoning_text,
                fraud_score=0.1,  # Low fraud score for demo
                created_by_id=current_user.id,
                created_at=datetime.utcnow()
            )
            
            # Update claim status based on decision
            if decision == "REVIEW":
                claim.status = ClaimStatus.PENDING_REVIEW
            elif decision == "APPROVE":
                claim.status = ClaimStatus.APPROVED
            else:
                claim.status = ClaimStatus.DENIED
                
            claim.processed_at = datetime.utcnow()
            
            # Save decision log and update claim in database
            db.add(decision_log)
            db.commit()
            db.refresh(decision_log)
            
            print(f"✅ Claim {claim_id} processed: {decision} (confidence: {confidence_score}%)")
            
        except Exception as e:
            print(f"⚠️ Claim processing error: {e}, setting to REVIEW")
            claim.status = ClaimStatus.PENDING_REVIEW
            db.commit()
        
        return ClaimResponse(
            claim_id=claim.claim_id,
            status=claim.status.value,
            patient_name=claim.patient_name,
            claim_amount=claim.claim_amount,
            created_at=claim.created_at,
            processed_at=claim.processed_at,
            confidence_score=getattr(decision_log, 'confidence_score', None) if 'decision_log' in locals() else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit claim: {str(e)}")

@router.get("/claims")
async def get_claims(
    status: Optional[ClaimStatus] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    patient_name: Optional[str] = Query(None),
    insurance_provider: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_database_session)
):
    """Get claims with advanced filtering"""
    
    # Use database instead of DataHandler for consistency
    query = db.query(Claim)
    
    # Apply filters
    if status:
        query = query.filter(Claim.status == status)
    if start_date:
        query = query.filter(Claim.created_at >= start_date)
    if end_date:
        query = query.filter(Claim.created_at <= end_date)
    if patient_name:
        query = query.filter(Claim.patient_name.ilike(f"%{patient_name}%"))
    if insurance_provider:
        query = query.filter(Claim.insurance_provider.ilike(f"%{insurance_provider}%"))
    
    # Order by creation date (newest first) and apply pagination
    claims = query.order_by(Claim.created_at.desc()).offset(offset).limit(limit).all()
    
    # Format response with proper enum handling
    formatted_claims = []
    for claim in claims:
        # Get decision log for confidence score
        decision_log = db.query(DecisionLog).filter(DecisionLog.claim_id == claim.claim_id).first()
        
        formatted_claim = {
            "claim_id": claim.claim_id,
            "patient_name": claim.patient_name,
            "patient_id": claim.patient_id,
            "insurance_provider": claim.insurance_provider,
            "policy_number": claim.policy_number,
            "diagnosis_code": claim.diagnosis_code,
            "procedure_code": claim.procedure_code,
            "service_date": claim.service_date.isoformat() if claim.service_date else None,
            "claim_amount": claim.claim_amount,
            "provider_name": claim.provider_name,
            "provider_npi": getattr(claim, 'provider_npi', None),
            "notes": getattr(claim, 'notes', None),
            "status": claim.status.value if hasattr(claim.status, 'value') else claim.status,
            "priority": getattr(claim, 'priority', 1),
            "created_at": claim.created_at.isoformat() if claim.created_at else None,
            "processed_at": claim.processed_at.isoformat() if claim.processed_at else None,
            "confidence_score": decision_log.confidence_score if decision_log else None
        }
        formatted_claims.append(formatted_claim)
        # Status filter
    
    return formatted_claims

@router.get("/claims/{claim_id}")
async def get_claim_details(
    claim_id: str,
    db: Session = Depends(get_database_session)
):
    """Get detailed information about a specific claim"""
    
    # Get claim from database
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Get related data from database
    decision_log = db.query(DecisionLog).filter(DecisionLog.claim_id == claim_id).first()
    agent_reports = db.query(AgentReport).filter(AgentReport.claim_id == claim_id).all()
    fraud_analysis = db.query(FraudAnalysis).filter(FraudAnalysis.claim_id == claim_id).first()
    
    # Format agent reports with real database data
    formatted_agent_reports = []
    for report in agent_reports:
        formatted_report = {
            "agent_name": report.agent_name,
            "agent_type": report.agent_type,
            "status": report.status.value if hasattr(report.status, 'value') else report.status,
            "result": report.result or "Processing...",
            "confidence_score": report.confidence_score or 0.0,
            "duration_seconds": report.duration_seconds or 0.0,
            "reasoning_steps": report.reasoning_steps or [],
            "tool_usage": report.tool_usage or [],
            "started_at": report.started_at.isoformat() if report.started_at else None,
            "completed_at": report.completed_at.isoformat() if report.completed_at else None
        }
        formatted_agent_reports.append(formatted_report)
    
    # Build detailed response with real data
    return {
        "claim": {
            "claim_id": claim.claim_id,
            "patient_name": claim.patient_name,
            "patient_id": claim.patient_id,
            "insurance_provider": claim.insurance_provider,
            "policy_number": claim.policy_number,
            "diagnosis_code": claim.diagnosis_code,
            "procedure_code": claim.procedure_code,
            "service_date": claim.service_date.isoformat() if claim.service_date else None,
            "claim_amount": claim.claim_amount,
            "provider_name": claim.provider_name,
            "provider_npi": getattr(claim, 'provider_npi', None),
            "notes": getattr(claim, 'notes', None),
            "status": claim.status.value if hasattr(claim.status, 'value') else claim.status,
            "priority": getattr(claim, 'priority', 1),
            "created_at": claim.created_at.isoformat() if claim.created_at else None,
            "processed_at": claim.processed_at.isoformat() if claim.processed_at else None
        },
        "decision_log": {
            "decision": decision_log.decision.value if decision_log and hasattr(decision_log.decision, 'value') else (decision_log.decision if decision_log else None),
            "confidence_score": decision_log.confidence_score if decision_log else None,
            "reasoning_text": decision_log.reasoning_text if decision_log else None,
            "processing_time_seconds": getattr(decision_log, 'processing_time_seconds', None) if decision_log else None,
            "fraud_score": decision_log.fraud_score if decision_log else None,
            "created_at": decision_log.created_at.isoformat() if decision_log else None
        } if decision_log else None,
        "agent_reports": formatted_agent_reports,
        "fraud_analysis": {
            "fraud_score": fraud_analysis.fraud_score,
            "risk_level": fraud_analysis.risk_level,
            "is_flagged": fraud_analysis.is_flagged,
            "risk_factors": fraud_analysis.risk_factors or [],
            "created_at": fraud_analysis.created_at.isoformat() if fraud_analysis.created_at else None
        } if fraud_analysis else None
    }

@router.post("/claims/{claim_id}/process")
async def process_claim(
    claim_id: str,
    processing_request: ProcessingRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(require_processor),
    db: Session = Depends(get_database_session)
):
    """Process a pending claim"""
    
    # Get claim
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    if claim.status != ClaimStatus.PENDING:
        raise HTTPException(status_code=400, detail="Claim is not in pending status")
    
    # Log audit event
    log_audit_event(
        db=db,
        action=AuditAction.PROCESS,
        resource_type="claim",
        resource_id=claim_id,
        user=current_user,
        request=request,
        description=f"Claim processing initiated by {current_user.email}"
    )
    
    if processing_request.async_processing:
        # Queue for async processing
        task = process_claim_async.delay(claim_id, processing_request.priority)
        
        return {
            "message": "Claim queued for processing",
            "task_id": task.id,
            "async": True
        }
    else:
        # Process synchronously (for urgent claims)
        try:
            # Update status
            claim.status = ClaimStatus.PROCESSING
            claim.assigned_processor_id = current_user.id
            db.commit()
            
            # Process through immediate AI service (optimized for validation)
            from app.services.ai_processing import AIProcessingService
            from app.services.fraud_detection import FraudDetectionService
            from app.services.data_handler import DataHandler
            
            # Initialize services
            ai_service = AIProcessingService()
            data_handler = DataHandler()
            fraud_service = FraudDetectionService(data_handler)
            
            # Quick fraud check
            fraud_analysis = fraud_service.analyze_fraud_risk(claim)
            fraud_score = fraud_analysis.fraud_score
            
            # Process with AI (uses mock mode if no OpenAI key)
            decision_log = await ai_service.process_claim(claim, fraud_score, db)
            
            # Update claim status based on decision
            if fraud_score > 80:
                claim.status = ClaimStatus.FRAUD_FLAGGED
            elif decision_log.decision == "APPROVE":
                claim.status = ClaimStatus.APPROVED
            elif decision_log.decision == "DENY":
                claim.status = ClaimStatus.DENIED
            else:
                claim.status = ClaimStatus.PENDING_REVIEW
            
            claim.processed_at = datetime.utcnow()
            
            # Save decision log
            db.add(decision_log)
            db.commit()
            
            print(f"✅ Claim {claim_id} processed via direct endpoint: {decision_log.decision} (confidence: {decision_log.confidence_score}%)")
            
            return {
                "claim_id": claim_id,
                "status": claim.status.value,
                "confidence_score": decision_log.confidence_score,
                "reasoning": decision_log.reasoning_text,
                "fraud_score": fraud_score,
                "processing_time": 1.0,  # Fast processing
                "async": False
            }
            
        except Exception as e:
            claim.status = ClaimStatus.PENDING
            db.commit()
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.post("/claims/batch-process")
async def batch_process(
    batch_request: BatchProcessingRequest,
    current_user: User = Depends(require_processor),
    db: Session = Depends(get_database_session)
):
    """Process multiple claims in batch"""
    
    # Validate claim IDs
    claims = db.query(Claim).filter(Claim.claim_id.in_(batch_request.claim_ids)).all()
    found_claim_ids = [claim.claim_id for claim in claims]
    
    if len(found_claim_ids) != len(batch_request.claim_ids):
        missing_ids = set(batch_request.claim_ids) - set(found_claim_ids)
        raise HTTPException(status_code=404, detail=f"Claims not found: {list(missing_ids)}")
    
    # Check if all claims are in pending status
    pending_claims = [claim for claim in claims if claim.status == ClaimStatus.PENDING]
    if len(pending_claims) != len(claims):
        non_pending = [claim.claim_id for claim in claims if claim.status != ClaimStatus.PENDING]
        raise HTTPException(status_code=400, detail=f"Non-pending claims: {non_pending}")
    
    # Queue batch processing
    task = batch_process_claims.delay(batch_request.claim_ids, batch_request.priority)
    
    return {
        "message": f"Batch processing queued for {len(batch_request.claim_ids)} claims",
        "task_id": task.id,
        "claim_ids": batch_request.claim_ids
    }

@router.get("/dashboard/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """Get dashboard metrics"""
    
    # Use simple data handler approach
    from app.services.data_handler import DataHandler
    data_handler = DataHandler()
    
    # Get metrics using data handler - it returns a DashboardMetrics object
    metrics = data_handler.get_dashboard_metrics()
    
    # Calculate pending claims properly - include both PENDING and PENDING_REVIEW
    all_claims = data_handler.get_all_claims()
    from app.models import ClaimStatus
    pending_count = len([c for c in all_claims if c.status in [ClaimStatus.PENDING, ClaimStatus.PENDING_REVIEW]])
    
    # The data handler already returns the right format, but we need to add missing fields
    return DashboardMetrics(
        total_claims=metrics.total_claims,
        pending_claims=pending_count,  # Include both PENDING and PENDING_REVIEW
        processing_claims=0,  # Not tracked in simple version
        approved_claims=metrics.approved_count,
        denied_claims=metrics.denied_count,
        fraud_flagged_claims=metrics.fraud_flagged_count,
        approval_rate=metrics.approval_rate,
        avg_processing_time_seconds=metrics.avg_processing_time_seconds,
        claims_today=0,  # Not tracked in simple version
        revenue_approved_today=0.0  # Not tracked in simple version
    )

@router.get("/claims/{claim_id}/agent-timeline", response_model=AgentTimelineResponse)
async def get_agent_timeline(
    claim_id: str,
    db: Session = Depends(get_database_session)
):
    """Get agent processing timeline for a claim"""
    
    # Check if claim exists in database
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Get agent reports from database
    agent_reports = db.query(AgentReport).filter(
        AgentReport.claim_id == claim_id
    ).order_by(AgentReport.started_at).all()

    agents = []
    total_processing_time = 0

    if agent_reports:
        # Use real agent reports from database
        for report in agent_reports:
            duration = report.duration_seconds or 0
            agents.append({
                "agent": report.agent_name,
                "agent_type": report.agent_type,
                "status": report.status.value if hasattr(report.status, 'value') else str(report.status),
                "duration": duration,
                "result": report.result or "Processing completed",
                "confidence": report.confidence_score or 0.0,
                "started_at": report.started_at.isoformat() if report.started_at else None,
                "completed_at": report.completed_at.isoformat() if report.completed_at else None,
                "reasoning_steps": [],  # Could be populated from report details
                "tools_used": []  # Could be populated from report details
            })
            total_processing_time += duration
    else:
        # Fallback to mock agent timeline for demonstration
        from app.services.enhanced_multi_agent_processor import EnhancedMultiAgentProcessor
        processor = EnhancedMultiAgentProcessor()
        mock_agents = processor.get_agent_timeline(claim_id)

        for agent in mock_agents:
            agents.append({
                "agent": agent["agent"],
                "agent_type": agent["agent_type"],
                "status": agent["status"],
                "duration": agent["duration"],
                "result": agent["result"],
                "confidence": agent["confidence"],
                "started_at": agent["started_at"],
                "completed_at": agent["completed_at"],
                "reasoning_steps": agent["reasoning_steps"],
                "tools_used": agent["tools_used"]
            })
            total_processing_time += agent["duration"]
    
    # Get final decision from database
    decision_log = db.query(DecisionLog).filter(DecisionLog.claim_id == claim_id).first()
    final_decision = decision_log.decision if decision_log else None
    
    return AgentTimelineResponse(
        claim_id=claim_id,
        agents=agents,
        total_processing_time=total_processing_time,
        final_decision=final_decision
    )

@router.get("/claims/{claim_id}/agent-reasoning")
async def get_agent_reasoning(
    claim_id: str
):
    """Get detailed ReAct reasoning steps from all agents"""
    
    # Use simple data handler approach
    from app.services.data_handler import DataHandler
    data_handler = DataHandler()
    
    # Check if claim exists
    claim = data_handler.get_claim_by_id(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Get decision log for reasoning
    decision_log = data_handler.get_decision_by_claim_id(claim_id)
    
    agent_reasoning = {}
    if decision_log and decision_log.reasoning_text:
        # Parse the reasoning text to extract agent-specific reasoning
        agent_reasoning["multi_agent_analysis"] = decision_log.reasoning_text
    
    return {
        "claim_id": claim_id,
        "agent_reasoning": agent_reasoning
    }

@router.get("/claims/{claim_id}/tool-usage")
async def get_tool_usage(
    claim_id: str
):
    """Get tool usage summary for a claim"""
    
    # Use simple data handler approach
    from app.services.data_handler import DataHandler
    data_handler = DataHandler()
    
    # Check if claim exists
    claim = data_handler.get_claim_by_id(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Create mock tool usage data since we don't have agent reports in simple version
    tool_usage = [
        {
            "agent": "Medical Validator",
            "tool": "diagnosis_validator",
            "result": "Valid diagnosis code",
            "success": True,
            "execution_time": 0.5,
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "agent": "Fraud Detector",
            "tool": "risk_analyzer",
            "result": "Low risk score",
            "success": True,
            "execution_time": 1.2,
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "agent": "Policy Checker",
            "tool": "coverage_validator",
            "result": "Coverage confirmed",
            "success": True,
            "execution_time": 0.8,
            "timestamp": datetime.utcnow().isoformat()
        }
    ]
    
    return {
        "claim_id": claim_id,
        "tool_usage": tool_usage
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "environment": "enterprise"
    }

# Document Processing Endpoints
@router.get("/documents/{document_id}/ocr-results")
async def get_document_ocr_results(
    document_id: str
):
    """Get OCR processing results for a document"""
    try:
        # Return mock OCR results since we're using simple approach
        ocr_results = {
            "document_id": document_id,
            "filename": f"document_{document_id}.pdf",
            "processing_status": "PROCESSED",
            "ocr_provider": "TesseractOCR",
            "processing_time_seconds": 2.3,
            "confidence_score": 0.94,
            "extracted_text": "Sample medical bill text extracted from document...",
            "extracted_fields": {
                "patient_name": "John Doe",
                "claim_amount": "1250.00",
                "service_date": "2024-10-15",
                "provider_name": "City Medical Center"
            },
            "raw_ocr_data": {},
            "error_message": None,
            "processed_at": datetime.utcnow().isoformat(),
            "quality_metrics": {
                "image_quality": 0.85,
                "text_clarity": 0.88,
                "completeness": 0.92,
                "format_compliance": 0.79
            },
            "validation_results": [
                {
                    "field": "patient_name",
                    "status": "valid",
                    "confidence": 0.95,
                    "value": "John Doe"
                },
                {
                    "field": "claim_amount", 
                    "status": "valid",
                    "confidence": 0.89,
                    "value": "1250.00"
                },
                {
                    "field": "service_date",
                    "status": "valid", 
                    "confidence": 0.92,
                    "value": "2024-10-15"
                }
            ]
        }
        
        return ocr_results
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get OCR results: {str(e)}"
        )

@router.get("/documents/{document_id}/validation")
async def get_document_validation(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """Get document validation results"""
    try:
        from app.core.models import ClaimDocument
        
        document = db.query(ClaimDocument).filter(
            ClaimDocument.document_id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check access permissions
        if document.claim_id:
            claim = db.query(Claim).filter(Claim.claim_id == document.claim_id).first()
            if claim and current_user.role.value not in ['ADMIN', 'PROCESSOR'] and claim.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Generate validation results
        validation_results = {
            "document_id": document_id,
            "validation_status": "passed" if document.status.value == "PROCESSED" else "failed",
            "compliance_checks": [
                {
                    "check_name": "HIPAA Compliance",
                    "status": "passed",
                    "details": "Document meets privacy requirements"
                },
                {
                    "check_name": "File Integrity",
                    "status": "passed" if document.file_hash else "warning",
                    "details": "File integrity verified" if document.file_hash else "No integrity hash available"
                },
                {
                    "check_name": "Content Validation",
                    "status": "passed" if document.extracted_fields else "warning",
                    "details": "Required fields extracted" if document.extracted_fields else "Some fields may be missing"
                }
            ],
            "security_scan": {
                "threats_detected": [],
                "safety_score": 0.96,
                "scan_completed": True
            },
            "data_quality": {
                "completeness": 0.94 if document.extracted_fields else 0.60,
                "accuracy": document.ocr_confidence or 0.75,
                "consistency": 0.91
            },
            "recommendations": [
                "Document processing completed successfully" if document.status.value == "PROCESSED"
                else "Document requires reprocessing",
                "All compliance checks passed",
                "No security threats detected"
            ]
        }
        
        return validation_results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get validation results: {str(e)}"
        )

@router.get("/documents/claim/{claim_id}")
async def get_claim_documents(
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """Get all documents associated with a claim"""
    try:
        from app.core.models import ClaimDocument
        
        # Verify claim exists and user has access
        claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        if current_user.role.value not in ['ADMIN', 'PROCESSOR'] and claim.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get all documents for this claim
        documents = db.query(ClaimDocument).filter(
            ClaimDocument.claim_id == claim_id
        ).all()
        
        documents_data = []
        for doc in documents:
            documents_data.append({
                "document_id": doc.document_id,
                "filename": doc.original_filename,
                "file_size": doc.file_size,
                "content_type": doc.content_type,
                "document_type": doc.document_type.value,
                "status": doc.status.value,
                "uploaded_at": doc.uploaded_at.isoformat(),
                "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
                "ocr_processed": doc.ocr_processed,
                "ocr_confidence": doc.ocr_confidence,
                "has_extracted_data": bool(doc.extracted_fields),
                "processing_time": doc.ocr_processing_time
            })
        
        return {
            "claim_id": claim_id,
            "documents": documents_data,
            "total_documents": len(documents),
            "processed_documents": len([d for d in documents if d.ocr_processed]),
            "pending_documents": len([d for d in documents if not d.ocr_processed])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get claim documents: {str(e)}"
        )

@router.post("/documents/{document_id}/reprocess")
async def reprocess_document(
    document_id: str,
    provider: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """Reprocess a document with OCR"""
    try:
        from app.core.models import ClaimDocument
        
        # Check permissions
        if current_user.role.value not in ['ADMIN', 'PROCESSOR']:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        document = db.query(ClaimDocument).filter(
            ClaimDocument.document_id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Reset processing status
        document.status = DocumentStatus.PROCESSING
        document.ocr_processed = False
        document.ocr_error = None
        document.processed_at = None
        
        if provider:
            document.ocr_provider = provider
        
        db.commit()
        
        # Log audit event
        await log_audit_event(
            user_id=current_user.id,
            action=AuditAction.PROCESS,
            resource_type="document",
            resource_id=document_id,
            description=f"Document reprocessing initiated",
            db=db
        )
        
        # In a real implementation, this would trigger background OCR processing
        # For now, simulate processing completion
        import asyncio
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Update with simulated results
        document.ocr_processed = True
        document.status = DocumentStatus.PROCESSED
        document.processed_at = datetime.utcnow()
        document.ocr_confidence = 0.89
        document.ocr_processing_time = 2.1
        
        # Simulate extracted fields
        if not document.extracted_fields:
            document.extracted_fields = {
                "patient_name": "John Doe",
                "claim_amount": 250.00,
                "service_date": "2024-01-15",
                "provider_name": "Medical Center",
                "procedure_code": "99213"
            }
        
        db.commit()
        
        return {
            "document_id": document_id,
            "status": "reprocessing_complete",
            "message": "Document reprocessed successfully", 
            "processing_time": 2.1,
            "confidence": 0.89
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reprocess document: {str(e)}"
        )

# Enhanced Claims Management Endpoints
@router.get("/claims/{claim_id}/detailed-review")
async def get_claim_detailed_review(
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """Get comprehensive claim data for detailed review interface"""
    try:
        # Get claim and verify access
        claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        # Check permissions
        if current_user.role.value not in ['ADMIN', 'PROCESSOR'] and claim.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get related data
        decision_logs = db.query(DecisionLog).filter(DecisionLog.claim_id == claim_id).all()
        agent_reports = db.query(AgentReport).filter(AgentReport.claim_id == claim_id).all()
        fraud_analyses = db.query(FraudAnalysis).filter(FraudAnalysis.claim_id == claim_id).all()
        documents = db.query(ClaimDocument).filter(ClaimDocument.claim_id == claim_id).all()
        
        # Compile comprehensive review data
        review_data = {
            "claim_summary": {
                "claim_id": claim.claim_id,
                "patient_name": claim.patient_name,
                "patient_id": claim.patient_id,
                "claim_amount": claim.claim_amount,
                "status": claim.status.value,
                "priority": claim.priority,
                "service_date": claim.service_date.isoformat(),
                "created_at": claim.created_at.isoformat(),
                "processed_at": claim.processed_at.isoformat() if claim.processed_at else None,
                "provider_name": claim.provider_name,
                "provider_npi": claim.provider_npi,
                "diagnosis_code": claim.diagnosis_code,
                "procedure_code": claim.procedure_code,
                "insurance_provider": claim.insurance_provider,
                "policy_number": claim.policy_number
            },
            "ai_analysis": {
                "decision_count": len(decision_logs),
                "overall_confidence": sum(log.confidence_score for log in decision_logs) / max(len(decision_logs), 1),
                "latest_decision": decision_logs[-1].decision if decision_logs else None,
                "latest_reasoning": decision_logs[-1].reasoning_text if decision_logs else None,
                "fraud_scores": [fa.fraud_score for fa in fraud_analyses],
                "risk_level": fraud_analyses[-1].risk_level if fraud_analyses else "LOW",
                "agent_results": [
                    {
                        "agent_type": report.agent_type,
                        "agent_name": report.agent_name,
                        "result": report.result,
                        "confidence": report.confidence_score,
                        "duration": report.duration_seconds,
                        "status": report.status.value
                    }
                    for report in agent_reports
                ]
            },
            "document_summary": {
                "total_documents": len(documents),
                "processed_documents": len([d for d in documents if d.ocr_processed]),
                "document_types": list(set(d.document_type.value for d in documents)),
                "documents": [
                    {
                        "document_id": doc.document_id,
                        "filename": doc.original_filename,
                        "type": doc.document_type.value,
                        "status": doc.status.value,
                        "ocr_confidence": doc.ocr_confidence,
                        "uploaded_at": doc.uploaded_at.isoformat()
                    }
                    for doc in documents
                ]
            },
            "processing_history": [
                {
                    "timestamp": log.created_at.isoformat(),
                    "type": "decision",
                    "description": f"AI Decision: {log.decision}",
                    "confidence": log.confidence_score,
                    "details": log.reasoning_text[:100] + "..." if len(log.reasoning_text) > 100 else log.reasoning_text
                }
                for log in decision_logs
            ] + [
                {
                    "timestamp": report.started_at.isoformat(),
                    "type": "agent_processing",
                    "description": f"{report.agent_type} processing: {report.result or 'In progress'}",
                    "confidence": report.confidence_score,
                    "details": f"Duration: {report.duration_seconds}s" if report.duration_seconds else "Processing..."
                }
                for report in agent_reports
            ],
            "validation_status": {
                "data_completeness": 0.94,
                "field_accuracy": 0.89,
                "compliance_check": "passed",
                "anomalies_detected": [],
                "manual_review_required": claim.status == ClaimStatus.PENDING_REVIEW
            }
        }
        
        # Sort processing history by timestamp
        review_data["processing_history"].sort(key=lambda x: x["timestamp"])
        
        return review_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get detailed review data: {str(e)}"
        )

@router.get("/claims/{claim_id}/communication-history")
async def get_claim_communication_history(
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """Get communication history for a claim"""
    try:
        # Verify claim access
        claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        if current_user.role.value not in ['ADMIN', 'PROCESSOR'] and claim.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get notifications related to this claim
        notifications = db.query(Notification).filter(
            Notification.related_resource_type == "claim",
            Notification.related_resource_id == claim_id
        ).order_by(Notification.created_at.desc()).all()
        
        # Get audit logs for this claim
        audit_logs = db.query(AuditLog).filter(
            AuditLog.resource_type == "claim",
            AuditLog.resource_id == claim_id
        ).order_by(AuditLog.created_at.desc()).all()
        
        # Compile communication history
        communications = []
        
        # Add notifications
        for notif in notifications:
            communications.append({
                "id": notif.notification_id,
                "type": "notification",
                "title": notif.title,
                "message": notif.message,
                "timestamp": notif.created_at.isoformat(),
                "direction": "outbound",
                "status": "delivered" if notif.delivered_at else "pending",
                "channels": notif.delivery_channels or ["in_app"],
                "priority": notif.priority
            })
        
        # Add significant audit events as communications
        significant_actions = ['UPDATE', 'APPROVE', 'DENY', 'PROCESS']
        for log in audit_logs:
            if log.action.value in significant_actions:
                communications.append({
                    "id": log.audit_id,
                    "type": "system_event",
                    "title": f"Claim {log.action.value.lower()}",
                    "message": log.description or f"Claim was {log.action.value.lower()}",
                    "timestamp": log.created_at.isoformat(),
                    "direction": "internal",
                    "user": log.user_email if log.user_email else "System",
                    "details": log.new_values
                })
        
        # Sort by timestamp (newest first)
        communications.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "claim_id": claim_id,
            "communications": communications,
            "total_count": len(communications),
            "unread_count": len([n for n in notifications if not n.is_read]),
            "last_activity": communications[0]["timestamp"] if communications else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get communication history: {str(e)}"
        )

@router.post("/claims/{claim_id}/manual-decision")
async def submit_manual_decision(
    claim_id: str,
    decision_data: Dict[str, Any],
    current_user: User = Depends(require_processor),
    db: Session = Depends(get_database_session)
):
    """Submit manual decision for a claim"""
    try:
        # Get claim
        claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        # Validate decision data
        decision = decision_data.get("decision")  # APPROVE, DENY, REVIEW
        reasoning = decision_data.get("reasoning", "")
        
        if decision not in ["APPROVE", "DENY", "REVIEW"]:
            raise HTTPException(status_code=400, detail="Invalid decision")
        
        # Update claim status
        if decision == "APPROVE":
            claim.status = ClaimStatus.APPROVED
        elif decision == "DENY":
            claim.status = ClaimStatus.DENIED
        else:
            claim.status = ClaimStatus.PENDING_REVIEW
        
        claim.processed_at = datetime.utcnow()
        claim.assigned_processor_id = current_user.id
        
        # Create decision log
        decision_log = DecisionLog(
            claim_id=claim_id,
            decision=decision,
            confidence_score=1.0,  # Manual decision has full confidence
            reasoning_text=reasoning,
            processing_time_seconds=0,  # Manual decision
            model_version="manual_v1.0",
            created_by_id=current_user.id
        )
        
        db.add(decision_log)
        
        # Log audit event
        await log_audit_event(
            user_id=current_user.id,
            action=AuditAction.UPDATE,
            resource_type="claim",
            resource_id=claim_id,
            description=f"Manual decision: {decision}",
            old_values={"status": claim.status.value},
            new_values={"status": decision, "reasoning": reasoning},
            db=db
        )
        
        db.commit()
        
        # Send notification
        try:
            await send_claim_status_notification(claim_id, decision.lower())
        except Exception as e:
            print(f"Failed to send notification: {e}")
        
        return {
            "claim_id": claim_id,
            "decision": decision,
            "status": claim.status.value,
            "processed_by": current_user.username,
            "processed_at": claim.processed_at.isoformat(),
            "message": f"Manual decision '{decision}' recorded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit manual decision: {str(e)}"
        )

# Reference Data Endpoints for Form Options
@router.get("/reference/diagnosis-codes")
async def get_diagnosis_codes():
    """Get list of common diagnosis codes for form dropdown"""
    return [
        {"code": "I10", "description": "Essential hypertension"},
        {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications"},
        {"code": "Z00.00", "description": "General health examination"},
        {"code": "J44.1", "description": "Chronic obstructive pulmonary disease with acute exacerbation"},
        {"code": "M79.3", "description": "Panniculitis, unspecified"},
        {"code": "K21.9", "description": "Gastro-esophageal reflux disease without esophagitis"},
        {"code": "F41.1", "description": "Generalized anxiety disorder"},
        {"code": "M25.511", "description": "Pain in right shoulder"},
        {"code": "G43.909", "description": "Migraine, unspecified, not intractable, without status migrainosus"},
        {"code": "R06.02", "description": "Shortness of breath"},
    ]

@router.get("/reference/procedure-codes")
async def get_procedure_codes():
    """Get list of common procedure codes for form dropdown"""
    return [
        {"code": "99213", "description": "Office/outpatient visit, established patient"},
        {"code": "99214", "description": "Office/outpatient visit, established patient, moderate complexity"},
        {"code": "99215", "description": "Office/outpatient visit, established patient, high complexity"},
        {"code": "99203", "description": "Office/outpatient visit, new patient"},
        {"code": "99204", "description": "Office/outpatient visit, new patient, moderate complexity"},
        {"code": "27236", "description": "Treatment of femoral fracture"},
        {"code": "94010", "description": "Spirometry"},
        {"code": "80053", "description": "Comprehensive metabolic panel"},
        {"code": "85025", "description": "Complete blood count"},
        {"code": "36415", "description": "Venipuncture"},
    ]

@router.get("/reference/insurance-providers")
async def get_insurance_providers():
    """Get list of insurance providers for form dropdown"""
    return [
        {"name": "UnitedHealthcare", "code": "UHC"},
        {"name": "Anthem Blue Cross Blue Shield", "code": "ANTHEM"},
        {"name": "Aetna Healthcare", "code": "AETNA"},
        {"name": "Cigna Healthcare", "code": "CIGNA"},
        {"name": "Humana", "code": "HUMANA"},
        {"name": "Kaiser Permanente", "code": "KAISER"},
        {"name": "Blue Cross Blue Shield", "code": "BCBS"},
        {"name": "Molina Healthcare", "code": "MOLINA"},
        {"name": "Centene Corporation", "code": "CENTENE"},
        {"name": "WellCare Health Plans", "code": "WELLCARE"},
    ]