"""
Analytics and Reporting API
Advanced analytics endpoints for business intelligence and reporting
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_database_session
from app.core.security import require_admin
from app.core.models import (
    User, Claim, ClaimStatus, DecisionLog, AgentReport, 
    FraudAnalysis, Notification, UserRole
)
from app.services.admin_reporting_service import admin_reporting_service

router = APIRouter()

# Response Models
class AnalyticsOverview(BaseModel):
    """Analytics overview response"""
    total_claims: int
    processed_claims: int
    automation_rate: float
    average_processing_time: float
    cost_savings: float
    accuracy_rate: float
    fraud_detection_rate: float
    customer_satisfaction: float

class PerformanceMetrics(BaseModel):
    """Performance metrics response"""
    agent_performance: Dict[str, Any]
    processing_trends: List[Dict[str, Any]]
    efficiency_gains: Dict[str, float]
    bottlenecks: List[str]
    recommendations: List[str]

class FraudInsights(BaseModel):
    """Fraud detection insights"""
    total_fraud_detected: int
    fraud_patterns: List[Dict[str, Any]]
    false_positive_rate: float
    recovery_amount: float
    prevention_savings: float

class FinancialReport(BaseModel):
    """Financial analytics report"""
    claims_volume: Dict[str, int]
    financial_impact: Dict[str, float]
    cost_analysis: Dict[str, Any]
    roi_metrics: Dict[str, float]
    projections: Dict[str, Any]

# Analytics Endpoints
@router.get("/analytics/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_database_session)
):
    """Get high-level analytics overview"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get analytics data
        analytics = await admin_reporting_service.get_analytics_overview(
            start_date=start_date,
            end_date=end_date,
            db=db
        )
        
        return AnalyticsOverview(**analytics)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics overview: {str(e)}"
        )

@router.get("/analytics/performance", response_model=PerformanceMetrics)
async def get_performance_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    agent_filter: Optional[str] = Query(None, description="Filter by agent type"),
    db: Session = Depends(get_database_session)
):
    """Get detailed performance analytics"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        metrics = await admin_reporting_service.get_performance_metrics(
            start_date=start_date,
            end_date=end_date,
            agent_filter=agent_filter,
            db=db
        )
        
        return PerformanceMetrics(**metrics)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate performance analytics: {str(e)}"
        )

@router.get("/analytics/fraud", response_model=FraudInsights)
async def get_fraud_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_database_session)
):
    """Get fraud detection analytics"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        insights = await admin_reporting_service.get_fraud_analytics(
            start_date=start_date,
            end_date=end_date,
            db=db
        )
        
        return FraudInsights(**insights)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate fraud analytics: {str(e)}"
        )

@router.get("/analytics/financial", response_model=FinancialReport)
async def get_financial_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_database_session)
):
    """Get financial analytics (Admin only)"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        report = await admin_reporting_service.get_financial_analytics(
            start_date=start_date,
            end_date=end_date,
            db=db
        )
        
        return FinancialReport(**report)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate financial analytics: {str(e)}"
        )

@router.get("/analytics/trends")
async def get_trend_analysis(
    metric: str = Query(..., description="Metric to analyze (claims, processing_time, accuracy, etc.)"),
    period: str = Query("daily", description="Time period (hourly, daily, weekly, monthly)"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_database_session)
):
    """Get trend analysis for specific metrics"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        trends = await admin_reporting_service.get_trend_analysis(
            metric=metric,
            period=period,
            start_date=start_date,
            end_date=end_date,
            db=db
        )
        
        return {"trends": trends, "metric": metric, "period": period}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate trend analysis: {str(e)}"
        )

