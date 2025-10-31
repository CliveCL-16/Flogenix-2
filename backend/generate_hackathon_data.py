#!/usr/bin/env python3
"""
Generate and process dummy claims for hackathon demo
Creates realistic claims data and processes them through the enhanced multi-agent system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import random
from datetime import datetime, timedelta
from faker import Faker

from app.core.database import get_database_session, init_database
from app.core.models import Claim, ClaimStatus, DecisionLog, AgentReport, User, UserRole, AgentStatus
from app.core.security import auth_service, pwd_context
from app.services.enhanced_multi_agent_processor import EnhancedMultiAgentProcessor

fake = Faker()

class HackathonDummyDataGenerator:
    """Generate realistic dummy claims for hackathon demo"""
    
    def __init__(self):
        self.enhanced_processor = EnhancedMultiAgentProcessor()
        
    def ensure_demo_user(self, session):
        """Ensure there's a demo user for foreign key constraints"""
        demo_user = session.query(User).filter(User.email == "demo@flogenix.com").first()
        if not demo_user:
            demo_user = User(
                email="demo@flogenix.com",
                username="demo_user",
                first_name="Demo",
                last_name="User",
                role=UserRole.USER,
                is_active=True
            )
            # Set password
            demo_user.hashed_password = pwd_context.hash("demo123")
            session.add(demo_user)
            session.commit()
            print(f"✅ Created demo user: {demo_user.email}")
        return demo_user.id
        
    def setup_data(self):
        """Setup realistic patient data"""
    def setup_data(self):
        """Setup realistic patient data"""
        # Realistic patient data
        self.patients = [
            {"name": "John Smith", "id": "PAT001", "age": 35},
            {"name": "Sarah Johnson", "id": "PAT002", "age": 42},
            {"name": "Michael Brown", "id": "PAT003", "age": 28},
            {"name": "Emily Davis", "id": "PAT004", "age": 67},
            {"name": "Robert Wilson", "id": "PAT005", "age": 45},
            {"name": "Lisa Anderson", "id": "PAT006", "age": 33},
            {"name": "David Miller", "id": "PAT007", "age": 58},
            {"name": "Jennifer Garcia", "id": "PAT008", "age": 39},
            {"name": "Christopher Lee", "id": "PAT009", "age": 52},
            {"name": "Amanda Taylor", "id": "PAT010", "age": 26},
            {"name": "Matthew Rodriguez", "id": "PAT011", "age": 31},
            {"name": "Jessica Martinez", "id": "PAT012", "age": 44},
            {"name": "Daniel Thompson", "id": "PAT013", "age": 55},
            {"name": "Ashley White", "id": "PAT014", "age": 29},
            {"name": "Kevin Harris", "id": "PAT015", "age": 48}
        ]
        
        self.insurance_providers = [
            "Blue Cross Blue Shield",
            "Aetna Healthcare", 
            "Cigna Health",
            "UnitedHealthcare",
            "Humana Health",
            "Kaiser Permanente"
        ]
        
        self.providers = [
            {"name": "City Medical Center", "npi": "1234567890"},
            {"name": "Downtown Clinic", "npi": "2345678901"},
            {"name": "Family Health Associates", "npi": "3456789012"},
            {"name": "Specialty Care Center", "npi": "4567890123"},
            {"name": "Emergency Medical Group", "npi": "5678901234"}
        ]
        
        # Medical scenarios with expected outcomes
        self.scenarios = {
            "routine_care": {
                "diagnosis": "Z00.00",  # General health examination
                "procedure": "99213",   # Office visit
                "cost_range": [80, 250],
                "expected": "APPROVE",
                "weight": 40  # 40% of claims
            },
            "diabetes_management": {
                "diagnosis": "E11.9",   # Type 2 diabetes
                "procedure": "99213",   # Office visit
                "cost_range": [120, 300],
                "expected": "APPROVE", 
                "weight": 20
            },
            "fracture_surgery": {
                "diagnosis": "S72.001A", # Femur fracture
                "procedure": "27236",    # Fracture repair
                "cost_range": [15000, 40000],
                "expected": "APPROVE",
                "weight": 5
            },
            "fraud_high_cost": {
                "diagnosis": "Z00.00",  # Simple checkup
                "procedure": "99213",   # Office visit
                "cost_range": [10000, 75000],  # Ridiculously high
                "expected": "DENY/REVIEW",
                "weight": 10
            },
            "invalid_codes": {
                "diagnosis": "Z00.00",  # Checkup
                "procedure": "27236",   # Surgery - incompatible
                "cost_range": [500, 2000],
                "expected": "DENY",
                "weight": 15
            },
            "hypertension": {
                "diagnosis": "I10",     # Essential hypertension
                "procedure": "99213",   # Office visit
                "cost_range": [100, 250],
                "expected": "APPROVE",
                "weight": 10
            }
        }
    
    def generate_claim_id(self):
        """Generate unique claim ID"""
        return f"CLM-{random.randint(100000, 999999)}"
    
    def select_scenario(self):
        """Select a scenario based on weights"""
        scenarios = list(self.scenarios.keys())
        weights = [self.scenarios[s]["weight"] for s in scenarios]
        return random.choices(scenarios, weights=weights)[0]
    
    def create_claim_data(self, scenario_type, user_id):
        """Create a realistic claim"""
        scenario = self.scenarios[scenario_type]
        patient = random.choice(self.patients)
        insurance = random.choice(self.insurance_providers)
        provider = random.choice(self.providers)
        
        # Generate realistic amounts within scenario range
        amount = random.uniform(scenario["cost_range"][0], scenario["cost_range"][1])
        
        # Generate service date (last 90 days)
        days_ago = random.randint(1, 90)
        service_date = (datetime.utcnow() - timedelta(days=days_ago)).date()
        
        # Generate policy number
        policy_number = f"POL-{random.randint(100000, 999999)}"
        
        claim = Claim(
            claim_id=self.generate_claim_id(),
            patient_name=patient["name"],
            patient_id=patient["id"],
            insurance_provider=insurance,
            policy_number=policy_number,
            diagnosis_code=scenario["diagnosis"],
            procedure_code=scenario["procedure"],
            service_date=service_date,
            claim_amount=round(amount, 2),
            provider_name=provider["name"],
            provider_npi=provider["npi"],
            notes=f"Generated claim for {scenario_type.replace('_', ' ')} scenario",
            status=ClaimStatus.PENDING,
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, days_ago)),
            priority=random.randint(1, 3),
            user_id=user_id  # Use provided user id
        )
        
        return claim, scenario_type, scenario["expected"]
    
    async def process_claim_through_agents(self, claim, scenario_type):
        """Process claim through enhanced multi-agent system"""
        print(f"🤖 Processing {claim.claim_id} through AI agents...")
        
        # Prepare claim data for processing
        claim_data = {
            "patient_name": claim.patient_name,
            "patient_id": claim.patient_id,
            "insurance_provider": claim.insurance_provider,
            "policy_number": claim.policy_number,
            "diagnosis_code": claim.diagnosis_code,
            "procedure_code": claim.procedure_code,
            "claim_amount": claim.claim_amount,
            "service_date": claim.service_date.isoformat(),
            "provider_name": claim.provider_name,
            "provider_npi": claim.provider_npi,
            "notes": claim.notes
        }
        
        try:
            # Process with enhanced multi-agent system
            processing_result = await self.enhanced_processor.process_claim(claim_data, claim.claim_id)
            
            # Update claim status based on decision
            if processing_result.final_decision == "APPROVE":
                claim.status = ClaimStatus.APPROVED
            elif processing_result.final_decision == "DENY":
                claim.status = ClaimStatus.DENIED
            else:  # REVIEW
                claim.status = ClaimStatus.PENDING_REVIEW
            
            # Create decision log
            decision_log = DecisionLog(
                claim_id=claim.claim_id,
                decision=processing_result.final_decision,
                confidence_score=processing_result.confidence_score,
                reasoning_text=processing_result.reasoning,
                processing_time_seconds=0.5,  # Simulated processing time
                created_at=datetime.utcnow()
            )
            
            # Create agent reports
            agent_reports = []
            for agent_name, agent_result in processing_result.agent_results.items():
                agent_report = AgentReport(
                    claim_id=claim.claim_id,
                    agent_name=agent_name,
                    agent_type=agent_name.lower(),  # intake, eligibility, clinical, fraud, adjudication
                    status=AgentStatus.COMPLETED,  # Since processing completed
                    result=agent_result.status.value,
                    confidence_score=agent_result.confidence_score,
                    reasoning_steps=[step.content for step in agent_result.reasoning_steps[:3]] if hasattr(agent_result, 'reasoning_steps') else [],
                    tool_usage=[{"tool": str(tool), "result": "success"} for tool in agent_result.tool_calls[:3]] if hasattr(agent_result, 'tool_calls') else [],
                    duration_seconds=agent_result.duration_seconds if hasattr(agent_result, 'duration_seconds') else 0.5,
                    started_at=datetime.utcnow() - timedelta(seconds=1),
                    completed_at=datetime.utcnow()
                )
                agent_reports.append(agent_report)
            
            print(f"     🎯 Decision: {processing_result.final_decision} (confidence: {processing_result.confidence_score:.1f}%)")
            
            return claim, decision_log, agent_reports, processing_result
            
        except Exception as e:
            print(f"     ❌ Error processing claim: {str(e)}")
            claim.status = ClaimStatus.DENIED
            return claim, None, [], None
    
    async def generate_demo_data(self, num_claims=30):
        """Generate comprehensive demo data"""
        print("🚀 Flogenix Hackathon Demo Data Generator")
        print("=" * 60)
        print(f"Creating {num_claims} realistic claims with AI processing...")
        print()
        
        # Initialize database and create demo user
        init_database()
        session = next(get_database_session())
        
        # Ensure demo user exists
        demo_user_id = self.ensure_demo_user(session)
        
        # Setup data
        self.setup_data()
        
        all_claims = []
        all_decision_logs = []
        all_agent_reports = []
        
        scenario_counts = {}
        decision_counts = {"APPROVE": 0, "DENY": 0, "REVIEW": 0}
        
        try:
            for i in range(num_claims):
                scenario_type = self.select_scenario()
                scenario_counts[scenario_type] = scenario_counts.get(scenario_type, 0) + 1
                
                print(f"📋 Creating claim {i+1}/{num_claims}: {scenario_type.replace('_', ' ').title()}")
                
                # Create claim
                claim, scenario, expected = self.create_claim_data(scenario_type, demo_user_id)
                
                # Process through AI agents
                processed_claim, decision_log, agent_reports, processing_result = await self.process_claim_through_agents(claim, scenario_type)
                
                # Collect data
                all_claims.append(processed_claim)
                if decision_log:
                    all_decision_logs.append(decision_log)
                all_agent_reports.extend(agent_reports)
                
                # Track decisions
                decision_counts[processed_claim.status.value.upper()] = decision_counts.get(processed_claim.status.value.upper(), 0) + 1
                
                print(f"     💾 Saved: {processed_claim.patient_name} - ${processed_claim.claim_amount:,.2f}")
                print()
            
            # Bulk insert to database
            print("💾 Saving to database...")
            session.add_all(all_claims)
            session.add_all(all_decision_logs)
            session.add_all(all_agent_reports)
            session.commit()
            
            print("🎉 Demo data generation complete!")
            print("=" * 50)
            
            # Display summary
            print(f"📊 GENERATION SUMMARY:")
            print(f"   Total Claims Created: {len(all_claims)}")
            print(f"   Decision Logs: {len(all_decision_logs)}")
            print(f"   Agent Reports: {len(all_agent_reports)}")
            print()
            
            print(f"📈 SCENARIO DISTRIBUTION:")
            for scenario, count in scenario_counts.items():
                print(f"   {scenario.replace('_', ' ').title()}: {count}")
            print()
            
            print(f"🎯 DECISION SUMMARY:")
            for decision, count in decision_counts.items():
                print(f"   {decision}: {count}")
            print()
            
            # Calculate some demo metrics
            total_amount = sum(claim.claim_amount for claim in all_claims)
            avg_amount = total_amount / len(all_claims)
            
            fraud_claims = [c for c in all_claims if 'fraud' in c.notes.lower()]
            fraud_detected = sum(1 for c in fraud_claims if c.status == ClaimStatus.DENIED)
            
            print(f"💰 FINANCIAL SUMMARY:")
            print(f"   Total Claims Value: ${total_amount:,.2f}")
            print(f"   Average Claim: ${avg_amount:,.2f}")
            print(f"   Fraud Claims Generated: {len(fraud_claims)}")
            print(f"   Fraud Successfully Detected: {fraud_detected}")
            print()
            
            print(f"🎊 Ready for hackathon demo!")
            print(f"🔗 Your database now contains realistic claims data")
            print(f"   with AI processing results and agent reports!")
            
        except Exception as e:
            print(f"❌ Error during generation: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()

async def main():
    """Main execution"""
    generator = HackathonDummyDataGenerator()
    await generator.generate_demo_data(30)  # Generate 30 claims

if __name__ == "__main__":
    asyncio.run(main())