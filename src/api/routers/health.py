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

@router.get("/metrics")
async def get_dashboard_metrics():
    """
    Fetch live system metrics for the UI Dashboard:
    - Qdrant Vector Count
    - Supabase Dataset Details (Dynamic tables created)
    """
    # Run Qdrant and Supabase queries IN PARALLEL for maximum speed
    async def _get_qdrant_metrics():
        try:
            from src.infrastructure.db.qdrant_client import collection_info
            info = await asyncio.to_thread(collection_info)
            return {
                "status": "healthy",
                "points_count": info.get("points_count", 0),
                "collection": info.get("name")
            }
        except Exception as e:
            log.error(f"Failed to fetch Qdrant metrics: {e}")
            return {"status": "unhealthy", "points_count": 0}

    async def _get_supabase_metrics():
        try:
            def _fetch():
                if not engine:
                    return {"status": "unhealthy", "tables_count": 0, "rows_count": 0}
                with engine.connect() as conn:
                    tables_res = conn.execute(text("""
                        SELECT tablename 
                        FROM pg_tables 
                        WHERE schemaname='public' 
                        AND tablename NOT IN ('mem_vectors', 'mem_episodes', 'chat_messages', 'chat_sessions', 'users', 'table_registry')
                    """))
                    table_names = [row[0] for row in tables_res.fetchall()]

                    rows_res = conn.execute(text("""
                        SELECT sum(n_live_tup) 
                        FROM pg_stat_user_tables 
                        WHERE schemaname = 'public'
                        AND relname NOT IN ('mem_vectors', 'mem_episodes', 'chat_messages', 'chat_sessions', 'users', 'table_registry')
                    """))
                    rows_count = rows_res.scalar() or 0

                    return {
                        "status": "healthy",
                        "tables_count": len(table_names),
                        "rows_count": int(rows_count),
                        "table_names": table_names
                    }
            return await asyncio.to_thread(_fetch)
        except Exception as e:
            log.error(f"Failed to fetch Supabase metrics: {e}")
            return {"status": "unhealthy", "tables_count": 0, "rows_count": 0}

    qdrant_result, supabase_result = await asyncio.gather(
        _get_qdrant_metrics(),
        _get_supabase_metrics()
    )

    return {"qdrant": qdrant_result, "supabase": supabase_result}

