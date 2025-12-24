import sqlite3
import csv
import os
import sys
from datetime import datetime

# Add current directory to path to allow imports
sys.path.append(os.getcwd())

import database

DB_NAME = "repair_system.db"
IMPORT_DIR = "import_БытСервис"

def get_db_connection():
    return sqlite3.connect(DB_NAME)

def get_role_id(cursor, role_name):
    cursor.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    return None

def get_status_id(cursor, status_name):
    # Try exact match first
    cursor.execute("SELECT id FROM statuses WHERE name = ?", (status_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    
    # Map CSV status to DB status
    mapping = {
        "Новая заявка": "New",
        "В процессе ремонта": "In Progress",
        "Готова к выдаче": "Completed",
        "Ожидание запчастей": "Waiting for Parts"
    }
    mapped_name = mapping.get(status_name)
    if mapped_name:
        cursor.execute("SELECT id FROM statuses WHERE name = ?", (mapped_name,))
        result = cursor.fetchone()
        if result:
            return result[0]
            
    # Default to 'Registered' or 'New' if unknown
    cursor.execute("SELECT id FROM statuses WHERE name = 'New'")
    return cursor.fetchone()[0]

def run_import():
    print("Initializing database...")
    database.init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear seeded users to avoid confusion, but keep admin?
    # Actually, let's keep seeded users (ids 1-5). 
    # Imported users will get new IDs starting from 6.
    
    user_map = {}   # csv_userID -> db_id
    client_map = {} # csv_userID -> db_id
    request_map = {} # csv_requestID -> db_id
    
    # 1. Import Users
    users_file = os.path.join(IMPORT_DIR, "Пользователи", "inputDataUsers.csv")
    print(f"Importing users from {users_file}...")
    
    with open(users_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            user_id_csv = row['userID']
            fio = row['fio']
            phone = row['phone']
            login = row['login']
            password = row['password']
            user_type = row['type']
            
            if user_type == "Заказчик":
                cursor.execute("INSERT INTO clients (full_name, phone) VALUES (?, ?)", (fio, phone))
                client_map[user_id_csv] = cursor.lastrowid
            else:
                # Map role
                role_name = "Specialist" # Default
                if user_type == "Менеджер":
                    role_name = "Manager"
                elif user_type == "Оператор":
                    role_name = "Operator"
                elif user_type == "Мастер":
                    role_name = "Specialist"
                
                role_id = get_role_id(cursor, role_name)
                
                # Check if username exists (seeded users might conflict by username)
                cursor.execute("SELECT id FROM users WHERE username = ?", (login,))
                existing = cursor.fetchone()
                if existing:
                    print(f"User {login} already exists (seeded). Mapping CSV ID {user_id_csv} to DB ID {existing[0]}")
                    user_map[user_id_csv] = existing[0]
                else:
                    cursor.execute("INSERT INTO users (username, password, full_name, role_id) VALUES (?, ?, ?, ?)",
                                   (login, password, fio, role_id))
                    user_map[user_id_csv] = cursor.lastrowid

    # 2. Import Requests
    requests_file = os.path.join(IMPORT_DIR, "Заявки", "inputDataRequests.csv")
    print(f"Importing requests from {requests_file}...")
    
    with open(requests_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            req_id_csv = row['requestID']
            start_date = row['startDate']
            tech_type = row.get('homeTechType') or row.get('climateTechType') # Handle potential column name diff
            tech_model = row.get('homeTechModel') or row.get('climateTechModel')
            problem = row.get('problemDescryption') or row.get('problemDescription')
            status_str = row['requestStatus']
            completion_date = row['completionDate']
            if completion_date == 'null': completion_date = None
            
            master_id_csv = row['masterID']
            client_id_csv = row['clientID']
            
            # Resolve Client
            client_id = client_map.get(client_id_csv)
            if not client_id:
                print(f"Warning: Client ID {client_id_csv} not found for request {req_id_csv}. Skipping.")
                continue
                
            # Create Equipment
            # Generate a serial number since CSV doesn't have it
            serial_number = f"SN-{req_id_csv}-{int(datetime.now().timestamp())}"
            cursor.execute("INSERT INTO equipment (serial_number, model, type, client_id) VALUES (?, ?, ?, ?)",
                           (serial_number, tech_model, tech_type, client_id))
            equipment_id = cursor.lastrowid
            
            # Resolve Status
            status_id = get_status_id(cursor, status_str)
            
            # Insert Request
            cursor.execute("""
                INSERT INTO requests (request_number, creation_date, problem_description, client_id, equipment_id, status_id, completion_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (req_id_csv, start_date, problem, client_id, equipment_id, status_id, completion_date))
            
            new_req_id = cursor.lastrowid
            request_map[req_id_csv] = new_req_id
            
            # Assign Specialist
            if master_id_csv and master_id_csv != 'null':
                specialist_id = user_map.get(master_id_csv)
                if specialist_id:
                    cursor.execute("INSERT INTO request_specialists (request_id, specialist_id) VALUES (?, ?)",
                                   (new_req_id, specialist_id))
                else:
                    print(f"Warning: Master ID {master_id_csv} not found for request {req_id_csv}")

    # 3. Import Comments
    comments_file = os.path.join(IMPORT_DIR, "Комментарии", "inputDataComments.csv")
    print(f"Importing comments from {comments_file}...")
    
    with open(comments_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            msg = row['message']
            master_id_csv = row['masterID']
            req_id_csv = row['requestID']
            
            req_id = request_map.get(req_id_csv)
            user_id = user_map.get(master_id_csv)
            
            if req_id and user_id:
                # Use current time for created_at as it's missing in CSV
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("INSERT INTO comments (request_id, user_id, text, created_at) VALUES (?, ?, ?, ?)",
                               (req_id, user_id, msg, created_at))
            else:
                if not req_id:
                    print(f"Warning: Request ID {req_id_csv} not found for comment.")
                if not user_id:
                    print(f"Warning: User ID {master_id_csv} not found for comment.")

    conn.commit()
    conn.close()
    print("Import completed successfully.")

if __name__ == "__main__":
    run_import()
