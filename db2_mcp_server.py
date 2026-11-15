import json
import sys
from mcp.server import MCPServer
from mcp.types import Tool, TextContent
from sqlalchemy import create_engine, text
import ibm_db_sa

# Configure MCP Server
app = MCPServer("db2-server")

# Database connection parameters (replace with your actual values)
DB2_HOST = "localhost"
DB2_PORT = 50050
DB2_DATABASE = "dbcdw"
DB2_USER = "db2inst1"
DB2_PASSWORD = "Babalu07"

# Construct connection string for ibm_db_sa
# Format: ibm_db_sa://{user}:{password}@{host}:{port}/{database}
CONNECTION_STRING = f"ibm_db_sa://{DB2_USER}:{DB2_PASSWORD}@{DB2_HOST}:{DB2_PORT}/{DB2_DATABASE}"

# Create SQLAlchemy engine
try:
    engine = create_engine(CONNECTION_STRING)
except Exception as e:
    print(f"Failed to connect to DB2: {e}")
    sys.exit(1)

# Allow non-SELECT statements (e.g. CREATE/INSERT) when explicitly enabled.
# Set DB2_ALLOW_WRITE=1 (or "true"/"yes") in the MCP server environment to enable.
import os
ALLOW_WRITE = os.getenv("DB2_ALLOW_WRITE", "").lower() in ("1", "true", "yes")
ALLOWED_PREFIXES = ("SELECT", "WITH", "CREATE", "ALTER", "DROP", "INSERT", "UPDATE", "DELETE", "MERGE", "GRANT", "REVOKE")

@app.tool()
async def query_db2(query: str) -> dict:
    """
    Execute a query on the DB2 database.
    By default only SELECT/WITH queries are allowed. Set DB2_ALLOW_WRITE=1 to allow write/DDL statements.
    """
    query_stripped = query.strip()
    query_upper = query_stripped.upper()

    if not ALLOW_WRITE and not (query_upper.startswith("SELECT") or query_upper.startswith("WITH")):
        return {
            "content": [TextContent(type="text", text="❌ Error: Only SELECT/WITH queries are allowed. Set DB2_ALLOW_WRITE=1 for the db2-server MCP process to allow CREATE/INSERT/UPDATE/DELETE statements.")],
            "isError": False
        }

    if ALLOW_WRITE and not query_upper.startswith(ALLOWED_PREFIXES):
        return {
            "content": [TextContent(type="text", text="❌ Error: Query type not allowed.")],
            "isError": False
        }

    try:
        with engine.begin() as conn:
            result = conn.execute(text(query_stripped))
            if result.returns_rows:
                columns = result.keys()
                rows = result.fetchall()
                data = [dict(zip(columns, row)) for row in rows]
                return {
                    "content": [TextContent(type="text", text=json.dumps(data, indent=2, default=str))],
                    "isError": False
                }
            else:
                rowcount = result.rowcount
                return {
                    "content": [TextContent(type="text", text=json.dumps({"ok": True, "rowcount": rowcount}, indent=2))],
                    "isError": False
                }
    except Exception as e:
        return {
            "content": [TextContent(type="text", text=f"❌ Database Error: {str(e)}")],
            "isError": True
        }


@app.tool()
async def describe_table(table_name: str) -> dict:
    """
    Get schema information (columns, types) for a specific table in DB2.
    """
    try:
        # Query DB2 system catalog for table metadata
        query = text("""
            SELECT 
                COLNAME AS COLUMN_NAME,
                TYPENAME AS DATA_TYPE,
                LENGTH AS CHARACTER_MAXIMUM_LENGTH,
                SCALE AS NUMERIC_SCALE,
                NULLABLE AS IS_NULLABLE
            FROM SYSCAT.COLUMNS
            WHERE TABNAME = :table_name
            ORDER BY COLNO
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"table_name": table_name.upper()})
            columns = result.keys()
            rows = result.fetchall()
            
            data = [dict(zip(columns, row)) for row in rows]
            
            if not data:
                return {
                    "content": [TextContent(type="text", text=f"❌ Table '{table_name}' not found.")],
                    "isError": True
                }
                
            return {
                "content": [TextContent(type="text", text=json.dumps(data, indent=2, default=str))],
                "isError": False
            }
    except Exception as e:
        return {
            "content": [TextContent(type="text", text=f"❌ Error describing table: {str(e)}")],
            "isError": True
        }


@app.tool()
async def list_tables() -> dict:
    """
    List all user tables in the current DB2 schema.
    """
    try:
        query = text("""
            SELECT TABNAME AS TABLE_NAME
            FROM SYSCAT.TABLES
            WHERE TABSCHEMA = CURRENT SCHEMA
              AND TYPE = 'T'
            ORDER BY TABNAME
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query)
            tables = [row[0] for row in result.fetchall()]
            
            return {
                "content": [TextContent(type="text", text=json.dumps(tables, indent=2))],
                "isError": False
            }
    except Exception as e:
        return {
            "content": [TextContent(type="text", text=f"❌ Error listing tables: {str(e)}")],
            "isError": True
        }


if __name__ == "__main__":
    print("Starting DB2 MCP Server...")
    app.run()

