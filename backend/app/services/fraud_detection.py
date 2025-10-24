from datetime import datetime, timedelta
from typing import List, Dict, Any
import statistics

from app.models import Claim, FraudAnalysis
from app.services.data_handler import DataHandler


class FraudDetectionService:
    """Handles fraud detection and risk scoring"""
    
    def __init__(self, data_handler: DataHandler):
        self.data_handler = data_handler
        
        # Historical averages for common procedures (for demo)
        self.procedure_averages = {
            "99213": 150.0,   # Office visit, established patient, low complexity
            "99214": 250.0,   # Office visit, established patient, moderate complexity
            "99215": 350.0,   # Office visit, established patient, high complexity
            "92004": 200.0,   # Ophthalmological examination
            "27447": 15000.0, # Knee arthroplasty
            "73721": 800.0,   # MRI lower extremity
            "36415": 25.0,    # Blood collection
            "85025": 50.0     # Complete blood count
        }
    
    def analyze_fraud_risk(self, claim: Claim) -> FraudAnalysis:
        """Analyze claim for fraud risk and return analysis"""
        
        risk_factors = []
        fraud_score = 0.0
        analysis_details = {}
        
        # Check for duplicate claims
        duplicate_score, duplicate_factors = self._check_duplicates(claim)
        fraud_score += duplicate_score
        risk_factors.extend(duplicate_factors)
        analysis_details["duplicate_check"] = {
            "score": duplicate_score,
            "factors": duplicate_factors
        }
        
        # Check amount outliers
        amount_score, amount_factors = self._check_amount_outliers(claim)
        fraud_score += amount_score
        risk_factors.extend(amount_factors)
        analysis_details["amount_check"] = {
            "score": amount_score,
            "factors": amount_factors
        }
        
        # Check provider patterns
        provider_score, provider_factors = self._check_provider_patterns(claim)
        fraud_score += provider_score
        risk_factors.extend(provider_factors)
        analysis_details["provider_check"] = {
            "score": provider_score,
            "factors": provider_factors
        }
        
        # Check timing anomalies
        timing_score, timing_factors = self._check_timing_anomalies(claim)
        fraud_score += timing_score
        risk_factors.extend(timing_factors)
        analysis_details["timing_check"] = {
            "score": timing_score,
            "factors": timing_factors
        }
        
        # Normalize fraud score to 0-100
        fraud_score = min(100, max(0, fraud_score))
        
        return FraudAnalysis(
            claim_id=claim.claim_id,
            fraud_score=fraud_score,
            risk_factors=risk_factors,
            is_flagged=fraud_score > 70,
            analysis_details=analysis_details
        )
    
    def _check_duplicates(self, claim: Claim) -> tuple[float, List[str]]:
        """Check for duplicate claims"""
        score = 0.0
        factors = []
        
        # Get all existing claims
        all_claims = self.data_handler.get_all_claims()
        
        for existing_claim in all_claims:
            if existing_claim.claim_id == claim.claim_id:
                continue  # Skip self
            
            # Check for exact duplicates
            if (existing_claim.patient_id == claim.patient_id and
                existing_claim.service_date == claim.service_date):
                
                score += 50  # Higher score for same patient and date
                factors.append(f"Duplicate claim detected - same patient and date as claim {existing_claim.claim_id}")
                
                # Additional score if procedure is also the same
                if existing_claim.procedure_code == claim.procedure_code:
                    score += 30  # Total 80 points for exact duplicate
                    factors.append("Same procedure code in duplicate claim - highly suspicious")
            
            # Check for same patient, same day, different procedures (suspicious)
            elif (existing_claim.patient_id == claim.patient_id and
                  existing_claim.service_date == claim.service_date and
                  existing_claim.procedure_code != claim.procedure_code):
                
                score += 15  # Moderate score for multiple procedures same day
                factors.append(f"Multiple procedures same day as claim {existing_claim.claim_id}")
        
        return score, factors
    
    def _check_amount_outliers(self, claim: Claim) -> tuple[float, List[str]]:
        """Check for amount outliers compared to historical averages"""
        score = 0.0
        factors = []
        
        # Get expected amount for this procedure
        expected_amount = self.procedure_averages.get(claim.procedure_code)
        
        if expected_amount:
            ratio = claim.claim_amount / expected_amount
            
            # Flag if amount is significantly higher than average
            if ratio > 2.0:  # More than 200% of average
                score += 25
                factors.append(f"Amount ${claim.claim_amount:,.2f} is {ratio:.1f}x higher than average ${expected_amount:,.2f}")
            elif ratio > 1.5:  # More than 150% of average
                score += 10
                factors.append(f"Amount ${claim.claim_amount:,.2f} is {ratio:.1f}x higher than average ${expected_amount:,.2f}")
            
            # Also flag if suspiciously low (potential unbundling)
            elif ratio < 0.3:  # Less than 30% of average
                score += 15
                factors.append(f"Amount ${claim.claim_amount:,.2f} is unusually low compared to average ${expected_amount:,.2f}")
        
        # Flag high amounts regardless of procedure
        if claim.claim_amount > 50000:
            score += 35  # Increased from 20
            factors.append(f"High-value claim: ${claim.claim_amount:,.2f}")
        elif claim.claim_amount > 10000:
            score += 25
            factors.append(f"Significant claim amount: ${claim.claim_amount:,.2f}")
        
        return score, factors
    
    def _check_provider_patterns(self, claim: Claim) -> tuple[float, List[str]]:
        """Check provider-specific patterns"""
        score = 0.0
        factors = []
        
        # Get all claims for this provider
        all_claims = self.data_handler.get_all_claims()
        provider_claims = [c for c in all_claims if c.provider_name == claim.provider_name]
        
        if len(provider_claims) > 5:  # Only analyze if sufficient data
            # Calculate denial rate
            denied_claims = [c for c in provider_claims if c.status.value == "DENIED"]
            denial_rate = len(denied_claims) / len(provider_claims) * 100
            
            if denial_rate > 30:
                score += 20
                factors.append(f"Provider has high denial rate: {denial_rate:.1f}%")
            
            # Check for unusual volume patterns
            if len(provider_claims) > 50:  # High volume provider
                recent_claims = [c for c in provider_claims 
                               if (datetime.now() - c.created_at).days <= 30]
                if len(recent_claims) > 20:  # More than 20 claims in last 30 days
                    score += 15
                    factors.append(f"High claim volume: {len(recent_claims)} claims in last 30 days")
        
        return score, factors
    
    def _check_timing_anomalies(self, claim: Claim) -> tuple[float, List[str]]:
        """Check for timing-related anomalies"""
        score = 0.0
        factors = []
        
        # Check delay between service and submission
        days_delay = (claim.created_at.date() - claim.service_date).days
        
        if days_delay > 90:  # More than 90 days delay
            score += 25
            factors.append(f"Claim submitted {days_delay} days after service date")
        elif days_delay > 30:  # More than 30 days delay
            score += 10
            factors.append(f"Claim submitted {days_delay} days after service date")
        
        # Check for weekend/holiday service dates (some procedures unlikely)
        if claim.service_date.weekday() >= 5:  # Weekend
            if claim.procedure_code in ["99213", "99214", "99215"]:  # Routine office visits
                score += 5
                factors.append("Routine office visit scheduled on weekend")
        
        return score, factors
    
    def get_provider_statistics(self, provider_name: str) -> Dict[str, Any]:
        """Get statistics for a specific provider"""
        all_claims = self.data_handler.get_all_claims()
        provider_claims = [c for c in all_claims if c.provider_name == provider_name]
        
        if not provider_claims:
            return {"total_claims": 0}
        
        total_claims = len(provider_claims)
        approved_claims = len([c for c in provider_claims if c.status.value == "APPROVED"])
        denied_claims = len([c for c in provider_claims if c.status.value == "DENIED"])
        
        total_amount = sum(c.claim_amount for c in provider_claims)
        avg_amount = total_amount / total_claims if total_claims > 0 else 0
        
        return {
            "total_claims": total_claims,
            "approved_claims": approved_claims,
            "denied_claims": denied_claims,
            "approval_rate": (approved_claims / total_claims * 100) if total_claims > 0 else 0,
            "total_amount": total_amount,
            "average_amount": avg_amount
        }