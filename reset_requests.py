import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM requests")
cursor.execute("DELETE FROM sqlite_sequence WHERE name='requests'")

conn.commit()
conn.close()

print("Таблица requests очищена, автоинкремент сброшен")
