# server.py - Full Neo4j MCP Server
from fastmcp import FastMCP
from neo4j import GraphDatabase
import datetime

mcp = FastMCP("Neo4j Employee Management Server")

# ----------------------------------------------------
# 1. Neo4j Connection
# ----------------------------------------------------
driver = GraphDatabase.driver(
    "neo4j://127.0.0.1:7687",
    auth=("neo4j", "pas@123")
)

# ----------------------------------------------------
# 2. Schema Setup (equivalent to SQL tables)
# ----------------------------------------------------
SCHEMA_QUERIES = [
    """
    CREATE CONSTRAINT department_id_unique IF NOT EXISTS
    FOR (d:Department) REQUIRE d.id IS UNIQUE;
    """,
    """
    CREATE CONSTRAINT department_name_unique IF NOT EXISTS
    FOR (d:Department) REQUIRE d.name IS UNIQUE;
    """,
    """
    CREATE CONSTRAINT employee_id_unique IF NOT EXISTS
    FOR (e:Employee) REQUIRE e.id IS UNIQUE;
    """,
    """
    CREATE CONSTRAINT employee_email_unique IF NOT EXISTS
    FOR (e:Employee) REQUIRE e.email IS UNIQUE;
    """,
    """
    CREATE CONSTRAINT project_id_unique IF NOT EXISTS
    FOR (p:Project) REQUIRE p.id IS UNIQUE;
    """,
    """
    CREATE CONSTRAINT attendance_id_unique IF NOT EXISTS
    FOR (a:Attendance) REQUIRE a.id IS UNIQUE;
    """,
    """
    CREATE CONSTRAINT salary_history_id_unique IF NOT EXISTS
    FOR (s:SalaryHistory) REQUIRE s.id IS UNIQUE;
    """
]

def setup_schema():
    print("Setting up Neo4j Schema...")
    with driver.session() as session:
        for q in SCHEMA_QUERIES:
            session.run(q)
    print("Schema created.")

# ----------------------------------------------------
# 3. Helper to Run Cypher
# ----------------------------------------------------
def run_query(query, params=None):
    with driver.session() as session:
        result = session.run(query, params or {})
        return [record.data() for record in result]

# ----------------------------------------------------
# 4. MCP TOOLS
# ----------------------------------------------------

# ---------------- CREATE DEPARTMENT -----------------
@mcp.tool()
def create_department(id: int, name: str, location: str = None) -> str:
    query = """
    MERGE (d:Department {id:$id})
    SET d.name=$name, d.location=$location
    """
    run_query(query, {"id": id, "name": name, "location": location})
    return f"Department '{name}' created."

# ---------------- CREATE EMPLOYEE -------------------
@mcp.tool()
def create_employee(
    id: int,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    department_id: int,
    designation: str,
    salary: float,
    date_of_joining: str,
    status: str = "Active"
) -> str:

    query = """
    MATCH (d:Department {id:$department_id})
    CREATE (e:Employee {
        id:$id, first_name:$first_name, last_name:$last_name,
        email:$email, phone:$phone, designation:$designation,
        salary:$salary, date_of_joining:$date_of_joining, status:$status
    })
    CREATE (e)-[:WORKS_IN]->(d)
    """
    run_query(query, {
        "id": id, "first_name": first_name, "last_name": last_name,
        "email": email, "phone": phone, "designation": designation,
        "salary": salary, "date_of_joining": date_of_joining,
        "status": status, "department_id": department_id
    })

    return f"Employee {first_name} {last_name} created."

# ---------------- UPDATE EMPLOYEE -------------------
@mcp.tool()
def update_employee(id: int, field: str, value: str) -> str:
    query = f"""
    MATCH (e:Employee {{id:$id}})
    SET e.{field} = $value
    """
    run_query(query, {"id": id, "value": value})
    return f"Employee {id} updated: {field} = {value}"

# ---------------- DELETE EMPLOYEE -------------------
@mcp.tool()
def delete_employee(id: int) -> str:
    query = """
    MATCH (e:Employee {id:$id})
    DETACH DELETE e
    """
    run_query(query, {"id": id})
    return f"Employee {id} deleted."

# ---------------- ASSIGN PROJECT --------------------
@mcp.tool()
def assign_project(employee_id: int, project_id: int, project_name: str) -> str:
    query = """
    MATCH (e:Employee {id:$employee_id})
    MERGE (p:Project {id:$project_id})
    SET p.name=$project_name
    MERGE (e)-[:ASSIGNED_TO {assigned_on:date()}]->(p)
    """
    run_query(query, {
        "employee_id": employee_id,
        "project_id": project_id,
        "project_name": project_name
    })
    return f"Employee {employee_id} assigned to project {project_name}"

