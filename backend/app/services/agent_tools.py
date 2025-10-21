"""
LangChain tools for Flowgenix agents
Each tool represents a specific capability that agents can use
"""

from langchain.tools import tool
from typing import Dict, Any, List
from datetime import datetime
import json

from app.services.data_handler import DataHandler
from app.services.validation import ValidationService
from app.services.fraud_detection import FraudDetectionService
from app.models import Claim, ClaimState


# Initialize services
data_handler = DataHandler()
fraud_service = FraudDetectionService(data_handler)


@tool
def validate_required_fields(claim_data: Dict[str, Any]) -> str:
    """Validate that all required fields are present and properly formatted"""
    try:
        # Check required fields
        required_fields = [
            'patient_name', 'patient_id', 'insurance_provider', 
            'policy_number', 'diagnosis_code', 'procedure_code',
            'claim_amount', 'service_date', 'provider_name'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in claim_data or not claim_data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            return f"INVALID: Missing required fields: {', '.join(missing_fields)}"
        
        # Basic format validation
        if claim_data['claim_amount'] <= 0:
            return "INVALID: Claim amount must be greater than zero"
        
        return "VALID: All required fields present and properly formatted"
        
    except Exception as e:
        return f"ERROR: Validation failed - {str(e)}"


@tool
def extract_entities(claim_data: Dict[str, Any]) -> str:
    """Extract and count key entities from claim data"""
    try:
        entities = {
            'patient_info': ['patient_name', 'patient_id'],
            'insurance_info': ['insurance_provider', 'policy_number'],
            'medical_info': ['diagnosis_code', 'procedure_code', 'service_date'],
            'provider_info': ['provider_name', 'provider_npi'],
            'financial_info': ['claim_amount']
        }
        
        extracted = {}
        total_entities = 0
        
        for category, fields in entities.items():
            category_count = 0
            for field in fields:
                if field in claim_data and claim_data[field]:
                    category_count += 1
                    total_entities += 1
            extracted[category] = category_count
        
        return f"EXTRACTED: {total_entities} entities across {len(extracted)} categories: {extracted}"
        
    except Exception as e:
        return f"ERROR: Entity extraction failed - {str(e)}"


@tool
def call_eligibility_api(policy_number: str, insurance_provider: str) -> str:
    """Mock insurance eligibility API call to verify coverage"""
    try:
        # Mock API response based on policy patterns
        if policy_number.startswith("POL-"):
            # Simulate different coverage scenarios
            if "12345" in policy_number:
                return "ELIGIBLE: Coverage active, $20 copay, $500 deductible remaining, expires 2025-12-31"
            elif "67890" in policy_number:
                return "ELIGIBLE: Coverage active, $0 copay, $1000 deductible remaining, expires 2025-11-30"
            elif "99999" in policy_number:
                return "INELIGIBLE: Coverage expired on 2025-09-30"
            else:
                return "ELIGIBLE: Coverage active, $15 copay, $200 deductible remaining, expires 2025-12-31"
        else:
            return "ERROR: Invalid policy number format"
            
    except Exception as e:
        return f"ERROR: Eligibility check failed - {str(e)}"


@tool
def lookup_icd10_code(diagnosis_code: str) -> str:
    """Look up ICD-10 diagnosis code for validation"""
    try:
        description = ValidationService.get_code_description(diagnosis_code, "icd10")
        
        if description == "Unknown diagnosis code":
            return f"INVALID: ICD-10 code {diagnosis_code} not found in database"
        else:
            return f"VALID: {diagnosis_code} - {description}"
            
    except Exception as e:
        return f"ERROR: ICD-10 lookup failed - {str(e)}"


@tool
def lookup_cpt_code(procedure_code: str) -> str:
    """Look up CPT procedure code for validation"""
    try:
        description = ValidationService.get_code_description(procedure_code, "cpt")
        
        if description == "Unknown procedure code":
            return f"INVALID: CPT code {procedure_code} not found in database"
        else:
            return f"VALID: {procedure_code} - {description}"
            
    except Exception as e:
        return f"ERROR: CPT lookup failed - {str(e)}"


@tool
def check_code_compatibility(diagnosis_code: str, procedure_code: str) -> str:
    """Check if diagnosis and procedure codes are compatible"""
    try:
        is_compatible = ValidationService._validate_procedure_diagnosis_match(
            diagnosis_code, procedure_code
        )
        
        if is_compatible:
            return f"COMPATIBLE: Procedure {procedure_code} is appropriate for diagnosis {diagnosis_code}"
        else:
            return f"INCOMPATIBLE: Procedure {procedure_code} does not match diagnosis {diagnosis_code}"
            
    except Exception as e:
        return f"ERROR: Compatibility check failed - {str(e)}"


@tool
def query_claims_database(patient_id: str, procedure_code: str = None, service_date: str = None) -> str:
    """Query historical claims database for patterns"""
    try:
        all_claims = data_handler.get_all_claims()
        
        # Filter by patient_id
        patient_claims = [c for c in all_claims if c.patient_id == patient_id]
        
        if not patient_claims:
            return f"NO_HISTORY: No previous claims found for patient {patient_id}"
        
        # Further filtering
        if procedure_code:
            procedure_claims = [c for c in patient_claims if c.procedure_code == procedure_code]
            if service_date:
                same_day_claims = [c for c in procedure_claims 
                                 if c.service_date.isoformat() == service_date]
                if same_day_claims:
                    claim_ids = [c.claim_id for c in same_day_claims]
                    return f"DUPLICATE_FOUND: Found identical claims on same date: {claim_ids}"
        
        # Summary of patient history
        total_claims = len(patient_claims)
        total_amount = sum(c.claim_amount for c in patient_claims)
        recent_claims = [c for c in patient_claims 
                        if (datetime.now() - c.created_at).days <= 30]
        
        return f"HISTORY_FOUND: Patient has {total_claims} previous claims, total amount ${total_amount:,.2f}, {len(recent_claims)} in last 30 days"
        
    except Exception as e:
        return f"ERROR: Database query failed - {str(e)}"


@tool
def calculate_fraud_score(claim_id: str) -> str:
    """Calculate fraud risk score for a claim"""
    try:
        claim = data_handler.get_claim_by_id(claim_id)
        if not claim:
            return "ERROR: Claim not found"
        
        fraud_analysis = fraud_service.analyze_fraud_risk(claim)
        
        risk_level = "LOW"
        if fraud_analysis.fraud_score > 70:
            risk_level = "HIGH"
        elif fraud_analysis.fraud_score > 30:
            risk_level = "MEDIUM"
        
        factors_summary = "; ".join(fraud_analysis.risk_factors[:3])  # Top 3 factors
        
        return f"FRAUD_SCORE: {fraud_analysis.fraud_score:.1f}/100 ({risk_level} risk). Key factors: {factors_summary}"
        
    except Exception as e:
        return f"ERROR: Fraud score calculation failed - {str(e)}"


@tool
def flag_for_investigation(claim_id: str, reason: str) -> str:
    """Flag a claim for fraud investigation"""
    try:
        # In a real system, this would update a fraud investigation queue
        timestamp = datetime.now().isoformat()
        return f"FLAGGED: Claim {claim_id} flagged for investigation at {timestamp}. Reason: {reason}"
        
    except Exception as e:
        return f"ERROR: Failed to flag claim - {str(e)}"


@tool
def request_human_review(claim_id: str, reason: str, urgency: str = "normal") -> str:
    """Request human review for complex cases"""
    try:
        timestamp = datetime.now().isoformat()
        return f"ESCALATED: Claim {claim_id} escalated to human review at {timestamp}. Reason: {reason}. Urgency: {urgency}"
        
    except Exception as e:
        return f"ERROR: Failed to request human review - {str(e)}"


@tool
def approve_claim(claim_id: str, amount: float, reason: str) -> str:
    """Approve a claim for payment"""
    try:
        timestamp = datetime.now().isoformat()
        return f"APPROVED: Claim {claim_id} approved for ${amount:,.2f} at {timestamp}. Reason: {reason}"
        
    except Exception as e:
        return f"ERROR: Failed to approve claim - {str(e)}"


@tool
def deny_claim(claim_id: str, reason: str) -> str:
    """Deny a claim"""
    try:
        timestamp = datetime.now().isoformat()
        return f"DENIED: Claim {claim_id} denied at {timestamp}. Reason: {reason}"
        
    except Exception as e:
        return f"ERROR: Failed to deny claim - {str(e)}"


@tool
def check_prior_authorization(procedure_code: str, diagnosis_code: str) -> str:
    """Check if procedure requires prior authorization"""
    try:
        # High-value procedures typically require authorization
        high_auth_procedures = ["27447", "73721"]  # Knee surgery, MRI
        
        if procedure_code in high_auth_procedures:
            return f"REQUIRED: Procedure {procedure_code} requires prior authorization for diagnosis {diagnosis_code}"
        else:
            return f"NOT_REQUIRED: Procedure {procedure_code} does not require prior authorization"
            
    except Exception as e:
        return f"ERROR: Authorization check failed - {str(e)}"


@tool
def verify_provider_credentials(provider_name: str, provider_npi: str) -> str:
    """Verify provider is credentialed and in-network"""
    try:
        if not provider_npi or len(provider_npi) != 10:
            return f"INVALID: Provider NPI format invalid or missing"
        
        # Mock verification - in real system would check provider database
        if provider_npi.startswith("123") or provider_npi.startswith("987"):
            return f"VERIFIED: Provider {provider_name} (NPI: {provider_npi}) is credentialed and in-network"
        elif provider_npi.startswith("555"):
            return f"OUT_OF_NETWORK: Provider {provider_name} (NPI: {provider_npi}) is out-of-network"
        else:
            return f"VERIFIED: Provider {provider_name} (NPI: {provider_npi}) is credentialed and in-network"
            
    except Exception as e:
        return f"ERROR: Provider verification failed - {str(e)}"


# Tool groups for different agents
INTAKE_TOOLS = [validate_required_fields, extract_entities]
ELIGIBILITY_TOOLS = [call_eligibility_api, verify_provider_credentials]
CLINICAL_TOOLS = [lookup_icd10_code, lookup_cpt_code, check_code_compatibility, check_prior_authorization]
FRAUD_TOOLS = [query_claims_database, calculate_fraud_score, flag_for_investigation]
ADJUDICATION_TOOLS = [approve_claim, deny_claim, request_human_review]

ALL_TOOLS = INTAKE_TOOLS + ELIGIBILITY_TOOLS + CLINICAL_TOOLS + FRAUD_TOOLS + ADJUDICATION_TOOLS