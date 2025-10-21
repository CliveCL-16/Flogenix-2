"""
Demo scenarios and test data generator for Flowgenix
Generates the 4 key demo scenarios mentioned in the requirements
"""

import json
import requests
from datetime import datetime, date, timedelta
import time

# API base URL
API_BASE = "http://localhost:8000/api"

def submit_claim(claim_data):
    """Submit a claim to the API"""
    try:
        response = requests.post(f"{API_BASE}/claims/submit", json=claim_data)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error submitting claim: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception submitting claim: {e}")
        return None

def process_claim(claim_id):
    """Process a claim"""
    try:
        response = requests.post(f"{API_BASE}/claims/{claim_id}/process")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error processing claim: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception processing claim: {e}")
        return None

def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE}/health")
        return response.status_code == 200
    except:
        return False

def demo_scenario_1_happy_path():
    """
    Scenario 1: Happy Path - Instant Approval
    Submit valid routine checkup claim that should be approved quickly
    """
    print("\n=== DEMO SCENARIO 1: Happy Path - Instant Approval ===")
    
    claim_data = {
        "patient_name": "John Doe",
        "patient_id": "PAT-001",
        "insurance_provider": "Blue Cross Blue Shield",
        "policy_number": "POL-12345",
        "diagnosis_code": "Z00.00",  # General examination
        "procedure_code": "99213",   # Office visit
        "claim_amount": 150.00,
        "service_date": (date.today() - timedelta(days=1)).isoformat(),
        "provider_name": "Dr. Sarah Johnson",
        "provider_npi": "1234567890",
        "notes": "Routine annual checkup"
    }
    
    print("Submitting routine checkup claim...")
    claim = submit_claim(claim_data)
    
    if claim:
        print(f"✅ Claim submitted: {claim['claim_id']}")
        print("Processing claim...")
        
        start_time = time.time()
        result = process_claim(claim['claim_id'])
        end_time = time.time()
        
        if result:
            print(f"✅ Claim processed in {end_time - start_time:.2f} seconds")
            print(f"Status: {result['status']}")
            print(f"Decision: {result['decision']}")
            print(f"Confidence: {result['confidence_score']}%")
            print(f"Reasoning: {result['reasoning_text']}")
            return claim['claim_id']
    
    return None

def demo_scenario_2_exception_learning():
    """
    Scenario 2: Exception Handling - Missing Document Learning
    Submit specialist visit claim missing required referral, then submit similar claim
    """
    print("\n=== DEMO SCENARIO 2: Exception Learning - Missing Referral ===")
    
    # First claim - specialist visit
    claim_data_1 = {
        "patient_name": "Jane Smith",
        "patient_id": "PAT-002",
        "insurance_provider": "Aetna Healthcare",
        "policy_number": "POL-67890",
        "diagnosis_code": "M25.511",  # Shoulder pain
        "procedure_code": "92004",    # Eye exam (mismatch to trigger exception)
        "claim_amount": 200.00,
        "service_date": (date.today() - timedelta(days=2)).isoformat(),
        "provider_name": "Dr. Michael Chen",
        "provider_npi": "9876543210",
        "notes": "Specialist consultation referral required"
    }
    
    print("Submitting first specialist claim (will trigger exception)...")
    claim_1 = submit_claim(claim_data_1)
    
    if claim_1:
        print(f"✅ First claim submitted: {claim_1['claim_id']}")
        print("Processing first claim...")
        
        result_1 = process_claim(claim_1['claim_id'])
        if result_1:
            print(f"First claim processed: {result_1['status']}")
            
            # Simulate manual resolution by handling exception
            try:
                handle_response = requests.post(
                    f"{API_BASE}/claims/{claim_1['claim_id']}/handle-exception",
                    params={
                        "exception_type": "CODE_MISMATCH",
                        "exception_details": "Procedure does not match diagnosis"
                    }
                )
                if handle_response.status_code == 200:
                    print("Exception logged for learning...")
            except Exception as e:
                print(f"Error handling exception: {e}")
    
    # Second similar claim
    print("\nSubmitting second similar claim (should learn from first)...")
    claim_data_2 = {
        "patient_name": "Bob Wilson",
        "patient_id": "PAT-003", 
        "insurance_provider": "Cigna Health",
        "policy_number": "POL-54321",
        "diagnosis_code": "S52.501A",  # Fracture
        "procedure_code": "92004",     # Eye exam (same mismatch)
        "claim_amount": 180.00,
        "service_date": (date.today() - timedelta(days=1)).isoformat(),
        "provider_name": "Dr. Michael Chen",
        "provider_npi": "9876543210",
        "notes": "Similar case to previous"
    }
    
    claim_2 = submit_claim(claim_data_2)
    
    if claim_2:
        print(f"✅ Second claim submitted: {claim_2['claim_id']}")
        print("Processing second claim...")
        
        result_2 = process_claim(claim_2['claim_id'])
        if result_2:
            print(f"Second claim processed: {result_2['status']}")
            print("Learning behavior should be demonstrated in exception handling")
            return [claim_1['claim_id'], claim_2['claim_id']]
    
    return None

