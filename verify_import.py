import sqlite3
from database import DB_NAME

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

print("--- Verification Results ---")

# Users
cursor.execute("SELECT count(*) FROM users")
print(f"Users count: {cursor.fetchone()[0]}")

# Clients
cursor.execute("SELECT count(*) FROM clients")
print(f"Clients count: {cursor.fetchone()[0]}")

# Requests
cursor.execute("SELECT count(*) FROM requests")
print(f"Requests count: {cursor.fetchone()[0]}")

# Comments
cursor.execute("SELECT count(*) FROM comments")
print(f"Comments count: {cursor.fetchone()[0]}")

# Equipment
cursor.execute("SELECT count(*) FROM equipment")
print(f"Equipment count: {cursor.fetchone()[0]}")

print("\n--- Sample Requests ---")
cursor.execute("SELECT request_number, problem_description FROM requests LIMIT 3")
for row in cursor.fetchall():
    print(row)

print("\n--- Sample Comments ---")
cursor.execute("SELECT text FROM comments LIMIT 3")
for row in cursor.fetchall():
    print(row)

conn.close()