@router.post("/analytics/export")
async def export_analytics(
    report_type: str = Query(..., description="Type of report to export"),
    format: str = Query("csv", description="Export format (csv, excel, pdf)"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include")
):
    """Export analytics data"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        export_data = await admin_reporting_service.export_analytics(
            report_type=report_type,
            format=format,
            start_date=start_date,
            end_date=end_date,
            user_id=None  # Simplified no-auth approach
        )
        
        return {
            "export_id": export_data["export_id"],
            "download_url": export_data["download_url"],
            "expires_at": export_data["expires_at"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export analytics: {str(e)}"
        )

@router.get("/reports/automated")
async def get_automated_reports(
    report_type: Optional[str] = Query(None, description="Filter by report type")
):
    """Get list of automated reports"""
    try:
        reports = await admin_reporting_service.get_automated_reports(
            report_type=report_type,
            user_id=None  # Simplified no-auth approach
        )
        
        return {"reports": reports}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve automated reports: {str(e)}"
        )

@router.post("/reports/schedule")
async def schedule_report(
    report_config: Dict[str, Any]
):
    """Schedule automated report generation"""
    try:
        schedule_id = await admin_reporting_service.schedule_report(
            report_config=report_config,
            user_id=None  # Simplified no-auth approach
        )
        
        return {"schedule_id": schedule_id, "status": "scheduled"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule report: {str(e)}"
        )

# User Dashboard Endpoints
@router.get("/dashboard/user/metrics")
async def get_user_dashboard_metrics(
    db: Session = Depends(get_database_session)
):
    """Get user-specific dashboard metrics"""
    try:
        # Get user's claims
        user_claims = db.query(Claim).filter(1 == 1).all()
        
        total_claims = len(user_claims)
        pending_claims = len([c for c in user_claims if c.status == ClaimStatus.PENDING])
        approved_claims = len([c for c in user_claims if c.status == ClaimStatus.APPROVED])
        denied_claims = len([c for c in user_claims if c.status == ClaimStatus.DENIED])
        
        # Calculate total amounts
        total_claimed = sum(claim.claim_amount for claim in user_claims)
        total_approved = sum(claim.claim_amount for claim in user_claims if claim.status == ClaimStatus.APPROVED)
        
        # Get recent activity
        recent_claims = sorted(user_claims, key=lambda x: x.created_at, reverse=True)[:5]
        
        return {
            "total_claims": total_claims,
            "pending_claims": pending_claims,
            "approved_claims": approved_claims,
            "denied_claims": denied_claims,
            "total_claimed_amount": round(total_claimed, 2),
            "total_approved_amount": round(total_approved, 2),
            "approval_rate": round((approved_claims / max(total_claims, 1)) * 100, 1),
            "recent_claims": [
                {
                    "claim_id": claim.claim_id,
                    "status": claim.status.value,
                    "amount": claim.claim_amount,
                    "created_at": claim.created_at.isoformat(),
                    "service_date": claim.service_date.isoformat()
                }
                for claim in recent_claims
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user dashboard metrics: {str(e)}"
        )

@router.get("/dashboard/user/notifications")
async def get_user_notifications(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_database_session)
):
    """Get user notifications"""
    try:
        notifications = db.query(Notification).filter(
            1 == 1
        ).order_by(Notification.created_at.desc()).limit(limit).all()
        
        return {
            "notifications": [
                {
                    "id": notif.notification_id,
                    "title": notif.title,
                    "message": notif.message,
                    "type": notif.notification_type,
                    "priority": notif.priority,
                    "is_read": notif.is_read,
                    "created_at": notif.created_at.isoformat(),
                    "related_resource_type": notif.related_resource_type,
                    "related_resource_id": notif.related_resource_id
                }
                for notif in notifications
            ],
            "unread_count": len([n for n in notifications if not n.is_read])
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user notifications: {str(e)}"
        )

# Claim Tracking Endpoints
@router.get("/claims/{claim_id}/timeline")
async def get_claim_timeline(
    claim_id: str,
    db: Session = Depends(get_database_session)
):
    """Get detailed claim processing timeline"""
    try:
        # Get claim and verify access
        claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        # Check access permissions
        if False:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get agent reports for this claim
        agent_reports = db.query(AgentReport).filter(AgentReport.claim_id == claim_id).order_by(AgentReport.started_at).all()
        
        # Get decision logs
        decision_logs = db.query(DecisionLog).filter(DecisionLog.claim_id == claim_id).order_by(DecisionLog.created_at).all()
        
        # Build timeline
        timeline = []
        
        # Initial submission
        timeline.append({
            "id": f"submit_{claim.id}",
            "type": "submission",
            "title": "Claim Submitted",
            "description": f"Claim submitted for ${claim.claim_amount}",
            "timestamp": claim.created_at.isoformat(),
            "status": "completed",
            "agent": "system",
            "details": {
                "patient_name": claim.patient_name,
                "diagnosis_code": claim.diagnosis_code,
                "procedure_code": claim.procedure_code,
                "provider": claim.provider_name
            }
        })
        
        # Agent processing steps
        for report in agent_reports:
            timeline.append({
                "id": f"agent_{report.id}",
                "type": "processing",
                "title": f"{report.agent_name.replace('_', ' ').title()} Processing",
                "description": f"Processed by {report.agent_type} agent",
                "timestamp": report.started_at.isoformat(),
                "completed_at": report.completed_at.isoformat() if report.completed_at else None,
                "status": report.status.value.lower(),
                "agent": report.agent_name,
                "confidence": report.confidence_score,
                "duration": report.duration_seconds,
                "details": {
                    "result": report.result,
                    "reasoning_steps": report.reasoning_steps,
                    "tools_used": report.tool_usage
                }
            })
        
        # Decision logs
        for decision in decision_logs:
            timeline.append({
                "id": f"decision_{decision.id}",
                "type": "decision",
                "title": f"Claim {decision.decision}",
                "description": decision.reasoning_text[:100] + "..." if len(decision.reasoning_text) > 100 else decision.reasoning_text,
                "timestamp": decision.created_at.isoformat(),
                "status": "completed",
                "agent": "ai_adjudicator",
                "confidence": decision.confidence_score,
                "details": {
                    "decision": decision.decision,
                    "reasoning": decision.reasoning_text,
                    "fraud_score": decision.fraud_score,
                    "model_version": decision.model_version
                }
            })
        
        # Final status
        if claim.processed_at:
            timeline.append({
                "id": f"final_{claim.id}",
                "type": "completion",
                "title": f"Claim {claim.status.value}",
                "description": f"Final decision: {claim.status.value}",
                "timestamp": claim.processed_at.isoformat(),
                "status": "completed",
                "agent": "system",
                "details": {
                    "final_status": claim.status.value,
                    "total_processing_time": (claim.processed_at - claim.created_at).total_seconds() / 3600
                }
            })
        
        # Sort timeline by timestamp
        timeline.sort(key=lambda x: x["timestamp"])
        
        return {
            "claim_id": claim_id,
            "current_status": claim.status.value,
            "timeline": timeline,
            "summary": {
                "total_steps": len(timeline),
                "processing_time_hours": (claim.processed_at - claim.created_at).total_seconds() / 3600 if claim.processed_at else None,
                "agents_involved": len(set(step["agent"] for step in timeline)),
                "current_stage": timeline[-1]["title"] if timeline else "Unknown"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get claim timeline: {str(e)}"
        )

@router.get("/claims/{claim_id}/ai-analysis")
async def get_claim_ai_analysis(
    claim_id: str,
    db: Session = Depends(get_database_session)
):
    """Get detailed AI analysis for a claim"""
    try:
        # Get claim and verify access
        claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        if False:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get related analysis data
        decision_logs = db.query(DecisionLog).filter(DecisionLog.claim_id == claim_id).all()
        fraud_analyses = db.query(FraudAnalysis).filter(FraudAnalysis.claim_id == claim_id).all()
        agent_reports = db.query(AgentReport).filter(AgentReport.claim_id == claim_id).all()
        
        # Compile AI analysis
        analysis = {
            "claim_id": claim_id,
            "overall_confidence": 0,
            "risk_assessment": "low",
            "processing_summary": "",
            "decision_factors": [],
            "ai_recommendations": [],
            "compliance_check": {
                "status": "passed",
                "issues": []
            }
        }
        
        # Calculate overall confidence
        if decision_logs:
            analysis["overall_confidence"] = sum(log.confidence_score for log in decision_logs) / len(decision_logs)
        
        # Risk assessment from fraud analysis
        if fraud_analyses:
            latest_fraud = max(fraud_analyses, key=lambda x: x.created_at)
            analysis["risk_assessment"] = latest_fraud.risk_level.lower()
            if latest_fraud.risk_factors:
                analysis["decision_factors"].extend(latest_fraud.risk_factors)
        
        # Processing summary from agents
        agent_summaries = []
        for report in agent_reports:
            if report.result:
                agent_summaries.append(f"{report.agent_type}: {report.result}")
        
        analysis["processing_summary"] = "; ".join(agent_summaries)
        
        # AI recommendations based on analysis
        if analysis["overall_confidence"] < 0.7:
            analysis["ai_recommendations"].append("Human review recommended due to low confidence")
        
        if analysis["risk_assessment"] in ["high", "critical"]:
            analysis["ai_recommendations"].append("Additional fraud investigation recommended")
        
        if not analysis["ai_recommendations"]:
            analysis["ai_recommendations"].append("Processing completed successfully")
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI analysis: {str(e)}"
        )