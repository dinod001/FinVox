from typing import Dict
from sqlalchemy import text
from src.infrastructure.db.crm_client import engine
from src.infrastructure.log import log

# In-memory cache for user KPIs. Key: user_id, Value: Formatted KPI Markdown String
_KPI_CACHE: Dict[str, str] = {}

def invalidate_kpi_cache(user_id: str):
    """Clears the KPI cache for a specific user. Call this on CRUD operations."""
    if user_id in _KPI_CACHE:
        del _KPI_CACHE[user_id]
        log.info(f"Invalidated KPI cache for user {user_id}")

async def get_kpis_for_user(user_id: str) -> str:
    """
    Retrieves all registered KPIs for a user and formats them into a Markdown string 
    for injection into the LLM context. Uses in-memory caching for zero-latency retrieval.
    Returns an empty string if no KPIs exist.
    """
    # 1. Check Cache
    if user_id in _KPI_CACHE:
        return _KPI_CACHE[user_id]

    # 2. Cache Miss - Fetch from DB
    if not engine:
        return ""
        
    try:
        def _fetch():
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT kpi_name, formula, target_value, description FROM kpi_registry WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )
                return result.fetchall()
                
        import asyncio
        rows = await asyncio.to_thread(_fetch)
        
        if not rows:
            return ""
            
        kpi_lines = []
        for row in rows:
            name = row[0]
            formula = row[1]
            target = row[2]
            desc = row[3] or ""
            
            kpi_str = f"- **{name}**: Formula: `{formula}`"
            if target:
                kpi_str += f", Target: `{target}`"
            if desc:
                kpi_str += f" (Description: {desc})"
            kpi_lines.append(kpi_str)
        formatted_kpis = "\n".join(kpi_lines)
        _KPI_CACHE[user_id] = formatted_kpis
        return formatted_kpis
        
    except Exception as e:
        log.error(f"Failed to fetch KPIs for LLM context: {e}")
        return ""
