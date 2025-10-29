#!/usr/bin/env python3
"""
Debug script to test AI processing with agent report saving
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.core.database import get_database_session
from app.core.models import Claim, ClaimStatus
from app.services.ai_processing import AIProcessingService
from datetime import datetime, date

async def test_ai_processing():
    print("🔬 Testing AI processing with agent report saving...")
    
    # Get database session
    db_session = next(get_database_session())
    
    try:
        # Use an existing claim from the database
        existing_claim = db_session.query(Claim).filter(
            Claim.claim_id == "CLM-F04650CE"  # One of our recent test claims
        ).first()
        
        if not existing_claim:
            print("❌ Test claim CLM-F04650CE not found. Please run a claim submission first.")
            return
        
        print(f"� Using existing claim: {existing_claim.claim_id}")
        
        # Initialize AI processing service
        ai_service = AIProcessingService()
        print(f"🤖 AI Service initialized, mock_mode: {ai_service.mock_mode}")
        
        # Process the claim
        fraud_score = 25.0
        decision_log = await ai_service.process_claim(existing_claim, fraud_score, db_session)
        
        print(f"📋 Decision log created:")
        print(f"  - Decision: {decision_log.decision}")
        print(f"  - Confidence: {decision_log.confidence_score}")
        print(f"  - Reasoning: {decision_log.reasoning_text[:100]}...")
        
        # Check if agent reports were saved
        from app.core.models import AgentReport
        agent_reports = db_session.query(AgentReport).filter(
            AgentReport.claim_id == existing_claim.claim_id
        ).all()
        
        print(f"🔍 Found {len(agent_reports)} agent reports in database for claim {existing_claim.claim_id}")
        for report in agent_reports:
            print(f"  - {report.agent_name}: {report.status} - {report.result[:50]}...")
        
    except Exception as e:
        print(f"❌ Error during AI processing test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db_session.close()

if __name__ == "__main__":
    asyncio.run(test_ai_processing())