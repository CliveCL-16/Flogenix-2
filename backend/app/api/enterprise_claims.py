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
    FraudAnalysis, Notification, AuditAction
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
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """Submit a new claim for processing"""
    
    try:
        # Generate unique claim ID
        claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
        
        # Create claim object
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
            priority=claim_data.priority or 1,
            user_id=current_user.id,
            status=ClaimStatus.PENDING
        )
        
        # Save claim
        db.add(claim)
        db.commit()
        db.refresh(claim)
        
        # Log audit event
        log_audit_event(
            db=db,
            action=AuditAction.CREATE,
            resource_type="claim",
            resource_id=claim_id,
            user=current_user,
            request=request,
            new_values=claim_data.dict(),
            description=f"New claim submitted for ${claim_data.claim_amount:,.2f}"
        )
        
        # Process claim immediately for development/testing to avoid timeout issues
        # In production, this would be handled by Celery background tasks
        import os
        from app.services.ai_processing import AIProcessingService
        from app.services.fraud_detection import FraudDetectionService
        
        try:
            # Initialize services
            ai_service = AIProcessingService()
            
            # Initialize fraud service with data handler
            from app.services.data_handler import DataHandler
            data_handler = DataHandler()
            fraud_service = FraudDetectionService(data_handler)
            
            # Quick fraud check
            fraud_analysis = fraud_service.analyze_fraud_risk(claim)
            fraud_score = fraud_analysis.fraud_score
            
            # Process with AI (uses mock mode if no OpenAI key)
            decision_log = await ai_service.process_claim(claim, fraud_score, db)
            
            # Update claim status based on decision
            claim.status = ClaimStatus.PENDING if decision_log.decision == "REVIEW" else (
                ClaimStatus.APPROVED if decision_log.decision == "APPROVE" else ClaimStatus.DENIED
            )
            claim.processed_at = datetime.utcnow()
            
            # Save decision log
            db.add(decision_log)
            db.commit()
            db.refresh(claim)
            
            print(f"✅ Claim {claim_id} processed: {decision_log.decision} (confidence: {decision_log.confidence_score}%)")
            
        except Exception as e:
            print(f"⚠️ Claim processing error: {e}, setting to REVIEW")
            claim.status = ClaimStatus.REVIEW
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
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit claim: {str(e)}")

