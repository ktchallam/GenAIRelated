# server.py
import sqlite3
from fastmcp import FastMCP
import csv

mcp = FastMCP("My DB CURD opertion server")
DB_PATH = "./mydatabase.db"


# ----------------------------------------------------------
# TOOL 1 — Get all users from SQLite
# ----------------------------------------------------------
@mcp.tool()
def get_user_data(name: str) -> list:
    """
    Returns all rows from the 'users' table in mydatabase.db
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if name =="All":
        cursor.execute("SELECT * FROM users")
    else:        
        cursor.execute("SELECT * FROM users WHERE name=?",(name,))
    
    rows = cursor.fetchall()
    result = [dict(row) for row in rows]  # Convert Rows → dicts

    conn.close()
    return result


# ----------------------------------------------------------
# TOOL 2 — Insert a user into SQLite
# ----------------------------------------------------------
@mcp.tool()
def set_user_data(name: str, email: str) -> str:
    """
    Inserts a new user into the 'users' table and returns a message.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (name, email) VALUES (?, ?)",
        (name, email)
    )

    conn.commit()
    conn.close()

    return f"User '{name}' added successfully."

@mcp.tool()
def update_user(id: int, name: str = None, email: str = None) -> str:
    """
    Updates user fields based on the given id.
    Only updates fields provided (name or email).
    """
    if name is None and email is None:
        return "No fields to update."

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Build dynamic SQL
    fields = []
    values = []

    if name is not None:
        fields.append("name=?")
        values.append(name)

    if email is not None:
        fields.append("email=?")
        values.append(email)

    # Add id to values
    values.append(id)

    sql = f"UPDATE users SET {', '.join(fields)} WHERE id=?"
    cursor.execute(sql, tuple(values))
    conn.commit()
    conn.close()

    return f"User with id {id} updated successfully."


@mcp.tool()
def delete_user(id: int) -> str:
    """
    Deletes a user from the users table using their ID.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return f"User with id {id} deleted successfully."


if __name__ == "__main__":
    # HTTP transport on port 8000
    mcp.run(transport="http", host="0.0.0.0", port=8000)
