"""
Admin Dashboard API
Endpoints for viewing detailed AI decision reports and analytics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

from app.services.admin_reporting_service import (
    admin_reporting_service, 
    DetailedAIReport, 
    ReportType, 
    DecisionSeverity
)
from app.core.security import require_admin

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@router.get("/reports/summary", response_model=Dict[str, Any])
async def get_dashboard_summary(
    current_admin=Depends(require_admin)
):
    """Get admin dashboard summary with key metrics"""
    
    try:
        summary = await admin_reporting_service.generate_admin_dashboard_summary()
        return {
            "success": True,
            "data": summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dashboard summary: {str(e)}")


@router.get("/reports", response_model=Dict[str, Any])
async def get_ai_reports(
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    claim_id: Optional[str] = Query(None, description="Filter by claim ID"),
    human_review_needed: Optional[bool] = Query(None, description="Filter by human review requirement"),
    limit: int = Query(50, description="Limit number of results", le=500),
    current_admin=Depends(require_admin)
):
    """Get AI decision reports with filtering options"""
    
    try:
        # Convert string enums to enum objects
        report_type_enum = None
        if report_type:
            try:
                report_type_enum = ReportType(report_type.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid report type: {report_type}")
        
        severity_enum = None
        if severity:
            try:
                severity_enum = DecisionSeverity(severity.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity level: {severity}")
        
        # Get filtered reports
        reports = await admin_reporting_service.get_reports_by_criteria(
            report_type=report_type_enum,
            severity=severity_enum,
            start_date=start_date,
            end_date=end_date,
            claim_id=claim_id,
            human_review_needed=human_review_needed,
            limit=limit
        )
        
        # Convert reports to dict format for JSON serialization
        report_data = []
        for report in reports:
            report_dict = {
                "report_id": report.report_id,
                "report_type": report.report_type.value,
                "severity": report.severity.value,
                "claim_id": report.claim_id,
                "customer_id": report.customer_id,
                "timestamp": report.timestamp.isoformat(),
                "duration_seconds": report.duration_seconds,
                "summary": report.summary,
                "final_decision": report.final_decision,
                "confidence_score": report.confidence_score,
                "business_impact": report.business_impact,
                "human_review_needed": report.human_review_needed,
                "tags": report.tags or []
            }
            report_data.append(report_dict)
        
        return {
            "success": True,
            "data": {
                "reports": report_data,
                "total_count": len(report_data),
                "filters_applied": {
                    "report_type": report_type,
                    "severity": severity,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "claim_id": claim_id,
                    "human_review_needed": human_review_needed
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving reports: {str(e)}")


@router.get("/reports/{report_id}", response_model=Dict[str, Any])
async def get_detailed_report(
    report_id: str,
    current_admin=Depends(require_admin)
):
    """Get detailed view of a specific AI decision report"""
    
    try:
        # Find the report
        all_reports = await admin_reporting_service.get_reports_by_criteria(limit=1000)
        report = next((r for r in all_reports if r.report_id == report_id), None)
        
        if not report:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        
        # Convert to detailed dict
        detailed_report = {
            "report_id": report.report_id,
            "report_type": report.report_type.value,
            "severity": report.severity.value,
            "claim_id": report.claim_id,
            "customer_id": report.customer_id,
            "timestamp": report.timestamp.isoformat(),
            "duration_seconds": report.duration_seconds,
            
            # Core information
            "summary": report.summary,
            "final_decision": report.final_decision,
            "confidence_score": report.confidence_score,
            "business_impact": report.business_impact,
            
            # Detailed reasoning
            "ai_reasoning": report.ai_reasoning,
            "decision_factors": report.decision_factors,
            "risk_analysis": report.risk_analysis,
            "compliance_notes": report.compliance_notes,
            
            # Process tracking
            "decision_steps": [
                {
                    "step_id": step.step_id,
                    "timestamp": step.timestamp.isoformat(),
                    "agent_name": step.agent_name,
                    "action_taken": step.action_taken,
                    "reasoning": step.reasoning,
                    "confidence_score": step.confidence_score,
                    "processing_time_ms": step.processing_time_ms,
                    "model_response": step.model_response,
                    "alternative_options": step.alternative_options,
                    "risk_assessment": step.risk_assessment
                } for step in report.decision_steps
            ],
            "data_sources_used": report.data_sources_used,
            "models_involved": report.models_involved,
            
            # Quality metrics
            "accuracy_indicators": report.accuracy_indicators,
            "bias_assessment": report.bias_assessment,
            "transparency_score": report.transparency_score,
            
            # Follow-up
            "recommended_actions": report.recommended_actions,
            "monitoring_requirements": report.monitoring_requirements,
            "human_review_needed": report.human_review_needed,
            "escalation_triggers": report.escalation_triggers,
            
            # Metadata
            "created_by": report.created_by,
            "reviewed_by": report.reviewed_by,
            "tags": report.tags or []
        }
        
        return {
            "success": True,
            "data": detailed_report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving detailed report: {str(e)}")


@router.get("/reports/analytics/patterns", response_model=Dict[str, Any])
async def get_decision_patterns(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    current_admin=Depends(require_admin)
):
    """Get analytics on AI decision patterns over time"""
    
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        reports = await admin_reporting_service.get_reports_by_criteria(
            start_date=start_date,
            limit=10000
        )
        
        # Analyze patterns
        patterns = {
            "total_decisions": len(reports),
            "automation_rate": 0,
            "confidence_trends": {},
            "decision_types": {},
            "severity_distribution": {},
            "human_review_rate": 0,
            "processing_time_avg": 0,
            "top_escalation_triggers": {},
            "accuracy_by_type": {}
        }
        
        if reports:
            # Calculate automation rate
            automated_decisions = len([r for r in reports if not r.human_review_needed])
            patterns["automation_rate"] = round(automated_decisions / len(reports) * 100, 1)
            
            # Calculate human review rate
            patterns["human_review_rate"] = round((len(reports) - automated_decisions) / len(reports) * 100, 1)
            
            # Decision type distribution
            for report in reports:
                report_type = report.report_type.value
                patterns["decision_types"][report_type] = patterns["decision_types"].get(report_type, 0) + 1
            
            # Severity distribution
            for report in reports:
                severity = report.severity.value
                patterns["severity_distribution"][severity] = patterns["severity_distribution"].get(severity, 0) + 1
            
            # Average processing time
            avg_processing_time = sum(r.duration_seconds for r in reports) / len(reports)
            patterns["processing_time_avg"] = round(avg_processing_time, 2)
            
            # Confidence score trends (by week)
            confidence_by_week = {}
            for report in reports:
                week_key = report.timestamp.strftime("%Y-W%W")
                if week_key not in confidence_by_week:
                    confidence_by_week[week_key] = []
                confidence_by_week[week_key].append(report.confidence_score)
            
            patterns["confidence_trends"] = {
                week: round(sum(scores) / len(scores), 3)
                for week, scores in confidence_by_week.items()
            }
            
            # Top escalation triggers
            escalation_triggers = {}
            for report in reports:
                for trigger in report.escalation_triggers:
                    escalation_triggers[trigger] = escalation_triggers.get(trigger, 0) + 1
            
            patterns["top_escalation_triggers"] = dict(
                sorted(escalation_triggers.items(), key=lambda x: x[1], reverse=True)[:10]
            )
        
        return {
            "success": True,
            "data": {
                "analysis_period": f"{days} days",
                "start_date": start_date.isoformat(),
                "end_date": datetime.now().isoformat(),
                "patterns": patterns
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing decision patterns: {str(e)}")


@router.post("/reports/{report_id}/review", response_model=Dict[str, Any])
async def mark_report_reviewed(
    report_id: str,
    review_notes: str = Query(..., description="Review notes from admin"),
    current_admin=Depends(require_admin)
):
    """Mark a report as reviewed by admin"""
    
    try:
        # Find and update the report
        all_reports = await admin_reporting_service.get_reports_by_criteria(limit=1000)
        report = next((r for r in all_reports if r.report_id == report_id), None)
        
        if not report:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        
        # Update review status
        report.reviewed_by = current_admin.username
        report.compliance_notes += f"\n\nAdmin Review ({datetime.now().isoformat()}): {review_notes}"
        
        return {
            "success": True,
            "message": f"Report {report_id} marked as reviewed",
            "reviewed_by": current_admin.username,
            "review_timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating report review status: {str(e)}")


@router.get("/reports/types", response_model=Dict[str, Any])
async def get_report_types(
    current_admin=Depends(require_admin)
):
    """Get available report types and severity levels for filtering"""
    
    return {
        "success": True,
        "data": {
            "report_types": [rt.value for rt in ReportType],
            "severity_levels": [sl.value for sl in DecisionSeverity],
            "description": {
                "report_types": {
                    "exception_handling": "Autonomous exception resolution decisions",
                    "learning_event": "Continuous learning and adaptation events",
                    "triage_decision": "Dynamic claims triage and routing decisions",
                    "fraud_detection": "Fraud pattern detection and risk assessment",
                    "customer_interaction": "AI customer support interactions",
                    "escalation": "Human-in-the-loop escalation decisions",
                    "multi_agent_process": "Multi-agent workflow processing"
                },
                "severity_levels": {
                    "low": "Routine decisions with high confidence",
                    "medium": "Standard decisions requiring monitoring",
                    "high": "Important decisions with potential impact",
                    "critical": "High-risk decisions requiring immediate attention"
                }
            }
        }
    }