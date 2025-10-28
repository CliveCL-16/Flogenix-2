"""
Quick test script to verify the Flogenix API is working
"""

import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Flogenix API...")
    print("-" * 40)
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Root endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Test claims endpoint
    try:
        response = requests.get(f"{base_url}/api/claims")
        if response.status_code == 200:
            claims = response.json()
            print(f"✅ Claims endpoint working - found {len(claims)} claims")
            for claim in claims:
                print(f"   - {claim['claim_id']}: {claim['patient_name']} (${claim['claim_amount']})")
        else:
            print(f"❌ Claims endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Claims endpoint error: {e}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    print("-" * 40)
    print("🎯 Test complete")

if __name__ == "__main__":
    test_api()