import os
import sys

if os.environ.get("CI") == "true":
    print("Skipping tests in CI environment.")
    sys.exit(0)

# Ensure project root and src are in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.infrastructure.db.crm_client import check_connection, check_pgvector

def test_supabase_connection():
    print("="*60)
    print("Integration Test: Supabase PostgreSQL Connection & Extensions")
    print("="*60)
    
    print("\nTesting connection to Supabase...")
    is_connected = check_connection()
    
    print("\nChecking for pgvector extension...")
    has_pgvector = check_pgvector()
    
    print("\n" + "="*60)
    if is_connected and has_pgvector:
        print("✅ Success: Connected to Supabase AND pgvector is enabled!")
    elif is_connected:
        print("⚠️ Warning: Connected to Supabase, but pgvector is NOT enabled.")
    else:
        print("❌ Failed: Could not connect to Supabase Database. Check your .env file.")
    print("="*60)

if __name__ == "__main__":
    test_supabase_connection()
