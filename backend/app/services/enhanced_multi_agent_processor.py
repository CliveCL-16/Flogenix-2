"""
Enhanced Multi-Agent System for Claims Processing
Implements specialized agents with ReAct pattern logging and advanced collaboration
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
import logging

from app.core.config import get_settings
from app.core.models import AgentStatus

logger = logging.getLogger(__name__)

class ReActStepType(Enum):
    """Types of ReAct pattern steps"""
    REASON = "REASON"
    ACT = "ACT"
    OBSERVE = "OBSERVE"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"

@dataclass
class ReActStep:
    """Single step in ReAct reasoning pattern"""
    step_number: int
    step_type: ReActStepType
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ToolCall:
    """Represents a tool call made by an agent"""
    tool_name: str
    parameters: Dict[str, Any]
    result: Any
    success: bool
    error_message: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class AgentResult:
    """Result from an agent's processing"""
    agent_name: str
    status: AgentStatus
    result: str
    confidence_score: float
    reasoning_steps: List[ReActStep]
    tool_calls: List[ToolCall]
    duration_seconds: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ClaimProcessingState:
    """Maintains state throughout the multi-agent processing pipeline"""
    claim_id: str
    claim_data: Dict[str, Any]
    
    # Processing status
    current_agent: Optional[str] = None
    processing_start_time: datetime = field(default_factory=datetime.utcnow)
    
    # Agent results
    agent_results: Dict[str, AgentResult] = field(default_factory=dict)
    
    # Intermediate results
    intake_result: Optional[Dict[str, Any]] = None
    eligibility_result: Optional[Dict[str, Any]] = None
    clinical_result: Optional[Dict[str, Any]] = None
    fraud_result: Optional[Dict[str, Any]] = None
    
    # Final decision
    final_decision: Optional[str] = None
    confidence_score: float = 0.0
    reasoning: Optional[str] = None
    
    # Error handling
    errors: List[str] = field(default_factory=list)
    retry_count: int = 0

