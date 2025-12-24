import csv
import sqlite3
import datetime
import os
from pathlib import Path
from database import get_connection, init_db

# Mappings
ROLE_MAP = {
    "Администратор": 1,
    "Оператор": 2,
    "Специалист": 3,
    "Менеджер": 4,
    "Менеджер по качеству": 5
    # "Заказчик" handled separately
}

STATUS_MAP = {
    "Новая заявка": 1,       # New
    "В процессе ремонта": 3, # In Progress
    "Готова к выдаче": 5,    # Completed (Close enough)
    "Завершена": 5,
    "Ожидание запчастей": 4
}
# Default to New if unknown

def parse_date(date_str):
    if not date_str or date_str.lower() == 'null':
        return None
    try:
        # Try YYYY-MM-DD
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def run_import(base_dir: str = None):
    if base_dir is None:
        base_dir = os.environ.get("IMPORT_DIR", "import_БытСервис")
    base_path = Path(base_dir)
    users_csv = base_path / "Пользователи" / "inputDataUsers.csv"
    requests_csv = base_path / "Заявки" / "inputDataRequests.csv"
    comments_csv = base_path / "Комментарии" / "inputDataComments.csv"

    if not users_csv.exists():
        raise FileNotFoundError(f"Не найден файл пользователей: {users_csv}")
    if not requests_csv.exists():
        raise FileNotFoundError(f"Не найден файл заявок: {requests_csv}")
    if not comments_csv.exists():
        raise FileNotFoundError(f"Не найден файл комментариев: {comments_csv}")

    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM comments")
    cursor.execute("DELETE FROM request_specialists")
    cursor.execute("DELETE FROM requests")
    cursor.execute("DELETE FROM equipment")
    cursor.execute("DELETE FROM clients")
    cursor.execute("DELETE FROM users")
    conn.commit()
    
    # ID Mappings (Old CSV ID -> New DB ID)
    user_id_map = {}   # For employees
    client_id_map = {} # For clients
    request_id_map = {} 

    print("Importing Users and Clients...")
    with users_csv.open('r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            old_id = row['userID']
            fio = row['fio']
            phone = row['phone']
            login = row['login']
            password = row['password']
            role_type = row['type']
            
            if role_type == "Заказчик":
                # Check if exists by phone to avoid duplicates
                cursor.execute("SELECT id FROM clients WHERE phone = ?", (phone,))
                existing = cursor.fetchone()
                if existing:
                    client_id_map[old_id] = existing[0]
                else:
                    cursor.execute("INSERT INTO clients (full_name, phone) VALUES (?, ?)", (fio, phone))
                    client_id_map[old_id] = cursor.lastrowid
            else:
                # Employee
                role_id = ROLE_MAP.get(role_type, 2) # Default to Operator
                
                # Check duplicate login
                cursor.execute("SELECT id FROM users WHERE username = ?", (login,))
                existing = cursor.fetchone()
                if existing:
                    user_id_map[old_id] = existing[0]
                else:
                    cursor.execute("INSERT INTO users (username, password, full_name, role_id) VALUES (?, ?, ?, ?)",
                                   (login, password, fio, role_id))
                    user_id_map[old_id] = cursor.lastrowid

    print("Importing Requests...")
    with requests_csv.open('r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            old_req_id = row['requestID']
            start_date = parse_date(row['startDate'])
            tech_type = row['climateTechType']
            model = row['climateTechModel']
            desc = row['problemDescryption']
            status_str = row['requestStatus']
            comp_date = parse_date(row['completionDate'])
            master_id = row['masterID'] # Old user ID
            client_id_old = row['clientID'] # Old user ID (Client)
            
            # Resolve Client
            real_client_id = client_id_map.get(client_id_old)
            if not real_client_id:
                print(f"Skipping request {old_req_id}: Client {client_id_old} not found")
                continue
                
            # Create Equipment (One per request for this data model as we don't have unique serials)
            # Generate dummy serial
            serial = f"LEGACY-{old_req_id}"
            cursor.execute("INSERT INTO equipment (serial_number, model, type, client_id) VALUES (?, ?, ?, ?)",
                           (serial, model, tech_type, real_client_id))
            eq_id = cursor.lastrowid
            
            # Map Status
            status_id = STATUS_MAP.get(status_str, 1) # Default New
            
            # Deadline: Start + 7 days
            deadline = None
            if start_date:
                dt = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
                deadline = (dt + datetime.timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            
            # Create Request
            req_number = f"REQ-OLD-{old_req_id}"
            cursor.execute("""
                INSERT INTO requests (request_number, creation_date, problem_description, client_id, equipment_id, status_id, completion_date, deadline_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (req_number, start_date, desc, real_client_id, eq_id, status_id, comp_date, deadline))
            new_req_id = cursor.lastrowid
            request_id_map[old_req_id] = new_req_id
            
            # Assign Specialist
            real_master_id = user_id_map.get(master_id)
            if real_master_id:
                try:
                    cursor.execute("INSERT INTO request_specialists (request_id, specialist_id) VALUES (?, ?)",
                                   (new_req_id, real_master_id))
                except sqlite3.IntegrityError:
                    pass

    print("Importing Comments...")
    try:
        with comments_csv.open('r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                msg = row['message']
                master_id_old = row['masterID']
                req_id_old = row['requestID']

                real_user_id = user_id_map.get(master_id_old)
                real_req_id = request_id_map.get(req_id_old)

                if real_user_id and real_req_id:
                    cursor.execute("INSERT INTO comments (request_id, user_id, text, created_at) VALUES (?, ?, ?, ?)",
                                   (real_req_id, real_user_id, msg, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    except FileNotFoundError:
        print("Comments file not found, skipping.")

    conn.commit()
    conn.close()
    print("Import completed successfully.")

if __name__ == "__main__":
    run_import()
