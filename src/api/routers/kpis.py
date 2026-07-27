import uuid
import asyncio
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.infrastructure.log import log
from src.services.kpi_service import invalidate_kpi_cache

router = APIRouter(prefix="/kpis", tags=["KPI Management"])

# ── Schemas ───────────────────────────────────────────────────────────────────

class KPICreate(BaseModel):
    user_id: str = Field(..., description="The ID of the user creating the KPI")
    kpi_name: str = Field(..., description="Name of the KPI, e.g. 'Net Profit Margin'")
    formula: str = Field(..., description="Formula for the KPI (can be plain English), e.g. 'Net Income divided by Revenue'")
    target_value: Optional[str] = Field(None, description="Target string, e.g. '>= 20%'")
    description: Optional[str] = Field(None, description="Detailed description of what this KPI measures")

class KPIUpdate(BaseModel):
    kpi_name: Optional[str] = None
    formula: Optional[str] = None
    target_value: Optional[str] = None
    description: Optional[str] = None

class KPIResponse(BaseModel):
    id: str
    user_id: str
    kpi_name: str
    formula: str
    target_value: Optional[str]
    description: Optional[str]

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=List[KPIResponse])
async def get_kpis(request: Request, user_id: str = Query(..., description="Get KPIs for this user")):
    """Retrieve all KPIs for a specific user."""
    engine: Engine = request.app.state.db_engine
    if not engine:
        raise HTTPException(status_code=500, detail="Database engine not initialized")
        
    def _fetch():
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, user_id, kpi_name, formula, target_value, description FROM kpi_registry WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            return result.fetchall()
            
    try:
        rows = await asyncio.to_thread(_fetch)
            
        return [
            KPIResponse(
                id=str(row[0]),
                user_id=row[1],
                kpi_name=row[2],
                formula=row[3],
                target_value=row[4],
                description=row[5]
            ) for row in rows
        ]
    except Exception as e:
        log.error(f"Failed to fetch KPIs for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch KPIs")

@router.post("", response_model=KPIResponse)
async def create_kpi(request: Request, kpi: KPICreate):
    """Create a new KPI for a user."""
    engine: Engine = request.app.state.db_engine
    if not engine:
        raise HTTPException(status_code=500, detail="Database engine not initialized")
        
    kpi_id = str(uuid.uuid4())
    
    def _insert():
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO kpi_registry (id, user_id, kpi_name, formula, target_value, description)
                    VALUES (:id, :user_id, :kpi_name, :formula, :target_value, :description)
                """),
                {
                    "id": kpi_id,
                    "user_id": kpi.user_id,
                    "kpi_name": kpi.kpi_name,
                    "formula": kpi.formula,
                    "target_value": kpi.target_value,
                    "description": kpi.description
                }
            )
            
    try:
        await asyncio.to_thread(_insert)
        invalidate_kpi_cache(kpi.user_id)
        log.success(f"Created KPI '{kpi.kpi_name}' for user {kpi.user_id}")
        return KPIResponse(id=kpi_id, **kpi.model_dump())
    except Exception as e:
        log.error(f"Failed to create KPI: {e}")
        raise HTTPException(status_code=500, detail="Failed to create KPI")

@router.put("/{kpi_id}", response_model=KPIResponse)
async def update_kpi(request: Request, kpi_id: str, kpi_update: KPIUpdate, user_id: str = Query(..., description="Ensure user owns KPI")):
    """Update an existing KPI."""
    engine: Engine = request.app.state.db_engine
    if not engine:
        raise HTTPException(status_code=500, detail="Database engine not initialized")
        
    def _update():
        with engine.begin() as conn:
            # Check existence and ownership
            res = conn.execute(
                text("SELECT id, user_id, kpi_name, formula, target_value, description FROM kpi_registry WHERE id = :id AND user_id = :user_id"),
                {"id": kpi_id, "user_id": user_id}
            )
            row = res.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="KPI not found or not owned by user")

            # Build update query
            updates = []
            params = {"id": kpi_id, "user_id": user_id}
            
            for key, value in kpi_update.model_dump(exclude_unset=True).items():
                updates.append(f"{key} = :{key}")
                params[key] = value
                
            if not updates:
                raise HTTPException(status_code=400, detail="No fields to update provided")
                
            set_clause = ", ".join(updates)
            
            conn.execute(
                text(f"UPDATE kpi_registry SET {set_clause} WHERE id = :id AND user_id = :user_id"),
                params
            )
            
            # Fetch updated row
            res = conn.execute(
                text("SELECT id, user_id, kpi_name, formula, target_value, description FROM kpi_registry WHERE id = :id"),
                {"id": kpi_id}
            )
            return res.fetchone()
            
    try:
        new_row = await asyncio.to_thread(_update)
        invalidate_kpi_cache(user_id)
            
        return KPIResponse(
            id=str(new_row[0]),
            user_id=new_row[1],
            kpi_name=new_row[2],
            formula=new_row[3],
            target_value=new_row[4],
            description=new_row[5]
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to update KPI {kpi_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update KPI")

@router.delete("/{kpi_id}")
async def delete_kpi(request: Request, kpi_id: str, user_id: str = Query(..., description="Ensure user owns KPI")):
    """Delete a KPI."""
    engine: Engine = request.app.state.db_engine
    if not engine:
        raise HTTPException(status_code=500, detail="Database engine not initialized")
        
    def _delete():
        with engine.begin() as conn:
            # Check existence and ownership
            res = conn.execute(
                text("SELECT id FROM kpi_registry WHERE id = :id AND user_id = :user_id"),
                {"id": kpi_id, "user_id": user_id}
            )
            if not res.fetchone():
                raise HTTPException(status_code=404, detail="KPI not found or not owned by user")
                
            conn.execute(
                text("DELETE FROM kpi_registry WHERE id = :id"),
                {"id": kpi_id}
            )
            
    try:
        await asyncio.to_thread(_delete)
        invalidate_kpi_cache(user_id)
        log.info(f"Deleted KPI {kpi_id} for user {user_id}")
        return {"success": True, "message": "KPI deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to delete KPI {kpi_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete KPI")
