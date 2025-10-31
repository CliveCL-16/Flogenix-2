"""
Enhanced Predictive Fraud Detection Service
Advanced fraud detection using Gemini AI and pattern recognition
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import statistics

from app.models import Claim, FraudAnalysis
from app.services.data_handler import DataHandler
from app.services.gemini_service import gemini_service
from app.services.admin_reporting_service import admin_reporting_service
from app.services.continuous_learning_service import continuous_learning_service
from app.services.continuous_learning_service import continuous_learning_service
from app.core.config import settings


@dataclass
class FraudPattern:
    """Represents a detected fraud pattern"""
    pattern_id: str
    pattern_type: str
    description: str
    indicators: List[str]
    confidence_score: float
    frequency: int
    first_detected: datetime
    last_seen: datetime


@dataclass
class AdvancedFraudAnalysis:
    """Enhanced fraud analysis with AI insights"""
    claim_id: str
    fraud_risk_score: float
    risk_level: str
    detected_patterns: List[FraudPattern]
    ai_reasoning: str
    red_flags: List[str]
    recommended_action: str
    investigation_priority: str
    confidence_level: float
    similar_cases: List[str]
    predictive_indicators: List[str]
    behavioral_anomalies: List[str]
    temporal_patterns: List[str]
    network_analysis: Dict[str, Any]
    timestamp: datetime


class EnhancedFraudDetectionService:
    """Advanced fraud detection service with AI and machine learning"""
    
    def __init__(self, data_handler: Optional[DataHandler] = None):
        """Initialize the enhanced fraud detection service"""
        self.data_handler = data_handler
        self.learned_patterns: Dict[str, FraudPattern] = {}
        self.provider_risk_profiles: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.patient_behavior_profiles: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.historical_analysis_cache: List[Dict[str, Any]] = []
        
        # Enhanced procedure averages with statistical data
        self.procedure_statistics = {
            "99213": {"avg": 150.0, "std": 25.0, "min": 100.0, "max": 200.0},
            "99214": {"avg": 250.0, "std": 40.0, "min": 180.0, "max": 320.0},
            "99215": {"avg": 350.0, "std": 60.0, "min": 250.0, "max": 450.0},
            "92004": {"avg": 200.0, "std": 30.0, "min": 150.0, "max": 280.0},
            "27447": {"avg": 15000.0, "std": 2500.0, "min": 10000.0, "max": 20000.0},
            "73721": {"avg": 800.0, "std": 150.0, "min": 600.0, "max": 1200.0},
            "36415": {"avg": 25.0, "std": 5.0, "min": 15.0, "max": 40.0},
            "85025": {"avg": 50.0, "std": 10.0, "min": 30.0, "max": 80.0}
        }
        
        print("✅ Enhanced Fraud Detection Service initialized")
    
    async def analyze_fraud_risk_advanced(self, claim: Claim) -> AdvancedFraudAnalysis:
        """Perform advanced fraud analysis using AI and pattern recognition with detailed reporting"""
        
        start_time = datetime.now()
        print(f"🔍 Performing advanced fraud analysis for claim {claim.claim_id}")
        
        try:
            # Gather historical context
            historical_data = await self._gather_historical_context(claim)
            
            # Perform traditional rule-based analysis
            traditional_analysis = await self._traditional_fraud_analysis(claim)
            
            # Use Gemini AI for advanced pattern detection
            ai_analysis = await gemini_service.detect_fraud_patterns(
                claim.to_dict(), historical_data
            )
            
            # Analyze provider behavior patterns
            provider_analysis = await self._analyze_provider_patterns(claim)
            
            # Analyze patient behavior patterns
            patient_analysis = await self._analyze_patient_patterns(claim)
            
            # Perform network analysis
            network_analysis = await self._perform_network_analysis(claim)
            
            # Detect temporal anomalies
            temporal_patterns = await self._detect_temporal_patterns(claim)
            
            # Combine all analyses
            combined_analysis = await self._combine_analyses(
                claim, traditional_analysis, ai_analysis, provider_analysis,
                patient_analysis, network_analysis, temporal_patterns
            )
            
            # Apply learned patterns
            pattern_adjustments = await self._apply_learned_patterns(claim, combined_analysis)
            
            # Create final analysis
            final_analysis = AdvancedFraudAnalysis(
                claim_id=claim.claim_id,
                fraud_risk_score=combined_analysis["fraud_risk_score"],
                risk_level=combined_analysis["risk_level"],
                detected_patterns=pattern_adjustments["detected_patterns"],
                ai_reasoning=ai_analysis.get("reasoning", "No AI reasoning available"),
                red_flags=combined_analysis["red_flags"],
                recommended_action=ai_analysis.get("recommended_action", "review"),
                investigation_priority=ai_analysis.get("investigation_priority", "medium"),
                confidence_level=ai_analysis.get("confidence_level", 50) / 100,
                similar_cases=ai_analysis.get("similar_fraudulent_cases", []),
                predictive_indicators=combined_analysis["predictive_indicators"],
                behavioral_anomalies=combined_analysis["behavioral_anomalies"],
                temporal_patterns=temporal_patterns,
                network_analysis=network_analysis,
                timestamp=datetime.utcnow()
            )
            
            # Update learned patterns
            await self._update_learned_patterns(final_analysis)
            
            # Record learning event
            await continuous_learning_service.record_learning_event(
                claim_id=claim.claim_id,
                agent_name="fraud_agent",
                event_type="analysis",
                context={
                    "claim_data": claim.to_dict(),
                    "analysis_result": {
                        "fraud_score": final_analysis.fraud_risk_score,
                        "risk_level": final_analysis.risk_level,
                        "detected_patterns": len(final_analysis.detected_patterns)
                    }
                },
                outcome="completed",
                confidence_before=final_analysis.confidence_level
            )
            
            # Generate detailed admin report
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            report = await admin_reporting_service.generate_fraud_detection_report(
                claim_data=claim.to_dict(),
                fraud_analysis=final_analysis,
                processing_time_ms=processing_time_ms
            )
            
            print(f"✅ Advanced fraud analysis completed: {final_analysis.risk_level} risk ({final_analysis.fraud_risk_score:.1f}%)")
            print(f"📋 Admin report generated: {report.report_id}")
            
            return final_analysis
            
        except Exception as e:
            print(f"❌ Error in advanced fraud analysis: {e}")
            
            # Fallback to basic analysis
            basic_analysis = await self._fallback_analysis(claim)
            return basic_analysis
    
    async def _gather_historical_context(self, claim: Claim) -> List[Dict[str, Any]]:
        """Gather historical context for analysis"""
        
        # Return empty context if no data handler available
        if not self.data_handler:
            return []
        
        try:
            # Get recent claims from same provider
            provider_claims = self.data_handler.get_claims_by_provider(
                claim.provider_npi, limit=20
            )
            
            # Get recent claims from same patient
            patient_claims = self.data_handler.get_claims_by_patient(
                claim.patient_id, limit=10
            )
            
            # Get claims with same procedure
            procedure_claims = self.data_handler.get_claims_by_procedure(
                claim.procedure_code, limit=15
            )
            
            # Combine and format for AI analysis
            historical_data = []
            
            for claims_list, context_type in [
                (provider_claims, "provider"),
                (patient_claims, "patient"),
                (procedure_claims, "procedure")
            ]:
                for hist_claim in claims_list:
                    if hist_claim.claim_id != claim.claim_id:  # Exclude current claim
                        historical_data.append({
                            "context_type": context_type,
                            "claim_id": hist_claim.claim_id,
                            "amount": hist_claim.claim_amount,
                            "procedure": hist_claim.procedure_code,
                            "diagnosis": hist_claim.diagnosis_code,
                            "provider": hist_claim.provider_npi,
                            "date": hist_claim.service_date.isoformat() if hist_claim.service_date else None,
                            "status": getattr(hist_claim, 'status', 'unknown')
                        })
            
            return historical_data[:50]  # Limit to prevent token overflow
            
        except Exception as e:
            print(f"❌ Error gathering historical context: {e}")
            return []
    
    async def _traditional_fraud_analysis(self, claim: Claim) -> Dict[str, Any]:
        """Perform traditional rule-based fraud analysis"""
        
        fraud_score = 0.0
        risk_factors = []
        
        # Amount analysis
        procedure_stats = self.procedure_statistics.get(claim.procedure_code)
        if procedure_stats:
            amount = claim.claim_amount
            avg = procedure_stats["avg"]
            std = procedure_stats["std"]
            
            # Calculate z-score
            z_score = abs(amount - avg) / std if std > 0 else 0
            
            if z_score > 3:  # More than 3 standard deviations
                fraud_score += 25
                risk_factors.append(f"Amount significantly higher than average (z-score: {z_score:.2f})")
            elif z_score > 2:
                fraud_score += 15
                risk_factors.append(f"Amount moderately higher than average (z-score: {z_score:.2f})")
        
        # Provider frequency analysis
        provider_claims_count = len(self.data_handler.get_claims_by_provider(
            claim.provider_npi, days_back=30
        ))
        
        if provider_claims_count > 100:  # High volume provider
            fraud_score += 10
            risk_factors.append(f"High volume provider ({provider_claims_count} claims in 30 days)")
        
        # Patient frequency analysis
        patient_claims_count = len(self.data_handler.get_claims_by_patient(
            claim.patient_id, days_back=30
        ))
        
        if patient_claims_count > 10:  # Frequent claimant
            fraud_score += 15
            risk_factors.append(f"Frequent claimant ({patient_claims_count} claims in 30 days)")
        
        # Time-based patterns
        service_date = claim.service_date
        if service_date:
            # Weekend claims might be suspicious for certain procedures
            if service_date.weekday() >= 5 and claim.procedure_code in ["99213", "99214"]:
                fraud_score += 5
                risk_factors.append("Office visit claimed on weekend")
            
            # Late night claims
            if hasattr(service_date, 'hour') and service_date.hour < 6 or service_date.hour > 22:
                fraud_score += 10
                risk_factors.append("Service provided during unusual hours")
        
        return {
            "fraud_score": fraud_score,
            "risk_factors": risk_factors,
            "analysis_method": "traditional_rules"
        }
    
    async def _analyze_provider_patterns(self, claim: Claim) -> Dict[str, Any]:
        """Analyze provider behavior patterns"""
        
        provider_npi = claim.provider_npi
        
        # Get provider's recent claims
        recent_claims = self.data_handler.get_claims_by_provider(provider_npi, days_back=90)
        
        if len(recent_claims) < 5:
            return {"anomalies": [], "risk_score": 0}
        
        anomalies = []
        risk_score = 0
        
        # Analyze billing patterns
        amounts = [c.claim_amount for c in recent_claims]
        procedures = [c.procedure_code for c in recent_claims]
        
        # Check for unusual amount patterns
        if len(amounts) > 1:
            avg_amount = statistics.mean(amounts)
            std_amount = statistics.stdev(amounts) if len(amounts) > 1 else 0
            
            if claim.claim_amount > avg_amount + 3 * std_amount:
                anomalies.append("Claim amount significantly higher than provider's recent average")
                risk_score += 20
        
        # Check for procedure concentration
        procedure_counts = {}
        for proc in procedures:
            procedure_counts[proc] = procedure_counts.get(proc, 0) + 1
        
        if len(procedure_counts) == 1 and len(recent_claims) > 10:
            anomalies.append("Provider only bills for single procedure type")
            risk_score += 15
        
        # Update provider risk profile
        self.provider_risk_profiles[provider_npi].update({
            "total_claims": len(recent_claims),
            "average_amount": statistics.mean(amounts),
            "procedure_diversity": len(procedure_counts),
            "last_updated": datetime.utcnow().isoformat()
        })
        
        return {
            "anomalies": anomalies,
            "risk_score": risk_score,
            "profile": self.provider_risk_profiles[provider_npi]
        }
    
    async def _analyze_patient_patterns(self, claim: Claim) -> Dict[str, Any]:
        """Analyze patient behavior patterns"""
        
        patient_id = claim.patient_id
        
        # Get patient's recent claims
        recent_claims = self.data_handler.get_claims_by_patient(patient_id, days_back=180)
        
        if len(recent_claims) < 2:
            return {"anomalies": [], "risk_score": 0}
        
        anomalies = []
        risk_score = 0
        
        # Analyze claim frequency
        claim_dates = [c.service_date for c in recent_claims if c.service_date]
        
        if len(claim_dates) > 1:
            # Check for clustering of claims
            sorted_dates = sorted(claim_dates)
            intervals = []
            for i in range(1, len(sorted_dates)):
                interval = (sorted_dates[i] - sorted_dates[i-1]).days
                intervals.append(interval)
            
            if intervals and statistics.mean(intervals) < 7:  # Claims within a week
                anomalies.append("High frequency of claims in short time period")
                risk_score += 15
        
        # Check for provider hopping
        providers = set(c.provider_npi for c in recent_claims)
        if len(providers) > 5:
            anomalies.append("Patient visits many different providers")
            risk_score += 10
        
        # Update patient behavior profile
        self.patient_behavior_profiles[patient_id].update({
            "total_claims": len(recent_claims),
            "unique_providers": len(providers),
            "claim_frequency": len(recent_claims) / 180 * 30,  # Claims per month
            "last_updated": datetime.utcnow().isoformat()
        })
        
        return {
            "anomalies": anomalies,
            "risk_score": risk_score,
            "profile": self.patient_behavior_profiles[patient_id]
        }
    
    async def _perform_network_analysis(self, claim: Claim) -> Dict[str, Any]:
        """Perform network analysis to detect fraud rings"""
        
        # Simplified network analysis - in production, this would be more sophisticated
        network_data = {
            "provider_connections": 0,
            "patient_connections": 0,
            "suspicious_clusters": [],
            "network_risk_score": 0
        }
        
        try:
            # Find providers that share patients with this provider
            provider_patients = set()
            provider_claims = self.data_handler.get_claims_by_provider(claim.provider_npi)
            for p_claim in provider_claims:
                provider_patients.add(p_claim.patient_id)
            
            # Find other providers treating the same patients
            connected_providers = set()
            for patient_id in provider_patients:
                patient_claims = self.data_handler.get_claims_by_patient(patient_id)
                for p_claim in patient_claims:
                    if p_claim.provider_npi != claim.provider_npi:
                        connected_providers.add(p_claim.provider_npi)
            
            network_data["provider_connections"] = len(connected_providers)
            
            # High connectivity might indicate fraud rings
            if len(connected_providers) > 20:
                network_data["suspicious_clusters"].append("High provider connectivity")
                network_data["network_risk_score"] += 15
            
        except Exception as e:
            print(f"❌ Error in network analysis: {e}")
        
        return network_data
    
    async def _detect_temporal_patterns(self, claim: Claim) -> List[str]:
        """Detect temporal anomalies and patterns"""
        
        patterns = []
        
        try:
            service_date = claim.service_date
            if not service_date:
                return patterns
            
            # Check for patterns around holidays or weekends
            if service_date.weekday() >= 5:  # Weekend
                patterns.append("Weekend service")
            
            # Check for end-of-month/year patterns
            if service_date.day >= 28:
                patterns.append("End of month billing")
            
            if service_date.month == 12 and service_date.day >= 28:
                patterns.append("End of year billing")
            
            # Check for same-day multiple claims
            same_day_claims = self.data_handler.get_claims_by_date(service_date)
            same_patient_same_day = [
                c for c in same_day_claims 
                if c.patient_id == claim.patient_id and c.claim_id != claim.claim_id
            ]
            
            if len(same_patient_same_day) > 2:
                patterns.append("Multiple claims same day")
            
        except Exception as e:
            print(f"❌ Error detecting temporal patterns: {e}")
        
        return patterns
    
    async def _combine_analyses(self, claim: Claim, traditional: Dict[str, Any],
                              ai_analysis: Dict[str, Any], provider: Dict[str, Any],
                              patient: Dict[str, Any], network: Dict[str, Any],
                              temporal: List[str]) -> Dict[str, Any]:
        """Combine all analyses into final assessment"""
        
        # Combine fraud scores
        total_score = (
            traditional["fraud_score"] +
            provider["risk_score"] +
            patient["risk_score"] +
            network["network_risk_score"] +
            ai_analysis.get("fraud_risk_score", 0)
        )
        
        # Weight the AI analysis more heavily
        ai_weight = 1.5
        final_score = (total_score + ai_analysis.get("fraud_risk_score", 0) * ai_weight) / (1 + ai_weight)
        
        # Normalize to 0-100
        final_score = min(100, max(0, final_score))
        
        # Determine risk level
        if final_score >= 80:
            risk_level = "critical"
        elif final_score >= 60:
            risk_level = "high"
        elif final_score >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Combine all red flags
        all_red_flags = (
            traditional["risk_factors"] +
            provider["anomalies"] +
            patient["anomalies"] +
            network["suspicious_clusters"] +
            ai_analysis.get("red_flags", []) +
            temporal
        )
        
        # Combine predictive indicators
        predictive_indicators = (
            ai_analysis.get("detected_patterns", []) +
            [f"Provider risk score: {provider['risk_score']}"] +
            [f"Patient risk score: {patient['risk_score']}"] +
            [f"Network risk score: {network['network_risk_score']}"]
        )
        
        return {
            "fraud_risk_score": final_score,
            "risk_level": risk_level,
            "red_flags": all_red_flags,
            "predictive_indicators": predictive_indicators,
            "behavioral_anomalies": provider["anomalies"] + patient["anomalies"],
            "component_scores": {
                "traditional": traditional["fraud_score"],
                "ai_analysis": ai_analysis.get("fraud_risk_score", 0),
                "provider": provider["risk_score"],
                "patient": patient["risk_score"],
                "network": network["network_risk_score"]
            }
        }
    
    async def _apply_learned_patterns(self, claim: Claim, 
                                    analysis: Dict[str, Any]) -> Dict[str, List[FraudPattern]]:
        """Apply learned fraud patterns to adjust analysis"""
        
        detected_patterns = []
        
        # Check against learned patterns
        for pattern_id, pattern in self.learned_patterns.items():
            if await self._pattern_matches_claim(pattern, claim, analysis):
                detected_patterns.append(pattern)
                # Update pattern frequency
                pattern.frequency += 1
                pattern.last_seen = datetime.utcnow()
        
        return {"detected_patterns": detected_patterns}
    
    async def _pattern_matches_claim(self, pattern: FraudPattern, claim: Claim,
                                   analysis: Dict[str, Any]) -> bool:
        """Check if a learned pattern matches the current claim"""
        
        # Simple pattern matching - could be enhanced with ML
        pattern_indicators = set(pattern.indicators)
        claim_indicators = set(analysis.get("red_flags", []))
        
        # Check for overlap in indicators
        overlap = len(pattern_indicators.intersection(claim_indicators))
        overlap_ratio = overlap / len(pattern_indicators) if pattern_indicators else 0
        
        return overlap_ratio >= 0.6  # 60% overlap threshold
    
    async def _update_learned_patterns(self, analysis: AdvancedFraudAnalysis) -> None:
        """Update learned patterns based on new analysis"""
        
        if analysis.fraud_risk_score >= 70:  # High risk claims
            # Create or update pattern
            pattern_signature = self._generate_pattern_signature(analysis)
            
            if pattern_signature in self.learned_patterns:
                # Update existing pattern
                pattern = self.learned_patterns[pattern_signature]
                pattern.frequency += 1
                pattern.last_seen = datetime.utcnow()
                pattern.confidence_score = (
                    pattern.confidence_score * 0.9 + analysis.confidence_level * 0.1
                )
            else:
                # Create new pattern
                new_pattern = FraudPattern(
                    pattern_id=pattern_signature,
                    pattern_type="high_risk",
                    description=f"Pattern with {len(analysis.red_flags)} red flags",
                    indicators=analysis.red_flags,
                    confidence_score=analysis.confidence_level,
                    frequency=1,
                    first_detected=datetime.utcnow(),
                    last_seen=datetime.utcnow()
                )
                self.learned_patterns[pattern_signature] = new_pattern
                
                print(f"🎯 New fraud pattern learned: {pattern_signature}")
    
    def _generate_pattern_signature(self, analysis: AdvancedFraudAnalysis) -> str:
        """Generate a signature for pattern matching"""
        
        # Use key indicators to create signature
        key_indicators = analysis.red_flags[:3]  # Top 3 red flags
        signature_parts = [
            analysis.risk_level,
            str(len(analysis.red_flags)),
            "|".join(sorted(key_indicators))
        ]
        
        return "||".join(signature_parts)
    
    async def _fallback_analysis(self, claim: Claim) -> AdvancedFraudAnalysis:
        """Fallback analysis when advanced methods fail"""
        
        return AdvancedFraudAnalysis(
            claim_id=claim.claim_id,
            fraud_risk_score=25.0,  # Medium risk default
            risk_level="medium",
            detected_patterns=[],
            ai_reasoning="Fallback analysis due to system error",
            red_flags=["Analysis system unavailable"],
            recommended_action="manual_review",
            investigation_priority="medium",
            confidence_level=0.5,
            similar_cases=[],
            predictive_indicators=[],
            behavioral_anomalies=[],
            temporal_patterns=[],
            network_analysis={},
            timestamp=datetime.utcnow()
        )
    
    def get_fraud_statistics(self) -> Dict[str, Any]:
        """Get fraud detection statistics and patterns"""
        
        return {
            "learned_patterns": len(self.learned_patterns),
            "provider_profiles": len(self.provider_risk_profiles),
            "patient_profiles": len(self.patient_behavior_profiles),
            "pattern_types": {
                pattern.pattern_type: sum(1 for p in self.learned_patterns.values() 
                                        if p.pattern_type == pattern.pattern_type)
                for pattern in self.learned_patterns.values()
            },
            "average_pattern_confidence": sum(p.confidence_score for p in self.learned_patterns.values()) / 
                                         len(self.learned_patterns) if self.learned_patterns else 0,
            "ai_enabled": settings.ai.enable_predictive_fraud
        }

# This will replace the existing fraud detection service
enhanced_fraud_detection = EnhancedFraudDetectionService()