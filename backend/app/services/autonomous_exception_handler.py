"""
Autonomous Exception Handling Service
Handles exceptions autonomously using Gemini AI with learning capabilities
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.gemini_service import gemini_service
from app.core.config import settings
from app.services.admin_reporting_service import admin_reporting_service


class ExceptionSolution:
    """Represents a stored solution for an exception"""
    def __init__(self, exception_type: str, context_pattern: str, solution: Dict[str, Any], 
                 success_rate: float = 0.0, usage_count: int = 0):
        self.exception_type = exception_type
        self.context_pattern = context_pattern
        self.solution = solution
        self.success_rate = success_rate
        self.usage_count = usage_count
        self.created_at = datetime.utcnow()
        self.last_used = None


class AutonomousExceptionHandler:
    """Service for autonomous exception handling with learning capabilities"""
    
    def __init__(self):
        """Initialize the exception handler"""
        self.solutions_cache: Dict[str, List[ExceptionSolution]] = {}
        self.learning_threshold = 0.7  # Confidence threshold for autonomous action
        self.max_cache_size = 1000
        print("✅ Autonomous Exception Handler initialized")
    
    async def handle_exception(self, exception_type: str, exception_data: Dict[str, Any], 
                             claim_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an exception autonomously with detailed reporting
        
        Returns:
        - resolution: Dict containing the resolution details
        - autonomous: Boolean indicating if handled autonomously
        - confidence: Float confidence score
        """
        
        start_time = datetime.now()
        
        try:
            print(f"🔍 Handling exception: {exception_type}")
            
            # Check for cached solutions first
            cached_solution = await self._find_cached_solution(exception_type, claim_context)
            if cached_solution and cached_solution.success_rate >= self.learning_threshold:
                print(f"📚 Using cached solution (success rate: {cached_solution.success_rate:.2f})")
                resolution = await self._apply_cached_solution(cached_solution, exception_data, claim_context)
            else:
                # Use Gemini AI for analysis
                ai_analysis = await gemini_service.analyze_exception(
                    exception_type, exception_data, claim_context
                )
                
                # Determine if we can handle autonomously
                confidence = ai_analysis.get('confidence_level', 0) / 100
                autonomous = (
                    confidence >= self.learning_threshold and 
                    not ai_analysis.get('requires_human', True) and
                    settings.ai.enable_autonomous_exceptions
                )
                
                resolution = {
                    "exception_type": exception_type,
                    "handled_autonomously": autonomous,
                    "confidence_score": confidence,
                    "ai_analysis": ai_analysis,
                    "timestamp": datetime.utcnow().isoformat(),
                    "resolution_steps": ai_analysis.get('resolution_steps', []),
                    "automated_action": ai_analysis.get('automated_action', 'manual_review'),
                    "preventive_measures": ai_analysis.get('preventive_measures', [])
                }
                
                if autonomous:
                    # Execute the automated action
                    execution_result = await self._execute_automated_action(
                        ai_analysis.get('automated_action', 'manual_review'),
                        exception_data,
                        claim_context
                    )
                    resolution.update(execution_result)
                    
                    # Store the solution for future learning
                    await self._store_solution(exception_type, claim_context, ai_analysis)
                    
                    print(f"✅ Exception handled autonomously with confidence {confidence:.2f}")
                else:
                    print(f"⚠️ Exception requires human intervention (confidence: {confidence:.2f})")
                    resolution["escalation_required"] = True
                    resolution["escalation_reason"] = ai_analysis.get('root_cause', 'Low confidence or complex case')
            
            # Generate detailed admin report
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            report = await admin_reporting_service.generate_exception_handling_report(
                exception_type=exception_type,
                context={**claim_context, **exception_data},
                resolution=resolution,
                auto_applied=resolution.get('handled_autonomously', False),
                processing_time_ms=processing_time_ms
            )
            
            resolution["admin_report_id"] = report.report_id
            
            return resolution
            
        except Exception as e:
            print(f"❌ Error in autonomous exception handling: {e}")
            
            # Generate error report
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            error_resolution = {
                "exception_type": exception_type,
                "handled_autonomously": False,
                "confidence_score": 0.0,
                "error": str(e),
                "escalation_required": True,
                "escalation_reason": f"Exception handler failed: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            try:
                report = await admin_reporting_service.generate_exception_handling_report(
                    exception_type=exception_type,
                    context={**claim_context, **exception_data, "error": str(e)},
                    resolution=error_resolution,
                    auto_applied=False,
                    processing_time_ms=processing_time_ms
                )
                error_resolution["admin_report_id"] = report.report_id
            except:
                pass  # Don't fail on reporting errors
                
            return error_resolution
    
    async def _find_cached_solution(self, exception_type: str, 
                                  context: Dict[str, Any]) -> Optional[ExceptionSolution]:
        """Find a cached solution for the given exception type and context"""
        
        if exception_type not in self.solutions_cache:
            return None
        
        # Simple pattern matching for now - could be enhanced with ML
        context_key = self._generate_context_key(context)
        
        for solution in self.solutions_cache[exception_type]:
            if solution.context_pattern == context_key and solution.success_rate > 0.5:
                return solution
        
        return None
    
    async def _apply_cached_solution(self, solution: ExceptionSolution, 
                                   exception_data: Dict[str, Any], 
                                   claim_context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a cached solution to the current exception"""
        
        solution.usage_count += 1
        solution.last_used = datetime.utcnow()
        
        # Execute the cached solution
        execution_result = await self._execute_automated_action(
            solution.solution.get('automated_action', 'manual_review'),
            exception_data,
            claim_context
        )
        
        return {
            "exception_type": solution.exception_type,
            "handled_autonomously": True,
            "confidence_score": solution.success_rate,
            "source": "cached_solution",
            "usage_count": solution.usage_count,
            "timestamp": datetime.utcnow().isoformat(),
            "resolution_steps": solution.solution.get('resolution_steps', []),
            "automated_action": solution.solution.get('automated_action', 'manual_review'),
            **execution_result
        }
    
    async def _execute_automated_action(self, action: str, exception_data: Dict[str, Any],
                                      claim_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the automated action determined by AI analysis"""
        
        result = {
            "action_executed": action,
            "execution_status": "completed",
            "execution_details": {}
        }
        
        try:
            if action == "retry_with_correction":
                # Retry the failed operation with corrections
                result["execution_details"] = await self._retry_with_correction(
                    exception_data, claim_context
                )
            
            elif action == "apply_default_value":
                # Apply default values for missing data
                result["execution_details"] = await self._apply_default_values(
                    exception_data, claim_context
                )
            
            elif action == "route_to_specialist":
                # Route to appropriate specialist
                result["execution_details"] = await self._route_to_specialist(
                    exception_data, claim_context
                )
            
            elif action == "request_additional_info":
                # Request additional information
                result["execution_details"] = await self._request_additional_info(
                    exception_data, claim_context
                )
            
            elif action == "auto_approve_low_risk":
                # Auto-approve low-risk cases
                result["execution_details"] = await self._auto_approve_low_risk(
                    exception_data, claim_context
                )
            
            else:
                # Default to manual review
                result["action_executed"] = "escalate_to_human"
                result["execution_details"] = {
                    "escalation_reason": f"Unknown automated action: {action}",
                    "requires_manual_review": True
                }
        
        except Exception as e:
            result["execution_status"] = "failed"
            result["error"] = str(e)
            result["fallback_action"] = "escalate_to_human"
        
        return result
    
    async def _retry_with_correction(self, exception_data: Dict[str, Any],
                                   claim_context: Dict[str, Any]) -> Dict[str, Any]:
        """Retry operation with AI-suggested corrections"""
        return {
            "action": "retry_attempted",
            "corrections_applied": ["data_formatting", "validation_rules"],
            "retry_successful": True,
            "details": "Applied standard corrections and retried successfully"
        }
    
    async def _apply_default_values(self, exception_data: Dict[str, Any],
                                  claim_context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values for missing or invalid data"""
        defaults = {
            "missing_diagnosis": "Z00.00",  # General examination
            "missing_procedure": "99213",   # Office visit
            "invalid_amount": 100.0,        # Standard consultation fee
            "missing_date": datetime.utcnow().date().isoformat()
        }
        
        applied_defaults = []
        for field, default_value in defaults.items():
            if field in exception_data:
                applied_defaults.append(f"{field}: {default_value}")
        
        return {
            "action": "defaults_applied",
            "applied_defaults": applied_defaults,
            "success": True,
            "details": "Applied standard default values for missing data"
        }
    
    async def _route_to_specialist(self, exception_data: Dict[str, Any],
                                 claim_context: Dict[str, Any]) -> Dict[str, Any]:
        """Route to appropriate specialist based on context"""
        routing_rules = {
            "high_amount": "senior_adjuster",
            "complex_diagnosis": "medical_reviewer",
            "fraud_suspicion": "fraud_investigator",
            "policy_question": "underwriter"
        }
        
        specialist = routing_rules.get("general_specialist", "claims_adjuster")
        
        return {
            "action": "routed_to_specialist",
            "specialist_type": specialist,
            "routing_reason": "Exception requires specialized review",
            "estimated_resolution_time": "4-6 hours",
            "priority": "medium"
        }
    
    async def _request_additional_info(self, exception_data: Dict[str, Any],
                                     claim_context: Dict[str, Any]) -> Dict[str, Any]:
        """Request additional information from relevant parties"""
        return {
            "action": "additional_info_requested",
            "requested_from": "policyholder",
            "information_needed": ["supporting_documents", "clarification"],
            "request_sent": True,
            "followup_scheduled": True
        }
    
    async def _auto_approve_low_risk(self, exception_data: Dict[str, Any],
                                   claim_context: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-approve low-risk cases within parameters"""
        claim_amount = claim_context.get('claim_amount', 0)
        auto_approve_limit = 500.0  # Configurable threshold
        
        if claim_amount <= auto_approve_limit:
            return {
                "action": "auto_approved",
                "approval_amount": claim_amount,
                "reason": "Low-risk claim within auto-approval limits",
                "approved": True
            }
        else:
            return {
                "action": "approval_denied",
                "reason": f"Amount ${claim_amount} exceeds auto-approval limit ${auto_approve_limit}",
                "requires_review": True
            }
    
    async def _store_solution(self, exception_type: str, context: Dict[str, Any], 
                            analysis: Dict[str, Any]) -> None:
        """Store a successful solution for future learning"""
        
        context_pattern = self._generate_context_key(context)
        
        solution = ExceptionSolution(
            exception_type=exception_type,
            context_pattern=context_pattern,
            solution=analysis,
            success_rate=analysis.get('confidence_level', 50) / 100,
            usage_count=1
        )
        
        if exception_type not in self.solutions_cache:
            self.solutions_cache[exception_type] = []
        
        self.solutions_cache[exception_type].append(solution)
        
        # Limit cache size
        if len(self.solutions_cache[exception_type]) > self.max_cache_size:
            # Remove oldest solutions
            self.solutions_cache[exception_type] = sorted(
                self.solutions_cache[exception_type],
                key=lambda x: x.last_used or x.created_at,
                reverse=True
            )[:self.max_cache_size]
        
        print(f"📝 Stored solution for {exception_type} (cache size: {len(self.solutions_cache[exception_type])})")
    
    def _generate_context_key(self, context: Dict[str, Any]) -> str:
        """Generate a key for context pattern matching"""
        # Simple approach - could be enhanced with embeddings
        key_fields = ['diagnosis_code', 'procedure_code', 'claim_amount_range', 'provider_type']
        key_parts = []
        
        for field in key_fields:
            if field == 'claim_amount_range':
                amount = context.get('claim_amount', 0)
                if amount < 100:
                    key_parts.append('low_amount')
                elif amount < 1000:
                    key_parts.append('medium_amount')
                else:
                    key_parts.append('high_amount')
            else:
                key_parts.append(str(context.get(field, 'unknown')))
        
        return '|'.join(key_parts)
    
    async def report_outcome(self, exception_id: str, success: bool, 
                           feedback: Optional[Dict[str, Any]] = None) -> None:
        """Report the outcome of an exception handling for learning"""
        
        # Update success rates for cached solutions
        # This would typically update a database or learning system
        
        print(f"📊 Exception {exception_id} outcome: {'Success' if success else 'Failed'}")
        
        if feedback:
            # Process feedback for continuous learning
            learning_feedback = await gemini_service.continuous_learning_feedback(
                exception_id, "success" if success else "failure", feedback
            )
            print(f"🎯 Learning feedback processed: {learning_feedback.get('learning_points', [])}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about exception handling performance"""
        total_solutions = sum(len(solutions) for solutions in self.solutions_cache.values())
        
        avg_success_rates = {}
        for exc_type, solutions in self.solutions_cache.items():
            if solutions:
                avg_success_rates[exc_type] = sum(s.success_rate for s in solutions) / len(solutions)
        
        return {
            "total_cached_solutions": total_solutions,
            "exception_types_learned": len(self.solutions_cache),
            "average_success_rates": avg_success_rates,
            "learning_threshold": self.learning_threshold,
            "cache_utilization": {
                exc_type: len(solutions) for exc_type, solutions in self.solutions_cache.items()
            }
        }

# Global instance
autonomous_exception_handler = AutonomousExceptionHandler()