class BaseAgent(ABC):
    """Base class for all specialized agents"""
    
    def __init__(self, name: str, agent_type: str):
        self.name = name
        self.agent_type = agent_type
        self.settings = get_settings()
        self.reasoning_steps: List[ReActStep] = []
        self.tool_calls: List[ToolCall] = []
    
    def add_reasoning_step(self, step_type: ReActStepType, content: str, metadata: Dict[str, Any] = None):
        """Add a reasoning step using ReAct pattern"""
        step = ReActStep(
            step_number=len(self.reasoning_steps) + 1,
            step_type=step_type,
            content=content,
            metadata=metadata or {}
        )
        self.reasoning_steps.append(step)
        logger.info(f"{self.name} - {step_type.value}: {content}")
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolCall:
        """Call a tool and record the result"""
        start_time = time.time()
        tool_call = ToolCall(
            tool_name=tool_name,
            parameters=parameters,
            result=None,
            success=False
        )
        
        try:
            # Simulate tool call - in production, this would call actual APIs/databases
            result = self._execute_tool(tool_name, parameters)
            tool_call.result = result
            tool_call.success = True
            
        except Exception as e:
            tool_call.error_message = str(e)
            tool_call.success = False
            logger.error(f"{self.name} tool call failed: {tool_name} - {e}")
        
        finally:
            tool_call.execution_time = time.time() - start_time
            self.tool_calls.append(tool_call)
        
        return tool_call
    
    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute the actual tool call - to be implemented by subclasses or external services"""
        # Mock implementation for demonstration
        if tool_name == "validate_fields":
            return {"status": "valid", "missing_fields": []}
        elif tool_name == "check_eligibility":
            return {"status": "eligible", "coverage": "active", "copay": 20}
        elif tool_name == "validate_codes":
            return {"status": "valid", "diagnosis_valid": True, "procedure_valid": True}
        elif tool_name == "check_fraud_indicators":
            return {"fraud_score": 15, "risk_factors": [], "flagged": False}
        elif tool_name == "calculate_approval_score":
            return {"approval_score": 85, "recommendation": "approve"}
        else:
            return {"status": "success", "message": f"Tool {tool_name} executed"}
    
    @abstractmethod
    async def process(self, state: ClaimProcessingState) -> AgentResult:
        """Process the claim and return results"""
        pass
    
    def create_result(self, status: AgentStatus, result: str, confidence: float, 
                     error_message: Optional[str] = None, metadata: Dict[str, Any] = None) -> AgentResult:
        """Create an AgentResult with current reasoning steps and tool calls"""
        return AgentResult(
            agent_name=self.name,
            status=status,
            result=result,
            confidence_score=confidence,
            reasoning_steps=self.reasoning_steps.copy(),
            tool_calls=self.tool_calls.copy(),
            duration_seconds=0.0,  # Will be calculated by caller
            error_message=error_message,
            metadata=metadata or {}
        )

class IntakeAgent(BaseAgent):
    """Specialized agent for claim intake and initial validation"""
    
    def __init__(self):
        super().__init__("Intake Agent", "intake")
    
    async def process(self, state: ClaimProcessingState) -> AgentResult:
        """Process claim intake and validation"""
        start_time = time.time()
        
        try:
            self.add_reasoning_step(
                ReActStepType.REASON,
                "I need to validate the incoming claim data and ensure all required fields are present"
            )
            
            # Validate required fields
            self.add_reasoning_step(ReActStepType.ACT, "Calling validate_fields tool to check data completeness")
            validation_result = self.call_tool("validate_fields", {"claim_data": state.claim_data})
            
            self.add_reasoning_step(
                ReActStepType.OBSERVE,
                f"Validation result: {validation_result.result}"
            )
            
            if not validation_result.success:
                self.add_reasoning_step(
                    ReActStepType.ERROR,
                    f"Field validation failed: {validation_result.error_message}"
                )
                return self.create_result(
                    AgentStatus.FAILED,
                    "Validation failed",
                    0.0,
                    validation_result.error_message
                )
            
            # Extract and validate entities
            self.add_reasoning_step(ReActStepType.ACT, "Extracting and validating claim entities")
            entity_result = self.call_tool("extract_entities", {"claim_data": state.claim_data})
            
            self.add_reasoning_step(
                ReActStepType.OBSERVE,
                f"Extracted {len(entity_result.result.get('entities', []))} entities successfully"
            )
            
            # Store intake results
            state.intake_result = {
                "status": "validated",
                "entities": entity_result.result.get('entities', []),
                "validation_score": 95
            }
            
            self.add_reasoning_step(
                ReActStepType.COMPLETE,
                "Claim intake validation completed successfully. All required fields present and valid."
            )
            
            result = self.create_result(
                AgentStatus.COMPLETED,
                "Intake validated successfully",
                95.0,
                metadata={"entities_count": len(entity_result.result.get('entities', []))}
            )
            
        except Exception as e:
            self.add_reasoning_step(ReActStepType.ERROR, f"Unexpected error during intake: {str(e)}")
            result = self.create_result(AgentStatus.FAILED, "Intake processing failed", 0.0, str(e))
        
        result.duration_seconds = time.time() - start_time
        return result

class EligibilityAgent(BaseAgent):
    """Specialized agent for insurance eligibility verification"""
    
    def __init__(self):
        super().__init__("Eligibility Agent", "eligibility")
    
    async def process(self, state: ClaimProcessingState) -> AgentResult:
        """Verify patient insurance eligibility"""
        start_time = time.time()
        
        try:
            self.add_reasoning_step(
                ReActStepType.REASON,
                "I need to verify the patient's insurance eligibility and coverage for the requested procedure"
            )
            
            # Check insurance eligibility
            self.add_reasoning_step(
                ReActStepType.ACT,
                f"Calling eligibility API for patient {state.claim_data['patient_id']} with {state.claim_data['insurance_provider']}"
            )
            
            eligibility_params = {
                "patient_id": state.claim_data["patient_id"],
                "insurance_provider": state.claim_data["insurance_provider"],
                "policy_number": state.claim_data["policy_number"],
                "procedure_code": state.claim_data["procedure_code"]
            }
            
            eligibility_result = self.call_tool("check_eligibility", eligibility_params)
            
            self.add_reasoning_step(
                ReActStepType.OBSERVE,
                f"Eligibility check result: {eligibility_result.result}"
            )
            
            if not eligibility_result.success:
                self.add_reasoning_step(
                    ReActStepType.ERROR,
                    f"Eligibility check failed: {eligibility_result.error_message}"
                )
                return self.create_result(
                    AgentStatus.FAILED,
                    "Eligibility verification failed",
                    0.0,
                    eligibility_result.error_message
                )
            
            eligibility_data = eligibility_result.result
            
            # Analyze eligibility results
            if eligibility_data["status"] == "eligible":
                confidence = 90.0
                result_message = "Patient eligible for coverage"
                
                self.add_reasoning_step(
                    ReActStepType.OBSERVE,
                    f"Patient has active coverage with ${eligibility_data.get('copay', 0)} copay"
                )
            else:
                confidence = 20.0
                result_message = "Patient not eligible for coverage"
                
                self.add_reasoning_step(
                    ReActStepType.OBSERVE,
                    f"Eligibility issue detected: {eligibility_data.get('reason', 'Unknown')}"
                )
            
            # Store eligibility results
            state.eligibility_result = eligibility_data
            
            self.add_reasoning_step(
                ReActStepType.COMPLETE,
                f"Eligibility verification completed. Patient is {eligibility_data['status']}"
            )
            
            result = self.create_result(
                AgentStatus.COMPLETED,
                result_message,
                confidence,
                metadata={"eligibility_status": eligibility_data["status"]}
            )
            
        except Exception as e:
            self.add_reasoning_step(ReActStepType.ERROR, f"Unexpected error during eligibility check: {str(e)}")
            result = self.create_result(AgentStatus.FAILED, "Eligibility check failed", 0.0, str(e))
        
        result.duration_seconds = time.time() - start_time
        return result

class ClinicalReviewAgent(BaseAgent):
    """Specialized agent for clinical review and medical code validation"""
    
    def __init__(self):
        super().__init__("Clinical Review Agent", "clinical")
    
    async def process(self, state: ClaimProcessingState) -> AgentResult:
        """Perform clinical review and validate medical codes"""
        start_time = time.time()
        
        try:
            self.add_reasoning_step(
                ReActStepType.REASON,
                "I need to validate the medical codes and ensure the procedure is appropriate for the diagnosis"
            )
            
            # Validate diagnosis and procedure codes
            self.add_reasoning_step(
                ReActStepType.ACT,
                f"Validating ICD-10 code {state.claim_data['diagnosis_code']} and CPT code {state.claim_data['procedure_code']}"
            )
            
            code_validation_params = {
                "diagnosis_code": state.claim_data["diagnosis_code"],
                "procedure_code": state.claim_data["procedure_code"],
                "service_date": state.claim_data["service_date"]
            }
            
            validation_result = self.call_tool("validate_codes", code_validation_params)
            
            self.add_reasoning_step(
                ReActStepType.OBSERVE,
                f"Code validation result: {validation_result.result}"
            )
            
            if not validation_result.success:
                self.add_reasoning_step(
                    ReActStepType.ERROR,
                    f"Code validation failed: {validation_result.error_message}"
                )
                return self.create_result(
                    AgentStatus.FAILED,
                    "Medical code validation failed",
                    0.0,
                    validation_result.error_message
                )
            
            validation_data = validation_result.result
            
            # Check code compatibility
            self.add_reasoning_step(
                ReActStepType.ACT,
                "Checking compatibility between diagnosis and procedure codes"
            )
            
            compatibility_result = self.call_tool("check_code_compatibility", {
                "diagnosis": state.claim_data["diagnosis_code"],
                "procedure": state.claim_data["procedure_code"]
            })
            
            self.add_reasoning_step(
                ReActStepType.OBSERVE,
                f"Code compatibility: {compatibility_result.result}"
            )
            
            # Determine clinical validity
            if validation_data["status"] == "valid" and compatibility_result.result.get("compatible", False):
                confidence = 95.0
                result_message = "Medical codes valid and compatible"
                clinical_status = "valid"
            else:
                confidence = 30.0
                result_message = "Medical code validation issues detected"
                clinical_status = "invalid"
            
            # Store clinical results
            state.clinical_result = {
                "status": clinical_status,
                "diagnosis_valid": validation_data.get("diagnosis_valid", False),
                "procedure_valid": validation_data.get("procedure_valid", False),
                "codes_compatible": compatibility_result.result.get("compatible", False)
            }
            
            self.add_reasoning_step(
                ReActStepType.COMPLETE,
                f"Clinical review completed. Medical codes are {clinical_status}"
            )
            
            result = self.create_result(
                AgentStatus.COMPLETED,
                result_message,
                confidence,
                metadata={"clinical_status": clinical_status}
            )
            
        except Exception as e:
            self.add_reasoning_step(ReActStepType.ERROR, f"Unexpected error during clinical review: {str(e)}")
            result = self.create_result(AgentStatus.FAILED, "Clinical review failed", 0.0, str(e))
        
        result.duration_seconds = time.time() - start_time
        return result

class FraudDetectionAgent(BaseAgent):
    """Specialized agent for fraud detection and risk analysis"""
    
    def __init__(self):
        super().__init__("Fraud Detection Agent", "fraud")
    
    async def process(self, state: ClaimProcessingState) -> AgentResult:
        """Analyze claim for fraud indicators and calculate risk score"""
        start_time = time.time()
        
        try:
            self.add_reasoning_step(
                ReActStepType.REASON,
                "I need to analyze this claim for potential fraud indicators and calculate a risk score"
            )
            
            # Check for duplicate claims
            self.add_reasoning_step(
                ReActStepType.ACT,
                "Searching for duplicate or similar claims in the database"
            )
            
            duplicate_check = self.call_tool("check_duplicates", {
                "patient_id": state.claim_data["patient_id"],
                "procedure_code": state.claim_data["procedure_code"],
                "service_date": state.claim_data["service_date"]
            })
            
            self.add_reasoning_step(
                ReActStepType.OBSERVE,
                f"Duplicate check result: {duplicate_check.result}"
            )
            
            # Analyze fraud indicators
            self.add_reasoning_step(
                ReActStepType.ACT,
                "Analyzing claim for fraud indicators and calculating risk score"
            )
            
            fraud_params = {
                "claim_data": state.claim_data,
                "provider_history": True,
                "patient_history": True
            }
            
            fraud_analysis = self.call_tool("check_fraud_indicators", fraud_params)
            
            self.add_reasoning_step(
                ReActStepType.OBSERVE,
                f"Fraud analysis complete. Risk score: {fraud_analysis.result.get('fraud_score', 0)}/100"
            )
            
            if not fraud_analysis.success:
                self.add_reasoning_step(
                    ReActStepType.ERROR,
                    f"Fraud analysis failed: {fraud_analysis.error_message}"
                )
                return self.create_result(
                    AgentStatus.FAILED,
                    "Fraud analysis failed",
                    0.0,
                    fraud_analysis.error_message
                )
            
            fraud_data = fraud_analysis.result
            fraud_score = fraud_data.get("fraud_score", 0)
            risk_factors = fraud_data.get("risk_factors", [])
            
            # Determine risk level and confidence
            if fraud_score >= 70:
                risk_level = "HIGH"
                confidence = 85.0
                result_message = f"High fraud risk detected (score: {fraud_score})"
                flagged = True
            elif fraud_score >= 30:
                risk_level = "MEDIUM"
                confidence = 75.0
                result_message = f"Medium fraud risk detected (score: {fraud_score})"
                flagged = False
            else:
                risk_level = "LOW"
                confidence = 90.0
                result_message = f"Low fraud risk (score: {fraud_score})"
                flagged = False
            
            # Store fraud results
            state.fraud_result = {
                "fraud_score": fraud_score,
                "risk_level": risk_level,
                "flagged": flagged,
                "risk_factors": risk_factors,
                "duplicate_claims": duplicate_check.result.get("duplicates", [])
            }
            
            if flagged:
                self.add_reasoning_step(
                    ReActStepType.OBSERVE,
                    f"🚨 FRAUD ALERT: High risk indicators detected: {', '.join(risk_factors)}"
                )
            else:
                self.add_reasoning_step(
                    ReActStepType.OBSERVE,
                    "✅ Fraud screening passed - no significant risk indicators"
                )
            
            self.add_reasoning_step(
                ReActStepType.COMPLETE,
                f"Fraud analysis completed. Risk level: {risk_level}, Score: {fraud_score}/100"
            )
            
            result = self.create_result(
                AgentStatus.COMPLETED,
                result_message,
                confidence,
                metadata={
                    "fraud_score": fraud_score,
                    "risk_level": risk_level,
                    "flagged": flagged
                }
            )
            
        except Exception as e:
            self.add_reasoning_step(ReActStepType.ERROR, f"Unexpected error during fraud analysis: {str(e)}")
            result = self.create_result(AgentStatus.FAILED, "Fraud analysis failed", 0.0, str(e))
        
        result.duration_seconds = time.time() - start_time
        return result

class AdjudicationAgent(BaseAgent):
    """Final adjudication agent that makes the approval/denial decision"""
    
    def __init__(self):
        super().__init__("Adjudication Agent", "adjudication")
    
    async def process(self, state: ClaimProcessingState) -> AgentResult:
        """Make final adjudication decision based on all agent results"""
        start_time = time.time()
        
        try:
            self.add_reasoning_step(
                ReActStepType.REASON,
                "I need to analyze all agent reports and make a final approval/denial decision"
            )
            
            # Analyze agent results
            self.add_reasoning_step(
                ReActStepType.ACT,
                "Reviewing results from intake, eligibility, clinical, and fraud detection agents"
            )
            
            # Check each agent's results
            issues = []
            
            # Intake check
            if not state.intake_result or state.intake_result.get("status") != "validated":
                issues.append("Intake validation failed")
            
            # Eligibility check
            if not state.eligibility_result or state.eligibility_result.get("status") != "eligible":
                issues.append("Patient not eligible for coverage")
            
            # Clinical check
            if not state.clinical_result or state.clinical_result.get("status") != "valid":
                issues.append("Medical codes invalid or incompatible")
            
            # Fraud check
            if state.fraud_result and state.fraud_result.get("flagged", False):
                issues.append("High fraud risk detected")
            
            self.add_reasoning_step(
                ReActStepType.OBSERVE,
                f"Analysis complete. Found {len(issues)} issues: {', '.join(issues) if issues else 'None'}"
            )
            
            # Calculate approval score
            self.add_reasoning_step(ReActStepType.ACT, "Calculating final approval score")
            
            approval_calculation = self.call_tool("calculate_approval_score", {
                "intake_result": state.intake_result,
                "eligibility_result": state.eligibility_result,
                "clinical_result": state.clinical_result,
                "fraud_result": state.fraud_result,
                "claim_amount": state.claim_data.get("claim_amount", 0)
            })
            
            approval_score = approval_calculation.result.get("approval_score", 0)
            
            self.add_reasoning_step(
                ReActStepType.OBSERVE,
                f"Calculated approval score: {approval_score}/100"
            )
            
            # Make final decision
            if issues:
                decision = "DENY"
                confidence = 90.0
                reasoning = f"Claim denied due to: {'; '.join(issues)}"
                
                self.add_reasoning_step(
                    ReActStepType.ACT,
                    f"❌ DENYING claim due to {len(issues)} critical issues"
                )
            elif approval_score >= 70:
                decision = "APPROVE"
                confidence = min(90.0, approval_score)
                reasoning = f"Claim approved. All validations passed with approval score {approval_score}/100"
                
                self.add_reasoning_step(
                    ReActStepType.ACT,
                    f"✅ APPROVING claim with high confidence (score: {approval_score})"
                )
            else:
                decision = "REVIEW"
                confidence = 60.0
                reasoning = f"Claim requires manual review. Approval score {approval_score}/100 below threshold"
                
                self.add_reasoning_step(
                    ReActStepType.ACT,
                    f"⚠️ FLAGGING for manual review due to low approval score"
                )
            
            # Store final decision
            state.final_decision = decision
            state.confidence_score = confidence
            state.reasoning = reasoning
            
            self.add_reasoning_step(
                ReActStepType.COMPLETE,
                f"Final adjudication complete. Decision: {decision} (confidence: {confidence:.1f}%)"
            )
            
            result = self.create_result(
                AgentStatus.COMPLETED,
                f"Decision: {decision}",
                confidence,
                metadata={
                    "decision": decision,
                    "approval_score": approval_score,
                    "issues_count": len(issues)
                }
            )
            
        except Exception as e:
            self.add_reasoning_step(ReActStepType.ERROR, f"Unexpected error during adjudication: {str(e)}")
            result = self.create_result(AgentStatus.FAILED, "Adjudication failed", 0.0, str(e))
        
        result.duration_seconds = time.time() - start_time
        return result

class EnhancedMultiAgentProcessor:
    """Enhanced multi-agent processor with ReAct pattern and advanced collaboration"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize specialized agents
        self.agents = {
            "intake": IntakeAgent(),
            "eligibility": EligibilityAgent(),
            "clinical": ClinicalReviewAgent(),
            "fraud": FraudDetectionAgent(),
            "adjudication": AdjudicationAgent()
        }
        
        # Define processing pipeline
        self.pipeline = ["intake", "eligibility", "clinical", "fraud", "adjudication"]
    
    async def process_claim(self, claim_data: Dict[str, Any], claim_id: str) -> ClaimProcessingState:
        """Process a claim through the multi-agent pipeline"""
        logger.info(f"Starting multi-agent processing for claim {claim_id}")
        
        # Initialize processing state
        state = ClaimProcessingState(
            claim_id=claim_id,
            claim_data=claim_data
        )
        
        try:
            # Process through each agent in the pipeline
            for agent_name in self.pipeline:
                state.current_agent = agent_name
                agent = self.agents[agent_name]
                
                logger.info(f"Processing with {agent.name}")
                
                # Execute agent
                try:
                    result = await agent.process(state)
                    state.agent_results[agent_name] = result
                    
                    # Check for critical failures
                    if result.status == AgentStatus.FAILED:
                        if agent_name in ["intake", "eligibility"]:  # Critical agents
                            logger.error(f"Critical agent {agent_name} failed: {result.error_message}")
                            state.errors.append(f"{agent_name} failed: {result.error_message}")
                            
                            # Stop processing on critical failures
                            state.final_decision = "DENY"
                            state.reasoning = f"Processing stopped due to {agent_name} failure: {result.error_message}"
                            break
                        else:
                            # Non-critical failures - continue with warning
                            logger.warning(f"Non-critical agent {agent_name} failed: {result.error_message}")
                            state.errors.append(f"{agent_name} failed: {result.error_message}")
                    
                except asyncio.TimeoutError:
                    error_msg = f"Agent {agent_name} timed out"
                    logger.error(error_msg)
                    state.errors.append(error_msg)
                    
                    # Create timeout result
                    timeout_result = AgentResult(
                        agent_name=agent.name,
                        status=AgentStatus.TIMEOUT,
                        result="Timed out",
                        confidence_score=0.0,
                        reasoning_steps=[],
                        tool_calls=[],
                        duration_seconds=self.settings.ai.max_agent_processing_time,
                        error_message=error_msg
                    )
                    state.agent_results[agent_name] = timeout_result
                
                except Exception as e:
                    error_msg = f"Agent {agent_name} crashed: {str(e)}"
                    logger.error(error_msg)
                    state.errors.append(error_msg)
                    
                    # Create error result
                    error_result = AgentResult(
                        agent_name=agent.name,
                        status=AgentStatus.FAILED,
                        result="Agent crashed",
                        confidence_score=0.0,
                        reasoning_steps=[],
                        tool_calls=[],
                        duration_seconds=0.0,
                        error_message=error_msg
                    )
                    state.agent_results[agent_name] = error_result
            
            # Ensure we have a final decision
            if not state.final_decision:
                state.final_decision = "REVIEW"
                state.reasoning = "Processing completed but no final decision was made"
                state.confidence_score = 50.0
            
            # Calculate total processing time
            total_duration = (datetime.utcnow() - state.processing_start_time).total_seconds()
            
            logger.info(f"Multi-agent processing completed for claim {claim_id} in {total_duration:.2f}s")
            logger.info(f"Final decision: {state.final_decision} (confidence: {state.confidence_score:.1f}%)")
            
            return state
            
        except Exception as e:
            logger.error(f"Multi-agent processing failed for claim {claim_id}: {str(e)}")
            state.errors.append(f"Pipeline failure: {str(e)}")
            state.final_decision = "REVIEW"
            state.reasoning = f"Processing failed due to system error: {str(e)}"
            return state
    
    def get_agent_timeline(self, claim_id: str) -> List[Dict[str, Any]]:
        """Get processing timeline for agents (mock data for now)"""
        # In production, this would retrieve from stored ClaimProcessingState
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
        """Get detailed ReAct reasoning steps from all agents"""
        # In production, this would retrieve from stored AgentResults
        return {
            "Intake Agent": [
                {"step": 1, "type": "REASON", "text": "I need to validate the claim data structure and ensure all required fields are present"},
                {"step": 2, "type": "ACT", "text": "Calling validate_fields() tool to check data completeness"},
                {"step": 3, "type": "OBSERVE", "text": "All required fields present and valid. Found 8 entities successfully extracted"},
                {"step": 4, "type": "COMPLETE", "text": "Intake validation completed successfully with 95% confidence"}
            ],
            "Eligibility Agent": [
                {"step": 1, "type": "REASON", "text": "I need to verify patient insurance eligibility for the requested procedure"},
                {"step": 2, "type": "ACT", "text": "Calling check_eligibility() API for insurance verification"},
                {"step": 3, "type": "OBSERVE", "text": "Patient has active coverage with $20 copay. Coverage confirmed for procedure"},
                {"step": 4, "type": "COMPLETE", "text": "Eligibility verification completed - patient is eligible"}
            ],
            "Clinical Review Agent": [
                {"step": 1, "type": "REASON", "text": "I need to validate medical codes and check diagnosis-procedure compatibility"},
                {"step": 2, "type": "ACT", "text": "Validating ICD-10 and CPT codes against medical databases"},
                {"step": 3, "type": "OBSERVE", "text": "Both codes are valid and compatible. Procedure appropriate for diagnosis"},
                {"step": 4, "type": "COMPLETE", "text": "Clinical review completed - medical codes valid and compatible"}
            ],
            "Fraud Detection Agent": [
                {"step": 1, "type": "REASON", "text": "I need to analyze this claim for fraud indicators and calculate risk score"},
                {"step": 2, "type": "ACT", "text": "Searching for duplicate claims and analyzing risk patterns"},
                {"step": 3, "type": "OBSERVE", "text": "No duplicate claims found. Provider has clean history"},
                {"step": 4, "type": "ACT", "text": "Calculating comprehensive fraud risk score"},
                {"step": 5, "type": "OBSERVE", "text": "Fraud score: 15/100 (Low risk). No significant risk indicators"},
                {"step": 6, "type": "COMPLETE", "text": "Fraud screening completed - low risk, safe to proceed"}
            ],
            "Adjudication Agent": [
                {"step": 1, "type": "REASON", "text": "I need to review all agent reports and make final approval decision"},
                {"step": 2, "type": "OBSERVE", "text": "All agents completed successfully: intake ✓, eligibility ✓, clinical ✓, fraud ✓"},
                {"step": 3, "type": "ACT", "text": "Calculating final approval score based on all validations"},
                {"step": 4, "type": "OBSERVE", "text": "Approval score: 88/100. All criteria met for approval"},
                {"step": 5, "type": "ACT", "text": "✅ APPROVING claim with high confidence"},
                {"step": 6, "type": "COMPLETE", "text": "Final adjudication completed - APPROVED with 88% confidence"}
            ]
        }
    
    def get_tool_usage(self, claim_id: str) -> List[Dict[str, Any]]:
        """Get comprehensive tool usage report from all agents"""
        # In production, this would aggregate from stored ToolCall objects
        return [
            {
                "agent": "Intake Agent",
                "tool": "validate_fields()",
                "result": "✅ All required fields present",
                "success": True
            },
            {
                "agent": "Intake Agent",
                "tool": "extract_entities()",
                "result": "✅ Extracted 8 entities successfully",
                "success": True
            },
            {
                "agent": "Eligibility Agent",
                "tool": "check_eligibility()",
                "result": "✅ Patient eligible, $20 copay",
                "success": True
            },
            {
                "agent": "Clinical Review Agent",
                "tool": "validate_codes()",
                "result": "✅ ICD-10 and CPT codes valid",
                "success": True
            },
            {
                "agent": "Clinical Review Agent",
                "tool": "check_code_compatibility()",
                "result": "✅ Diagnosis and procedure compatible",
                "success": True
            },
            {
                "agent": "Fraud Detection Agent",
                "tool": "check_duplicates()",
                "result": "✅ No duplicate claims found",
                "success": True
            },
            {
                "agent": "Fraud Detection Agent",
                "tool": "check_fraud_indicators()",
                "result": "✅ Low risk score: 15/100",
                "success": True
            },
            {
                "agent": "Adjudication Agent",
                "tool": "calculate_approval_score()",
                "result": "✅ Approval score: 88/100",
                "success": True
            }
        ]

# Global multi-agent processor instance
enhanced_multi_agent_processor = EnhancedMultiAgentProcessor()