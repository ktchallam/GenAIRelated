import sqlite3

# Create or connect to a database file
conn = sqlite3.connect("mydatabase.db")

# Create a table (optional)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT
)
""")

conn.commit()
conn.close()

print("Database created!")
