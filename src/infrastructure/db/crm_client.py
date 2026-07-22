"""
Database client for Supabase PostgreSQL using SQLAlchemy.
Includes support for pgvector (embeddings).
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from infrastructure.config import SUPABASE_DB_URL
from infrastructure.log import log

# Initialize the Base for ORM models
Base = declarative_base()

# SQLAlchemy Engine and Session factory
engine = None
SessionLocal = None

if not SUPABASE_DB_URL:
    log.warning("SUPABASE_DB_URL is not set in .env! Database features may fail.")
else:
    try:
        # Create the engine. We use pool_pre_ping to check connections before using them.
        engine = create_engine(SUPABASE_DB_URL, pool_pre_ping=True)
        
        # Create a configured "Session" class
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        log.info("✓ SQLAlchemy Engine connected to Supabase (pgvector supported)")
    except Exception as e:
        log.error(f"Failed to connect to Supabase: {e}")

def get_db():
    """
    Dependency to yield a database session.
    Can be used in FastAPI routes or anywhere else:
    
    Example:
    from infrastructure.db.crm_client import get_db
    
    def fetch_data():
        db = next(get_db())
        try:
            # Query the database
            results = db.query(MyModel).all()
            return results
        finally:
            db.close()
    """
    if not SessionLocal:
        raise ConnectionError("Database session could not be established. Check SUPABASE_DB_URL.")
        
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_connection() -> bool:
    """Check if the database connection is working."""
    if not engine:
        log.error("Cannot check connection: Engine is not initialized.")
        return False
        
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        log.info("✓ Database connection test passed!")
        return True
    except Exception as e:
        log.error(f"❌ Database connection test failed: {e}")
        return False

def check_pgvector() -> bool:
    """Check if pgvector extension is installed in the database."""
    if not engine:
        log.error("Cannot check pgvector: Engine is not initialized.")
        return False
        
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
            if result.fetchone():
                log.info("✓ pgvector extension is installed and ready!")
                return True
            else:
                log.warning("⚠️ pgvector extension is NOT installed. Run 'CREATE EXTENSION vector;' in Supabase.")
                return False
    except Exception as e:
        log.error(f"❌ Failed to check pgvector extension: {e}")
        return False

__all__ = ["Base", "engine", "SessionLocal", "get_db", "check_connection", "check_pgvector"]
