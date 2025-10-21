from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from app.models import Claim, ExceptionLog
from app.services.data_handler import DataHandler
from app.services.validation import ValidationService


class ExceptionType(str, Enum):
    MISSING_REFERRAL = "MISSING_REFERRAL"
    CODE_MISMATCH = "CODE_MISMATCH"
    MISSING_AUTHORIZATION = "MISSING_AUTHORIZATION"
    INVALID_PROVIDER = "INVALID_PROVIDER"
    COVERAGE_EXPIRED = "COVERAGE_EXPIRED"
    DUPLICATE_CLAIM = "DUPLICATE_CLAIM"
    AMOUNT_LIMIT_EXCEEDED = "AMOUNT_LIMIT_EXCEEDED"
    UNSUPPORTED_PROCEDURE = "UNSUPPORTED_PROCEDURE"


class ExceptionHandlingService:
    """Handles exception detection and learning-based resolution"""
    
    def __init__(self, data_handler: DataHandler):
        self.data_handler = data_handler
        
        # Exception detection rules
        self.exception_rules = {
            ExceptionType.MISSING_REFERRAL: self._check_missing_referral,
            ExceptionType.CODE_MISMATCH: self._check_code_mismatch,
            ExceptionType.MISSING_AUTHORIZATION: self._check_missing_authorization,
            ExceptionType.INVALID_PROVIDER: self._check_invalid_provider,
            ExceptionType.AMOUNT_LIMIT_EXCEEDED: self._check_amount_limit,
            ExceptionType.UNSUPPORTED_PROCEDURE: self._check_unsupported_procedure
        }
        
        # Procedures that typically require referrals
        self.referral_required_procedures = [
            "27447",  # Knee arthroplasty
            "73721",  # MRI lower extremity
            "92004"   # Ophthalmological examination
        ]
        
        # Procedures that require prior authorization
        self.authorization_required_procedures = [
            "27447",  # Knee arthroplasty
            "73721"   # MRI lower extremity
        ]
    
    def detect_exceptions(self, claim: Claim) -> List[Dict[str, Any]]:
        """Detect all exceptions for a given claim"""
        exceptions = []
        
        for exception_type, check_function in self.exception_rules.items():
            exception_data = check_function(claim)
            if exception_data:
                exceptions.append({
                    "type": exception_type,
                    "details": exception_data,
                    "claim_id": claim.claim_id
                })
        
        return exceptions
    
    def handle_exception(self, claim: Claim, exception_type: str, exception_details: str) -> Dict[str, Any]:
        """Handle an exception using learning from past cases"""
        
        # Look for similar past exceptions
        similar_exceptions = self.data_handler.find_similar_exceptions(exception_type)
        
        if similar_exceptions:
            # Learning behavior - use resolution from most recent similar case
            latest_exception = similar_exceptions[0]  # Most recent first
            
            # Apply learned resolution
            resolution_action = latest_exception.resolution_action
            
            # Log the exception with reference to learned case
            exception_log = ExceptionLog(
                claim_id=claim.claim_id,
                exception_type=exception_type,
                resolution_action=resolution_action,
                learned_from_case_id=latest_exception.claim_id,
                created_at=datetime.now()
            )
            
            self.data_handler.save_exception_log(exception_log)
            
            return {
                "resolution": "auto_resolved",
                "action": resolution_action,
                "learned_from": latest_exception.claim_id,
                "message": f"Learned from Case #{latest_exception.claim_id}: {resolution_action}",
                "confidence": "high"
            }
        
        else:
            # First occurrence - escalate to human review and prepare for learning
            resolution_action = self._generate_initial_resolution(exception_type, exception_details)
            
            # Log the exception for future learning
            exception_log = ExceptionLog(
                claim_id=claim.claim_id,
                exception_type=exception_type,
                resolution_action=resolution_action,
                learned_from_case_id=None,
                created_at=datetime.now()
            )
            
            self.data_handler.save_exception_log(exception_log)
            
            return {
                "resolution": "escalated",
                "action": resolution_action,
                "learned_from": None,
                "message": f"New exception type detected. Escalated for human review: {resolution_action}",
                "confidence": "medium"
            }
    
    def _generate_initial_resolution(self, exception_type: str, exception_details: str) -> str:
        """Generate initial resolution for new exception types"""
        
        resolution_templates = {
            ExceptionType.MISSING_REFERRAL: "Request referral documentation from provider",
            ExceptionType.CODE_MISMATCH: "Review diagnosis and procedure codes for accuracy",
            ExceptionType.MISSING_AUTHORIZATION: "Obtain prior authorization before processing",
            ExceptionType.INVALID_PROVIDER: "Verify provider credentials and network status",
            ExceptionType.AMOUNT_LIMIT_EXCEEDED: "Review policy limits and justify amount",
            ExceptionType.UNSUPPORTED_PROCEDURE: "Verify procedure coverage under current policy"
        }
        
        return resolution_templates.get(exception_type, "Escalate to senior claims adjudicator")
    
    # Exception detection methods
    def _check_missing_referral(self, claim: Claim) -> Optional[str]:
        """Check if referral is required but missing"""
        if claim.procedure_code in self.referral_required_procedures:
            # In real system, would check for referral document
            # For demo, simulate missing referral for specific scenarios
            if "specialist" in claim.notes.lower() if claim.notes else False:
                return f"Referral required for procedure {claim.procedure_code} but not provided"
        return None
    
    def _check_code_mismatch(self, claim: Claim) -> Optional[str]:
        """Check for diagnosis-procedure code mismatches"""
        if not ValidationService._validate_procedure_diagnosis_match(claim.diagnosis_code, claim.procedure_code):
            return f"Procedure {claim.procedure_code} does not match diagnosis {claim.diagnosis_code}"
        return None
    
    def _check_missing_authorization(self, claim: Claim) -> Optional[str]:
        """Check if prior authorization is required but missing"""
        if claim.procedure_code in self.authorization_required_procedures:
            # In real system, would check authorization database
            # For demo, simulate missing authorization for high-value procedures
            if claim.claim_amount > 10000:
                return f"Prior authorization required for procedure {claim.procedure_code} over $10,000"
        return None
    
    def _check_invalid_provider(self, claim: Claim) -> Optional[str]:
        """Check for invalid provider information"""
        # Simple validation - in real system would check provider database
        if not claim.provider_npi:
            return "NPI number missing for provider verification"
        
        if len(claim.provider_npi) != 10:
            return f"Invalid NPI format: {claim.provider_npi}"
        
        return None
    
    def _check_amount_limit(self, claim: Claim) -> Optional[str]:
        """Check if claim amount exceeds policy limits"""
        # Policy limits by procedure type (simplified for demo)
        procedure_limits = {
            "99213": 500,    # Office visit limit
            "99214": 800,    # Office visit limit
            "99215": 1200,   # Office visit limit
            "27447": 25000,  # Surgery limit
            "73721": 2000,   # Imaging limit
            "92004": 500     # Eye exam limit
        }
        
        limit = procedure_limits.get(claim.procedure_code, 50000)  # Default limit
        
        if claim.claim_amount > limit:
            return f"Claim amount ${claim.claim_amount:,.2f} exceeds policy limit ${limit:,.2f} for procedure {claim.procedure_code}"
        
        return None
    
    def _check_unsupported_procedure(self, claim: Claim) -> Optional[str]:
        """Check for unsupported procedures"""
        # For demo, all procedures in validation service are supported
        if claim.procedure_code not in ValidationService.VALID_CPT_CODES:
            return f"Procedure code {claim.procedure_code} is not covered under current policy"
        
        return None
    
    def get_exception_statistics(self) -> Dict[str, Any]:
        """Get statistics about exceptions and learning"""
        all_exceptions = []
        
        # Read all exception logs
        for file_data in self.data_handler._read_json_file(self.data_handler.exceptions_file):
            all_exceptions.append(file_data)
        
        if not all_exceptions:
            return {
                "total_exceptions": 0,
                "learned_resolutions": 0,
                "exception_types": {},
                "learning_rate": 0.0
            }
        
        total_exceptions = len(all_exceptions)
        learned_resolutions = len([e for e in all_exceptions if e.get("learned_from_case_id")])
        
        # Count by exception type
        exception_types = {}
        for exception in all_exceptions:
            exc_type = exception.get("exception_type", "unknown")
            exception_types[exc_type] = exception_types.get(exc_type, 0) + 1
        
        learning_rate = (learned_resolutions / total_exceptions * 100) if total_exceptions > 0 else 0.0
        
        return {
            "total_exceptions": total_exceptions,
            "learned_resolutions": learned_resolutions,
            "exception_types": exception_types,
            "learning_rate": learning_rate
        }