import sqlite3

# Check both database files
databases = ['enterprise_healthcare.db', 'flogenix_enterprise.db']

for db_name in databases:
    print(f'\n=== Checking {db_name} ===')
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        print(f'Found {len(tables)} tables:')
        for table in tables:
            print(f'  - {table[0]}')

        # If agent_reports exists, check its structure
        if any('agent_reports' in str(table) for table in tables):
            cursor.execute("PRAGMA table_info(agent_reports)")
            columns = cursor.fetchall()
            print('\nAgentReports table structure:')
            for col in columns:
                print(f'  - {col[1]} ({col[2]})')

        conn.close()
    except Exception as e:
        print(f'Error accessing {db_name}: {e}')