def demo_scenario_3_fraud_detection():
    """
    Scenario 3: Fraud Detection - Duplicate Claim
    Submit identical claims to trigger fraud detection
    """
    print("\n=== DEMO SCENARIO 3: Fraud Detection - Duplicate Claims ===")
    
    # Original claim
    claim_data = {
        "patient_name": "Alice Brown",
        "patient_id": "PAT-004",
        "insurance_provider": "UnitedHealth",
        "policy_number": "POL-98765",
        "diagnosis_code": "S52.501A",  # Broken arm
        "procedure_code": "27447",     # Knee surgery (high value)
        "claim_amount": 15000.00,
        "service_date": date.today().isoformat(),
        "provider_name": "Dr. Robert Kim",
        "provider_npi": "5555555555",
        "notes": "Knee arthroplasty procedure"
    }
    
    print("Submitting original high-value claim...")
    claim_1 = submit_claim(claim_data)
    
    if claim_1:
        print(f"✅ Original claim submitted: {claim_1['claim_id']}")
        
        # Wait a moment then submit duplicate
        time.sleep(2)
        
        print("Submitting duplicate claim (2 hours later simulation)...")
        claim_2 = submit_claim(claim_data)  # Exact same data
        
        if claim_2:
            print(f"✅ Duplicate claim submitted: {claim_2['claim_id']}")
            
            # Process the duplicate claim
            print("Processing duplicate claim...")
            result = process_claim(claim_2['claim_id'])
            
            if result:
                print(f"Duplicate claim processed: {result['status']}")
                print(f"Fraud score: {result['fraud_score']}")
                
                # Get fraud analysis
                try:
                    fraud_response = requests.get(f"{API_BASE}/claims/{claim_2['claim_id']}/fraud-analysis")
                    if fraud_response.status_code == 200:
                        fraud_data = fraud_response.json()
                        print(f"Fraud flagged: {fraud_data['is_flagged']}")
                        print("Risk factors:")
                        for factor in fraud_data['risk_factors']:
                            print(f"  • {factor}")
                except Exception as e:
                    print(f"Error getting fraud analysis: {e}")
                
                return [claim_1['claim_id'], claim_2['claim_id']]
    
    return None

def demo_scenario_4_code_mismatch():
    """
    Scenario 4: Code Mismatch with AI Reasoning
    Submit claim with diagnosis-procedure mismatch for AI to detect and explain
    """
    print("\n=== DEMO SCENARIO 4: Code Mismatch with AI Reasoning ===")
    
    claim_data = {
        "patient_name": "Charlie Davis",
        "patient_id": "PAT-005",
        "insurance_provider": "Kaiser Permanente",
        "policy_number": "POL-11111",
        "diagnosis_code": "S52.501A",  # Broken arm
        "procedure_code": "92004",     # Eye exam (clear mismatch)
        "claim_amount": 250.00,
        "service_date": (date.today() - timedelta(days=1)).isoformat(),
        "provider_name": "Dr. Lisa White",
        "provider_npi": "7777777777",
        "notes": "Patient presented with arm fracture"
    }
    
    print("Submitting claim with diagnosis-procedure mismatch...")
    claim = submit_claim(claim_data)
    
    if claim:
        print(f"✅ Claim submitted: {claim['claim_id']}")
        print("Processing claim with AI analysis...")
        
        result = process_claim(claim['claim_id'])
        
        if result:
            print(f"Claim processed: {result['status']}")
            print(f"Decision: {result['decision']}")
            print(f"Confidence: {result['confidence_score']}%")
            print(f"AI Reasoning: {result['reasoning_text']}")
            
            if result['status'] == 'DENIED':
                print("✅ AI correctly identified the code mismatch!")
            
            return claim['claim_id']
    
    return None

