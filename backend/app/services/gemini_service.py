"""
Gemini AI Service
Centralized service for all Gemini API interactions
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.core.config import settings
from app.models import ClaimState, AgentReport


class GeminiService:
    """Service for interacting with Google's Gemini API"""
    
    def __init__(self):
        """Initialize Gemini service with API key and configuration"""
        
        # Try to get API key from environment or settings
        self.api_key = os.getenv("GEMINI_API_KEY") or getattr(settings.ai, 'gemini_api_key', None)
        
        if not self.api_key:
            print("⚠️ GEMINI_API_KEY not found - Gemini service will be in fallback mode")
            self.fallback_mode = True
            return
        
        self.fallback_mode = False
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model_name = getattr(settings.ai, 'gemini_model', 'gemini-2.5-flash')
        self.temperature = getattr(settings.ai, 'gemini_temperature', 0.1)
        
        # Configure safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        try:
            # Initialize the model
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                safety_settings=self.safety_settings
            )
            print(f"✅ Gemini service initialized with model: {self.model_name}")
        except Exception as e:
            print(f"⚠️ Error initializing Gemini model: {e}")
            self.fallback_mode = True
    
    async def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate a response using Gemini API"""
        
        # Check if in fallback mode
        if getattr(self, 'fallback_mode', True):
            return f"Gemini service unavailable - fallback response for: {prompt[:50]}..."
        
        try:
            # Prepare the full prompt with context if provided
            full_prompt = prompt
            if context:
                context_str = json.dumps(context, indent=2)
                full_prompt = f"Context:\n{context_str}\n\nPrompt:\n{prompt}"
            
            # Generate response
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=getattr(settings.ai, 'max_tokens', 2000),
                )
            )
            
            # Handle different response scenarios
            if hasattr(response, 'text') and response.text:
                return response.text
            elif hasattr(response, 'candidates') and response.candidates:
                # Try to extract text from candidates if available
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content.parts:
                        return candidate.content.parts[0].text
                
                # If no text content, check finish reason
                finish_reason = response.candidates[0].finish_reason if response.candidates else None
                if finish_reason == 2:  # SAFETY filter
                    return "Content filtered by safety filters. Processing with basic validation rules."
                elif finish_reason == 3:  # RECITATION
                    return "Content may contain recitation. Processing with alternative approach."
                else:
                    return "Unable to generate response. Using fallback processing."
            else:
                return "No response generated. Using fallback processing."
            
        except Exception as e:
            print(f"❌ Error generating Gemini response: {e}")
            # Return a fallback response instead of raising
            return f"AI processing unavailable. Using rule-based analysis. Error: {str(e)[:100]}"
    
    async def analyze_claim_intent(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze claim intent for dynamic triage"""
        prompt = f"""
        Analyze the following insurance claim and determine:
        1. Primary intent (routine_checkup, emergency_care, specialty_treatment, diagnostic_imaging, surgical_procedure)
        2. Urgency level (low, medium, high, critical)
        3. Complexity score (1-10)
        4. Required reviewers (clinical, fraud, adjudication)
        5. Estimated processing time in hours
        6. Risk factors if any
        
        Claim Data:
        - Patient: {claim_data.get('patient_name', 'Unknown')}
        - Diagnosis: {claim_data.get('diagnosis_code', 'Unknown')} - {claim_data.get('diagnosis_description', '')}
        - Procedure: {claim_data.get('procedure_code', 'Unknown')} - {claim_data.get('procedure_description', '')}
        - Amount: ${claim_data.get('claim_amount', 0)}
        - Provider: {claim_data.get('provider_name', 'Unknown')}
        - Service Date: {claim_data.get('service_date', 'Unknown')}
        
        Respond in JSON format:
        {{
            "intent": "primary_intent_here",
            "urgency": "urgency_level_here",
            "complexity_score": complexity_number_here,
            "required_reviewers": ["reviewer1", "reviewer2"],
            "estimated_hours": estimated_hours_here,
            "risk_factors": ["factor1", "factor2"],
            "reasoning": "explanation_of_analysis"
        }}
        """
        
        response = await self.generate_response(prompt)
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
        except Exception as e:
            print(f"❌ Error parsing claim intent analysis: {e}")
            # Return default analysis
            return {
                "intent": "routine_checkup",
                "urgency": "medium",
                "complexity_score": 5,
                "required_reviewers": ["clinical", "adjudication"],
                "estimated_hours": 24,
                "risk_factors": [],
                "reasoning": f"Failed to parse analysis: {e}"
            }
    
    async def analyze_exception(self, exception_type: str, exception_data: Dict[str, Any], 
                              claim_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze an exception and suggest autonomous resolution"""
        prompt = f"""
        Analyze the following exception in insurance claims processing and suggest an autonomous resolution:
        
        Exception Type: {exception_type}
        Exception Data: {json.dumps(exception_data, indent=2)}
        Claim Context: {json.dumps(claim_context, indent=2)}
        
        Please provide:
        1. Root cause analysis
        2. Suggested resolution steps
        3. Confidence level (0-100)
        4. Whether human intervention is required
        5. Similar exceptions that might occur
        6. Preventive measures
        
        Respond in JSON format:
        {{
            "root_cause": "detailed_analysis",
            "resolution_steps": ["step1", "step2", "step3"],
            "confidence_level": confidence_percentage,
            "requires_human": true_or_false,
            "similar_exceptions": ["exception1", "exception2"],
            "preventive_measures": ["measure1", "measure2"],
            "automated_action": "specific_action_to_take"
        }}
        """
        
        response = await self.generate_response(prompt)
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"❌ Error parsing exception analysis: {e}")
            return {
                "root_cause": f"Analysis failed: {e}",
                "resolution_steps": ["Manual review required"],
                "confidence_level": 0,
                "requires_human": True,
                "similar_exceptions": [],
                "preventive_measures": [],
                "automated_action": "escalate_to_human"
            }
    
    async def detect_fraud_patterns(self, claim_data: Dict[str, Any], 
                                  historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Advanced fraud detection using pattern recognition"""
        prompt = f"""
        Analyze the following claim for potential fraud using advanced pattern recognition:
        
        Current Claim:
        {json.dumps(claim_data, indent=2)}
        
        Historical Context (similar claims):
        {json.dumps(historical_data[:5], indent=2)}  # Limit to avoid token overflow
        
        Look for:
        1. Unusual patterns in billing amounts
        2. Provider behavior anomalies
        3. Patient claim frequency patterns
        4. Diagnosis-procedure mismatches
        5. Temporal patterns (timing, frequency)
        6. Geographic anomalies
        
        Respond in JSON format:
        {{
            "fraud_risk_score": score_0_to_100,
            "risk_level": "low/medium/high/critical",
            "detected_patterns": ["pattern1", "pattern2"],
            "red_flags": ["flag1", "flag2"],
            "confidence_level": confidence_percentage,
            "recommended_action": "approve/review/investigate/deny",
            "investigation_priority": "low/medium/high",
            "similar_fraudulent_cases": ["case1", "case2"],
            "reasoning": "detailed_explanation"
        }}
        """
        
        response = await self.generate_response(prompt)
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"❌ Error parsing fraud analysis: {e}")
            return {
                "fraud_risk_score": 50,
                "risk_level": "medium",
                "detected_patterns": [],
                "red_flags": [],
                "confidence_level": 0,
                "recommended_action": "review",
                "investigation_priority": "medium",
                "similar_fraudulent_cases": [],
                "reasoning": f"Analysis failed: {e}"
            }
    
    async def generate_customer_response(self, customer_query: str, claim_context: Dict[str, Any],
                                       tone: str = "professional") -> Dict[str, Any]:
        """Generate customer support responses"""
        prompt = f"""
        Generate a {tone} customer service response for the following query:
        
        Customer Query: {customer_query}
        Claim Context: {json.dumps(claim_context, indent=2)}
        
        The response should:
        1. Address the customer's concern directly
        2. Provide relevant claim information
        3. Explain next steps if applicable
        4. Maintain empathy and professionalism
        5. Include escalation options if needed
        
        Respond in JSON format:
        {{
            "response_text": "customer_facing_response",
            "sentiment_detected": "positive/neutral/negative/frustrated",
            "escalation_recommended": true_or_false,
            "follow_up_required": true_or_false,
            "estimated_resolution_time": "time_estimate",
            "additional_actions": ["action1", "action2"]
        }}
        """
        
        response = await self.generate_response(prompt)
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"❌ Error generating customer response: {e}")
            return {
                "response_text": "Thank you for contacting us. We're reviewing your claim and will get back to you soon.",
                "sentiment_detected": "neutral",
                "escalation_recommended": False,
                "follow_up_required": True,
                "estimated_resolution_time": "24-48 hours",
                "additional_actions": ["manual_review_required"]
            }
    
    async def assess_human_intervention_need(self, claim_state: ClaimState, 
                                           agent_reports: List[AgentReport]) -> Dict[str, Any]:
        """Determine if human intervention is needed"""
        prompt = f"""
        Analyze the following claim processing state and determine if human intervention is required:
        
        Claim ID: {claim_state.claim_id}
        Current Status: Processing completed
        
        Agent Reports Summary:
        """
        
        for report in agent_reports:
            prompt += f"""
        - {report.agent_name}: {report.status.value} (Confidence: {report.confidence_score}%)
          Result: {report.result}
        """
        
        prompt += f"""
        
        Consider:
        1. Low confidence scores (<70%)
        2. Failed agent processing
        3. Conflicting results
        4. High-risk scenarios
        5. Regulatory compliance requirements
        6. Complex medical cases
        
        Respond in JSON format:
        {{
            "human_intervention_required": true_or_false,
            "urgency_level": "low/medium/high/critical",
            "reason": "detailed_explanation",
            "recommended_specialist": "type_of_expert_needed",
            "escalation_path": ["step1", "step2"],
            "review_priority": priority_score_1_to_10,
            "estimated_review_time": "time_estimate"
        }}
        """
        
        response = await self.generate_response(prompt)
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"❌ Error assessing human intervention need: {e}")
            return {
                "human_intervention_required": True,
                "urgency_level": "medium",
                "reason": f"Assessment failed: {e}",
                "recommended_specialist": "claims_adjuster",
                "escalation_path": ["manual_review"],
                "review_priority": 5,
                "estimated_review_time": "24 hours"
            }
    
    async def continuous_learning_feedback(self, claim_id: str, outcome: str, 
                                         feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process feedback for continuous learning"""
        prompt = f"""
        Process the following feedback for continuous learning improvement:
        
        Claim ID: {claim_id}
        Final Outcome: {outcome}
        Feedback Data: {json.dumps(feedback_data, indent=2)}
        
        Analyze:
        1. What went well in the processing
        2. What could be improved
        3. Patterns to remember for future cases
        4. Model adjustments needed
        5. Process optimizations
        
        Respond in JSON format:
        {{
            "learning_points": ["point1", "point2"],
            "process_improvements": ["improvement1", "improvement2"],
            "pattern_recognition": "new_patterns_identified",
            "confidence_adjustment": adjustment_factor,
            "future_applications": ["scenario1", "scenario2"],
            "training_data_value": score_1_to_10
        }}
        """
        
        response = await self.generate_response(prompt)
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"❌ Error processing learning feedback: {e}")
            return {
                "learning_points": [],
                "process_improvements": [],
                "pattern_recognition": "none",
                "confidence_adjustment": 1.0,
                "future_applications": [],
                "training_data_value": 5
            }

# Global instance
gemini_service = GeminiService()