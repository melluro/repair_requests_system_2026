import sqlite3
import os

db_path = "repair_system.db"

if not os.path.exists(db_path):
    print(f"Database file {db_path} does not exist!")
else:
    print(f"Database file found at {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check Users
        cursor.execute("SELECT count(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"Users count: {user_count}")
        
        # Check Requests
        cursor.execute("SELECT count(*) FROM requests")
        request_count = cursor.fetchone()[0]
        print(f"Requests count: {request_count}")
        
        cursor.execute("""
            SELECT r.id, r.request_number, c.full_name as client_name, s.name as status_name 
            FROM requests r
            JOIN clients c ON r.client_id = c.id
            JOIN statuses s ON r.status_id = s.id
            LIMIT 5
        """)
        requests = cursor.fetchall()
        print("First 5 requests:", requests)
        
        conn.close()
    except Exception as e:
        print(f"Error reading database: {e}")
