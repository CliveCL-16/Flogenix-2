import requests

# Login first
login_data = {'email_or_username': 'admin@demo.com', 'password': 'admin123'}
login_response = requests.post('http://localhost:8000/auth/login', json=login_data)

if login_response.status_code == 200:
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Check the agent timeline for the claim we just processed
    claim_id = 'CLM-F04650CE'
    timeline_response = requests.get(f'http://localhost:8000/api/claims/{claim_id}/agent-timeline', headers=headers)
    
    if timeline_response.status_code == 200:
        timeline_data = timeline_response.json()
        print(f'✅ Agent timeline for {claim_id}:')
        agents_count = len(timeline_data["agents"])
        print(f'📊 Total agents: {agents_count}')
        print(f'⏱️ Total processing time: {timeline_data["total_processing_time"]}s')
        print(f'🎯 Final decision: {timeline_data["final_decision"]}')
        
        # Show first few agents
        for i, agent in enumerate(timeline_data["agents"][:5]):
            print(f'  {i+1}. {agent["agent"]}: {agent["status"]} ({agent["duration"]}s)')
            print(f'     Result: {agent["result"][:50]}...')
    else:
        print(f'❌ Timeline error: {timeline_response.status_code} - {timeline_response.text}')
else:
    print(f'❌ Login error: {login_response.status_code} - {login_response.text}')