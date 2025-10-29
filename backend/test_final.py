import requests
import json

# Login first
login_data = {'email_or_username': 'admin@demo.com', 'password': 'admin123'}
login_response = requests.post('http://localhost:8000/auth/login', json=login_data)

if login_response.status_code == 200:
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Submit a fresh test claim
    claim_data = {
        'patient_name': 'Agent Timeline Success',
        'patient_id': 'PAT-SUCCESS',
        'insurance_provider': 'Success Insurance',
        'policy_number': 'POL-SUCCESS-001',
        'diagnosis_code': 'I25.10',
        'procedure_code': '93000',
        'claim_amount': 400.00,
        'service_date': '2024-10-28',
        'provider_name': 'Success Provider',
        'provider_npi': '1234567890',
        'notes': 'Final test claim to verify complete agent timeline functionality'
    }
    
    print('📤 Submitting final test claim...')
    response = requests.post('http://localhost:8000/api/claims/submit', json=claim_data, headers=headers)
    if response.status_code == 200:
        data = response.json()
        claim_id = data['claim_id']
        print(f'✅ Claim submitted: {claim_id}')
        
        # Now check the agent timeline for this fresh claim
        timeline_response = requests.get(f'http://localhost:8000/api/claims/{claim_id}/agent-timeline', headers=headers)
        if timeline_response.status_code == 200:
            timeline_data = timeline_response.json()
            print(f'📊 Timeline for new claim {claim_id}:')
            agents_count = len(timeline_data["agents"])
            print(f'  - Total agents: {agents_count}')
            print(f'  - Processing time: {timeline_data["total_processing_time"]}s')
            print(f'  - Final decision: {timeline_data["final_decision"]}')
            
            if agents_count > 0:
                print('🎉 SUCCESS! Agent timeline is working end-to-end!')
            else:
                print('❌ No agents found - something is still wrong')
        else:
            print(f'❌ Timeline error: {timeline_response.status_code} - {timeline_response.text}')
    else:
        print(f'❌ Submit error: {response.status_code} - {response.text}')
else:
    print(f'❌ Login error: {login_response.status_code} - {login_response.text}')