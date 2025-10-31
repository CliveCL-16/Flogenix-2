"""
AI-Driven Customer Support Service
Intelligent customer interaction using Gemini AI
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


class SentimentType(Enum):
    """Customer sentiment types"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"
    CONFUSED = "confused"


class InteractionType(Enum):
    """Types of customer interactions"""
    CLAIM_STATUS = "claim_status"
    CLAIM_SUBMISSION = "claim_submission"
    APPEAL_REQUEST = "appeal_request"
    GENERAL_INQUIRY = "general_inquiry"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"
    TECHNICAL_SUPPORT = "technical_support"


class EscalationLevel(Enum):
    """Escalation levels for customer support"""
    NONE = "none"
    TIER_2 = "tier_2"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    SPECIALIST = "specialist"


@dataclass
class CustomerInteraction:
    """Represents a customer interaction"""
    interaction_id: str
    customer_id: str
    claim_id: Optional[str]
    interaction_type: InteractionType
    customer_message: str
    ai_response: str
    sentiment: SentimentType
    confidence_score: float
    escalation_level: EscalationLevel
    escalation_reason: Optional[str]
    resolution_status: str
    satisfaction_score: Optional[float]
    follow_up_required: bool
    timestamp: datetime
    response_time_seconds: float


@dataclass
class CustomerProfile:
    """Customer interaction profile"""
    customer_id: str
    total_interactions: int
    average_sentiment: float
    preferred_communication_style: str
    escalation_frequency: float
    satisfaction_average: float
    last_interaction: datetime
    interaction_patterns: List[str]


