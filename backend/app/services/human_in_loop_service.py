"""
Human-in-the-Loop Escalation Service
Manages escalation pathways and human intervention in claims processing
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from uuid import uuid4

from app.services.gemini_service import gemini_service
from app.services.continuous_learning_service import continuous_learning_service
from app.core.config import settings


class EscalationReason(Enum):
    """Reasons for human escalation"""
    LOW_CONFIDENCE = "low_confidence"
    CONFLICTING_RESULTS = "conflicting_results"
    HIGH_RISK = "high_risk"
    COMPLEX_CASE = "complex_case"
    REGULATORY_CONCERN = "regulatory_concern"
    CUSTOMER_REQUEST = "customer_request"
    SYSTEM_ERROR = "system_error"
    FRAUD_SUSPICION = "fraud_suspicion"
    APPEAL_REQUIRED = "appeal_required"
    MEDICAL_COMPLEXITY = "medical_complexity"


class SpecialistType(Enum):
    """Types of human specialists"""
    CLAIMS_ADJUSTER = "claims_adjuster"
    SENIOR_ADJUSTER = "senior_adjuster"
    MEDICAL_DIRECTOR = "medical_director"
    FRAUD_INVESTIGATOR = "fraud_investigator"
    LEGAL_COUNSEL = "legal_counsel"
    CUSTOMER_SERVICE_MANAGER = "customer_service_manager"
    UNDERWRITER = "underwriter"
    COMPLIANCE_OFFICER = "compliance_officer"
    TECHNICAL_SUPPORT = "technical_support"


class EscalationPriority(Enum):
    """Escalation priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class EscalationStatus(Enum):
    """Status of escalation cases"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED_FURTHER = "escalated_further"
    RETURNED_TO_AI = "returned_to_ai"


@dataclass
class EscalationCase:
    """Represents a case escalated to human intervention"""
    case_id: str
    claim_id: str
    escalation_reason: EscalationReason
    specialist_type: SpecialistType
    priority: EscalationPriority
    status: EscalationStatus
    ai_analysis: Dict[str, Any]
    human_instructions: str
    estimated_resolution_time: int  # hours
    assigned_specialist: Optional[str]
    created_at: datetime
    assigned_at: Optional[datetime]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    ai_feedback: Optional[Dict[str, Any]]
    learning_value: float


@dataclass
class HumanFeedback:
    """Feedback from human specialists to improve AI"""
    feedback_id: str
    case_id: str
    specialist_type: SpecialistType
    ai_decision_correct: bool
    ai_confidence_appropriate: bool
    missed_factors: List[str]
    suggested_improvements: List[str]
    case_complexity_rating: int  # 1-10
    processing_difficulty: int  # 1-10
    would_escalate_again: bool
    feedback_notes: str
    timestamp: datetime


class HumanInTheLoopService:
    """Service for managing human intervention and escalation"""
    
    def __init__(self):
        """Initialize the human-in-the-loop service"""
        self.escalation_cases: Dict[str, EscalationCase] = {}
        self.specialist_workloads: Dict[str, List[str]] = {}  # specialist_id -> case_ids
        self.escalation_rules: Dict[str, Any] = self._load_escalation_rules()
        self.feedback_history: List[HumanFeedback] = []
        self.performance_metrics: Dict[str, float] = {
            "escalation_rate": 0.0,
            "resolution_time": 0.0,
            "ai_accuracy": 0.0,
            "specialist_satisfaction": 0.0
        }
        
        print("✅ Human-in-the-Loop Service initialized")
    
    def _load_escalation_rules(self) -> Dict[str, Any]:
        """Load escalation rules and thresholds"""
        return {
            "confidence_thresholds": {
                "critical_decisions": 0.9,
                "standard_decisions": 0.7,
                "routine_decisions": 0.5
            },
            "automatic_escalation": {
                "claim_amount_threshold": 50000,
                "fraud_score_threshold": 80,
                "conflicting_agent_results": True,
                "medical_complexity_threshold": 8,
                "regulatory_red_flags": True
            },
            "specialist_assignment": {
                EscalationReason.FRAUD_SUSPICION: SpecialistType.FRAUD_INVESTIGATOR,
                EscalationReason.MEDICAL_COMPLEXITY: SpecialistType.MEDICAL_DIRECTOR,
                EscalationReason.REGULATORY_CONCERN: SpecialistType.COMPLIANCE_OFFICER,
                EscalationReason.HIGH_RISK: SpecialistType.SENIOR_ADJUSTER,
                EscalationReason.APPEAL_REQUIRED: SpecialistType.LEGAL_COUNSEL,
                EscalationReason.CUSTOMER_REQUEST: SpecialistType.CUSTOMER_SERVICE_MANAGER
            },
            "priority_matrix": {
                (EscalationReason.SYSTEM_ERROR, "high_amount"): EscalationPriority.CRITICAL,
                (EscalationReason.FRAUD_SUSPICION, "high_amount"): EscalationPriority.HIGH,
                (EscalationReason.MEDICAL_COMPLEXITY, "any"): EscalationPriority.MEDIUM,
                (EscalationReason.LOW_CONFIDENCE, "low_amount"): EscalationPriority.LOW
            }
        }
    
    async def evaluate_escalation_need(self, claim_id: str, ai_analysis: Dict[str, Any],
                                     agent_reports: List[Dict[str, Any]]) -> Optional[EscalationCase]:
        """Evaluate if a case needs human escalation"""
        
        print(f"🤔 Evaluating escalation need for claim {claim_id}")
        
        # Use Gemini to assess escalation need
        escalation_assessment = await gemini_service.assess_human_intervention_need(
            claim_state=None,  # Would pass actual ClaimState object
            agent_reports=[]   # Would pass actual AgentReport objects
        )
        
        if not escalation_assessment.get("human_intervention_required", False):
            print("✅ No human intervention required")
            return None
        
        # Determine escalation reason
        escalation_reason = await self._determine_escalation_reason(ai_analysis, agent_reports)
        
        # Determine specialist type
        specialist_type = await self._determine_specialist_type(escalation_reason, ai_analysis)
        
        # Determine priority
        priority = await self._determine_priority(escalation_reason, ai_analysis)
        
        # Generate human instructions
        human_instructions = await self._generate_human_instructions(
            escalation_reason, ai_analysis, agent_reports
        )
        
        # Estimate resolution time
        estimated_time = await self._estimate_resolution_time(specialist_type, priority, ai_analysis)
        
        # Create escalation case
        case = EscalationCase(
            case_id=str(uuid4()),
            claim_id=claim_id,
            escalation_reason=escalation_reason,
            specialist_type=specialist_type,
            priority=priority,
            status=EscalationStatus.PENDING,
            ai_analysis=ai_analysis,
            human_instructions=human_instructions,
            estimated_resolution_time=estimated_time,
            assigned_specialist=None,
            created_at=datetime.utcnow(),
            assigned_at=None,
            resolved_at=None,
            resolution_notes=None,
            ai_feedback=None,
            learning_value=0.0
        )
        
        # Store case
        self.escalation_cases[case.case_id] = case
        
        # Record learning event
        await continuous_learning_service.record_learning_event(
            claim_id=claim_id,
            agent_name="escalation_manager",
            event_type="escalation",
            context={
                "escalation_reason": escalation_reason.value,
                "specialist_type": specialist_type.value,
                "priority": priority.value,
                "ai_confidence": ai_analysis.get("confidence", 0)
            },
            outcome="escalated",
            confidence_before=ai_analysis.get("confidence", 0)
        )
        
        print(f"🚨 Case escalated: {escalation_reason.value} -> {specialist_type.value} ({priority.value} priority)")
        
        return case
    
    async def _determine_escalation_reason(self, ai_analysis: Dict[str, Any],
                                         agent_reports: List[Dict[str, Any]]) -> EscalationReason:
        """Determine the primary reason for escalation"""
        
        # Check confidence levels
        confidence = ai_analysis.get("confidence", 0)
        if confidence < self.escalation_rules["confidence_thresholds"]["standard_decisions"]:
            return EscalationReason.LOW_CONFIDENCE
        
        # Check for conflicting agent results
        agent_outcomes = [report.get("outcome", "") for report in agent_reports]
        if len(set(agent_outcomes)) > 1:  # Different outcomes
            return EscalationReason.CONFLICTING_RESULTS
        
        # Check fraud score
        fraud_score = ai_analysis.get("fraud_score", 0)
        if fraud_score > self.escalation_rules["automatic_escalation"]["fraud_score_threshold"]:
            return EscalationReason.FRAUD_SUSPICION
        
        # Check claim amount
        claim_amount = ai_analysis.get("claim_amount", 0)
        if claim_amount > self.escalation_rules["automatic_escalation"]["claim_amount_threshold"]:
            return EscalationReason.HIGH_RISK
        
        # Check medical complexity
        complexity = ai_analysis.get("medical_complexity", 0)
        if complexity > self.escalation_rules["automatic_escalation"]["medical_complexity_threshold"]:
            return EscalationReason.MEDICAL_COMPLEXITY
        
        # Check for system errors
        if any("error" in report.get("status", "").lower() for report in agent_reports):
            return EscalationReason.SYSTEM_ERROR
        
        # Default to complex case
        return EscalationReason.COMPLEX_CASE
    
    async def _determine_specialist_type(self, reason: EscalationReason,
                                       ai_analysis: Dict[str, Any]) -> SpecialistType:
        """Determine the appropriate specialist type"""
        
        # Check predefined assignments
        if reason in self.escalation_rules["specialist_assignment"]:
            return self.escalation_rules["specialist_assignment"][reason]
        
        # Use AI to determine specialist
        specialist_analysis = await gemini_service.generate_response(
            f"""
            Based on the escalation reason '{reason.value}' and the following analysis,
            determine the most appropriate specialist type:
            
            Analysis: {json.dumps(ai_analysis, indent=2)}
            
            Available specialists:
            - claims_adjuster: Standard claim processing
            - senior_adjuster: Complex claims and high-value cases
            - medical_director: Medical complexity and clinical decisions
            - fraud_investigator: Fraud detection and investigation
            - legal_counsel: Legal issues and appeals
            - customer_service_manager: Customer complaints and satisfaction
            - underwriter: Policy and coverage questions
            - compliance_officer: Regulatory and compliance issues
            - technical_support: System and technical issues
            
            Respond with just the specialist type.
            """
        )
        
        # Parse response and validate
        specialist_str = specialist_analysis.strip().lower()
        for specialist_type in SpecialistType:
            if specialist_type.value in specialist_str:
                return specialist_type
        
        # Default to senior adjuster
        return SpecialistType.SENIOR_ADJUSTER
    
    async def _determine_priority(self, reason: EscalationReason,
                                ai_analysis: Dict[str, Any]) -> EscalationPriority:
        """Determine escalation priority"""
        
        claim_amount = ai_analysis.get("claim_amount", 0)
        
        # Check priority matrix
        amount_category = "high_amount" if claim_amount > 25000 else "low_amount"
        priority_key = (reason, amount_category)
        
        if priority_key in self.escalation_rules["priority_matrix"]:
            return self.escalation_rules["priority_matrix"][priority_key]
        
        # Fallback priority logic
        if reason in [EscalationReason.SYSTEM_ERROR, EscalationReason.FRAUD_SUSPICION]:
            return EscalationPriority.HIGH
        elif reason in [EscalationReason.CUSTOMER_REQUEST, EscalationReason.APPEAL_REQUIRED]:
            return EscalationPriority.MEDIUM
        else:
            return EscalationPriority.LOW
    
    async def _generate_human_instructions(self, reason: EscalationReason,
                                         ai_analysis: Dict[str, Any],
                                         agent_reports: List[Dict[str, Any]]) -> str:
        """Generate instructions for human specialists"""
        
        prompt = f"""
        Generate clear, actionable instructions for a human specialist handling this escalated case:
        
        Escalation Reason: {reason.value}
        AI Analysis: {json.dumps(ai_analysis, indent=2)}
        Agent Reports Summary: {len(agent_reports)} reports with varying outcomes
        
        Instructions should include:
        1. Specific areas to review
        2. Key decision points
        3. Risk factors to consider
        4. Regulatory requirements if applicable
        5. Next steps and timeline
        
        Keep instructions concise but comprehensive.
        """
        
        instructions = await gemini_service.generate_response(prompt)
        return instructions
    
    async def _estimate_resolution_time(self, specialist_type: SpecialistType,
                                      priority: EscalationPriority,
                                      ai_analysis: Dict[str, Any]) -> int:
        """Estimate resolution time in hours"""
        
        # Base times by specialist type
        base_times = {
            SpecialistType.CLAIMS_ADJUSTER: 4,
            SpecialistType.SENIOR_ADJUSTER: 8,
            SpecialistType.MEDICAL_DIRECTOR: 24,
            SpecialistType.FRAUD_INVESTIGATOR: 48,
            SpecialistType.LEGAL_COUNSEL: 72,
            SpecialistType.CUSTOMER_SERVICE_MANAGER: 2,
            SpecialistType.UNDERWRITER: 12,
            SpecialistType.COMPLIANCE_OFFICER: 24,
            SpecialistType.TECHNICAL_SUPPORT: 4
        }
        
        base_time = base_times.get(specialist_type, 8)
        
        # Adjust for priority
        priority_multipliers = {
            EscalationPriority.EMERGENCY: 0.25,
            EscalationPriority.CRITICAL: 0.5,
            EscalationPriority.HIGH: 0.7,
            EscalationPriority.MEDIUM: 1.0,
            EscalationPriority.LOW: 1.5
        }
        
        multiplier = priority_multipliers.get(priority, 1.0)
        
        # Adjust for complexity
        complexity = ai_analysis.get("complexity", 5)
        complexity_factor = 1.0 + (complexity - 5) * 0.1
        
        estimated_time = int(base_time * multiplier * complexity_factor)
        return max(estimated_time, 1)  # Minimum 1 hour
    
    async def assign_case(self, case_id: str, specialist_id: str) -> bool:
        """Assign a case to a specialist"""
        
        if case_id not in self.escalation_cases:
            print(f"❌ Case {case_id} not found")
            return False
        
        case = self.escalation_cases[case_id]
        case.assigned_specialist = specialist_id
        case.assigned_at = datetime.utcnow()
        case.status = EscalationStatus.ASSIGNED
        
        # Update specialist workload
        if specialist_id not in self.specialist_workloads:
            self.specialist_workloads[specialist_id] = []
        self.specialist_workloads[specialist_id].append(case_id)
        
        print(f"👤 Case {case_id} assigned to specialist {specialist_id}")
        return True
    
    async def resolve_case(self, case_id: str, resolution_notes: str,
                         human_feedback: Optional[HumanFeedback] = None) -> bool:
        """Mark a case as resolved and process feedback"""
        
        if case_id not in self.escalation_cases:
            print(f"❌ Case {case_id} not found")
            return False
        
        case = self.escalation_cases[case_id]
        case.resolved_at = datetime.utcnow()
        case.resolution_notes = resolution_notes
        case.status = EscalationStatus.RESOLVED
        
        # Calculate learning value
        case.learning_value = await self._calculate_learning_value(case, human_feedback)
        
        # Process human feedback
        if human_feedback:
            self.feedback_history.append(human_feedback)
            case.ai_feedback = asdict(human_feedback)
            
            # Use feedback for continuous learning
            await continuous_learning_service.process_feedback(
                case.claim_id,
                {
                    "case_id": case_id,
                    "ai_decision_correct": human_feedback.ai_decision_correct,
                    "specialist_feedback": human_feedback.feedback_notes,
                    "complexity_rating": human_feedback.case_complexity_rating,
                    "outcome": "resolved"
                }
            )
        
        # Update specialist workload
        if case.assigned_specialist and case.assigned_specialist in self.specialist_workloads:
            if case_id in self.specialist_workloads[case.assigned_specialist]:
                self.specialist_workloads[case.assigned_specialist].remove(case_id)
        
        # Record learning event
        await continuous_learning_service.record_learning_event(
            claim_id=case.claim_id,
            agent_name="escalation_manager",
            event_type="resolution",
            context={
                "case_id": case_id,
                "escalation_reason": case.escalation_reason.value,
                "resolution_time_hours": (case.resolved_at - case.created_at).total_seconds() / 3600,
                "specialist_type": case.specialist_type.value
            },
            outcome="resolved",
            confidence_before=case.ai_analysis.get("confidence", 0),
            feedback_score=human_feedback.case_complexity_rating / 10 if human_feedback else None
        )
        
        print(f"✅ Case {case_id} resolved (learning value: {case.learning_value:.3f})")
        return True
    
    async def _calculate_learning_value(self, case: EscalationCase,
                                      feedback: Optional[HumanFeedback]) -> float:
        """Calculate the learning value of a resolved case"""
        
        base_value = 1.0
        
        # Higher value for cases where AI was wrong
        if feedback and not feedback.ai_decision_correct:
            base_value *= 2.0
        
        # Higher value for complex cases
        if feedback:
            complexity_factor = feedback.case_complexity_rating / 10.0
            base_value *= (1.0 + complexity_factor)
        
        # Higher value for cases with missed factors
        if feedback and feedback.missed_factors:
            base_value *= (1.0 + len(feedback.missed_factors) * 0.2)
        
        # Lower value for routine escalations
        if case.escalation_reason == EscalationReason.LOW_CONFIDENCE:
            base_value *= 0.8
        
        return min(base_value, 5.0)  # Cap at 5.0
    
    def get_escalation_statistics(self) -> Dict[str, Any]:
        """Get escalation performance statistics"""
        
        total_cases = len(self.escalation_cases)
        
        if total_cases == 0:
            return {"message": "No escalation cases recorded yet"}
        
        # Status distribution
        status_counts = {}
        reason_counts = {}
        specialist_counts = {}
        
        resolved_cases = []
        for case in self.escalation_cases.values():
            status = case.status.value
            reason = case.escalation_reason.value
            specialist = case.specialist_type.value
            
            status_counts[status] = status_counts.get(status, 0) + 1
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            specialist_counts[specialist] = specialist_counts.get(specialist, 0) + 1
            
            if case.status == EscalationStatus.RESOLVED and case.resolved_at:
                resolved_cases.append(case)
        
        # Calculate metrics
        resolution_times = [
            (case.resolved_at - case.created_at).total_seconds() / 3600
            for case in resolved_cases
        ]
        
        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
        
        # AI accuracy from feedback
        feedback_with_accuracy = [f for f in self.feedback_history if hasattr(f, 'ai_decision_correct')]
        ai_accuracy = (sum(1 for f in feedback_with_accuracy if f.ai_decision_correct) / 
                      len(feedback_with_accuracy) if feedback_with_accuracy else 0)
        
        return {
            "total_cases": total_cases,
            "status_distribution": status_counts,
            "escalation_reasons": reason_counts,
            "specialist_distribution": specialist_counts,
            "average_resolution_time": f"{avg_resolution_time:.1f} hours",
            "ai_accuracy_from_feedback": f"{ai_accuracy:.3f}",
            "total_feedback_received": len(self.feedback_history),
            "cases_pending": status_counts.get("pending", 0),
            "cases_in_progress": status_counts.get("in_progress", 0),
            "human_in_loop_enabled": settings.ai.enable_human_in_loop
        }
    
    def get_specialist_workload(self, specialist_id: str) -> Dict[str, Any]:
        """Get workload information for a specialist"""
        
        assigned_cases = self.specialist_workloads.get(specialist_id, [])
        
        case_details = []
        for case_id in assigned_cases:
            if case_id in self.escalation_cases:
                case = self.escalation_cases[case_id]
                case_details.append({
                    "case_id": case_id,
                    "claim_id": case.claim_id,
                    "priority": case.priority.value,
                    "reason": case.escalation_reason.value,
                    "assigned_since": case.assigned_at.isoformat() if case.assigned_at else None,
                    "estimated_resolution": case.estimated_resolution_time
                })
        
        return {
            "specialist_id": specialist_id,
            "active_cases": len(assigned_cases),
            "case_details": case_details,
            "total_workload_hours": sum(
                case.estimated_resolution_time for case in [
                    self.escalation_cases[cid] for cid in assigned_cases 
                    if cid in self.escalation_cases
                ]
            )
        }

# Global instance
human_in_loop_service = HumanInTheLoopService()