def generate_additional_test_data():
    """Generate additional test claims for dashboard demonstration"""
    print("\n=== GENERATING ADDITIONAL TEST DATA ===")
    
    test_claims = [
        {
            "patient_name": "Emily Johnson",
            "patient_id": "PAT-006",
            "insurance_provider": "Humana",
            "policy_number": "POL-22222",
            "diagnosis_code": "E11.9",
            "procedure_code": "99214",
            "claim_amount": 280.00,
            "service_date": (date.today() - timedelta(days=3)).isoformat(),
            "provider_name": "Dr. Sarah Johnson",
            "provider_npi": "1234567890",
            "notes": "Diabetes follow-up"
        },
        {
            "patient_name": "David Miller",
            "patient_id": "PAT-007",
            "insurance_provider": "Anthem",
            "policy_number": "POL-33333",
            "diagnosis_code": "J06.9",
            "procedure_code": "99213",
            "claim_amount": 125.00,
            "service_date": (date.today() - timedelta(days=5)).isoformat(),
            "provider_name": "Dr. Michael Chen",
            "provider_npi": "9876543210",
            "notes": "Upper respiratory infection"
        },
        {
            "patient_name": "Susan Taylor",
            "patient_id": "PAT-008",
            "insurance_provider": "Blue Cross Blue Shield",
            "policy_number": "POL-44444",
            "diagnosis_code": "I10",
            "procedure_code": "85025",
            "claim_amount": 75.00,
            "service_date": (date.today() - timedelta(days=7)).isoformat(),
            "provider_name": "Dr. Lisa White",
            "provider_npi": "7777777777",
            "notes": "Hypertension monitoring - blood work"
        }
    ]
    
    submitted_claims = []
    
    for i, claim_data in enumerate(test_claims):
        print(f"Submitting test claim {i+1}...")
        claim = submit_claim(claim_data)
        
        if claim:
            submitted_claims.append(claim['claim_id'])
            
            # Process every other claim
            if i % 2 == 0:
                print(f"Processing claim {claim['claim_id']}...")
                process_claim(claim['claim_id'])
    
    print(f"✅ Generated {len(submitted_claims)} additional test claims")
    return submitted_claims

def main():
    """Run all demo scenarios"""
    print("🏥 FLOWGENIX DEMO SCENARIOS GENERATOR")
    print("=" * 50)
    
    # Check API health
    if not check_api_health():
        print("❌ API is not running. Please start the backend server first.")
        print("Run: cd backend && python main.py")
        return
    
    print("✅ API is running")
    
    # Run all demo scenarios
    scenarios = {
        "Happy Path": demo_scenario_1_happy_path,
        "Exception Learning": demo_scenario_2_exception_learning,
        "Fraud Detection": demo_scenario_3_fraud_detection,
        "Code Mismatch": demo_scenario_4_code_mismatch
    }
    
    results = {}
    
    for name, func in scenarios.items():
        try:
            result = func()
            results[name] = result
            time.sleep(1)  # Brief pause between scenarios
        except Exception as e:
            print(f"❌ Error in {name} scenario: {e}")
            results[name] = None
    
    # Generate additional test data
    try:
        additional_claims = generate_additional_test_data()
        results["Additional Test Data"] = additional_claims
    except Exception as e:
        print(f"❌ Error generating additional test data: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DEMO SCENARIOS SUMMARY")
    print("=" * 50)
    
    for scenario, result in results.items():
        if result:
            if isinstance(result, list):
                print(f"✅ {scenario}: {len(result)} claims created")
                for claim_id in result:
                    print(f"   - {claim_id}")
            else:
                print(f"✅ {scenario}: {result}")
        else:
            print(f"❌ {scenario}: Failed")
    
    print("\n🎯 Demo scenarios are ready!")
    print("You can now:")
    print("1. Open the Streamlit dashboard: streamlit run frontend/app.py")
    print("2. View the claims in the dashboard")
    print("3. Use the '🤖 Agent Processing' page to see multi-agent collaboration")
    print("4. Demonstrate the 4 key scenarios during your presentation")
    print("\n🤖 AGENTIC AI FEATURES TO HIGHLIGHT:")
    print("• Multi-agent collaboration with specialized agents")
    print("• Real-time agent reasoning visualization (ReAct pattern)")
    print("• Autonomous tool selection and execution")
    print("• Agent communication and handoffs")
    print("• Explainable AI with transparent decision making")
    print("\nAPI Documentation available at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()