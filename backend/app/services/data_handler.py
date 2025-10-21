import json
import os
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from app.models import Claim, DecisionLog, ExceptionLog, ClaimStatus, DashboardMetrics


class DataHandler:
    def __init__(self, data_dir: str = "../../data"):
        self.data_dir = Path(data_dir).resolve()
        self.claims_file = self.data_dir / "claims.json"
        self.decisions_file = self.data_dir / "decisions.json"
        self.exceptions_file = self.data_dir / "exceptions.json"
        self.history_file = self.data_dir / "claim_history.json"
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Create empty JSON files if they don't exist"""
        for file_path in [self.claims_file, self.decisions_file, self.exceptions_file, self.history_file]:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    def _read_json_file(self, file_path: Path) -> List[dict]:
        """Read JSON file and return list of dictionaries"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _write_json_file(self, file_path: Path, data: List[dict]):
        """Write list of dictionaries to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    # Claims CRUD operations
    def save_claim(self, claim: Claim) -> Claim:
        """Save a new claim or update existing one"""
        claims = self._read_json_file(self.claims_file)
        claim_dict = claim.model_dump()
        
        # Convert datetime objects to ISO format strings
        if isinstance(claim_dict.get('created_at'), datetime):
            claim_dict['created_at'] = claim.created_at.isoformat()
        if claim.processed_at and isinstance(claim_dict.get('processed_at'), datetime):
            claim_dict['processed_at'] = claim.processed_at.isoformat()
        
        # Check if claim exists, update or append
        existing_index = None
        for i, existing_claim in enumerate(claims):
            if existing_claim['claim_id'] == claim.claim_id:
                existing_index = i
                break
        
        if existing_index is not None:
            claims[existing_index] = claim_dict
        else:
            claims.append(claim_dict)
        
        self._write_json_file(self.claims_file, claims)
        return claim
    
    def get_claim_by_id(self, claim_id: str) -> Optional[Claim]:
        """Get claim by ID"""
        claims = self._read_json_file(self.claims_file)
        for claim_data in claims:
            if claim_data['claim_id'] == claim_id:
                # Convert ISO strings back to datetime
                if 'created_at' in claim_data and isinstance(claim_data['created_at'], str):
                    claim_data['created_at'] = datetime.fromisoformat(claim_data['created_at'])
                if 'processed_at' in claim_data and claim_data['processed_at'] and isinstance(claim_data['processed_at'], str):
                    claim_data['processed_at'] = datetime.fromisoformat(claim_data['processed_at'])
                return Claim(**claim_data)
        return None
    
    def get_all_claims(self, status_filter: Optional[ClaimStatus] = None) -> List[Claim]:
        """Get all claims, optionally filtered by status"""
        claims_data = self._read_json_file(self.claims_file)
        claims = []
        
        for claim_data in claims_data:
            # Convert ISO strings back to datetime
            if 'created_at' in claim_data and isinstance(claim_data['created_at'], str):
                claim_data['created_at'] = datetime.fromisoformat(claim_data['created_at'])
            if 'processed_at' in claim_data and claim_data['processed_at'] and isinstance(claim_data['processed_at'], str):
                claim_data['processed_at'] = datetime.fromisoformat(claim_data['processed_at'])
            
            claim = Claim(**claim_data)
            if status_filter is None or claim.status == status_filter:
                claims.append(claim)
        
        return sorted(claims, key=lambda x: x.created_at, reverse=True)
    
    # Decision logs
    def save_decision_log(self, decision_log: DecisionLog) -> DecisionLog:
        """Save a decision log"""
        decisions = self._read_json_file(self.decisions_file)
        decision_dict = decision_log.model_dump()
        
        if isinstance(decision_dict.get('created_at'), datetime):
            decision_dict['created_at'] = decision_log.created_at.isoformat()
        
        decisions.append(decision_dict)
        self._write_json_file(self.decisions_file, decisions)
        return decision_log
    
    def get_decision_by_claim_id(self, claim_id: str) -> Optional[DecisionLog]:
        """Get decision log for a specific claim"""
        decisions = self._read_json_file(self.decisions_file)
        for decision_data in decisions:
            if decision_data['claim_id'] == claim_id:
                if 'created_at' in decision_data and isinstance(decision_data['created_at'], str):
                    decision_data['created_at'] = datetime.fromisoformat(decision_data['created_at'])
                return DecisionLog(**decision_data)
        return None
    
    # Exception logs
    def save_exception_log(self, exception_log: ExceptionLog) -> ExceptionLog:
        """Save an exception log"""
        exceptions = self._read_json_file(self.exceptions_file)
        exception_dict = exception_log.model_dump()
        
        if isinstance(exception_dict.get('created_at'), datetime):
            exception_dict['created_at'] = exception_log.created_at.isoformat()
        
        exceptions.append(exception_dict)
        self._write_json_file(self.exceptions_file, exceptions)
        return exception_log
    
    def get_exceptions_by_claim_id(self, claim_id: str) -> List[ExceptionLog]:
        """Get all exception logs for a specific claim"""
        exceptions = self._read_json_file(self.exceptions_file)
        claim_exceptions = []
        
        for exception_data in exceptions:
            if exception_data['claim_id'] == claim_id:
                if 'created_at' in exception_data and isinstance(exception_data['created_at'], str):
                    exception_data['created_at'] = datetime.fromisoformat(exception_data['created_at'])
                claim_exceptions.append(ExceptionLog(**exception_data))
        
        return sorted(claim_exceptions, key=lambda x: x.created_at)
    
    def find_similar_exceptions(self, exception_type: str) -> List[ExceptionLog]:
        """Find previous exceptions of the same type for learning"""
        exceptions = self._read_json_file(self.exceptions_file)
        similar_exceptions = []
        
        for exception_data in exceptions:
            if exception_data['exception_type'] == exception_type:
                if 'created_at' in exception_data and isinstance(exception_data['created_at'], str):
                    exception_data['created_at'] = datetime.fromisoformat(exception_data['created_at'])
                similar_exceptions.append(ExceptionLog(**exception_data))
        
        return sorted(similar_exceptions, key=lambda x: x.created_at, reverse=True)
    
    # Dashboard metrics
    def get_dashboard_metrics(self) -> DashboardMetrics:
        """Calculate and return dashboard metrics"""
        claims = self.get_all_claims()
        total_claims = len(claims)
        
        if total_claims == 0:
            return DashboardMetrics(
                total_claims=0,
                approved_count=0,
                denied_count=0,
                pending_review_count=0,
                fraud_flagged_count=0,
                approval_rate=0.0,
                avg_processing_time_seconds=0.0
            )
        
        approved_count = len([c for c in claims if c.status == ClaimStatus.APPROVED])
        denied_count = len([c for c in claims if c.status == ClaimStatus.DENIED])
        pending_review_count = len([c for c in claims if c.status == ClaimStatus.PENDING_REVIEW])
        fraud_flagged_count = len([c for c in claims if c.status == ClaimStatus.FRAUD_FLAGGED])
        
        approval_rate = (approved_count / total_claims) * 100 if total_claims > 0 else 0.0
        
        # Calculate average processing time for processed claims
        processed_claims = [c for c in claims if c.processed_at]
        if processed_claims:
            processing_times = [(c.processed_at - c.created_at).total_seconds() for c in processed_claims]
            avg_processing_time = sum(processing_times) / len(processing_times)
        else:
            avg_processing_time = 0.0
        
        return DashboardMetrics(
            total_claims=total_claims,
            approved_count=approved_count,
            denied_count=denied_count,
            pending_review_count=pending_review_count,
            fraud_flagged_count=fraud_flagged_count,
            approval_rate=approval_rate,
            avg_processing_time_seconds=avg_processing_time
        )