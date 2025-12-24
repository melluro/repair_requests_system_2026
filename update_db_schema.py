import sqlite3
from database import DB_NAME

def migrate():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(requests)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "help_needed" not in columns:
            print("Adding help_needed column to requests table...")
            cursor.execute("ALTER TABLE requests ADD COLUMN help_needed INTEGER DEFAULT 0")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column help_needed already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
