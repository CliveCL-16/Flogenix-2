import requests

# Check if this claim exists in the database
login_data = {'email_or_username': 'admin@demo.com', 'password': 'admin123'}
auth_response = requests.post('http://localhost:8000/auth/login', json=login_data)
token = auth_response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Try to get the claim details from the main API
claim_id = 'CLM-EC152B96'
print(f'Checking claim {claim_id}...')

detail_response = requests.get(f'http://localhost:8000/api/claims/{claim_id}', headers=headers)
if detail_response.status_code == 200:
    claim = detail_response.json()
    print('✅ Claim found in database:')
    print(f'   Available fields: {list(claim.keys())}')
    print(f'   Status: {claim.get("status", "N/A")}')
    print(f'   Patient: {claim.get("patient_name", "N/A")}')
    print(f'   Amount: ${claim.get("claim_amount", "N/A")}')
else:
    print(f'❌ Claim not found: {detail_response.status_code}')
    print(f'   Error: {detail_response.text[:200]}')

# Now test the agent-timeline endpoint
print('\nTesting agent-timeline endpoint...')
timeline_response = requests.get(f'http://localhost:8000/api/claims/{claim_id}/agent-timeline', headers=headers)
print(f'Agent timeline: {timeline_response.status_code}')
if timeline_response.status_code != 200:
    print(f'   Error: {timeline_response.text[:200]}')
else:
    timeline = timeline_response.json()
    print(f'   ✅ Timeline found with {len(timeline.get("agents", []))} agents')