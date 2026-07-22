import pandas as pd
from sqlalchemy import text
import uuid
import re
from datetime import datetime

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
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(create_table_sql))
        log.info("✓ table_registry checked/created successfully.")
    except Exception as e:
        log.error(f"Failed to ensure table_registry: {e}")

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
        
        # 2. Register in table_registry
        with SessionLocal() as db:
            # Check if exists
            result = db.execute(text("SELECT id FROM table_registry WHERE table_name = :t"), {"t": table_name})
            exists = result.fetchone()
            
            if exists:
                # Update description
                db.execute(
                    text("UPDATE table_registry SET description = :d WHERE table_name = :t"),
                    {"d": description, "t": table_name}
                )
            else:
                # Insert new
                table_id = str(uuid.uuid4())
                db.execute(
                    text("INSERT INTO table_registry (id, table_name, description) VALUES (:id, :t, :d)"),
                    {"id": table_id, "t": table_name, "d": description}
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
