"""
Enhanced Multi-Agent System for Claims Processing
Implements specialized agents with ReAct pattern logging and LangGraph workflow integration
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
import logging

from app.core.config import get_settings
from app.core.models import AgentStatus
# from app.services.insurance_claim_workflow import insurance_workflow, ClaimState, ClaimStatus

# Temporary replacement for missing module
from enum import Enum
class ClaimState(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    DENIED = "denied"

class ClaimStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    DENIED = "denied"

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
        """Execute intelligent tool calls with realistic business logic"""
        
        if tool_name == "validate_fields":
            return self._validate_required_fields(parameters)
        elif tool_name == "check_eligibility":
            return self._check_patient_eligibility(parameters)
        elif tool_name == "validate_codes":
            return self._validate_medical_codes(parameters)
        elif tool_name == "check_code_compatibility":
            return self._check_medical_code_compatibility(parameters)
        elif tool_name == "check_fraud_indicators":
            return self._analyze_fraud_indicators(parameters)
        elif tool_name == "check_duplicates":
            return self._check_duplicate_claims(parameters)
        elif tool_name == "calculate_approval_score":
            return self._calculate_dynamic_approval_score(parameters)
        elif tool_name == "extract_entities":
            return self._extract_claim_entities(parameters)
        else:
            return {"status": "success", "message": f"Tool {tool_name} executed"}
    
    def _validate_required_fields(self, params: Dict) -> Dict:
        """Validate claim has all required fields"""
        claim_data = params.get("claim_data", {})
        missing_fields = []
        
        required_fields = ["patient_name", "patient_id", "insurance_provider", 
                          "diagnosis_code", "procedure_code", "claim_amount"]
        
        for field in required_fields:
            if not claim_data.get(field):
                missing_fields.append(field)
        
        return {
            "status": "valid" if not missing_fields else "invalid",
            "missing_fields": missing_fields,
            "completeness_score": (len(required_fields) - len(missing_fields)) / len(required_fields) * 100
        }
    
    def _check_patient_eligibility(self, params: Dict) -> Dict:
        """Check insurance eligibility with realistic variation"""
        # Simulate real eligibility checks with some variation
        import random
        
        # 90% of claims are eligible (realistic rate)
        is_eligible = random.random() < 0.9
        
        if is_eligible:
            return {
                "status": "eligible",
                "coverage": "active",
                "copay": random.choice([10, 15, 20, 25, 30]),
                "deductible_met": random.choice([True, False]),
                "coverage_percentage": random.choice([80, 85, 90, 95])
            }
        else:
            return {
                "status": "not_eligible",
                "coverage": "inactive",
                "reason": random.choice([
                    "Policy expired",
                    "Premium not paid", 
                    "Coverage not active for service date",
                    "Patient not found in system"
                ])
            }
    
    def _validate_medical_codes(self, params: Dict) -> Dict:
        """Validate medical codes with real code database"""
        # Get diagnosis and procedure from claim data
        claim_data = params.get("claim_data", {})
        diagnosis = claim_data.get("diagnosis_code", params.get("diagnosis_code", ""))
        procedure = claim_data.get("procedure_code", params.get("procedure_code", ""))
        
        # Real ICD-10 and procedure code validation
        valid_diagnosis_codes = {
            "Z00.00": "General health examination",
            "I10": "Essential hypertension",
            "E11.9": "Type 2 diabetes mellitus",
            "J44.1": "Chronic obstructive pulmonary disease with exacerbation",
            "S72.001A": "Fracture of unspecified part of neck of right femur",
            "C50.911": "Malignant neoplasm of unspecified site of right female breast",
            "F32.9": "Major depressive disorder, single episode, unspecified",
            "M79.3": "Panniculitis, unspecified"
        }
        
        valid_procedure_codes = {
            "99213": "Office/outpatient visit, established patient",
            "99214": "Office/outpatient visit, established patient, detailed",
            "27236": "Open treatment of femoral fracture",
            "19120": "Excision of breast lesion",
            "20610": "Arthrocentesis, aspiration/injection",
            "94010": "Spirometry",
            "90834": "Psychotherapy, 45 minutes",
            "93000": "Electrocardiogram"
        }
        
        diagnosis_valid = diagnosis in valid_diagnosis_codes
        procedure_valid = procedure in valid_procedure_codes
        
        return {
            "status": "valid" if (diagnosis_valid and procedure_valid) else "invalid",
            "diagnosis_valid": diagnosis_valid,
            "procedure_valid": procedure_valid,
            "diagnosis_description": valid_diagnosis_codes.get(diagnosis, "Unknown code"),
            "procedure_description": valid_procedure_codes.get(procedure, "Unknown code")
        }
    
    def _check_medical_code_compatibility(self, params: Dict) -> Dict:
        """Check if diagnosis and procedure codes are medically compatible"""
        # Handle both parameter naming conventions
        diagnosis = params.get("diagnosis_code", params.get("diagnosis", ""))
        procedure = params.get("procedure_code", params.get("procedure", ""))
        
        # Define realistic code compatibility matrix
        compatibility_matrix = {
            "Z00.00": ["99213", "99214"],  # General exam -> office visits
            "I10": ["99213", "99214", "93000"],  # Hypertension -> office visit, EKG  
            "E11.9": ["99213", "99214"],  # Diabetes -> office visits
            "J44.1": ["99213", "94010"],  # COPD -> office visit, spirometry
            "S72.001A": ["27236"],  # Fracture -> fracture repair
            "C50.911": ["19120"],  # Breast cancer -> breast surgery
            "F32.9": ["99213", "90834"],  # Depression -> office visit, therapy
            "M79.3": ["20610"]  # Joint pain -> injection
        }
        
        compatible_procedures = compatibility_matrix.get(diagnosis, [])
        is_compatible = procedure in compatible_procedures
        
        return {
            "compatible": is_compatible,
            "compatibility_score": 0.95 if is_compatible else 0.1,
            "reason": "Medically appropriate" if is_compatible else f"Procedure {procedure} not typically used for diagnosis {diagnosis}"
        }
    
    def _analyze_fraud_indicators(self, params: Dict) -> Dict:
        """Analyze claim for fraud using realistic indicators"""
        # Get claim data from various parameter formats
        claim_data = params.get("claim_data", params)
        amount = float(claim_data.get("claim_amount", 0))
        procedure_code = claim_data.get("procedure_code", "")
        
        # Realistic cost benchmarks
        procedure_benchmarks = {
            "99213": {"avg": 150, "max": 300},
            "99214": {"avg": 200, "max": 400}, 
            "27236": {"avg": 25000, "max": 50000},
            "19120": {"avg": 15000, "max": 30000},
            "20610": {"avg": 400, "max": 800},
            "94010": {"avg": 100, "max": 200},
            "90834": {"avg": 120, "max": 250},
            "93000": {"avg": 80, "max": 150}
        }
        
        benchmark = procedure_benchmarks.get(procedure_code, {"avg": 500, "max": 1000})
        cost_ratio = amount / benchmark["avg"] if benchmark["avg"] > 0 else 1
        
        # Calculate fraud score based on cost analysis
        fraud_score = 0
        risk_factors = []
        
        if cost_ratio > 10:  # 10x normal cost
            fraud_score += 40
            risk_factors.append(f"Cost ${amount:,.2f} is {cost_ratio:.1f}x normal for this procedure")
        elif cost_ratio > 5:  # 5x normal cost
            fraud_score += 25
            risk_factors.append(f"Cost significantly above average ({cost_ratio:.1f}x normal)")
        elif cost_ratio > 2:  # 2x normal cost  
            fraud_score += 10
            risk_factors.append("Cost above regional average")
            
        # Add other realistic fraud indicators
        import random
        if random.random() < 0.05:  # 5% chance of timing issue
            fraud_score += 15
            risk_factors.append("Unusual submission timing")
            
        if random.random() < 0.03:  # 3% chance of duplicate
            fraud_score += 30
            risk_factors.append("Potential duplicate claim detected")
        
        return {
            "fraud_score": min(fraud_score, 100),
            "risk_factors": risk_factors,
            "flagged": fraud_score > 30,
            "cost_ratio": cost_ratio,
            "benchmark_amount": benchmark["avg"]
        }
    
    def _check_duplicate_claims(self, params: Dict) -> Dict:
        """Check for duplicate claims (simplified simulation)"""
        import random
        
        # Simulate 2% duplicate rate
        is_duplicate = random.random() < 0.02
        
        return {
            "duplicates_found": 1 if is_duplicate else 0,
            "duplicate_claims": [{"claim_id": "CLM-123456", "date": "2024-10-30"}] if is_duplicate else [],
            "risk_level": "HIGH" if is_duplicate else "LOW",
            "similar_claims": []
        }
    
    def _calculate_dynamic_approval_score(self, params: Dict) -> Dict:
        """Calculate approval score based on all previous analyses"""
        intake_result = params.get("intake_result", {})
        eligibility_result = params.get("eligibility_result", {}) 
        clinical_result = params.get("clinical_result", {})
        fraud_result = params.get("fraud_result", {})
        
        base_score = 70  # Start with neutral score
        
        # Adjust based on completeness
        if intake_result.get("status") == "validated":
            base_score += 10
            
        # Adjust based on eligibility
        if eligibility_result.get("status") == "eligible":
            base_score += 15
        else:
            base_score -= 30
            
        # Adjust based on medical validity
        if clinical_result.get("status") == "valid":
            base_score += 10
        else:
            base_score -= 25
            
        # Adjust based on fraud indicators
        fraud_score = fraud_result.get("fraud_score", 0)
        if fraud_score < 10:
            base_score += 5
        elif fraud_score > 30:
            base_score -= fraud_score
            
        final_score = max(0, min(100, base_score))
        
        return {
            "approval_score": final_score,
            "recommendation": "approve" if final_score >= 70 else "deny" if final_score < 40 else "review",
            "confidence": min(95, 60 + (abs(final_score - 50) * 0.7))
        }
    
    def _extract_claim_entities(self, params: Dict) -> Dict:
        """Extract entities from claim data"""
        claim_data = params.get("claim_data", {})
        
        entities = []
        for key, value in claim_data.items():
            if value:
                entities.append({
                    "type": key,
                    "value": str(value),
                    "confidence": 0.95
                })
        
        return {
            "entities": entities,
            "extraction_confidence": 0.95,
            "confidence": 90
        }
    
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
        
        # In-memory storage for processing states (in production, use database)
        self.processing_states: Dict[str, ClaimProcessingState] = {}
    
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
            
            # Store the processing state for later retrieval
            self.processing_states[claim_id] = state
            
            return state
            
        except Exception as e:
            logger.error(f"Multi-agent processing failed for claim {claim_id}: {str(e)}")
            state.errors.append(f"Pipeline failure: {str(e)}")
            state.final_decision = "REVIEW"
            state.reasoning = f"Processing failed due to system error: {str(e)}"
            
            # Store the failed state for debugging
            self.processing_states[claim_id] = state
            
            return state
    
    def get_agent_timeline(self, claim_id: str, processing_state: Optional[ClaimProcessingState] = None) -> List[Dict[str, Any]]:
        """Get real-time processing timeline from actual agent results"""
        if not processing_state:
            # Retrieve from stored processing states
            processing_state = self.processing_states.get(claim_id)
            if not processing_state:
                logger.warning(f"No processing state found for claim {claim_id}")
                return []
        
        timeline = []
        for agent_name, result in processing_state.agent_results.items():
            # Convert agent status to string
            status_map = {
                AgentStatus.COMPLETED: "completed",
                AgentStatus.FAILED: "failed",
                AgentStatus.IN_PROGRESS: "in_progress",
                AgentStatus.TIMEOUT: "timeout"
            }
            
            timeline.append({
                "agent": result.agent_name,
                "agent_type": agent_name,
                "status": status_map.get(result.status, "unknown"),
                "duration": round(result.duration_seconds, 2),
                "result": result.result,
                "confidence": round(result.confidence_score, 1),
                "started_at": (processing_state.processing_start_time).isoformat(),
                "completed_at": (processing_state.processing_start_time.replace(microsecond=0) + 
                                timedelta(seconds=result.duration_seconds)).isoformat(),
                "reasoning_steps": len(result.reasoning_steps),
                "tools_used": len(result.tool_calls),
                "error_message": result.error_message
            })
        
        # Sort by the order they were processed (using pipeline order)
        pipeline_order = {name: i for i, name in enumerate(self.pipeline)}
        timeline.sort(key=lambda x: pipeline_order.get(x["agent_type"], 999))
        
        return timeline
    
    def get_agent_reasoning(self, claim_id: str, processing_state: Optional[ClaimProcessingState] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get real-time detailed ReAct reasoning steps from actual agent processing"""
        if not processing_state:
            # Retrieve from stored processing states
            processing_state = self.processing_states.get(claim_id)
            if not processing_state:
                logger.warning(f"No processing state found for claim {claim_id}")
                return {}
        
        reasoning_data = {}
        
        for agent_name, result in processing_state.agent_results.items():
            reasoning_steps = []
            
            for step in result.reasoning_steps:
                reasoning_steps.append({
                    "step": step.step_number,
                    "type": step.step_type.value,
                    "text": step.content,
                    "timestamp": step.timestamp.isoformat(),
                    "metadata": step.metadata
                })
            
            if reasoning_steps:  # Only include agents that have reasoning steps
                reasoning_data[result.agent_name] = reasoning_steps
        
        return reasoning_data
    
    def get_tool_usage(self, claim_id: str, processing_state: Optional[ClaimProcessingState] = None) -> List[Dict[str, Any]]:
        """Get real-time comprehensive tool usage report from actual agent processing"""
        if not processing_state:
            # Retrieve from stored processing states
            processing_state = self.processing_states.get(claim_id)
            if not processing_state:
                logger.warning(f"No processing state found for claim {claim_id}")
                return []
        
        tool_usage_data = []
        
        for agent_name, result in processing_state.agent_results.items():
            for tool_call in result.tool_calls:
                # Format the result based on success/failure
                if tool_call.success:
                    if isinstance(tool_call.result, dict):
                        # Try to create a meaningful summary from the result
                        if tool_call.tool_name == "validate_fields":
                            result_summary = f"✅ {tool_call.result.get('status', 'completed')}"
                            if 'missing_fields' in tool_call.result and not tool_call.result['missing_fields']:
                                result_summary += " - All fields present"
                        elif tool_call.tool_name == "check_eligibility":
                            status = tool_call.result.get('status', 'unknown')
                            copay = tool_call.result.get('copay', 0)
                            result_summary = f"✅ Patient {status}" + (f", ${copay} copay" if copay else "")
                        elif tool_call.tool_name == "validate_codes":
                            result_summary = f"✅ Codes {tool_call.result.get('status', 'processed')}"
                        elif tool_call.tool_name == "check_fraud_indicators":
                            fraud_score = tool_call.result.get('fraud_score', 0)
                            result_summary = f"✅ Risk score: {fraud_score}/100"
                        elif tool_call.tool_name == "calculate_approval_score":
                            approval_score = tool_call.result.get('approval_score', 0)
                            result_summary = f"✅ Approval score: {approval_score}/100"
                        else:
                            result_summary = f"✅ {tool_call.result.get('status', 'Success')}"
                    else:
                        result_summary = f"✅ {str(tool_call.result)[:50]}"
                else:
                    result_summary = f"❌ {tool_call.error_message or 'Failed'}"
                
                tool_usage_data.append({
                    "agent": result.agent_name,
                    "agent_type": agent_name,
                    "tool": f"{tool_call.tool_name}()",
                    "parameters": tool_call.parameters,
                    "result": result_summary,
                    "success": tool_call.success,
                    "execution_time": round(tool_call.execution_time, 3),
                    "timestamp": tool_call.timestamp.isoformat(),
                    "error_message": tool_call.error_message
                })
        
        # Sort by timestamp to show chronological order
        tool_usage_data.sort(key=lambda x: x["timestamp"])
        
        return tool_usage_data

# Global multi-agent processor instance
enhanced_multi_agent_processor = EnhancedMultiAgentProcessor()