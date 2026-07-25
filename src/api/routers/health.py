import asyncio
import time
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from src.infrastructure.db.crm_client import engine
from src.infrastructure.log import log

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
async def health_check():
    """
    Basic health check endpoint.
    Verifies that the API is running and checks the database connection.
    """
    status = {
        "api": "healthy",
        "timestamp": int(time.time()),
        "database": "unknown",
        "system": {}
    }
    
    # ── 1. Check Server Status (CPU, RAM) ──────────────────────────────────
    try:
        import psutil
        status["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_mb": round(psutil.virtual_memory().available / (1024 * 1024), 2)
        }
    except ImportError:
        status["system"] = "psutil not installed, cannot fetch system metrics"
    except Exception as e:
        status["system"] = f"Error fetching system metrics: {str(e)}"
    
    # ── 2. Check Database Connection ───────────────────────────────────────
    def _check_db():
        if not engine:
            return "uninitialized"
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return "healthy"
        except Exception as e:
            log.error(f"Database health check failed: {e}")
            return "unhealthy"

    db_status = await asyncio.to_thread(_check_db)
    status["database"] = db_status
    
    if db_status != "healthy":
        raise HTTPException(status_code=503, detail=status)
        
    return status
