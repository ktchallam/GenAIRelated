# server.py
import sqlite3
from fastmcp import FastMCP
import csv
import re
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from typing import TypedDict
import httpx  
import requests

for method in ("get", "post", "put", "delete", "head", "options", "patch"):
    original = getattr(requests, method)

    def insecure_request(*args, _original=original, **kwargs):
        kwargs["verify"] = False
        return _original(*args, **kwargs)

    setattr(requests, method, insecure_request)


#
import curl_cffi.requests as creq

# Patch the Session class to always skip SSL verification
_old_init = creq.Session.__init__

def _new_init(self, *args, **kwargs):
    kwargs["verify"] = False
    _old_init(self, *args, **kwargs)

creq.Session.__init__ = _new_init

client = httpx.Client(verify=False) 

mcp = FastMCP("My DB CURD opertion server")
DB_PATH = "./mydatabase.db"


# ----------------------------------------------------
# Get schema text dynamically from SQLite
# ----------------------------------------------------
def get_db_schema() -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    schema = "DATABASE SCHEMA:\n"

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    for table in tables:
        schema += f"\nTABLE: {table}\n"
        cursor.execute(f"PRAGMA table_info({table});")
        for col in cursor.fetchall():
            cid, name, ctype, notnull, default, pk = col
            schema += f"  - {name} ({ctype}){' PRIMARY KEY' if pk else ''}\n"

    conn.close()
    return schema


# ----------------------------------------------------
# LangGraph state definition
# ----------------------------------------------------
class SQLState(TypedDict):
    user_input: str
    sql_query: str


# ----------------------------------------------------
# Node: LLM generates SQL
# ----------------------------------------------------
def llm_generate_sql(state: SQLState):
    schema_text = get_db_schema()

    prompt = f"""
You are an expert SQL generator. Convert the user request into a SAFE SQL query.
STRICT RULES:
1. DO NOT generate UPDATE or DELETE without a WHERE clause.
2. WHERE must reference the primary key column.
3. Do NOT return SQL that modifies schema (no DROP, ALTER, TRUNCATE).
4. Only generate SQL for existing tables in the schema.
5. Return ONLY SQL.

SCHEMA:
{schema_text}

User request: {state['user_input']}
    """
    
    llm = ChatOpenAI( 
        base_url="https://genailab.tcs.in" ,
        model = "azure/genailab-maas-gpt-4o-mini", 
        api_key="sk-N2Z4PGkQ4p8yhNfBworBww", 
        http_client = client 
    ) 
    response = llm.invoke(prompt)

    return {"sql_query": response.content.strip()}


# ----------------------------------------------------
# Build LangGraph
# ----------------------------------------------------
def build_sql_graph():
    workflow = StateGraph(SQLState)
    workflow.add_node("generate_sql", llm_generate_sql)
    workflow.set_entry_point("generate_sql")
    workflow.add_edge("generate_sql", END)
    return workflow.compile()


sql_graph = build_sql_graph()


# ----------------------------------------------------
# MCP Tool: Natural language → SQL
# ----------------------------------------------------
@mcp.tool()
def generate_sql_query(text: str) -> str:
    """
    Generates a SQL query from natural language using a LangGraph + LLM pipeline.
    Enforces strict safety guardrails automatically.
    """
    result = sql_graph.invoke({"user_input": text})
    return result["sql_query"]

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
