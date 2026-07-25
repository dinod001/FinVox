import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.infrastructure.db.crm_client import engine
from sqlalchemy import text

def init_db():
    print("Connecting to DB...")
    with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
        print("Reading schema...")
        with open('database/auth_and_chat_schema.sql', 'r') as f:
            sql_schema = f.read()
            
        print("Executing schema...")
        conn.execute(text(sql_schema))
        
        print("Inserting dummy user...")
        conn.execute(text("INSERT INTO users (username, email, password_hash) VALUES ('test_user_finvox', 'test@finvox.ai', 'hash123') ON CONFLICT DO NOTHING;"))
        
        print("Inserting dummy session...")
        conn.execute(text("INSERT INTO chat_sessions (id, user_id, title) VALUES ('22222222-2222-2222-2222-222222222222', 'test_user_finvox', 'Test Session') ON CONFLICT DO NOTHING;"))
        
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()
