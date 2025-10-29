#!/usr/bin/env python3
"""
Test Multi-Agent Processor directly
"""

import sys
import asyncio
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.multi_agent_processor import MultiAgentProcessor

async def test_multi_agent():
    """Test the multi-agent processor directly"""
    
    processor = MultiAgentProcessor()
    
    # Test claim data
    claim_data = {
        "patient_name": "Test Patient",
        "patient_id": "PAT-TEST",
        "insurance_provider": "Test Insurance",
        "policy_number": "POL-12345",
        "diagnosis_code": "Z00.00",
        "procedure_code": "99213",
        "claim_amount": 150.0,
        "service_date": "2025-10-28",
        "provider_name": "Test Provider",
        "provider_npi": "1234567890",
        "notes": "Test claim"
    }
    
    print("🚀 Testing multi-agent processor...")
    print(f"📋 Claim data: {claim_data}")
    
    try:
        result = await processor.process_claim(claim_data, "CLM-TEST-123")
        
        print(f"✅ Processing completed")
        print(f"📊 Result type: {type(result)}")
        print(f"📄 Result: {result}")
        
        if hasattr(result, 'agent_reports'):
            print(f"🤖 Agent reports: {len(result.agent_reports)}")
            for report in result.agent_reports:
                print(f"  - {report.agent_name}: {report.result}")
        elif isinstance(result, dict) and 'agent_reports' in result:
            print(f"🤖 Agent reports (dict): {len(result['agent_reports'])}")
            for report in result['agent_reports']:
                print(f"  - {report.get('agent_name', 'Unknown')}: {report.get('result', 'No result')}")
        else:
            print("⚠️ No agent reports found in result")
            if isinstance(result, dict):
                print(f"📋 Dict keys: {list(result.keys())}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_multi_agent())