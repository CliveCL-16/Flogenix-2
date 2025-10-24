import re
from datetime import date, datetime, timedelta
from typing import List, Tuple

from app.models import Claim


class ValidationService:
    """Handles claim data validation"""
    
    # Common ICD-10 codes for demo
    VALID_ICD10_CODES = {
        # Regular checkups and conditions
        "Z00.00": "Encounter for general adult medical examination without abnormal findings",
        "S52.501A": "Unspecified fracture of the lower end of right radius, initial encounter",
        "M25.511": "Pain in right shoulder",
        "E11.9": "Type 2 diabetes mellitus without complications",
        "J06.9": "Acute upper respiratory infection, unspecified",
        "K21.9": "Gastro-esophageal reflux disease without esophagitis",
        "M79.3": "Panniculitis, unspecified",
        "I10": "Essential hypertension",
        
        # Complex conditions requiring review
        "C50.1": "Malignant neoplasm of central portion of breast",
        "C50.2": "Malignant neoplasm of upper-inner quadrant of breast",
        "I21.0": "ST elevation (STEMI) myocardial infarction of anterior wall",
        "I63.1": "Cerebral infarction due to embolism of precerebral arteries",
        "I63.2": "Cerebral infarction due to unspecified occlusion of cerebral arteries"
    }
    
    # Common CPT codes for demo
    VALID_CPT_CODES = {
        "99213": "Office visit, established patient, low complexity",
        "99214": "Office visit, established patient, moderate complexity",
        "99215": "Office visit, established patient, high complexity",
        "92004": "Ophthalmological examination and evaluation",
        "27447": "Arthroplasty, knee, condyle and plateau; medial or lateral compartment",
        "73721": "MRI lower extremity other than joint",
        "36415": "Collection of venous blood by venipuncture",
        "85025": "Blood count; complete (CBC), automated"
    }
    
    # Procedure-diagnosis compatibility
    COMPATIBLE_PROCEDURES = {
        # Regular procedures
        "Z00.00": ["99213", "99214", "99215"],  # General exam -> office visits
        "S52.501A": ["27447", "73721"],  # Fracture -> orthopedic procedures
        "M25.511": ["99213", "99214", "73721"],  # Shoulder pain -> visits/imaging
        "E11.9": ["99213", "99214", "85025"],  # Diabetes -> visits/lab work
        "J06.9": ["99213", "99214"],  # Respiratory infection -> office visits
        "K21.9": ["99213", "99214"],  # GERD -> office visits
        "M79.3": ["99213", "99214"],  # Panniculitis -> office visits
        "I10": ["99213", "99214", "85025"],  # Hypertension -> visits/lab work
        
        # Complex conditions
        "C50.1": ["99215", "27447", "73721"],  # Breast cancer -> complex visits and procedures
        "C50.2": ["99215", "27447", "73721"],  # Breast cancer -> complex visits and procedures
        "I21.0": ["99215", "27447", "85025"],  # Heart attack -> complex visits and cardiac care
        "I63.1": ["99215", "73721", "85025"],  # Stroke -> complex visits and imaging
        "I63.2": ["99215", "73721", "85025"]   # Stroke -> complex visits and imaging
    }
    
    @classmethod
    def validate_claim_data(cls, claim: Claim) -> Tuple[bool, List[str]]:
        """Validate claim data and return (is_valid, error_messages)"""
        errors = []
        
        # Validate patient information
        if not cls._validate_patient_name(claim.patient_name):
            errors.append("Patient name contains invalid characters")
        
        if not cls._validate_patient_id(claim.patient_id):
            errors.append("Patient ID format is invalid")
        
        # Validate insurance information
        if not claim.insurance_provider.strip():
            errors.append("Insurance provider is required")
        
        if not cls._validate_policy_number(claim.policy_number):
            errors.append("Policy number format is invalid")
        
        # Validate medical codes
        if not cls._validate_icd10_code(claim.diagnosis_code):
            errors.append(f"Invalid ICD-10 diagnosis code: {claim.diagnosis_code}")
        
        if not cls._validate_cpt_code(claim.procedure_code):
            errors.append(f"Invalid CPT procedure code: {claim.procedure_code}")
        
        # Validate procedure-diagnosis compatibility
        if not cls._validate_procedure_diagnosis_match(claim.diagnosis_code, claim.procedure_code):
            errors.append(f"Procedure code {claim.procedure_code} is not compatible with diagnosis {claim.diagnosis_code}")
        
        # Validate claim amount
        if claim.claim_amount <= 0:
            errors.append("Claim amount must be greater than zero")
        elif claim.claim_amount > 100000:  # Reasonable upper limit
            errors.append("Claim amount exceeds maximum limit ($100,000)")
        
        # Validate service date
        if not cls._validate_service_date(claim.service_date):
            errors.append("Service date is invalid (cannot be in the future or more than 1 year old)")
        
        # Validate provider information
        if not claim.provider_name.strip():
            errors.append("Provider name is required")
        
        if claim.provider_npi and not cls._validate_npi(claim.provider_npi):
            errors.append("NPI format is invalid (must be 10 digits)")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_patient_name(name: str) -> bool:
        """Validate patient name format"""
        if not name or len(name.strip()) < 2:
            return False
        # Allow letters, spaces, hyphens, apostrophes
        pattern = r"^[A-Za-z\s\-'\.]+$"
        return bool(re.match(pattern, name.strip()))
    
    @staticmethod
    def _validate_patient_id(patient_id: str) -> bool:
        """Validate patient ID format"""
        if not patient_id or len(patient_id.strip()) < 3:
            return False
        # Allow alphanumeric characters and hyphens
        pattern = r"^[A-Za-z0-9\-]+$"
        return bool(re.match(pattern, patient_id.strip()))
    
    @staticmethod
    def _validate_policy_number(policy_number: str) -> bool:
        """Validate insurance policy number format"""
        if not policy_number or len(policy_number.strip()) < 5:
            return False
        # Allow alphanumeric characters and hyphens
        pattern = r"^[A-Za-z0-9\-]+$"
        return bool(re.match(pattern, policy_number.strip()))
    
    @classmethod
    def _validate_icd10_code(cls, code: str) -> bool:
        """Validate ICD-10 diagnosis code"""
        if not code:
            return False
        # For MVP, check against our predefined list
        return code.strip() in cls.VALID_ICD10_CODES
    
    @classmethod
    def _validate_cpt_code(cls, code: str) -> bool:
        """Validate CPT procedure code"""
        if not code:
            return False
        # For MVP, check against our predefined list
        return code.strip() in cls.VALID_CPT_CODES
    
    @classmethod
    def _validate_procedure_diagnosis_match(cls, diagnosis_code: str, procedure_code: str) -> bool:
        """Check if procedure code is compatible with diagnosis code"""
        if diagnosis_code not in cls.COMPATIBLE_PROCEDURES:
            return False
        return procedure_code in cls.COMPATIBLE_PROCEDURES[diagnosis_code]
    
    @staticmethod
    def _validate_service_date(service_date: date) -> bool:
        """Validate service date"""
        today = date.today()
        one_year_ago = today - timedelta(days=365)
        
        # Service date cannot be in the future or more than 1 year old
        return one_year_ago <= service_date <= today
    
    @staticmethod
    def _validate_npi(npi: str) -> bool:
        """Validate National Provider Identifier"""
        if not npi:
            return True  # NPI is optional
        # NPI must be exactly 10 digits
        pattern = r"^\d{10}$"
        return bool(re.match(pattern, npi.strip()))
    
    @classmethod
    def get_code_description(cls, code: str, code_type: str) -> str:
        """Get description for a medical code"""
        if code_type.lower() == "icd10":
            return cls.VALID_ICD10_CODES.get(code, "Unknown diagnosis code")
        elif code_type.lower() == "cpt":
            return cls.VALID_CPT_CODES.get(code, "Unknown procedure code")
        return "Unknown code"