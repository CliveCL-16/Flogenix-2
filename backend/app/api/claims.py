from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import uuid
import time

from app.models import (
    ClaimSubmission, Claim, ClaimStatus, ClaimDetail, 
    DashboardMetrics, ProcessClaimResponse, FraudAnalysis,
    AgentTimelineResponse, AgentReasoningResponse, ToolUsageResponse
)
from app.services.data_handler import DataHandler
from app.services.validation import ValidationService
from app.services.ai_processing import AIProcessingService
from app.services.fraud_detection import FraudDetectionService
from app.services.exception_handling import ExceptionHandlingService

router = APIRouter()
data_handler = DataHandler()
ai_service = AIProcessingService()
fraud_service = FraudDetectionService(data_handler)
exception_service = ExceptionHandlingService(data_handler)


@router.post("/claims/submit", response_model=Claim)
async def submit_claim(claim_submission: ClaimSubmission):
    """Submit a new claim for processing"""
    
    # Generate unique claim ID
    claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
    
    # Create claim object
    claim = Claim(
        **claim_submission.model_dump(),
        claim_id=claim_id,
        status=ClaimStatus.PENDING,
        created_at=datetime.now()
    )
    
    # Validate claim data
    is_valid, errors = ValidationService.validate_claim_data(claim)
    if not is_valid:
        raise HTTPException(status_code=400, detail={"errors": errors})
    
    # Save claim
    saved_claim = data_handler.save_claim(claim)
    
    return saved_claim


@router.get("/claims", response_model=List[Claim])
async def get_claims(status: Optional[ClaimStatus] = Query(None, description="Filter by claim status")):
    """Get all claims, optionally filtered by status"""
    claims = data_handler.get_all_claims(status_filter=status)
    return claims


@router.get("/claims/{claim_id}", response_model=ClaimDetail)
async def get_claim_details(claim_id: str):
    """Get detailed information about a specific claim"""
    
    # Get base claim
    claim = data_handler.get_claim_by_id(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Get related data
    decision_log = data_handler.get_decision_by_claim_id(claim_id)
    exception_logs = data_handler.get_exceptions_by_claim_id(claim_id)
    
    # Create detailed response
    claim_detail = ClaimDetail(
        **claim.model_dump(),
        decision_log=decision_log,
        exception_logs=exception_logs
    )
    
    return claim_detail


@router.get("/dashboard/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """Get dashboard metrics for overview"""
    metrics = data_handler.get_dashboard_metrics()
    return metrics


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@router.post("/claims/{claim_id}/process", response_model=ProcessClaimResponse)
async def process_claim(claim_id: str):
    """Process a pending claim with AI decision making"""
    start_time = time.time()
    
    # Get claim
    claim = data_handler.get_claim_by_id(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    if claim.status != ClaimStatus.PENDING:
        raise HTTPException(status_code=400, detail="Claim is not in pending status")
    
    try:
        # Run fraud detection
        fraud_analysis = fraud_service.analyze_fraud_risk(claim)
        
        # Check for exceptions
        exceptions = exception_service.detect_exceptions(claim)
        
        # Handle exceptions if any
        if exceptions:
            for exception in exceptions:
                exception_service.handle_exception(
                    claim, 
                    exception["type"], 
                    exception["details"]
                )
        
        # Process with AI
        decision_log = await ai_service.process_claim(claim, fraud_analysis.fraud_score)
        
        # Update claim status based on decision
        if fraud_analysis.is_flagged:
            claim.status = ClaimStatus.FRAUD_FLAGGED
        elif decision_log.decision.value == "APPROVE":
            claim.status = ClaimStatus.APPROVED
        elif decision_log.decision.value == "DENY":
            claim.status = ClaimStatus.DENIED
        else:  # REVIEW
            claim.status = ClaimStatus.PENDING_REVIEW
        
        claim.processed_at = datetime.now()
        
        # Save updates
        data_handler.save_claim(claim)
        data_handler.save_decision_log(decision_log)
        
        processing_time = time.time() - start_time
        
        return ProcessClaimResponse(
            claim_id=claim_id,
            status=claim.status,
            decision=decision_log.decision,
            confidence_score=decision_log.confidence_score,
            reasoning_text=decision_log.reasoning_text,
            fraud_score=fraud_analysis.fraud_score,
            processing_time_seconds=round(processing_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/claims/{claim_id}/fraud-analysis", response_model=FraudAnalysis)
async def get_fraud_analysis(claim_id: str):
    """Get fraud analysis for a specific claim"""
    
    claim = data_handler.get_claim_by_id(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    fraud_analysis = fraud_service.analyze_fraud_risk(claim)
    return fraud_analysis


@router.post("/claims/{claim_id}/handle-exception")
async def handle_exception(claim_id: str, exception_type: str, exception_details: str = ""):
    """Handle an exception for a specific claim"""
    
    claim = data_handler.get_claim_by_id(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    result = exception_service.handle_exception(claim, exception_type, exception_details)
    return result


@router.get("/claims/{claim_id}/agent-timeline", response_model=AgentTimelineResponse)
async def get_agent_timeline(claim_id: str):
    """Get agent processing timeline for a claim"""
    
    claim = data_handler.get_claim_by_id(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    agents = ai_service.get_agent_timeline(claim_id)
    
    return AgentTimelineResponse(
        claim_id=claim_id,
        agents=agents
    )


@router.get("/claims/{claim_id}/agent-reasoning", response_model=AgentReasoningResponse)
async def get_agent_reasoning(claim_id: str):
    """Get detailed reasoning steps from all agents"""
    
    claim = data_handler.get_claim_by_id(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    agent_reasoning = ai_service.get_agent_reasoning(claim_id)
    
    return AgentReasoningResponse(
        claim_id=claim_id,
        agent_reasoning=agent_reasoning
    )


@router.get("/claims/{claim_id}/tool-usage", response_model=ToolUsageResponse)
async def get_tool_usage(claim_id: str):
    """Get tool usage summary for a claim"""
    
    claim = data_handler.get_claim_by_id(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    tool_usage = ai_service.get_tool_usage(claim_id)
    
    return ToolUsageResponse(
        claim_id=claim_id,
        tool_usage=tool_usage
    )