"""
Continuous Learning Service
Implements feedback loops and adaptive learning for the claims processing system
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import numpy as np

from app.services.gemini_service import gemini_service
from app.core.config import settings


@dataclass
class LearningEvent:
    """Represents a learning event from claim processing"""
    event_id: str
    claim_id: str
    agent_name: str
    event_type: str  # decision, outcome, feedback, error
    timestamp: datetime
    context: Dict[str, Any]
    outcome: str
    confidence_before: float
    confidence_after: Optional[float] = None
    feedback_score: Optional[float] = None
    learning_value: float = 0.0


@dataclass
class LearningPattern:
    """Represents a learned pattern from historical data"""
    pattern_id: str
    pattern_type: str  # success, failure, optimization
    context_signature: str
    frequency: int
    success_rate: float
    learned_rules: List[str]
    confidence_boost: float
    created_at: datetime
    last_updated: datetime


class ContinuousLearningService:
    """Service for implementing continuous learning and adaptation"""
    
    def __init__(self):
        """Initialize the continuous learning service"""
        self.learning_events: deque = deque(maxlen=10000)  # Keep last 10k events
        self.learned_patterns: Dict[str, LearningPattern] = {}
        self.agent_performance_metrics: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.learning_rate = 0.1
        self.pattern_threshold = 5  # Minimum occurrences to form a pattern
        self.confidence_adjustment_factor = 0.05
        
        print("✅ Continuous Learning Service initialized")
    
    async def record_learning_event(self, claim_id: str, agent_name: str, 
                                  event_type: str, context: Dict[str, Any],
                                  outcome: str, confidence_before: float,
                                  feedback_score: Optional[float] = None) -> str:
        """Record a learning event from claim processing"""
        
        event_id = f"{claim_id}_{agent_name}_{datetime.utcnow().timestamp()}"
        
        learning_event = LearningEvent(
            event_id=event_id,
            claim_id=claim_id,
            agent_name=agent_name,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            context=context,
            outcome=outcome,
            confidence_before=confidence_before,
            feedback_score=feedback_score
        )
        
        # Calculate learning value
        learning_event.learning_value = await self._calculate_learning_value(learning_event)
        
        # Store the event
        self.learning_events.append(learning_event)
        
        # Update agent performance metrics
        await self._update_agent_metrics(learning_event)
        
        # Check for new patterns
        await self._detect_new_patterns(learning_event)
        
        print(f"📚 Recorded learning event: {event_id} (value: {learning_event.learning_value:.3f})")
        
        return event_id
    
    async def _calculate_learning_value(self, event: LearningEvent) -> float:
        """Calculate the learning value of an event"""
        
        base_value = 1.0
        
        # Higher value for unexpected outcomes
        if event.event_type == "error" or event.outcome == "failed":
            base_value *= 1.5
        
        # Higher value for low confidence decisions that succeeded
        if event.confidence_before < 0.7 and event.outcome == "success":
            base_value *= 1.3
        
        # Higher value for feedback events
        if event.feedback_score is not None:
            if event.feedback_score > 0.8:
                base_value *= 1.2
            elif event.feedback_score < 0.3:
                base_value *= 1.4  # Learn more from failures
        
        # Adjust based on event complexity
        context_complexity = len(event.context.get('features', {})) / 10.0
        base_value *= (1.0 + context_complexity * 0.1)
        
        return min(base_value, 3.0)  # Cap at 3.0
    
    async def _update_agent_metrics(self, event: LearningEvent) -> None:
        """Update performance metrics for agents"""
        
        agent_name = event.agent_name
        
        if agent_name not in self.agent_performance_metrics:
            self.agent_performance_metrics[agent_name] = {
                "total_events": 0,
                "success_rate": 0.0,
                "average_confidence": 0.0,
                "learning_velocity": 0.0,
                "last_updated": datetime.utcnow().timestamp()
            }
        
        metrics = self.agent_performance_metrics[agent_name]
        
        # Update counters
        metrics["total_events"] += 1
        
        # Update success rate
        current_success = 1.0 if event.outcome == "success" else 0.0
        metrics["success_rate"] = (
            (metrics["success_rate"] * (metrics["total_events"] - 1) + current_success) /
            metrics["total_events"]
        )
        
        # Update average confidence
        metrics["average_confidence"] = (
            (metrics["average_confidence"] * (metrics["total_events"] - 1) + event.confidence_before) /
            metrics["total_events"]
        )
        
        # Update learning velocity (how much the agent is improving)
        if metrics["total_events"] > 10:
            recent_events = [e for e in self.learning_events 
                           if e.agent_name == agent_name][-10:]
            recent_success_rate = sum(1 for e in recent_events if e.outcome == "success") / len(recent_events)
            metrics["learning_velocity"] = recent_success_rate - metrics["success_rate"]
        
        metrics["last_updated"] = datetime.utcnow().timestamp()
    
    async def _detect_new_patterns(self, event: LearningEvent) -> None:
        """Detect new learning patterns from events"""
        
        # Generate context signature for pattern matching
        context_signature = await self._generate_context_signature(event.context)
        
        # Look for similar events
        similar_events = [
            e for e in self.learning_events
            if await self._are_events_similar(e, event) and 
            e.timestamp > datetime.utcnow() - timedelta(days=30)  # Last 30 days
        ]
        
        if len(similar_events) >= self.pattern_threshold:
            # Check if we already have this pattern
            pattern_id = f"{event.agent_name}_{context_signature}"
            
            if pattern_id not in self.learned_patterns:
                # Create new pattern
                success_rate = sum(1 for e in similar_events if e.outcome == "success") / len(similar_events)
                
                learned_rules = await self._extract_rules_from_events(similar_events)
                
                pattern = LearningPattern(
                    pattern_id=pattern_id,
                    pattern_type="success" if success_rate > 0.8 else "failure" if success_rate < 0.3 else "mixed",
                    context_signature=context_signature,
                    frequency=len(similar_events),
                    success_rate=success_rate,
                    learned_rules=learned_rules,
                    confidence_boost=self._calculate_confidence_boost(success_rate),
                    created_at=datetime.utcnow(),
                    last_updated=datetime.utcnow()
                )
                
                self.learned_patterns[pattern_id] = pattern
                print(f"🎯 New pattern detected: {pattern_id} (success rate: {success_rate:.3f})")
            else:
                # Update existing pattern
                pattern = self.learned_patterns[pattern_id]
                pattern.frequency += 1
                pattern.last_updated = datetime.utcnow()
    
    async def _generate_context_signature(self, context: Dict[str, Any]) -> str:
        """Generate a signature for context matching"""
        
        # Key features for pattern recognition
        key_features = [
            'diagnosis_code',
            'procedure_code',
            'claim_amount_range',
            'provider_type',
            'complexity_level'
        ]
        
        signature_parts = []
        
        for feature in key_features:
            if feature == 'claim_amount_range':
                amount = context.get('claim_amount', 0)
                if amount < 100:
                    signature_parts.append('low')
                elif amount < 1000:
                    signature_parts.append('medium')
                else:
                    signature_parts.append('high')
            elif feature == 'complexity_level':
                # Infer complexity from context
                complexity = len(context.get('features', {}))
                if complexity < 5:
                    signature_parts.append('simple')
                elif complexity < 10:
                    signature_parts.append('moderate')
                else:
                    signature_parts.append('complex')
            else:
                value = context.get(feature, 'unknown')
                signature_parts.append(str(value)[:20])  # Limit length
        
        return '|'.join(signature_parts)
    
    async def _are_events_similar(self, event1: LearningEvent, event2: LearningEvent) -> bool:
        """Check if two events are similar for pattern detection"""
        
        # Same agent and event type
        if event1.agent_name != event2.agent_name or event1.event_type != event2.event_type:
            return False
        
        # Similar context
        sig1 = await self._generate_context_signature(event1.context)
        sig2 = await self._generate_context_signature(event2.context)
        
        return sig1 == sig2
    
    async def _extract_rules_from_events(self, events: List[LearningEvent]) -> List[str]:
        """Extract learned rules from a group of similar events"""
        
        # Use Gemini to analyze the events and extract patterns
        events_summary = {
            "total_events": len(events),
            "success_events": [e for e in events if e.outcome == "success"],
            "failure_events": [e for e in events if e.outcome == "failed"],
            "average_confidence": sum(e.confidence_before for e in events) / len(events),
            "context_features": events[0].context if events else {}
        }
        
        prompt = f"""
        Analyze these similar events and extract learned rules:
        
        Events Summary: {json.dumps(events_summary, default=str, indent=2)}
        
        Please identify:
        1. Success patterns and rules
        2. Failure patterns to avoid
        3. Confidence level adjustments
        4. Process optimizations
        
        Return as a JSON list of actionable rules:
        ["rule1", "rule2", "rule3"]
        """
        
        try:
            response = await gemini_service.generate_response(prompt)
            
            # Extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"❌ Error extracting rules: {e}")
        
        # Default rules if AI fails
        return [
            f"Similar cases have {events_summary['total_events']} occurrences",
            f"Success rate: {len(events_summary['success_events'])/len(events)*100:.1f}%",
            f"Average confidence: {events_summary['average_confidence']:.3f}"
        ]
    
    def _calculate_confidence_boost(self, success_rate: float) -> float:
        """Calculate confidence boost based on success rate"""
        
        if success_rate > 0.9:
            return 0.1  # High confidence boost for very successful patterns
        elif success_rate > 0.8:
            return 0.05  # Medium confidence boost
        elif success_rate < 0.3:
            return -0.1  # Negative boost for failure patterns
        else:
            return 0.0  # No boost for mixed patterns
    
    async def get_confidence_adjustment(self, agent_name: str, context: Dict[str, Any]) -> float:
        """Get confidence adjustment based on learned patterns"""
        
        context_signature = await self._generate_context_signature(context)
        pattern_id = f"{agent_name}_{context_signature}"
        
        if pattern_id in self.learned_patterns:
            pattern = self.learned_patterns[pattern_id]
            print(f"🎯 Applying learned pattern: {pattern_id} (boost: {pattern.confidence_boost:.3f})")
            return pattern.confidence_boost
        
        return 0.0
    
    async def get_recommendations(self, agent_name: str, context: Dict[str, Any]) -> List[str]:
        """Get recommendations based on learned patterns"""
        
        context_signature = await self._generate_context_signature(context)
        pattern_id = f"{agent_name}_{context_signature}"
        
        if pattern_id in self.learned_patterns:
            pattern = self.learned_patterns[pattern_id]
            return pattern.learned_rules
        
        return []
    
    async def process_feedback(self, claim_id: str, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process external feedback for learning"""
        
        # Find related learning events
        related_events = [e for e in self.learning_events if e.claim_id == claim_id]
        
        if not related_events:
            return {"status": "no_events_found", "claim_id": claim_id}
        
        # Use Gemini to process the feedback
        feedback_analysis = await gemini_service.continuous_learning_feedback(
            claim_id, feedback_data.get('outcome', 'unknown'), feedback_data
        )
        
        # Update learning events with feedback
        for event in related_events:
            event.feedback_score = feedback_data.get('satisfaction_score', 0.5)
            event.confidence_after = event.confidence_before + (
                feedback_analysis.get('confidence_adjustment', 0) * self.confidence_adjustment_factor
            )
        
        # Update patterns based on feedback
        await self._update_patterns_with_feedback(related_events, feedback_analysis)
        
        print(f"📊 Processed feedback for claim {claim_id}: {feedback_analysis.get('learning_points', [])}")
        
        return {
            "status": "processed",
            "claim_id": claim_id,
            "events_updated": len(related_events),
            "learning_points": feedback_analysis.get('learning_points', []),
            "confidence_adjustment": feedback_analysis.get('confidence_adjustment', 0)
        }
    
    async def _update_patterns_with_feedback(self, events: List[LearningEvent], 
                                           feedback_analysis: Dict[str, Any]) -> None:
        """Update learned patterns based on feedback"""
        
        for event in events:
            context_signature = await self._generate_context_signature(event.context)
            pattern_id = f"{event.agent_name}_{context_signature}"
            
            if pattern_id in self.learned_patterns:
                pattern = self.learned_patterns[pattern_id]
                
                # Adjust confidence boost based on feedback
                feedback_adjustment = feedback_analysis.get('confidence_adjustment', 0)
                pattern.confidence_boost += feedback_adjustment * 0.1
                
                # Add new learned rules
                new_rules = feedback_analysis.get('process_improvements', [])
                pattern.learned_rules.extend(new_rules)
                
                # Remove duplicates
                pattern.learned_rules = list(set(pattern.learned_rules))
                
                pattern.last_updated = datetime.utcnow()
    
    def get_agent_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all agents"""
        
        summary = {}
        
        for agent_name, metrics in self.agent_performance_metrics.items():
            summary[agent_name] = {
                "total_processed": metrics["total_events"],
                "success_rate": f"{metrics['success_rate']:.3f}",
                "average_confidence": f"{metrics['average_confidence']:.3f}",
                "learning_velocity": f"{metrics['learning_velocity']:.3f}",
                "patterns_learned": len([p for p in self.learned_patterns.keys() 
                                       if p.startswith(agent_name)]),
                "last_activity": datetime.fromtimestamp(metrics["last_updated"]).isoformat()
            }
        
        return summary
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get overall learning statistics"""
        
        return {
            "total_learning_events": len(self.learning_events),
            "total_patterns_learned": len(self.learned_patterns),
            "average_learning_value": sum(e.learning_value for e in self.learning_events) / len(self.learning_events) if self.learning_events else 0,
            "pattern_types": {
                "success": len([p for p in self.learned_patterns.values() if p.pattern_type == "success"]),
                "failure": len([p for p in self.learned_patterns.values() if p.pattern_type == "failure"]),
                "mixed": len([p for p in self.learned_patterns.values() if p.pattern_type == "mixed"])
            },
            "learning_rate": self.learning_rate,
            "recent_activity": len([e for e in self.learning_events 
                                  if e.timestamp > datetime.utcnow() - timedelta(hours=24)])
        }

# Global instance
continuous_learning_service = ContinuousLearningService()