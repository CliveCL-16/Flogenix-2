"""
Asynchronous Claim Processing Tasks
Handles background processing of claims through the multi-agent system
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import get_database_session
from app.core.models import Claim, ClaimStatus, DecisionLog, AgentReport, FraudAnalysis
from app.services.enhanced_multi_agent_processor import enhanced_multi_agent_processor
from app.services.enhanced_fraud_detection import enhanced_fraud_detection
from app.tasks.notification_tasks import send_claim_status_notification

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def process_claim_async(self, claim_id: str, priority: int = 1):
    """
    Process a claim asynchronously through the multi-agent system
    """
    try:
        # Get database session
        db = next(get_database_session())
        
        # Get claim from database
        claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")
        
        # Update status to processing
        claim.status = ClaimStatus.PROCESSING
        db.commit()
        
        # Prepare claim data for processing
        claim_data = {
            "patient_name": claim.patient_name,
            "patient_id": claim.patient_id,
            "insurance_provider": claim.insurance_provider,
            "policy_number": claim.policy_number,
            "diagnosis_code": claim.diagnosis_code,
            "procedure_code": claim.procedure_code,
            "claim_amount": claim.claim_amount,
            "service_date": claim.service_date.isoformat() if claim.service_date else None,
            "provider_name": claim.provider_name,
            "provider_npi": claim.provider_npi,
            "notes": claim.notes
        }
        
        # Process through multi-agent system
        processing_state = asyncio.run(
            enhanced_multi_agent_processor.process_claim(claim_data, claim_id)
        )
        
        # Store agent reports
        for agent_name, agent_result in processing_state.agent_results.items():
            agent_report = AgentReport(
                claim_id=claim_id,
                agent_name=agent_result.agent_name,
                agent_type=agent_name,
                status=agent_result.status,
                started_at=datetime.utcnow() - timedelta(seconds=agent_result.duration_seconds),
                completed_at=datetime.utcnow(),
                duration_seconds=agent_result.duration_seconds,
                result=agent_result.result,
                confidence_score=agent_result.confidence_score,
                reasoning_steps=[
                    {
                        "step": step.step_number,
                        "type": step.step_type.value,
                        "content": step.content,
                        "timestamp": step.timestamp.isoformat(),
                        "metadata": step.metadata
                    }
                    for step in agent_result.reasoning_steps
                ],
                tool_usage=[
                    {
                        "tool_name": tool.tool_name,
                        "parameters": tool.parameters,
                        "result": str(tool.result),
                        "success": tool.success,
                        "error_message": tool.error_message,
                        "execution_time": tool.execution_time,
                        "timestamp": tool.timestamp.isoformat()
                    }
                    for tool in agent_result.tool_calls
                ],
                error_message=agent_result.error_message
            )
            db.add(agent_report)
        
        # Store fraud analysis if available
        if processing_state.fraud_result:
            fraud_analysis = FraudAnalysis(
                claim_id=claim_id,
                fraud_score=processing_state.fraud_result["fraud_score"],
                risk_level=processing_state.fraud_result["risk_level"],
                is_flagged=processing_state.fraud_result["flagged"],
                risk_factors=processing_state.fraud_result["risk_factors"],
                analysis_model="enhanced_multi_agent_v1",
                processing_time_seconds=sum(
                    result.duration_seconds 
                    for result in processing_state.agent_results.values()
                )
            )
            db.add(fraud_analysis)
        
        # Create decision log
        decision_log = DecisionLog(
            claim_id=claim_id,
            decision=processing_state.final_decision or "REVIEW",
            confidence_score=processing_state.confidence_score,
            reasoning_text=processing_state.reasoning or "Multi-agent processing completed",
            processing_time_seconds=sum(
                result.duration_seconds 
                for result in processing_state.agent_results.values()
            ),
            model_version="enhanced_multi_agent_v1",
            fraud_score=processing_state.fraud_result.get("fraud_score", 0) if processing_state.fraud_result else 0
        )
        db.add(decision_log)
        
        # Update claim status based on decision
        if processing_state.fraud_result and processing_state.fraud_result.get("flagged", False):
            claim.status = ClaimStatus.FRAUD_FLAGGED
        elif processing_state.final_decision == "APPROVE":
            claim.status = ClaimStatus.APPROVED
        elif processing_state.final_decision == "DENY":
            claim.status = ClaimStatus.DENIED
        else:
            claim.status = ClaimStatus.PENDING_REVIEW
        
        claim.processed_at = datetime.utcnow()
        
        # Commit all changes
        db.commit()
        
        # Send notification asynchronously
        send_claim_status_notification.delay(
            claim_id=claim_id,
            new_status=claim.status.value,
            decision=processing_state.final_decision,
            confidence_score=processing_state.confidence_score
        )
        
        return {
            "claim_id": claim_id,
            "status": claim.status.value,
            "decision": processing_state.final_decision,
            "confidence_score": processing_state.confidence_score,
            "processing_time": sum(
                result.duration_seconds 
                for result in processing_state.agent_results.values()
            ),
            "agents_executed": len(processing_state.agent_results),
            "errors": processing_state.errors
        }
        
    except Exception as e:
        # Update claim status to indicate error
        try:
            db = next(get_database_session())
            claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
            if claim:
                claim.status = ClaimStatus.PENDING_REVIEW
                claim.notes = f"Processing error: {str(e)}"
                db.commit()
        except:
            pass  # Don't let cleanup errors mask the original error
        
        # Re-raise the exception for Celery retry handling
        raise e
    
    finally:
        if 'db' in locals():
            db.close()

@celery_app.task
def batch_process_claims(claim_ids: list, priority: int = 1):
    """
    Process multiple claims in batch
    """
    results = []
    
    for claim_id in claim_ids:
        try:
            # Queue individual claim processing
            result = process_claim_async.delay(claim_id, priority)
            results.append({
                "claim_id": claim_id,
                "task_id": result.id,
                "status": "queued"
            })
        except Exception as e:
            results.append({
                "claim_id": claim_id,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "total_claims": len(claim_ids),
        "queued_successfully": len([r for r in results if r["status"] == "queued"]),
        "errors": len([r for r in results if r["status"] == "error"]),
        "results": results
    }

@celery_app.task
def reprocess_failed_claims():
    """
    Reprocess claims that failed during processing
    """
    try:
        db = next(get_database_session())
        
        # Find claims that are stuck in processing status
        stuck_claims = db.query(Claim).filter(
            Claim.status == ClaimStatus.PROCESSING,
            Claim.updated_at < datetime.utcnow() - timedelta(hours=1)
        ).all()
        
        results = []
        
        for claim in stuck_claims:
            try:
                # Reset status and requeue
                claim.status = ClaimStatus.PENDING
                db.commit()
                
                # Requeue for processing
                task = process_claim_async.delay(claim.claim_id, priority=2)
                
                results.append({
                    "claim_id": claim.claim_id,
                    "action": "requeued",
                    "task_id": task.id
                })
                
            except Exception as e:
                results.append({
                    "claim_id": claim.claim_id,
                    "action": "failed_to_requeue",
                    "error": str(e)
                })
        
        return {
            "processed_claims": len(stuck_claims),
            "results": results
        }
        
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        if 'db' in locals():
            db.close()

@celery_app.task
def generate_processing_report(start_date: str, end_date: str):
    """
    Generate a processing report for claims in a date range
    """
    try:
        db = next(get_database_session())
        
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Get claims in date range
        claims = db.query(Claim).filter(
            Claim.created_at >= start_dt,
            Claim.created_at <= end_dt
        ).all()
        
        # Calculate metrics
        total_claims = len(claims)
        approved_claims = len([c for c in claims if c.status == ClaimStatus.APPROVED])
        denied_claims = len([c for c in claims if c.status == ClaimStatus.DENIED])
        pending_claims = len([c for c in claims if c.status == ClaimStatus.PENDING])
        fraud_flagged = len([c for c in claims if c.status == ClaimStatus.FRAUD_FLAGGED])
        
        # Get average processing time
        processed_claims = [c for c in claims if c.processed_at]
        avg_processing_time = 0
        if processed_claims:
            total_time = sum([
                (c.processed_at - c.created_at).total_seconds() 
                for c in processed_claims
            ])
            avg_processing_time = total_time / len(processed_claims)
        
        # Get agent performance
        agent_reports = db.query(AgentReport).join(Claim).filter(
            Claim.created_at >= start_dt,
            Claim.created_at <= end_dt
        ).all()
        
        agent_stats = {}
        for report in agent_reports:
            agent_name = report.agent_name
            if agent_name not in agent_stats:
                agent_stats[agent_name] = {
                    "total_runs": 0,
                    "successful_runs": 0,
                    "failed_runs": 0,
                    "avg_duration": 0,
                    "total_duration": 0
                }
            
            agent_stats[agent_name]["total_runs"] += 1
            agent_stats[agent_name]["total_duration"] += report.duration_seconds or 0
            
            if report.status == "COMPLETED":
                agent_stats[agent_name]["successful_runs"] += 1
            else:
                agent_stats[agent_name]["failed_runs"] += 1
        
        # Calculate averages
        for agent_name in agent_stats:
            stats = agent_stats[agent_name]
            if stats["total_runs"] > 0:
                stats["avg_duration"] = stats["total_duration"] / stats["total_runs"]
                stats["success_rate"] = (stats["successful_runs"] / stats["total_runs"]) * 100
        
        report = {
            "report_period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "claim_metrics": {
                "total_claims": total_claims,
                "approved_claims": approved_claims,
                "denied_claims": denied_claims,
                "pending_claims": pending_claims,
                "fraud_flagged": fraud_flagged,
                "approval_rate": (approved_claims / total_claims * 100) if total_claims > 0 else 0,
                "avg_processing_time_seconds": avg_processing_time
            },
            "agent_performance": agent_stats,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return report
        
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        if 'db' in locals():
            db.close()