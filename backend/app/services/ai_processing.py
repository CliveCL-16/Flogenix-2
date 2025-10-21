import os
from datetime import datetime
from typing import Dict, Any, List
import openai
from dotenv import load_dotenv

from app.models import Claim, DecisionType, DecisionLog, ClaimState
from app.services.validation import ValidationService
from app.services.multi_agent_processor import MultiAgentProcessor

# Load environment variables
load_dotenv()

class AIProcessingService:
    """Handles AI-powered claim processing and decision making using multi-agent system"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Warning: OPENAI_API_KEY not found in environment variables")
            self.client = None
        else:
            self.client = openai.OpenAI(api_key=api_key)
        
        # Initialize multi-agent processor
        self.multi_agent_processor = MultiAgentProcessor()
    
    async def process_claim(self, claim: Claim, fraud_score: float) -> DecisionLog:
        """Process a claim using multi-agent AI system and return decision log"""
        
        try:
            # Prepare claim data for agents
            claim_data = {
                "patient_name": claim.patient_name,
                "patient_id": claim.patient_id,
                "insurance_provider": claim.insurance_provider,
                "policy_number": claim.policy_number,
                "diagnosis_code": claim.diagnosis_code,
                "procedure_code": claim.procedure_code,
                "claim_amount": claim.claim_amount,
                "service_date": claim.service_date,
                "provider_name": claim.provider_name,
                "provider_npi": claim.provider_npi,
                "notes": claim.notes
            }
            
            # Process through multi-agent system
            result_state = await self.multi_agent_processor.process_claim(claim_data, claim.claim_id)
            
            # Create decision log from agent results
            decision_log = DecisionLog(
                claim_id=claim.claim_id,
                decision=result_state.final_decision or DecisionType.REVIEW,
                confidence_score=result_state.confidence_score,
                reasoning_text=self._format_agent_reasoning(result_state),
                fraud_score=fraud_score,
                created_at=datetime.now()
            )
            
            return decision_log
            
        except Exception as e:
            print(f"Multi-agent processing failed, using fallback: {e}")
            return self._fallback_processing(claim, fraud_score)
    
    def _format_agent_reasoning(self, state: ClaimState) -> str:
        """Format the reasoning from all agents into a comprehensive explanation"""
        
        reasoning_parts = []
        
        # Add main decision reasoning
        if state.reasoning:
            reasoning_parts.append(f"**Final Decision:** {state.reasoning}")
        
        # Add agent summaries
        if state.agent_reports:
            reasoning_parts.append("\n**Agent Analysis:**")
            
            for report in state.agent_reports:
                status_emoji = "✅" if report.status.value == "COMPLETED" else "❌"
                reasoning_parts.append(
                    f"• {status_emoji} **{report.agent_name}** ({report.duration_seconds:.1f}s): {report.result}"
                )
        
        # Add specific findings
        findings = []
        
        if state.eligibility_result:
            if state.eligibility_result["status"] == "eligible":
                findings.append("✅ Patient coverage verified")
            else:
                findings.append(f"❌ Eligibility issue: {state.eligibility_result['details']}")
        
        if state.clinical_result:
            if state.clinical_result["status"] == "valid":
                findings.append("✅ Medical codes validated and compatible")
            else:
                findings.append("❌ Medical code validation issues detected")
        
        if state.fraud_result:
            if state.fraud_result["flagged"]:
                findings.append(f"🚨 Fraud risk detected: {state.fraud_result['details']}")
            else:
                findings.append("✅ Fraud screening passed")
        
        if findings:
            reasoning_parts.append("\n**Key Findings:**")
            reasoning_parts.extend([f"• {finding}" for finding in findings])
        
        return "\n".join(reasoning_parts)
    
    def get_agent_timeline(self, claim_id: str) -> List[Dict[str, Any]]:
        """Get agent processing timeline for a claim"""
        # This would be stored/retrieved from database in production
        # For now, return mock data based on typical flow
        return [
            {
                "agent": "Intake Agent",
                "status": "completed",
                "duration": 0.5,
                "result": "validated",
                "confidence": 95
            },
            {
                "agent": "Eligibility Agent", 
                "status": "completed",
                "duration": 1.2,
                "result": "eligible",
                "confidence": 90
            },
            {
                "agent": "Clinical Review Agent",
                "status": "completed", 
                "duration": 0.8,
                "result": "codes_valid",
                "confidence": 95
            },
            {
                "agent": "Fraud Detection Agent",
                "status": "completed",
                "duration": 1.5,
                "result": "low_risk",
                "confidence": 85
            },
            {
                "agent": "Adjudication Agent",
                "status": "completed",
                "duration": 0.3,
                "result": "approved",
                "confidence": 88
            }
        ]
    
    def get_agent_reasoning(self, claim_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get detailed reasoning steps from all agents"""
        # Mock data - in production would retrieve from stored ClaimState
        return {
            "Intake Agent": [
                {"step": 1, "type": "REASON", "text": "I need to validate the claim data structure"},
                {"step": 2, "type": "ACT", "text": "Calling validate_required_fields()"},
                {"step": 3, "type": "OBSERVE", "text": "All required fields present and valid"},
                {"step": 4, "type": "COMPLETE", "text": "Intake validation completed successfully"}
            ],
            "Fraud Detection Agent": [
                {"step": 1, "type": "REASON", "text": "I need to check for duplicate claims"},
                {"step": 2, "type": "ACT", "text": "Calling query_claims_database()"},
                {"step": 3, "type": "OBSERVE", "text": "No duplicate claims found"},
                {"step": 4, "type": "ACT", "text": "Calling calculate_fraud_score()"},
                {"step": 5, "type": "OBSERVE", "text": "Fraud score: 15/100 (Low risk)"},
                {"step": 6, "type": "COMPLETE", "text": "Fraud screening completed - low risk"}
            ],
            "Adjudication Agent": [
                {"step": 1, "type": "REASON", "text": "Analyzing all agent reports for final decision"},
                {"step": 2, "type": "OBSERVE", "text": "All validations passed, no fraud indicators"},
                {"step": 3, "type": "ACT", "text": "Calling approve_claim()"},
                {"step": 4, "type": "COMPLETE", "text": "Claim approved for payment"}
            ]
        }
    
    def get_tool_usage(self, claim_id: str) -> List[Dict[str, Any]]:
        """Get tool usage summary for a claim"""
        # Mock data - in production would retrieve from stored agent reports
        return [
            {
                "agent": "Intake Agent",
                "tool": "validate_required_fields()",
                "result": "✅ All fields present",
                "success": True
            },
            {
                "agent": "Intake Agent", 
                "tool": "extract_entities()",
                "result": "✅ Extracted 8 entities",
                "success": True
            },
            {
                "agent": "Eligibility Agent",
                "tool": "call_eligibility_api()",
                "result": "✅ Coverage active, $20 copay",
                "success": True
            },
            {
                "agent": "Clinical Review Agent",
                "tool": "lookup_icd10_code('Z00.00')",
                "result": "✅ Valid - Routine health exam",
                "success": True
            },
            {
                "agent": "Clinical Review Agent",
                "tool": "check_code_compatibility()",
                "result": "✅ Codes compatible",
                "success": True
            },
            {
                "agent": "Fraud Detection Agent",
                "tool": "query_claims_database()",
                "result": "✅ No duplicates found",
                "success": True
            },
            {
                "agent": "Adjudication Agent",
                "tool": "approve_claim()",
                "result": "✅ Claim approved",
                "success": True
            }
        ]
    
    def _prepare_claim_context(self, claim: Claim, fraud_score: float) -> str:
        """Prepare claim information for AI analysis"""
        
        # Get code descriptions
        diagnosis_desc = ValidationService.get_code_description(claim.diagnosis_code, "icd10")
        procedure_desc = ValidationService.get_code_description(claim.procedure_code, "cpt")
        
        context = f"""
HEALTHCARE CLAIM ANALYSIS

Patient Information:
- Name: {claim.patient_name}
- Patient ID: {claim.patient_id}
- Insurance: {claim.insurance_provider}
- Policy: {claim.policy_number}

Medical Information:
- Diagnosis Code: {claim.diagnosis_code} ({diagnosis_desc})
- Procedure Code: {claim.procedure_code} ({procedure_desc})
- Service Date: {claim.service_date}
- Claim Amount: ${claim.claim_amount:,.2f}

Provider Information:
- Provider: {claim.provider_name}
- NPI: {claim.provider_npi or 'Not provided'}

Risk Assessment:
- Fraud Score: {fraud_score}/100
- Created: {claim.created_at.strftime('%Y-%m-%d %H:%M')}

Additional Notes: {claim.notes or 'None'}

VALIDATION RESULTS:
{self._get_validation_summary(claim)}
"""
        return context
    
    def _get_validation_summary(self, claim: Claim) -> str:
        """Get validation results summary"""
        is_valid, errors = ValidationService.validate_claim_data(claim)
        
        if is_valid:
            return "✅ All validation checks passed"
        else:
            return "❌ Validation Issues:\n" + "\n".join([f"  - {error}" for error in errors])
    
    async def _get_ai_decision(self, claim_context: str) -> str:
        """Get decision from OpenAI"""
        
        system_prompt = """You are an expert healthcare claims adjudicator AI. Analyze the provided claim and make a decision.

DECISION OPTIONS:
- APPROVE: Claim meets all requirements and should be paid
- DENY: Claim has issues that prevent payment
- REVIEW: Claim needs human review due to complexity or unusual circumstances

ANALYSIS CRITERIA:
1. Medical Necessity: Does the procedure match the diagnosis?
2. Coverage Verification: Is the patient covered for this service?
3. Policy Compliance: Does the claim meet insurance policy requirements?
4. Fraud Indicators: Are there any red flags in the claim data?
5. Documentation: Is all required information present and valid?

RESPONSE FORMAT (JSON):
{
    "decision": "APPROVE|DENY|REVIEW",
    "confidence_score": 85,
    "reasoning": "Detailed explanation of the decision including specific factors considered",
    "key_factors": ["factor1", "factor2", "factor3"],
    "recommendations": "Any recommendations for next steps"
}

Be thorough but concise. Focus on medical accuracy and policy compliance."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": claim_context}
                ],
                temperature=0.1,  # Low temperature for consistent decisions
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OpenAI API call failed: {e}")
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI response and extract decision data"""
        try:
            import json
            
            # Try to extract JSON from response
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = ai_response[start_idx:end_idx]
                data = json.loads(json_str)
                
                # Validate required fields
                decision = data.get("decision", "REVIEW").upper()
                if decision not in ["APPROVE", "DENY", "REVIEW"]:
                    decision = "REVIEW"
                
                confidence = float(data.get("confidence_score", 50))
                confidence = max(0, min(100, confidence))  # Clamp to 0-100
                
                reasoning = data.get("reasoning", "AI analysis completed")
                
                return {
                    "decision": DecisionType(decision),
                    "confidence_score": confidence,
                    "reasoning": reasoning
                }
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            print(f"Failed to parse AI response: {e}")
            # Fallback parsing
            return self._fallback_parse_response(ai_response)
    
    def _fallback_parse_response(self, response: str) -> Dict[str, Any]:
        """Fallback method to parse AI response"""
        response_lower = response.lower()
        
        if "approve" in response_lower:
            decision = DecisionType.APPROVE
        elif "deny" in response_lower:
            decision = DecisionType.DENY
        else:
            decision = DecisionType.REVIEW
        
        # Extract confidence if mentioned
        confidence = 75  # Default
        if "confidence" in response_lower:
            import re
            conf_match = re.search(r'(\d+)%', response)
            if conf_match:
                confidence = min(100, max(0, int(conf_match.group(1))))
        
        return {
            "decision": decision,
            "confidence_score": confidence,
            "reasoning": response[:500]  # Truncate if too long
        }
    
    def _fallback_processing(self, claim: Claim, fraud_score: float) -> DecisionLog:
        """Rule-based fallback when AI is not available"""
        
        # Simple rule-based logic
        is_valid, errors = ValidationService.validate_claim_data(claim)
        
        if not is_valid:
            decision = DecisionType.DENY
            confidence = 95
            reasoning = f"Claim denied due to validation errors: {'; '.join(errors)}"
        elif fraud_score > 70:
            decision = DecisionType.DENY
            confidence = 90
            reasoning = f"Claim denied due to high fraud score ({fraud_score}/100)"
        elif claim.claim_amount > 50000:
            decision = DecisionType.REVIEW
            confidence = 80
            reasoning = f"High-value claim (${claim.claim_amount:,.2f}) requires manual review"
        else:
            decision = DecisionType.APPROVE
            confidence = 85
            reasoning = "Claim meets basic validation requirements and has low fraud risk"
        
        return DecisionLog(
            claim_id=claim.claim_id,
            decision=decision,
            confidence_score=confidence,
            reasoning_text=reasoning,
            fraud_score=fraud_score,
            created_at=datetime.now()
        )