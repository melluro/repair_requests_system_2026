import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Удаляем старую таблицу
cursor.execute("DROP TABLE IF EXISTS users")

# Создаём новую
cursor.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("Таблица users создана заново!")
