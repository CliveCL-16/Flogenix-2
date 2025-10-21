#!/usr/bin/env python3
"""
Flowgenix Integration Test - Buildathon Demo Validation
Tests all critical components before presentation
"""

import asyncio
import json
import requests
import time
from pathlib import Path

# Test configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:8501"
TEST_TIMEOUT = 30

class DemoValidator:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def test(self, description):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                self.total_tests += 1
                print(f"🧪 Testing: {description}")
                try:
                    result = await func(*args, **kwargs)
                    if result:
                        print(f"✅ PASS: {description}")
                        self.passed_tests += 1
                        self.results.append({"test": description, "status": "PASS", "details": "Success"})
                    else:
                        print(f"❌ FAIL: {description}")
                        self.results.append({"test": description, "status": "FAIL", "details": "Test returned False"})
                    return result
                except Exception as e:
                    print(f"❌ ERROR: {description} - {str(e)}")
                    self.results.append({"test": description, "status": "ERROR", "details": str(e)})
                    return False
            return wrapper
        return decorator

validator = DemoValidator()

@validator.test("Backend health check")
async def test_backend_health():
    response = requests.get(f"{BACKEND_URL}/health", timeout=5)
    return response.status_code == 200 and response.json().get("status") == "healthy"

@validator.test("Demo data files exist")
async def test_demo_data():
    data_dir = Path("backend/data")
    required_files = ["claims.json", "policies.json", "providers.json", "exceptions.json"]
    
    for file in required_files:
        if not (data_dir / file).exists():
            return False
            
    # Check if claims have demo data
    with open(data_dir / "claims.json") as f:
        claims = json.load(f)
        return len(claims) >= 4  # Should have at least 4 demo scenarios

@validator.test("Multi-agent processor imports")
async def test_multi_agent_imports():
    try:
        import sys
        sys.path.append("backend")
        from app.services.multi_agent_processor import MultiAgentProcessor
        from app.services import agent_tools  # Test agent tools module
        processor = MultiAgentProcessor()
        return hasattr(processor, 'process_claim_async')
    except ImportError as e:
        print(f"Import error: {e}")
        return False

@validator.test("Agent tools functionality")
async def test_agent_tools():
    try:
        import sys
        sys.path.append("backend")
        from app.services.agent_tools import validate_required_fields, query_claims_database
        
        # Test a simple tool call
        result = validate_required_fields("test", "test", "test", "test")
        return isinstance(result, str)
    except Exception as e:
        print(f"Agent tools error: {e}")
        return False

@validator.test("Claims API endpoints")
async def test_claims_api():
    # Test submit claim
    claim_data = {
        "patient_name": "Test Patient",
        "patient_id": "TEST001",
        "procedure_codes": ["99213"],
        "diagnosis_codes": ["Z00.00"],
        "claim_amount": 100.00,
        "provider_id": "PROV001",
        "service_date": "2024-01-01"
    }
    
    response = requests.post(f"{BACKEND_URL}/api/claims/submit", 
                           json=claim_data, timeout=10)
    
    if response.status_code != 201:
        return False
        
    claim_id = response.json().get("claim_id")
    
    # Test get claim
    response = requests.get(f"{BACKEND_URL}/api/claims/{claim_id}", timeout=5)
    return response.status_code == 200

@validator.test("Agent processing endpoint")
async def test_agent_processing():
    # Get a demo claim ID
    try:
        with open("backend/data/claims.json") as f:
            claims = json.load(f)
            if not claims:
                return False
            claim_id = list(claims.keys())[0]
    except:
        return False
        
    # Test agent processing (this will take time)
    response = requests.post(f"{BACKEND_URL}/api/claims/process-agents", 
                           json={"claim_id": claim_id}, timeout=45)
    
    if response.status_code != 200:
        return False
        
    result = response.json()
    return "final_decision" in result and "agent_reports" in result

@validator.test("Agent timeline endpoint")
async def test_agent_timeline():
    # Get a demo claim ID
    try:
        with open("backend/data/claims.json") as f:
            claims = json.load(f)
            if not claims:
                return False
            claim_id = list(claims.keys())[0]
    except:
        return False
        
    response = requests.get(f"{BACKEND_URL}/api/claims/{claim_id}/timeline", timeout=5)
    return response.status_code == 200

@validator.test("Statistics endpoint")
async def test_statistics():
    response = requests.get(f"{BACKEND_URL}/api/claims/statistics", timeout=5)
    if response.status_code != 200:
        return False
        
    stats = response.json()
    required_fields = ["total_claims", "approved_claims", "pending_claims", "denied_claims"]
    return all(field in stats for field in required_fields)

async def run_all_tests():
    print("🚀 FLOWGENIX BUILDATHON DEMO VALIDATION")
    print("=" * 50)
    print()
    
    # Critical tests for demo
    await test_backend_health()
    await test_demo_data()
    await test_multi_agent_imports()
    await test_agent_tools()
    await test_claims_api()
    await test_statistics()
    await test_agent_timeline()
    
    # This test takes longer - only run if basic tests pass
    if validator.passed_tests >= 6:
        print("\n🤖 Running full agent processing test (may take 30+ seconds)...")
        await test_agent_processing()
    else:
        print("\n⚠️  Skipping agent processing test due to failures")
    
    # Results summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    for result in validator.results:
        status_icon = "✅" if result["status"] == "PASS" else "❌"
        print(f"{status_icon} {result['test']}: {result['status']}")
        if result["status"] != "PASS":
            print(f"   Details: {result['details']}")
    
    print(f"\nOverall: {validator.passed_tests}/{validator.total_tests} tests passed")
    
    # Demo readiness assessment
    if validator.passed_tests >= 7:
        print("\n🎉 DEMO READY! All critical systems working.")
        print("💡 Recommendation: Proceed with buildathon presentation")
    elif validator.passed_tests >= 5:
        print("\n⚠️  MOSTLY READY: Some non-critical issues found")
        print("💡 Recommendation: Fix minor issues but demo should work")
    else:
        print("\n🚨 NOT READY: Critical issues found")
        print("💡 Recommendation: Fix issues before presentation")
    
    # Next steps
    print("\n🎯 NEXT STEPS FOR DEMO:")
    print("1. Start backend: cd backend && python main.py")
    print("2. Start frontend: cd frontend && streamlit run app.py")
    print("3. Open http://localhost:8501")
    print("4. Navigate to '🤖 Agent Processing' tab")
    print("5. Use demo claim IDs for presentation")
    
    return validator.passed_tests >= 5

if __name__ == "__main__":
    print("⏳ Starting validation tests...")
    print("Note: Make sure backend is running on http://localhost:8000")
    print()
    
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)