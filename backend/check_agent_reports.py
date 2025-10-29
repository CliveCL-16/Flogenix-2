import sqlite3

# Check agent reports in the correct database
conn = sqlite3.connect('flogenix_enterprise.db')
cursor = conn.cursor()

# Count total agent reports
cursor.execute('SELECT COUNT(*) FROM agent_reports')
total_count = cursor.fetchone()[0]
print(f'Total agent reports in database: {total_count}')

# Get recent agent reports
cursor.execute('''
SELECT claim_id, agent_name, agent_type, status, result, completed_at 
FROM agent_reports 
ORDER BY completed_at DESC LIMIT 20
''')
reports = cursor.fetchall()

if reports:
    print('\nRecent agent reports:')
    for report in reports:
        print(f'  - Claim: {report[0]}, Agent: {report[1]}, Type: {report[2]}, Status: {report[3]}, Time: {report[5]}')
        print(f'    Result: {report[4][:50]}...')
else:
    print('No agent reports found')

# Check which claims we have
cursor.execute('SELECT claim_id, status, patient_name FROM claims ORDER BY created_at DESC LIMIT 10')
claims = cursor.fetchall()
print(f'\nRecent claims ({len(claims)}):')
for claim in claims:
    print(f'  - {claim[0]}: {claim[1]} - {claim[2]}')

conn.close()