# ---------------- ATTENDANCE RECORD ------------------
@mcp.tool()
def add_attendance(employee_id: int, status: str) -> str:
    query = """
    MATCH (e:Employee {id:$employee_id})
    CREATE (a:Attendance {
        id: apoc.create.uuid(),
        date: date(), 
        status: $status
    })
    CREATE (e)-[:HAS_ATTENDANCE]->(a)
    """
    run_query(query, {"employee_id": employee_id, "status": status})
    return "Attendance recorded."

# ---------------- SALARY CHANGE ---------------------
@mcp.tool()
def add_salary_change(employee_id: int, new_salary: float) -> str:
    query = """
    MATCH (e:Employee {id:$employee_id})
    CREATE (s:SalaryHistory {
        id: apoc.create.uuid(),
        old_salary: e.salary,
        new_salary: $new_salary,
        changed_on: datetime()
    })
    SET e.salary = $new_salary
    CREATE (e)-[:HAS_SALARY_HISTORY]->(s)
    """
    run_query(query, {"employee_id": employee_id, "new_salary": new_salary})
    return "Salary updated."

# ---------------- GET EMPLOYEE ----------------------
@mcp.tool()
def get_employee(id: int) -> list:
    query = """
    MATCH (e:Employee {id:$id})
    RETURN e
    """
    return run_query(query, {"id": id})

# ---------------- GET ALL EMPLOYEES -----------------
@mcp.tool()
def get_all_employees() -> list:
    query = "MATCH (e:Employee) RETURN e"
    return run_query(query)

# ---------------- GET EMPLOYEE GRAPH ----------------
@mcp.tool()
def get_employee_graph(id: int) -> list:
    query = """
    MATCH (e:Employee {id:$id})-[r]->(n)
    RETURN e, r, n
    """
    return run_query(query, {"id": id})


# INTERNAL FUNCTIONS (call inside server, not exposed)

def _create_department(id, name, location):
    query = """
    MERGE (d:Department {id:$id})
    SET d.name=$name, d.location=$location
    """
    run_query(query, {"id": id, "name": name, "location": location})


def _create_employee(data):
    query = """
    MATCH (d:Department {id:$department_id})
    CREATE (e:Employee {
        id:$id, first_name:$first_name, last_name:$last_name,
        email:$email, phone:$phone, designation:$designation,
        salary:$salary, date_of_joining:$date_of_joining, status:$status
    })
    CREATE (e)-[:WORKS_IN]->(d)
    """
    run_query(query, data)

# ----------------------------------------------------
# 5. Load Sample Data (5 Employees)
# ----------------------------------------------------
def load_demo_data():
    print("Loading demo data...")

    # Departments
    _create_department(1, "Engineering", "Bangalore")
    _create_department(2, "Human Resources", "Hyderabad")

    # 5 Employees
    employees = [
        {
            "id": 1, "first_name": "Arun", "last_name": "Kumar",
            "email": "arun@example.com", "phone": "9876543210",
            "department_id": 1, "designation": "Software Engineer",
            "salary": 80000, "date_of_joining": "2020-05-01", "status": "Active"
        },
        {
            "id": 2, "first_name": "Prashant", "last_name": "Singh",
            "email": "prashant@example.com", "phone": "9988776655",
            "department_id": 2, "designation": "Manager",
            "salary": 120000, "date_of_joining": "2018-03-12", "status": "Active"
        },
        {
            "id": 3, "first_name": "John", "last_name": "Doe",
            "email": "john@example.com", "phone": "9000000001",
            "department_id": 1, "designation": "Developer",
            "salary": 90000, "date_of_joining": "2021-06-10", "status": "Active"
        },
        {
            "id": 4, "first_name": "Asha", "last_name": "Rani",
            "email": "asha@example.com", "phone": "9888888888",
            "department_id": 1, "designation": "QA Engineer",
            "salary": 70000, "date_of_joining": "2022-01-20", "status": "Active"
        },
        {
            "id": 5, "first_name": "Ravi", "last_name": "Sharma",
            "email": "ravi@example.com", "phone": "9777777777",
            "department_id": 2, "designation": "HR Executive",
            "salary": 60000, "date_of_joining": "2019-11-05", "status": "Active"
        }
    ]

    for emp in employees:
        _create_employee(emp)

    print("Demo data loaded successfully.")

# ----------------------------------------------------
# 6. Main Entry
# ----------------------------------------------------
if __name__ == "__main__":
    setup_schema()
    load_demo_data()

    print("Starting Neo4j MCP Server on port 8000...")
    mcp.run(transport="http", host="0.0.0.0", port=8000)