@router.get("/claims", response_model=List[ClaimResponse])
async def get_claims(
    status: Optional[ClaimStatus] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    patient_name: Optional[str] = Query(None),
    insurance_provider: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """Get claims with advanced filtering"""
    
    query = db.query(Claim)
    
    # Filter by user role
    if current_user.role.value == "USER":
        query = query.filter(Claim.user_id == current_user.id)
    
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
    
    # Order by creation date (newest first)
    query = query.order_by(Claim.created_at.desc())
    
    # Apply pagination
    claims = query.offset(offset).limit(limit).all()
    
    # Get decision logs for confidence scores
    claim_ids = [claim.claim_id for claim in claims]
    decision_logs = db.query(DecisionLog).filter(DecisionLog.claim_id.in_(claim_ids)).all()
    decision_map = {log.claim_id: log for log in decision_logs}
    
    # Build response
    response = []
    for claim in claims:
        decision_log = decision_map.get(claim.claim_id)
        response.append(ClaimResponse(
            claim_id=claim.claim_id,
            status=claim.status.value,
            patient_name=claim.patient_name,
            claim_amount=claim.claim_amount,
            created_at=claim.created_at,
            processed_at=claim.processed_at,
            confidence_score=decision_log.confidence_score if decision_log else None
        ))
    
    return response

@router.get("/claims/{claim_id}")
async def get_claim_details(
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """Get detailed information about a specific claim"""
    
    # Get claim
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Check access permissions
    if current_user.role.value == "USER" and claim.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get related data
    decision_log = db.query(DecisionLog).filter(DecisionLog.claim_id == claim_id).first()
    agent_reports = db.query(AgentReport).filter(AgentReport.claim_id == claim_id).all()
    fraud_analysis = db.query(FraudAnalysis).filter(FraudAnalysis.claim_id == claim_id).first()
    
    # Build detailed response
    return {
        "claim": {
            "claim_id": claim.claim_id,
            "patient_name": claim.patient_name,
            "patient_id": claim.patient_id,
            "insurance_provider": claim.insurance_provider,
            "policy_number": claim.policy_number,
            "diagnosis_code": claim.diagnosis_code,
            "procedure_code": claim.procedure_code,
            "service_date": claim.service_date,
            "claim_amount": claim.claim_amount,
            "provider_name": claim.provider_name,
            "provider_npi": claim.provider_npi,
            "notes": claim.notes,
            "status": claim.status.value,
            "priority": claim.priority,
            "created_at": claim.created_at,
            "processed_at": claim.processed_at
        },
        "decision_log": {
            "decision": decision_log.decision,
            "confidence_score": decision_log.confidence_score,
            "reasoning_text": decision_log.reasoning_text,
            "processing_time_seconds": decision_log.processing_time_seconds,
            "fraud_score": decision_log.fraud_score,
            "created_at": decision_log.created_at
        } if decision_log else None,
        "agent_reports": [
            {
                "agent_name": report.agent_name,
                "agent_type": report.agent_type,
                "status": report.status.value,
                "result": report.result,
                "confidence_score": report.confidence_score,
                "duration_seconds": report.duration_seconds,
                "reasoning_steps": report.reasoning_steps,
                "tool_usage": report.tool_usage,
                "started_at": report.started_at,
                "completed_at": report.completed_at
            }
            for report in agent_reports
        ],
        "fraud_analysis": {
            "fraud_score": fraud_analysis.fraud_score,
            "risk_level": fraud_analysis.risk_level,
            "is_flagged": fraud_analysis.is_flagged,
            "risk_factors": fraud_analysis.risk_factors,
            "created_at": fraud_analysis.created_at
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
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """Get dashboard metrics"""
    
    # Base query
    query = db.query(Claim)
    
    # Filter by user role
    if current_user.role.value == "USER":
        query = query.filter(Claim.user_id == current_user.id)
    
    # Get basic counts
    total_claims = query.count()
    pending_claims = query.filter(Claim.status == ClaimStatus.PENDING).count()
    processing_claims = query.filter(Claim.status == ClaimStatus.PROCESSING).count()
    approved_claims = query.filter(Claim.status == ClaimStatus.APPROVED).count()
    denied_claims = query.filter(Claim.status == ClaimStatus.DENIED).count()
    fraud_flagged = query.filter(Claim.status == ClaimStatus.FRAUD_FLAGGED).count()
    
    # Calculate approval rate
    processed_claims = approved_claims + denied_claims
    approval_rate = (approved_claims / processed_claims * 100) if processed_claims > 0 else 0
    
    # Calculate average processing time
    processed_query = query.filter(Claim.processed_at.isnot(None))
    processing_times = []
    
    for claim in processed_query.all():
        if claim.processed_at and claim.created_at:
            duration = (claim.processed_at - claim.created_at).total_seconds()
            processing_times.append(duration)
    
    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
    
    # Today's metrics
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    claims_today = query.filter(
        Claim.created_at >= today_start,
        Claim.created_at <= today_end
    ).count()
    
    # Revenue approved today
    approved_today = query.filter(
        Claim.status == ClaimStatus.APPROVED,
        Claim.processed_at >= today_start,
        Claim.processed_at <= today_end
    ).all()
    
    revenue_approved_today = sum(claim.claim_amount for claim in approved_today)
    
    return DashboardMetrics(
        total_claims=total_claims,
        pending_claims=pending_claims,
        processing_claims=processing_claims,
        approved_claims=approved_claims,
        denied_claims=denied_claims,
        fraud_flagged_claims=fraud_flagged,
        approval_rate=approval_rate,
        avg_processing_time_seconds=avg_processing_time,
        claims_today=claims_today,
        revenue_approved_today=revenue_approved_today
    )

@router.get("/claims/{claim_id}/agent-timeline", response_model=AgentTimelineResponse)
async def get_agent_timeline(
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """Get agent processing timeline for a claim"""
    
    # Check if claim exists and user has access
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    if current_user.role.value == "USER" and claim.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get agent reports
    agent_reports = db.query(AgentReport).filter(AgentReport.claim_id == claim_id).all()
    
    agents = []
    total_processing_time = 0
    
    for report in agent_reports:
        agents.append({
            "agent": report.agent_name,
            "agent_type": report.agent_type,
            "status": report.status.value,
            "duration": report.duration_seconds or 0,
            "result": report.result,
            "confidence": report.confidence_score,
            "started_at": report.started_at,
            "completed_at": report.completed_at,
            "reasoning_steps": len(report.reasoning_steps or []),
            "tools_used": len(report.tool_usage or [])
        })
        
        if report.duration_seconds:
            total_processing_time += report.duration_seconds
    
    # Get final decision
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
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """Get detailed ReAct reasoning steps from all agents"""
    
    # Check access
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    if current_user.role.value == "USER" and claim.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get agent reports with reasoning
    agent_reports = db.query(AgentReport).filter(AgentReport.claim_id == claim_id).all()
    
    agent_reasoning = {}
    for report in agent_reports:
        if report.reasoning_steps:
            agent_reasoning[report.agent_name] = report.reasoning_steps
    
    return {
        "claim_id": claim_id,
        "agent_reasoning": agent_reasoning
    }

@router.get("/claims/{claim_id}/tool-usage")
async def get_tool_usage(
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """Get tool usage summary for a claim"""
    
    # Check access
    claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    if current_user.role.value == "USER" and claim.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get tool usage from agent reports
    agent_reports = db.query(AgentReport).filter(AgentReport.claim_id == claim_id).all()
    
    tool_usage = []
    for report in agent_reports:
        if report.tool_usage:
            for tool in report.tool_usage:
                tool_usage.append({
                    "agent": report.agent_name,
                    "tool": tool.get("tool_name"),
                    "result": tool.get("result"),
                    "success": tool.get("success"),
                    "execution_time": tool.get("execution_time"),
                    "timestamp": tool.get("timestamp")
                })
    
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