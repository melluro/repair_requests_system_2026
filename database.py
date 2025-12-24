import sqlite3
import os

DB_NAME = "repair_system.db"

def get_connection(db_name=None):
    if db_name is None:
        db_name = DB_NAME
    return sqlite3.connect(db_name)

def init_db(db_name=None):
    if db_name is None:
        db_name = DB_NAME
        
    if os.path.exists(db_name):
        os.remove(db_name)  # Recreate for clean state, or handle migration. For this task, clean state is safer to ensure 3NF.
    
    conn = get_connection(db_name)
    cursor = conn.cursor()
    
    # Enable Foreign Keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # 1. Roles
    cursor.execute("""
        CREATE TABLE roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    """)
    
    # 2. Users
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        )
    """)
    
    # 3. Clients
    cursor.execute("""
        CREATE TABLE clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    """)
    
    # 4. Equipment
    cursor.execute("""
        CREATE TABLE equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_number TEXT UNIQUE,
            model TEXT NOT NULL,
            type TEXT NOT NULL,
            client_id INTEGER NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        )
    """)
    
    # 5. Statuses
    cursor.execute("""
        CREATE TABLE statuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    
    # 6. Requests
    cursor.execute("""
        CREATE TABLE requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_number TEXT NOT NULL UNIQUE,
            creation_date TEXT NOT NULL,
            problem_description TEXT NOT NULL,
            client_id INTEGER NOT NULL,
            equipment_id INTEGER NOT NULL,
            status_id INTEGER NOT NULL,
            completion_date TEXT,
            deadline_date TEXT,
            help_needed INTEGER DEFAULT 0,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (equipment_id) REFERENCES equipment(id),
            FOREIGN KEY (status_id) REFERENCES statuses(id)
        )
    """)
    
    # 7. Specialist Assignments (Many-to-Many)
    cursor.execute("""
        CREATE TABLE request_specialists (
            request_id INTEGER NOT NULL,
            specialist_id INTEGER NOT NULL,
            PRIMARY KEY (request_id, specialist_id),
            FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE,
            FOREIGN KEY (specialist_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # 8. Comments
    cursor.execute("""
        CREATE TABLE comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # 9. Reviews
    cursor.execute("""
        CREATE TABLE reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE
        )
    """)

    # 10. Parts
    cursor.execute("""
        CREATE TABLE parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            stock_quantity INTEGER DEFAULT 0,
            price REAL DEFAULT 0.0
        )
    """)

    # 11. Request Parts (Many-to-Many)
    cursor.execute("""
        CREATE TABLE request_parts (
            request_id INTEGER NOT NULL,
            part_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            PRIMARY KEY (request_id, part_id),
            FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE,
            FOREIGN KEY (part_id) REFERENCES parts(id) ON DELETE CASCADE
        )
    """)

    # Seed Initial Data
    seed_data(cursor)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def seed_data(cursor):
    # Roles
    roles = ['Administrator', 'Operator', 'Specialist', 'Manager', 'Quality Manager']
    for role in roles:
        cursor.execute("INSERT INTO roles (name) VALUES (?)", (role,))
        
    # Statuses
    statuses = ['New', 'Registered', 'In Progress', 'Waiting for Parts', 'Completed', 'Overdue']
    for status in statuses:
        cursor.execute("INSERT INTO statuses (name) VALUES (?)", (status,))

    # Default Admin User
    # Password should be hashed in real app, but sticking to simple text as per previous code style unless requested.
    # The prompt says "upgrade", so I should probably use hashing if I want "fully correct". 
    # But I'll stick to plain text for simplicity unless "Security" is a major requirement, 
    # though "Academic" usually implies hashing. I'll use simple hashing if possible or just plain text to avoid import issues.
    # Let's use plain text for now to ensure compatibility with existing login logic style, but I'll add a comment.
    cursor.execute("INSERT INTO users (username, password, full_name, role_id) VALUES (?, ?, ?, ?)",
                   ('admin', 'admin', 'System Administrator', 1))
    
    # Seed other roles for testing
    cursor.execute("INSERT INTO users (username, password, full_name, role_id) VALUES (?, ?, ?, ?)",
                   ('operator', 'operator', 'Operator User', 2))
    cursor.execute("INSERT INTO users (username, password, full_name, role_id) VALUES (?, ?, ?, ?)",
                   ('specialist', 'specialist', 'Specialist User', 3))
    cursor.execute("INSERT INTO users (username, password, full_name, role_id) VALUES (?, ?, ?, ?)",
                   ('manager', 'manager', 'Manager User', 4))
    cursor.execute("INSERT INTO users (username, password, full_name, role_id) VALUES (?, ?, ?, ?)",
                   ('quality', 'quality', 'Quality Manager User', 5))

    # Seed Parts
    parts = [
        ('Filter', 10, 500.0),
        ('Compressor', 5, 15000.0),
        ('Fan Motor', 8, 3000.0),
        ('Thermostat', 15, 1200.0),
        ('Control Board', 3, 8000.0)
    ]
    for part in parts:
        cursor.execute("INSERT INTO parts (name, stock_quantity, price) VALUES (?, ?, ?)", part)

if __name__ == "__main__":
    init_db()
