import sqlite3
from datetime import datetime, timedelta
from database import get_connection
from models import User, Request, Client, Equipment, Comment, Part
import csv

# Status Constants
STATUS_NEW = 1
STATUS_REGISTERED = 2
STATUS_IN_PROGRESS = 3
STATUS_WAITING_PARTS = 4
STATUS_COMPLETED = 5
STATUS_OVERDUE = 6

class UserService:
    @staticmethod
    def login(username, password):
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT u.id, u.username, u.full_name, u.role_id, r.name 
            FROM users u 
            JOIN roles r ON u.role_id = r.id 
            WHERE u.username = ? AND u.password = ?
        """
        cursor.execute(query, (username, password))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                id=row[0], 
                username=row[1], 
                full_name=row[2], 
                role_id=row[3], 
                role_name=row[4]
            )
        return None

    @staticmethod
    def get_all_users():
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT u.id, u.username, u.full_name, u.role_id, r.name 
            FROM users u 
            JOIN roles r ON u.role_id = r.id
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        users = []
        for row in rows:
            users.append(User(
                id=row[0], 
                username=row[1], 
                full_name=row[2], 
                role_id=row[3], 
                role_name=row[4]
            ))
        return users

    @staticmethod
    def create_user(username, password, full_name, role_id):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, full_name, role_id) VALUES (?, ?, ?, ?)",
                (username, password, full_name, role_id)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
            
    @staticmethod
    def get_specialists():
        conn = get_connection()
        cursor = conn.cursor()
        # Role 3 is Specialist
        query = "SELECT id, full_name FROM users WHERE role_id = 3"
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return rows

class RequestService:
    @staticmethod
    def create_request(client_data, equipment_data, problem_desc):
        # client_data: (full_name, phone)
        # equipment_data: (serial, model, type)
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Create or Get Client
            cursor.execute("SELECT id FROM clients WHERE phone = ?", (client_data[1],))
            client_row = cursor.fetchone()
            if client_row:
                client_id = client_row[0]
            else:
                cursor.execute("INSERT INTO clients (full_name, phone) VALUES (?, ?)", client_data)
                client_id = cursor.lastrowid
                
            # 2. Create Equipment
            # Check if exists by serial, else create
            cursor.execute("SELECT id FROM equipment WHERE serial_number = ?", (equipment_data[0],))
            eq_row = cursor.fetchone()
            if eq_row:
                equipment_id = eq_row[0]
            else:
                cursor.execute(
                    "INSERT INTO equipment (serial_number, model, type, client_id) VALUES (?, ?, ?, ?)",
                    (equipment_data[0], equipment_data[1], equipment_data[2], client_id)
                )
                equipment_id = cursor.lastrowid
                
            # 3. Create Request
            req_number = f"REQ-{int(datetime.now().timestamp())}"
            # Default deadline: 7 days
            deadline = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                INSERT INTO requests (request_number, creation_date, problem_description, client_id, equipment_id, status_id, deadline_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (req_number, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), problem_desc, client_id, equipment_id, STATUS_NEW, deadline)
            )
            conn.commit()
            return req_number
        except Exception as e:
            print(f"Error creating request: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    @staticmethod
    def get_requests(user_role, user_id, filter_status=None):
        conn = get_connection()
        cursor = conn.cursor()
        
        base_query = """
            SELECT r.id, r.request_number, r.creation_date, r.problem_description, 
                   r.client_id, r.equipment_id, r.status_id, s.name as status_name,
                   c.full_name as client_name, c.phone as client_phone, e.model as eq_model, r.completion_date, r.deadline_date, r.help_needed
            FROM requests r
            JOIN statuses s ON r.status_id = s.id
            JOIN clients c ON r.client_id = c.id
            JOIN equipment e ON r.equipment_id = e.id
        """
        
        params = []
        where_clauses = []
        
        # Role based filtering
        if user_role == 'Specialist':
            # Only assigned requests
            base_query += " JOIN request_specialists rs ON r.id = rs.request_id"
            where_clauses.append("rs.specialist_id = ?")
            params.append(user_id)
            
        if filter_status:
            where_clauses.append("r.status_id = ?")
            params.append(filter_status)
            
        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)
            
        base_query += " ORDER BY r.help_needed DESC, r.creation_date DESC"
        
        cursor.execute(base_query, tuple(params))
        rows = cursor.fetchall()
        
        requests = []
        for row in rows:
            req = Request(
                id=row[0],
                request_number=row[1],
                creation_date=row[2],
                problem_description=row[3],
                client_id=row[4],
                equipment_id=row[5],
                status_id=row[6],
                status_name=row[7],
                client_name=row[8],
                client_phone=row[9],
                equipment_model=row[10],
                completion_date=row[11],
                deadline_date=row[12],
                help_needed=bool(row[13])
            )
            # Fetch assigned specialists
            cursor.execute("""
                SELECT u.full_name FROM users u
                JOIN request_specialists rs ON u.id = rs.specialist_id
                WHERE rs.request_id = ?
            """, (req.id,))
            specs = cursor.fetchall()
            req.assigned_specialists = [s[0] for s in specs]
            requests.append(req)
            
        conn.close()
        return requests

    @staticmethod
    def update_status(request_id, new_status_id):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            update_query = "UPDATE requests SET status_id = ?"
            params = [new_status_id]
            
            if new_status_id == STATUS_COMPLETED:
                update_query += ", completion_date = ?"
                params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                
            update_query += " WHERE id = ?"
            params.append(request_id)
            
            cursor.execute(update_query, tuple(params))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating status: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def assign_specialist(request_id, specialist_id):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO request_specialists (request_id, specialist_id) VALUES (?, ?)",
                (request_id, specialist_id)
            )
            # Update status to Registered or In Progress if New
            cursor.execute("UPDATE requests SET status_id = ? WHERE id = ? AND status_id = ?", 
                           (STATUS_REGISTERED, request_id, STATUS_NEW))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # Already assigned
        finally:
            conn.close()

    @staticmethod
    def extend_deadline(request_id, days):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT deadline_date FROM requests WHERE id = ?", (request_id,))
            current = cursor.fetchone()[0]
            if current:
                new_date = datetime.strptime(current, "%Y-%m-%d %H:%M:%S") + timedelta(days=days)
                cursor.execute("UPDATE requests SET deadline_date = ? WHERE id = ?", 
                               (new_date.strftime("%Y-%m-%d %H:%M:%S"), request_id))
                conn.commit()
                return True
            return False
        except Exception as e:
            print(f"Error extending deadline: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def add_comment(request_id, user_id, text):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO comments (request_id, user_id, text, created_at) VALUES (?, ?, ?, ?)",
            (request_id, user_id, text, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_comments(request_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.request_id, c.user_id, c.text, c.created_at, u.full_name
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.request_id = ?
            ORDER BY c.created_at ASC
        """, (request_id,))
        rows = cursor.fetchall()
        conn.close()
        return [Comment(id=r[0], request_id=r[1], user_id=r[2], text=r[3], created_at=r[4], user_name=r[5]) for r in rows]

    @staticmethod
    def toggle_help_needed(request_id, needed: bool):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE requests SET help_needed = ? WHERE id = ?", (1 if needed else 0, request_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error toggling help: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def update_deadline(request_id, new_date_str):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE requests SET deadline_date = ? WHERE id = ?", (new_date_str, request_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating deadline: {e}")
            return False
        finally:
            conn.close()

class PartService:
    @staticmethod
    def get_all_parts():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, stock_quantity, price FROM parts")
        rows = cursor.fetchall()
        conn.close()
        return [Part(id=r[0], name=r[1], stock_quantity=r[2], price=r[3]) for r in rows]

    @staticmethod
    def add_part(name, stock, price):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO parts (name, stock_quantity, price) VALUES (?, ?, ?)", (name, stock, price))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    @staticmethod
    def assign_part_to_request(request_id, part_id, quantity):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Check stock
            cursor.execute("SELECT stock_quantity FROM parts WHERE id = ?", (part_id,))
            stock = cursor.fetchone()[0]
            if stock < quantity:
                return False, "Not enough stock"

            # Deduct stock
            cursor.execute("UPDATE parts SET stock_quantity = stock_quantity - ? WHERE id = ?", (quantity, part_id))
            
            # Add to request (or update if exists)
            cursor.execute("SELECT quantity FROM request_parts WHERE request_id = ? AND part_id = ?", (request_id, part_id))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("UPDATE request_parts SET quantity = quantity + ? WHERE request_id = ? AND part_id = ?", 
                               (quantity, request_id, part_id))
            else:
                cursor.execute("INSERT INTO request_parts (request_id, part_id, quantity) VALUES (?, ?, ?)", 
                               (request_id, part_id, quantity))
            
            conn.commit()
            return True, "Part assigned"
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def get_parts_for_request(request_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.name, p.stock_quantity, p.price, rp.quantity
            FROM parts p
            JOIN request_parts rp ON p.id = rp.part_id
            WHERE rp.request_id = ?
        """, (request_id,))
        rows = cursor.fetchall()
        conn.close()
        return [Part(id=r[0], name=r[1], stock_quantity=r[2], price=r[3], quantity_used=r[4]) for r in rows]

class ImportService:
    @staticmethod
    def import_users_from_csv(file_path):
        # Format: username,password,full_name,role_id
        count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None) # Skip header
                for row in reader:
                    if len(row) >= 4:
                        if UserService.create_user(row[0], row[1], row[2], int(row[3])):
                            count += 1
            return True, f"Imported {count} users"
        except Exception as e:
            return False, str(e)
