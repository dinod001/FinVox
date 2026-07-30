from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime, timedelta
import uuid
import asyncio
from sqlalchemy import text

from src.infrastructure.log import log

router = APIRouter(prefix="/api/deadlines", tags=["Deadlines"])

class DeadlineCreate(BaseModel):
    title: str
    due_date: date
    recurring_type: Optional[str] = "none"
    description: Optional[str] = ""

class DeadlineResponse(BaseModel):
    id: str
    title: str
    due_date: date
    recurring_type: str
    description: Optional[str]
    created_at: datetime

@router.get("/", response_model=List[DeadlineResponse])
async def get_all_deadlines(request: Request):
    """Fetch all registered regulatory deadlines."""
    engine = request.app.state.db_engine
    
    def _fetch():
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id, title, due_date, recurring_type, description, created_at FROM regulatory_deadlines ORDER BY due_date ASC"))
            return result.fetchall()
            
    try:
        rows = await asyncio.to_thread(_fetch)
        return [
            DeadlineResponse(
                id=str(row[0]),
                title=row[1],
                due_date=row[2],
                recurring_type=row[3],
                description=row[4],
                created_at=row[5]
            ) for row in rows
        ]
    except Exception as e:
        log.error(f"Error fetching deadlines: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch deadlines.")

@router.get("/upcoming", response_model=List[DeadlineResponse])
async def get_upcoming_deadlines(request: Request, days: int = 14):
    """Fetch deadlines that are due within the next N days or are overdue."""
    engine = request.app.state.db_engine
    
    def _fetch():
        with engine.connect() as conn:
            cutoff_date = date.today() + timedelta(days=days)
            result = conn.execute(
                text("SELECT id, title, due_date, recurring_type, description, created_at FROM regulatory_deadlines WHERE due_date <= :cutoff ORDER BY due_date ASC"),
                {"cutoff": cutoff_date}
            )
            return result.fetchall()
            
    try:
        rows = await asyncio.to_thread(_fetch)
        return [
            DeadlineResponse(
                id=str(row[0]),
                title=row[1],
                due_date=row[2],
                recurring_type=row[3],
                description=row[4],
                created_at=row[5]
            ) for row in rows
        ]
    except Exception as e:
        log.error(f"Error fetching upcoming deadlines: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch upcoming deadlines.")

@router.post("/", response_model=DeadlineResponse)
async def create_deadline(request: Request, deadline: DeadlineCreate):
    """Create a new regulatory deadline."""
    engine = request.app.state.db_engine
    new_id = str(uuid.uuid4())
    
    def _create():
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO regulatory_deadlines (id, title, due_date, recurring_type, description)
                    VALUES (:id, :title, :due_date, :recurring_type, :description)
                """),
                {
                    "id": new_id,
                    "title": deadline.title,
                    "due_date": deadline.due_date,
                    "recurring_type": deadline.recurring_type,
                    "description": deadline.description
                }
            )
            
            result = conn.execute(
                text("SELECT id, title, due_date, recurring_type, description, created_at FROM regulatory_deadlines WHERE id = :id"),
                {"id": new_id}
            )
            return result.fetchone()
            
    try:
        row = await asyncio.to_thread(_create)
        if not row:
             raise HTTPException(status_code=500, detail="Failed to retrieve created deadline.")
             
        return DeadlineResponse(
            id=str(row[0]),
            title=row[1],
            due_date=row[2],
            recurring_type=row[3],
            description=row[4],
            created_at=row[5]
        )
    except Exception as e:
        log.error(f"Error creating deadline: {e}")
        raise HTTPException(status_code=500, detail="Failed to create deadline.")

@router.put("/{deadline_id}", response_model=DeadlineResponse)
async def update_deadline(request: Request, deadline_id: str, deadline: DeadlineCreate):
    """Update an existing regulatory deadline."""
    engine = request.app.state.db_engine
    
    def _update():
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE regulatory_deadlines 
                    SET title = :title, due_date = :due_date, recurring_type = :recurring_type, description = :description
                    WHERE id = :id
                """),
                {
                    "id": deadline_id,
                    "title": deadline.title,
                    "due_date": deadline.due_date,
                    "recurring_type": deadline.recurring_type,
                    "description": deadline.description
                }
            )
            
            result = conn.execute(
                text("SELECT id, title, due_date, recurring_type, description, created_at FROM regulatory_deadlines WHERE id = :id"),
                {"id": deadline_id}
            )
            return result.fetchone()
            
    try:
        row = await asyncio.to_thread(_update)
        if not row:
             raise HTTPException(status_code=404, detail="Deadline not found.")
             
        return DeadlineResponse(
            id=str(row[0]),
            title=row[1],
            due_date=row[2],
            recurring_type=row[3],
            description=row[4],
            created_at=row[5]
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error updating deadline: {e}")
        raise HTTPException(status_code=500, detail="Failed to update deadline.")

@router.delete("/{deadline_id}")
async def delete_deadline(request: Request, deadline_id: str):
    """Delete a regulatory deadline."""
    engine = request.app.state.db_engine
    
    def _delete():
        with engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM regulatory_deadlines WHERE id = :id"),
                {"id": deadline_id}
            )
            return result.rowcount
            
    try:
        rowcount = await asyncio.to_thread(_delete)
        if rowcount == 0:
            raise HTTPException(status_code=404, detail="Deadline not found.")
        return {"success": True, "message": "Deadline deleted successfully."}
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error deleting deadline {deadline_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete deadline.")

import calendar
def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = int(sourcedate.year + month / 12)
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

@router.post("/{deadline_id}/complete")
async def complete_deadline(request: Request, deadline_id: str):
    """Mark a deadline as complete. Increments date if recurring, otherwise deletes it."""
    engine = request.app.state.db_engine
    
    def _process():
        with engine.begin() as conn:
            # Get current deadline
            result = conn.execute(
                text("SELECT id, due_date, recurring_type FROM regulatory_deadlines WHERE id = :id"),
                {"id": deadline_id}
            )
            row = result.fetchone()
            if not row:
                return None
                
            recurring_type = row[2]
            current_date = row[1]
            
            if recurring_type == 'none':
                # One time, just delete it
                conn.execute(text("DELETE FROM regulatory_deadlines WHERE id = :id"), {"id": deadline_id})
                return {"action": "deleted"}
            
            # Calculate next date
            if recurring_type == 'monthly':
                next_date = add_months(current_date, 1)
            elif recurring_type == 'quarterly':
                next_date = add_months(current_date, 3)
            elif recurring_type == 'yearly':
                next_date = add_months(current_date, 12)
            else:
                next_date = current_date + timedelta(days=30)
                
            # Update
            conn.execute(
                text("UPDATE regulatory_deadlines SET due_date = :next_date WHERE id = :id"),
                {"next_date": next_date, "id": deadline_id}
            )
            return {"action": "updated", "next_date": next_date}

    try:
        res = await asyncio.to_thread(_process)
        if res is None:
            raise HTTPException(status_code=404, detail="Deadline not found.")
        return res
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error completing deadline {deadline_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete deadline.")