class AICustomerSupportService:
    """AI-driven customer support service"""
    
    def __init__(self):
        """Initialize the customer support service"""
        self.interaction_history: List[CustomerInteraction] = []
        self.customer_profiles: Dict[str, CustomerProfile] = {}
        self.escalation_rules: Dict[str, Any] = self._load_escalation_rules()
        self.response_templates: Dict[str, str] = self._load_response_templates()
        self.performance_metrics: Dict[str, float] = {
            "average_response_time": 0.0,
            "resolution_rate": 0.0,
            "customer_satisfaction": 0.0,
            "escalation_rate": 0.0
        }
        
        print("✅ AI Customer Support Service initialized")
    
    def _load_escalation_rules(self) -> Dict[str, Any]:
        """Load escalation rules for customer support"""
        return {
            "sentiment_based": {
                SentimentType.ANGRY: EscalationLevel.SUPERVISOR,
                SentimentType.FRUSTRATED: EscalationLevel.TIER_2,
                SentimentType.CONFUSED: EscalationLevel.NONE
            },
            "interaction_based": {
                InteractionType.COMPLAINT: EscalationLevel.TIER_2,
                InteractionType.APPEAL_REQUEST: EscalationLevel.SPECIALIST,
                InteractionType.TECHNICAL_SUPPORT: EscalationLevel.TIER_2
            },
            "keywords": {
                "lawsuit": EscalationLevel.MANAGER,
                "discrimination": EscalationLevel.MANAGER,
                "fraud": EscalationLevel.SPECIALIST,
                "emergency": EscalationLevel.SUPERVISOR,
                "urgent": EscalationLevel.TIER_2
            },
            "repeat_contact": {
                "same_day": EscalationLevel.TIER_2,
                "within_week": EscalationLevel.SUPERVISOR
            }
        }
    
    def _load_response_templates(self) -> Dict[str, str]:
        """Load response templates for different scenarios"""
        return {
            "claim_status_approved": "Great news! Your claim {claim_id} has been approved for ${amount}. Payment will be processed within 3-5 business days.",
            "claim_status_denied": "I understand your concern about claim {claim_id}. Unfortunately, it was denied due to {reason}. You have the right to appeal this decision.",
            "claim_status_pending": "Your claim {claim_id} is currently under review. Based on our current processing times, you can expect a decision within {estimated_days} business days.",
            "general_greeting": "Hello! I'm here to help you with your insurance needs. How can I assist you today?",
            "escalation_notice": "I understand this is important to you. Let me connect you with a specialist who can provide more detailed assistance.",
            "satisfaction_survey": "Thank you for contacting us. On a scale of 1-10, how satisfied were you with the service you received today?"
        }
    
    async def handle_customer_interaction(self, customer_id: str, message: str,
                                        claim_id: Optional[str] = None,
                                        interaction_context: Optional[Dict[str, Any]] = None) -> CustomerInteraction:
        """Handle a customer interaction using AI"""
        
        start_time = datetime.utcnow()
        interaction_id = f"interaction_{customer_id}_{int(start_time.timestamp())}"
        
        print(f"💬 Handling customer interaction: {interaction_id}")
        
        try:
            # Analyze customer message
            message_analysis = await self._analyze_customer_message(message, interaction_context)
            
            # Get customer profile
            customer_profile = await self._get_customer_profile(customer_id)
            
            # Determine interaction type
            interaction_type = InteractionType(message_analysis.get("interaction_type", "general_inquiry"))
            
            # Analyze sentiment
            sentiment = SentimentType(message_analysis.get("sentiment", "neutral"))
            
            # Generate AI response
            response_data = await self._generate_customer_response(
                message, claim_id, interaction_type, sentiment, customer_profile, interaction_context
            )
            
            # Determine escalation needs
            escalation_level, escalation_reason = await self._determine_escalation(
                message, sentiment, interaction_type, customer_profile
            )
            
            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create interaction record
            interaction = CustomerInteraction(
                interaction_id=interaction_id,
                customer_id=customer_id,
                claim_id=claim_id,
                interaction_type=interaction_type,
                customer_message=message,
                ai_response=response_data["response_text"],
                sentiment=sentiment,
                confidence_score=response_data.get("confidence_score", 0.8),
                escalation_level=escalation_level,
                escalation_reason=escalation_reason,
                resolution_status="pending",
                satisfaction_score=None,
                follow_up_required=response_data.get("follow_up_required", False),
                timestamp=start_time,
                response_time_seconds=response_time
            )
            
            # Store interaction
            self.interaction_history.append(interaction)
            
            # Update customer profile
            await self._update_customer_profile(customer_id, interaction)
            
            # Record learning event
            await continuous_learning_service.record_learning_event(
                claim_id=claim_id or "no_claim",
                agent_name="customer_support",
                event_type="interaction",
                context={
                    "customer_message": message,
                    "interaction_type": interaction_type.value,
                    "sentiment": sentiment.value,
                    "escalation_level": escalation_level.value
                },
                outcome="completed",
                confidence_before=interaction.confidence_score
            )
            
            print(f"✅ Customer interaction handled: {sentiment.value} sentiment, {escalation_level.value} escalation")
            
            return interaction
            
        except Exception as e:
            print(f"❌ Error handling customer interaction: {e}")
            
            # Fallback response
            fallback_interaction = CustomerInteraction(
                interaction_id=interaction_id,
                customer_id=customer_id,
                claim_id=claim_id,
                interaction_type=InteractionType.GENERAL_INQUIRY,
                customer_message=message,
                ai_response="I apologize, but I'm experiencing technical difficulties. Please hold while I connect you with a human representative.",
                sentiment=SentimentType.NEUTRAL,
                confidence_score=0.0,
                escalation_level=EscalationLevel.TIER_2,
                escalation_reason=f"AI system error: {e}",
                resolution_status="escalated",
                satisfaction_score=None,
                follow_up_required=True,
                timestamp=start_time,
                response_time_seconds=(datetime.utcnow() - start_time).total_seconds()
            )
            
            return fallback_interaction
    
    async def _analyze_customer_message(self, message: str, 
                                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze customer message to understand intent and sentiment"""
        
        prompt = f"""
        Analyze the following customer service message and determine:
        
        Customer Message: "{message}"
        Context: {json.dumps(context or {}, indent=2)}
        
        Please identify:
        1. Interaction type (claim_status, claim_submission, appeal_request, general_inquiry, complaint, compliment, technical_support)
        2. Sentiment (positive, neutral, negative, frustrated, angry, confused)
        3. Urgency level (low, medium, high, critical)
        4. Key topics and concerns
        5. Specific requests or questions
        6. Emotional indicators
        
        Respond in JSON format:
        {{
            "interaction_type": "type_here",
            "sentiment": "sentiment_here",
            "urgency_level": "urgency_here",
            "key_topics": ["topic1", "topic2"],
            "specific_requests": ["request1", "request2"],
            "emotional_indicators": ["indicator1", "indicator2"],
            "confidence_score": confidence_percentage
        }}
        """
        
        response = await gemini_service.generate_response(prompt)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"❌ Error analyzing customer message: {e}")
        
        # Default analysis
        return {
            "interaction_type": "general_inquiry",
            "sentiment": "neutral",
            "urgency_level": "medium",
            "key_topics": ["general_inquiry"],
            "specific_requests": ["assistance"],
            "emotional_indicators": [],
            "confidence_score": 50
        }
    
    async def _get_customer_profile(self, customer_id: str) -> CustomerProfile:
        """Get or create customer profile"""
        
        if customer_id not in self.customer_profiles:
            # Create new profile
            self.customer_profiles[customer_id] = CustomerProfile(
                customer_id=customer_id,
                total_interactions=0,
                average_sentiment=0.0,
                preferred_communication_style="professional",
                escalation_frequency=0.0,
                satisfaction_average=0.0,
                last_interaction=datetime.utcnow(),
                interaction_patterns=[]
            )
        
        return self.customer_profiles[customer_id]
    
    async def _generate_customer_response(self, message: str, claim_id: Optional[str],
                                        interaction_type: InteractionType, sentiment: SentimentType,
                                        customer_profile: CustomerProfile,
                                        context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate appropriate customer response using AI"""
        
        # Determine communication style based on customer profile and sentiment
        if sentiment in [SentimentType.ANGRY, SentimentType.FRUSTRATED]:
            tone = "empathetic and apologetic"
        elif sentiment == SentimentType.CONFUSED:
            tone = "clear and educational"
        elif sentiment == SentimentType.POSITIVE:
            tone = "friendly and enthusiastic"
        else:
            tone = customer_profile.preferred_communication_style
        
        # Use Gemini to generate response
        response_data = await gemini_service.generate_customer_response(
            customer_query=message,
            claim_context=context or {},
            tone=tone
        )
        
        # Enhance response based on interaction type
        if interaction_type == InteractionType.CLAIM_STATUS and claim_id:
            # Add claim-specific information
            response_data["response_text"] = self._enhance_claim_status_response(
                response_data["response_text"], claim_id, context
            )
        
        elif interaction_type == InteractionType.APPEAL_REQUEST:
            # Add appeal process information
            response_data["response_text"] += "\n\nI can help you start the appeal process. Would you like me to guide you through the steps?"
        
        return response_data
    
    def _enhance_claim_status_response(self, base_response: str, claim_id: str,
                                     context: Optional[Dict[str, Any]]) -> str:
        """Enhance response with claim-specific information"""
        
        if not context:
            return base_response
        
        claim_status = context.get("claim_status", "unknown")
        claim_amount = context.get("claim_amount", 0)
        
        if claim_status == "approved":
            template = self.response_templates["claim_status_approved"]
            return template.format(claim_id=claim_id, amount=claim_amount)
        
        elif claim_status == "denied":
            denial_reason = context.get("denial_reason", "policy terms")
            template = self.response_templates["claim_status_denied"]
            return template.format(claim_id=claim_id, reason=denial_reason)
        
        elif claim_status == "pending":
            estimated_days = context.get("estimated_processing_days", "5-7")
            template = self.response_templates["claim_status_pending"]
            return template.format(claim_id=claim_id, estimated_days=estimated_days)
        
        return base_response
    
    async def _determine_escalation(self, message: str, sentiment: SentimentType,
                                  interaction_type: InteractionType,
                                  customer_profile: CustomerProfile) -> Tuple[EscalationLevel, Optional[str]]:
        """Determine if escalation is needed"""
        
        escalation_level = EscalationLevel.NONE
        escalation_reason = None
        
        # Check sentiment-based escalation
        if sentiment in self.escalation_rules["sentiment_based"]:
            escalation_level = self.escalation_rules["sentiment_based"][sentiment]
            escalation_reason = f"Customer sentiment: {sentiment.value}"
        
        # Check interaction type-based escalation
        if interaction_type in self.escalation_rules["interaction_based"]:
            suggested_level = self.escalation_rules["interaction_based"][interaction_type]
            if suggested_level.value > escalation_level.value:
                escalation_level = suggested_level
                escalation_reason = f"Interaction type: {interaction_type.value}"
        
        # Check keyword-based escalation
        message_lower = message.lower()
        for keyword, level in self.escalation_rules["keywords"].items():
            if keyword in message_lower:
                if level.value > escalation_level.value:
                    escalation_level = level
                    escalation_reason = f"Keyword detected: {keyword}"
        
        # Check repeat contact patterns
        recent_interactions = [
            i for i in self.interaction_history
            if i.customer_id == customer_profile.customer_id and
            i.timestamp > datetime.utcnow() - timedelta(days=1)
        ]
        
        if len(recent_interactions) > 2:  # Multiple contacts same day
            if escalation_level.value < EscalationLevel.TIER_2.value:
                escalation_level = EscalationLevel.TIER_2
                escalation_reason = "Multiple contacts within 24 hours"
        
        # Check customer's escalation history
        if customer_profile.escalation_frequency > 0.5:  # Frequently escalated customer
            if escalation_level == EscalationLevel.NONE:
                escalation_level = EscalationLevel.TIER_2
                escalation_reason = "Customer with high escalation frequency"
        
        return escalation_level, escalation_reason
    
    async def _update_customer_profile(self, customer_id: str, interaction: CustomerInteraction) -> None:
        """Update customer profile based on interaction"""
        
        profile = self.customer_profiles[customer_id]
        
        # Update counters
        profile.total_interactions += 1
        profile.last_interaction = interaction.timestamp
        
        # Update sentiment average
        sentiment_scores = {
            SentimentType.POSITIVE: 1.0,
            SentimentType.NEUTRAL: 0.5,
            SentimentType.NEGATIVE: 0.2,
            SentimentType.FRUSTRATED: 0.1,
            SentimentType.ANGRY: 0.0,
            SentimentType.CONFUSED: 0.3
        }
        
        current_sentiment_score = sentiment_scores.get(interaction.sentiment, 0.5)
        profile.average_sentiment = (
            (profile.average_sentiment * (profile.total_interactions - 1) + current_sentiment_score) /
            profile.total_interactions
        )
        
        # Update escalation frequency
        escalations = sum(1 for i in self.interaction_history 
                         if i.customer_id == customer_id and i.escalation_level != EscalationLevel.NONE)
        profile.escalation_frequency = escalations / profile.total_interactions
        
        # Update interaction patterns
        pattern = f"{interaction.interaction_type.value}_{interaction.sentiment.value}"
        if pattern not in profile.interaction_patterns:
            profile.interaction_patterns.append(pattern)
    
    async def update_interaction_outcome(self, interaction_id: str, 
                                       resolution_status: str,
                                       satisfaction_score: Optional[float] = None) -> None:
        """Update interaction outcome for learning"""
        
        # Find interaction
        interaction = None
        for i in self.interaction_history:
            if i.interaction_id == interaction_id:
                interaction = i
                break
        
        if not interaction:
            print(f"⚠️ Interaction {interaction_id} not found")
            return
        
        # Update interaction
        interaction.resolution_status = resolution_status
        interaction.satisfaction_score = satisfaction_score
        
        # Update customer profile satisfaction
        if satisfaction_score is not None:
            customer_profile = self.customer_profiles[interaction.customer_id]
            if customer_profile.satisfaction_average == 0.0:
                customer_profile.satisfaction_average = satisfaction_score
            else:
                # Calculate weighted average
                total_satisfied_interactions = sum(
                    1 for i in self.interaction_history 
                    if i.customer_id == interaction.customer_id and i.satisfaction_score is not None
                )
                customer_profile.satisfaction_average = (
                    (customer_profile.satisfaction_average * (total_satisfied_interactions - 1) + satisfaction_score) /
                    total_satisfied_interactions
                )
        
        # Record learning event
        await continuous_learning_service.record_learning_event(
            claim_id=interaction.claim_id or "no_claim",
            agent_name="customer_support",
            event_type="outcome",
            context={
                "interaction_type": interaction.interaction_type.value,
                "sentiment": interaction.sentiment.value,
                "escalation_level": interaction.escalation_level.value,
                "resolution_status": resolution_status
            },
            outcome=resolution_status,
            confidence_before=interaction.confidence_score,
            feedback_score=satisfaction_score
        )
        
        print(f"📊 Updated interaction outcome: {interaction_id} -> {resolution_status}")
    
    def get_customer_support_statistics(self) -> Dict[str, Any]:
        """Get customer support performance statistics"""
        
        total_interactions = len(self.interaction_history)
        
        if total_interactions == 0:
            return {"message": "No interactions recorded yet"}
        
        # Calculate metrics
        escalated_interactions = sum(
            1 for i in self.interaction_history 
            if i.escalation_level != EscalationLevel.NONE
        )
        
        resolved_interactions = sum(
            1 for i in self.interaction_history 
            if i.resolution_status in ["resolved", "satisfied"]
        )
        
        satisfaction_scores = [
            i.satisfaction_score for i in self.interaction_history 
            if i.satisfaction_score is not None
        ]
        
        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
        
        response_times = [i.response_time_seconds for i in self.interaction_history]
        avg_response_time = sum(response_times) / len(response_times)
        
        # Sentiment distribution
        sentiment_counts = {}
        interaction_type_counts = {}
        
        for interaction in self.interaction_history:
            sentiment = interaction.sentiment.value
            interaction_type = interaction.interaction_type.value
            
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            interaction_type_counts[interaction_type] = interaction_type_counts.get(interaction_type, 0) + 1
        
        return {
            "total_interactions": total_interactions,
            "escalation_rate": f"{(escalated_interactions / total_interactions * 100):.1f}%",
            "resolution_rate": f"{(resolved_interactions / total_interactions * 100):.1f}%",
            "average_satisfaction": f"{avg_satisfaction:.2f}",
            "average_response_time": f"{avg_response_time:.2f} seconds",
            "sentiment_distribution": sentiment_counts,
            "interaction_type_distribution": interaction_type_counts,
            "active_customer_profiles": len(self.customer_profiles),
            "ai_enabled": settings.ai.enable_ai_customer_support
        }

# Global instance
ai_customer_support = AICustomerSupportService()