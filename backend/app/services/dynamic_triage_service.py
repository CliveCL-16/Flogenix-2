"""
Dynamic Claims Triage Service
Uses Gemini AI for intelligent claim routing and prioritization
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from app.services.gemini_service import gemini_service
from app.services.continuous_learning_service import continuous_learning_service
from app.core.config import settings


class TriagePriority(Enum):
    """Triage priority levels"""
    CRITICAL = "critical"
    HIGH = "high"  
    MEDIUM = "medium"
    LOW = "low"


class TriageRoute(Enum):
    """Possible routing destinations"""
    FAST_TRACK = "fast_track"
    STANDARD_PROCESSING = "standard_processing"
    COMPLEX_REVIEW = "complex_review"
    FRAUD_INVESTIGATION = "fraud_investigation"
    MEDICAL_REVIEW = "medical_review"
    SENIOR_ADJUSTER = "senior_adjuster"
    DENIAL_PROCESSING = "denial_processing"


@dataclass
class TriageDecision:
    """Represents a triage decision"""
    claim_id: str
    priority: TriagePriority
    route: TriageRoute
    estimated_processing_time: int  # hours
    required_agents: List[str]
    confidence_score: float
    reasoning: str
    risk_factors: List[str]
    special_instructions: List[str]
    timestamp: datetime


class DynamicClaimsTriageService:
    """Service for intelligent claims triage using AI"""
    
    def __init__(self):
        """Initialize the dynamic triage service"""
        self.triage_history: List[TriageDecision] = []
        self.routing_rules: Dict[str, Dict[str, Any]] = self._load_routing_rules()
        self.performance_metrics: Dict[str, float] = {
            "accuracy": 0.0,
            "average_processing_time": 0.0,
            "customer_satisfaction": 0.0
        }
        
        print("✅ Dynamic Claims Triage Service initialized")
    
    def _load_routing_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load base routing rules"""
        return {
            "emergency_criteria": {
                "keywords": ["emergency", "urgent", "life-threatening", "critical"],
                "diagnosis_codes": ["I21", "I46", "R06.0"],  # Heart attack, cardiac arrest, dyspnea
                "amount_threshold": 50000,
                "priority": TriagePriority.CRITICAL,
                "route": TriageRoute.MEDICAL_REVIEW
            },
            "fast_track_criteria": {
                "amount_threshold": 500,
                "routine_procedures": ["99213", "99214", "36415"],  # Office visits, blood work
                "low_risk_diagnoses": ["Z00.00", "J06.9"],  # Checkup, common cold
                "priority": TriagePriority.LOW,
                "route": TriageRoute.FAST_TRACK
            },
            "fraud_criteria": {
                "red_flag_patterns": ["duplicate_claims", "unusual_billing", "provider_anomaly"],
                "amount_threshold": 10000,
                "priority": TriagePriority.HIGH,
                "route": TriageRoute.FRAUD_INVESTIGATION
            },
            "complex_criteria": {
                "multiple_diagnoses": 3,
                "rare_procedures": ["27447", "33533"],  # Knee replacement, cardiac surgery
                "amount_threshold": 25000,
                "priority": TriagePriority.MEDIUM,
                "route": TriageRoute.COMPLEX_REVIEW
            }
        }
    
    async def perform_triage(self, claim_id: str, claim_data: Dict[str, Any]) -> TriageDecision:
        """Perform intelligent triage on a claim"""
        
        print(f"🎯 Performing dynamic triage for claim {claim_id}")
        
        try:
            # Get AI analysis
            intent_analysis = await gemini_service.analyze_claim_intent(claim_data)
            
            # Apply learned patterns
            confidence_adjustment = await continuous_learning_service.get_confidence_adjustment(
                "triage_agent", claim_data
            )
            
            # Get recommendations from learning
            recommendations = await continuous_learning_service.get_recommendations(
                "triage_agent", claim_data
            )
            
            # Determine priority and routing
            priority, route, reasoning = await self._determine_routing(
                claim_data, intent_analysis, confidence_adjustment
            )
            
            # Calculate estimated processing time
            estimated_time = await self._estimate_processing_time(
                priority, route, intent_analysis
            )
            
            # Determine required agents
            required_agents = await self._determine_required_agents(
                route, intent_analysis, claim_data
            )
            
            # Calculate confidence score
            base_confidence = intent_analysis.get('complexity_score', 5) / 10
            adjusted_confidence = min(max(base_confidence + confidence_adjustment, 0.0), 1.0)
            
            # Extract risk factors
            risk_factors = intent_analysis.get('risk_factors', [])
            
            # Create triage decision
            triage_decision = TriageDecision(
                claim_id=claim_id,
                priority=priority,
                route=route,
                estimated_processing_time=estimated_time,
                required_agents=required_agents,
                confidence_score=adjusted_confidence,
                reasoning=reasoning,
                risk_factors=risk_factors,
                special_instructions=recommendations,
                timestamp=datetime.utcnow()
            )
            
            # Store decision for learning
            self.triage_history.append(triage_decision)
            
            # Record learning event
            await continuous_learning_service.record_learning_event(
                claim_id=claim_id,
                agent_name="triage_agent",
                event_type="decision",
                context={
                    "claim_data": claim_data,
                    "intent_analysis": intent_analysis,
                    "triage_decision": {
                        "priority": priority.value,
                        "route": route.value,
                        "estimated_time": estimated_time
                    }
                },
                outcome="success",
                confidence_before=adjusted_confidence
            )
            
            print(f"✅ Triage completed: {priority.value} priority, {route.value} route")
            
            return triage_decision
            
        except Exception as e:
            print(f"❌ Error in dynamic triage: {e}")
            
            # Fallback to standard processing
            fallback_decision = TriageDecision(
                claim_id=claim_id,
                priority=TriagePriority.MEDIUM,
                route=TriageRoute.STANDARD_PROCESSING,
                estimated_processing_time=48,
                required_agents=["intake", "eligibility", "clinical", "adjudication"],
                confidence_score=0.5,
                reasoning=f"Fallback due to triage error: {e}",
                risk_factors=["triage_error"],
                special_instructions=["Manual review recommended"],
                timestamp=datetime.utcnow()
            )
            
            return fallback_decision
    
    async def _determine_routing(self, claim_data: Dict[str, Any], 
                               intent_analysis: Dict[str, Any],
                               confidence_adjustment: float) -> Tuple[TriagePriority, TriageRoute, str]:
        """Determine the optimal routing for a claim"""
        
        claim_amount = claim_data.get('claim_amount', 0)
        diagnosis_code = claim_data.get('diagnosis_code', '')
        procedure_code = claim_data.get('procedure_code', '')
        urgency = intent_analysis.get('urgency', 'medium')
        complexity = intent_analysis.get('complexity_score', 5)
        
        # Check emergency criteria first
        if urgency == "critical" or any(code in diagnosis_code for code in 
                                      self.routing_rules["emergency_criteria"]["diagnosis_codes"]):
            return (
                TriagePriority.CRITICAL,
                TriageRoute.MEDICAL_REVIEW,
                "Critical case requiring immediate medical review"
            )
        
        # Check for fraud indicators
        risk_factors = intent_analysis.get('risk_factors', [])
        fraud_indicators = ['unusual_amount', 'provider_anomaly', 'duplicate_pattern']
        if any(indicator in risk_factors for indicator in fraud_indicators) or claim_amount > 10000:
            return (
                TriagePriority.HIGH,
                TriageRoute.FRAUD_INVESTIGATION,
                "Potential fraud indicators detected"
            )
        
        # Check for fast track eligibility
        if (claim_amount <= 500 and 
            procedure_code in self.routing_rules["fast_track_criteria"]["routine_procedures"] and
            complexity <= 3):
            return (
                TriagePriority.LOW,
                TriageRoute.FAST_TRACK,
                "Routine claim eligible for fast track processing"
            )
        
        # Check for complex review
        if (complexity >= 8 or 
            claim_amount > 25000 or
            procedure_code in self.routing_rules["complex_criteria"]["rare_procedures"]):
            return (
                TriagePriority.MEDIUM,
                TriageRoute.COMPLEX_REVIEW,
                "Complex case requiring specialized review"
            )
        
        # Default to standard processing
        return (
            TriagePriority.MEDIUM,
            TriageRoute.STANDARD_PROCESSING,
            "Standard claim processing workflow"
        )
    
    async def _estimate_processing_time(self, priority: TriagePriority, 
                                      route: TriageRoute,
                                      intent_analysis: Dict[str, Any]) -> int:
        """Estimate processing time in hours"""
        
        base_times = {
            TriageRoute.FAST_TRACK: 2,
            TriageRoute.STANDARD_PROCESSING: 24,
            TriageRoute.COMPLEX_REVIEW: 72,
            TriageRoute.FRAUD_INVESTIGATION: 120,
            TriageRoute.MEDICAL_REVIEW: 48,
            TriageRoute.SENIOR_ADJUSTER: 96,
            TriageRoute.DENIAL_PROCESSING: 24
        }
        
        base_time = base_times.get(route, 24)
        
        # Adjust based on priority
        priority_multipliers = {
            TriagePriority.CRITICAL: 0.5,
            TriagePriority.HIGH: 0.7,
            TriagePriority.MEDIUM: 1.0,
            TriagePriority.LOW: 1.2
        }
        
        multiplier = priority_multipliers.get(priority, 1.0)
        
        # Adjust based on complexity
        complexity = intent_analysis.get('complexity_score', 5)
        complexity_factor = 1.0 + (complexity - 5) * 0.1
        
        estimated_time = int(base_time * multiplier * complexity_factor)
        
        return max(estimated_time, 1)  # Minimum 1 hour
    
    async def _determine_required_agents(self, route: TriageRoute, 
                                       intent_analysis: Dict[str, Any],
                                       claim_data: Dict[str, Any]) -> List[str]:
        """Determine which agents are required for processing"""
        
        base_agents = ["intake", "eligibility"]
        
        route_agents = {
            TriageRoute.FAST_TRACK: ["adjudication"],
            TriageRoute.STANDARD_PROCESSING: ["clinical", "adjudication"],
            TriageRoute.COMPLEX_REVIEW: ["clinical", "medical_specialist", "senior_adjuster"],
            TriageRoute.FRAUD_INVESTIGATION: ["fraud", "investigation_specialist"],
            TriageRoute.MEDICAL_REVIEW: ["clinical", "medical_director"],
            TriageRoute.SENIOR_ADJUSTER: ["clinical", "senior_adjuster"],
            TriageRoute.DENIAL_PROCESSING: ["clinical", "legal_review"]
        }
        
        required_agents = base_agents + route_agents.get(route, ["clinical", "adjudication"])
        
        # Add fraud agent if risk factors present
        if intent_analysis.get('risk_factors'):
            if "fraud" not in required_agents:
                required_agents.append("fraud")
        
        return list(set(required_agents))  # Remove duplicates
    
    async def update_triage_outcome(self, claim_id: str, actual_processing_time: int,
                                  outcome: str, customer_feedback: Optional[Dict[str, Any]] = None) -> None:
        """Update triage decision with actual outcome for learning"""
        
        # Find the triage decision
        triage_decision = None
        for decision in self.triage_history:
            if decision.claim_id == claim_id:
                triage_decision = decision
                break
        
        if not triage_decision:
            print(f"⚠️ No triage decision found for claim {claim_id}")
            return
        
        # Calculate accuracy
        time_accuracy = 1.0 - abs(actual_processing_time - triage_decision.estimated_processing_time) / max(
            triage_decision.estimated_processing_time, actual_processing_time
        )
        
        # Update performance metrics
        self._update_performance_metrics(time_accuracy, customer_feedback)
        
        # Record learning event
        await continuous_learning_service.record_learning_event(
            claim_id=claim_id,
            agent_name="triage_agent",
            event_type="outcome",
            context={
                "triage_decision": {
                    "priority": triage_decision.priority.value,
                    "route": triage_decision.route.value,
                    "estimated_time": triage_decision.estimated_processing_time
                },
                "actual_outcome": {
                    "processing_time": actual_processing_time,
                    "outcome": outcome
                }
            },
            outcome=outcome,
            confidence_before=triage_decision.confidence_score,
            feedback_score=customer_feedback.get('satisfaction_score', 0.5) if customer_feedback else None
        )
        
        print(f"📊 Updated triage outcome for {claim_id}: {outcome} (accuracy: {time_accuracy:.3f})")
    
    def _update_performance_metrics(self, time_accuracy: float, 
                                  customer_feedback: Optional[Dict[str, Any]]) -> None:
        """Update overall performance metrics"""
        
        # Update accuracy (simple moving average)
        if hasattr(self, '_accuracy_samples'):
            self._accuracy_samples.append(time_accuracy)
            if len(self._accuracy_samples) > 100:
                self._accuracy_samples = self._accuracy_samples[-100:]
        else:
            self._accuracy_samples = [time_accuracy]
        
        self.performance_metrics["accuracy"] = sum(self._accuracy_samples) / len(self._accuracy_samples)
        
        # Update customer satisfaction if provided
        if customer_feedback and 'satisfaction_score' in customer_feedback:
            satisfaction = customer_feedback['satisfaction_score']
            
            if hasattr(self, '_satisfaction_samples'):
                self._satisfaction_samples.append(satisfaction)
                if len(self._satisfaction_samples) > 100:
                    self._satisfaction_samples = self._satisfaction_samples[-100:]
            else:
                self._satisfaction_samples = [satisfaction]
            
            self.performance_metrics["customer_satisfaction"] = sum(self._satisfaction_samples) / len(self._satisfaction_samples)
    
    def get_triage_statistics(self) -> Dict[str, Any]:
        """Get triage performance statistics"""
        
        total_decisions = len(self.triage_history)
        
        if total_decisions == 0:
            return {"message": "No triage decisions recorded yet"}
        
        # Route distribution
        route_counts = {}
        priority_counts = {}
        
        for decision in self.triage_history:
            route = decision.route.value
            priority = decision.priority.value
            
            route_counts[route] = route_counts.get(route, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Recent performance (last 24 hours)
        recent_decisions = [
            d for d in self.triage_history 
            if d.timestamp > datetime.utcnow() - timedelta(hours=24)
        ]
        
        avg_confidence = sum(d.confidence_score for d in self.triage_history) / total_decisions
        avg_estimated_time = sum(d.estimated_processing_time for d in self.triage_history) / total_decisions
        
        return {
            "total_decisions": total_decisions,
            "recent_decisions_24h": len(recent_decisions),
            "route_distribution": route_counts,
            "priority_distribution": priority_counts,
            "average_confidence": f"{avg_confidence:.3f}",
            "average_estimated_time": f"{avg_estimated_time:.1f} hours",
            "performance_metrics": self.performance_metrics,
            "learning_enabled": settings.ai.enable_dynamic_triage
        }
    
    async def get_routing_recommendations(self, claim_preview: Dict[str, Any]) -> Dict[str, Any]:
        """Get routing recommendations without full triage"""
        
        # Quick analysis for preview
        intent_analysis = await gemini_service.analyze_claim_intent(claim_preview)
        
        priority, route, reasoning = await self._determine_routing(
            claim_preview, intent_analysis, 0.0
        )
        
        estimated_time = await self._estimate_processing_time(
            priority, route, intent_analysis
        )
        
        return {
            "recommended_priority": priority.value,
            "recommended_route": route.value,
            "estimated_processing_time": estimated_time,
            "reasoning": reasoning,
            "complexity_score": intent_analysis.get('complexity_score', 5),
            "risk_factors": intent_analysis.get('risk_factors', [])
        }

# Global instance
dynamic_triage_service = DynamicClaimsTriageService()