import pandas as pd
from sqlalchemy import text
import uuid
import re
from datetime import datetime
import json

from src.infrastructure.db.crm_client import engine, SessionLocal
from src.infrastructure.log import log

def sanitize_table_name(filename: str) -> str:
    """
    Sanitize a filename to be used as a valid PostgreSQL table name.
    """
    # Remove file extension
    name = filename.rsplit('.', 1)[0]
    # Replace non-alphanumeric characters with underscores
    name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    # Ensure it doesn't start with a number
    if name[0].isdigit():
        name = "tbl_" + name
    # Convert to lowercase
    return name.lower()

def ensure_table_registry():
    """
    Ensure the table_registry table exists in Supabase.
    This tracks all dynamically created tables.
    """
    if not engine:
        log.error("Database engine not initialized. Cannot create table_registry.")
        return
        
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS table_registry (
        id UUID PRIMARY KEY,
        table_name TEXT UNIQUE NOT NULL,
        description TEXT,
        schema_info TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    alter_table_sql = """
    ALTER TABLE table_registry ADD COLUMN IF NOT EXISTS schema_info TEXT;
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(create_table_sql))
            conn.execute(text(alter_table_sql))
        log.info("✓ table_registry checked/created successfully.")
    except Exception as e:
        log.error(f"Failed to ensure table_registry: {e}")

def ensure_kpi_registry():
    """
    Ensure the kpi_registry table exists in Supabase.
    This stores company-specific KPIs.
    """
    if not engine:
        log.error("Database engine not initialized. Cannot create kpi_registry.")
        return
        
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS kpi_registry (
        id UUID PRIMARY KEY,
        user_id VARCHAR NOT NULL,
        kpi_name VARCHAR NOT NULL,
        formula TEXT,
        target_value VARCHAR,
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(create_table_sql))
        log.info("✓ kpi_registry checked/created successfully.")
    except Exception as e:
        log.error(f"Failed to ensure kpi_registry: {e}")

def ensure_deadline_registry():
    """
    Ensure the regulatory_deadlines table exists in Supabase.
    This stores upcoming payment deadlines like EPF, ETF, VAT.
    """
    if not engine:
        log.error("Database engine not initialized. Cannot create regulatory_deadlines.")
        return
        
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS regulatory_deadlines (
        id UUID PRIMARY KEY,
        title TEXT NOT NULL,
        due_date DATE NOT NULL,
        recurring_type TEXT DEFAULT 'none',
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(create_table_sql))
        log.info("✓ regulatory_deadlines checked/created successfully.")
    except Exception as e:
        log.error(f"Failed to ensure regulatory_deadlines: {e}")

def save_dataframe_to_supabase(df: pd.DataFrame, filename: str, description: str = "") -> dict:
    """
    Save a pandas DataFrame directly as a native PostgreSQL table.
    Registers the table in table_registry.
    """
    if not engine:
        return {"success": False, "error": "Database engine not initialized."}
        
    ensure_table_registry()
    
    table_name = sanitize_table_name(filename)
    
    try:
        # 1. Save DataFrame to SQL (creates table automatically based on column types)
        # Using if_exists='replace' to overwrite if the user uploads the same file again
        log.info(f"Saving dataframe to Supabase table: '{table_name}'")
        df.to_sql(name=table_name, con=engine, if_exists='replace', index=False)
        
        # 2. Extract schema (column names and types)
        schema_dict = {col: str(dtype) for col, dtype in df.dtypes.items()}
        schema_json = json.dumps(schema_dict)
        
        # 3. Register in table_registry
        with SessionLocal() as db:
            # Check if exists
            result = db.execute(text("SELECT id FROM table_registry WHERE table_name = :t"), {"t": table_name})
            exists = result.fetchone()
            
            if exists:
                # Update description and schema
                db.execute(
                    text("UPDATE table_registry SET description = :d, schema_info = :s WHERE table_name = :t"),
                    {"d": description, "s": schema_json, "t": table_name}
                )
            else:
                # Insert new
                table_id = str(uuid.uuid4())
                db.execute(
                    text("INSERT INTO table_registry (id, table_name, description, schema_info) VALUES (:id, :t, :d, :s)"),
                    {"id": table_id, "t": table_name, "d": description, "s": schema_json}
                )
            db.commit()
            
        log.success(f"Successfully saved and registered table: {table_name}")
        return {
            "success": True, 
            "table_name": table_name, 
            "rows_inserted": len(df)
        }
    except Exception as e:
        log.error(f"Failed to save table to Supabase: {e}")
        return {"success": False, "error": str(e)}

def delete_supabase_table(table_id: str) -> dict:
    """
    Drop a dynamically created table from Supabase and remove it from table_registry using its ID.
    """
    if not engine:
        return {"success": False, "error": "Database engine not initialized."}
        
    try:
        with engine.begin() as conn:
            # 0. Get the table name from the registry
            res = conn.execute(
                text("SELECT table_name FROM table_registry WHERE id = :id"),
                {"id": table_id}
            )
            row = res.fetchone()
            if not row:
                return {"success": False, "error": "Table ID not found in registry."}
                
            table_name = row[0]
            
            # 1. Drop the actual data table
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
            
            # 2. Remove from registry
            conn.execute(
                text("DELETE FROM table_registry WHERE id = :id"),
                {"id": table_id}
            )
            
        log.success(f"Successfully deleted table and registry entry for ID: {table_id}")
        return {"success": True, "message": f"Table {table_name} deleted successfully."}
    except Exception as e:
        log.error(f"Failed to delete table with ID {table_id}: {e}")
        return {"success": False, "error": str(e)}

def get_registered_tables() -> list:
    """
    Fetch a list of all active registered structured datasets from Supabase.
    Returns a list of dicts with 'table_name' and 'description'.
    """
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT table_name, description FROM table_registry"))
            return [{"table_name": row[0], "description": row[1] or ""} for row in res.fetchall()]
    except Exception as e:
        log.error(f"Failed to fetch registered tables: {e}")
        return []
