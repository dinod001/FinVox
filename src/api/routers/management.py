import asyncio
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text
from typing import List, Dict, Any

from src.infrastructure.log import log
from src.infrastructure.db.table_manager import delete_supabase_table
from src.infrastructure.db.qdrant_client import delete_chunks_by_document_id, get_unique_documents

router = APIRouter(prefix="/management", tags=["Data Management"])

@router.get("/datasets")
async def get_all_datasets(request: Request):
    """
    Fetch all user-uploaded datasets from both Supabase (Structured) and Qdrant (Unstructured).
    """
    engine = request.app.state.db_engine
    async def _get_sql():
        try:
            def _fetch_sql():
                if not engine:
                    return []
                with engine.connect() as conn:
                    res = conn.execute(text("SELECT id, table_name, description, created_at FROM table_registry ORDER BY created_at DESC"))
                    return [{"id": str(row[0]), "name": row[1], "description": row[2], "type": "Structured (CSV/Excel)", "created_at": str(row[3])} for row in res.fetchall()]
            return await asyncio.to_thread(_fetch_sql)
        except Exception as e:
            log.error(f"Failed to fetch SQL datasets for management: {e}")
            return []

    async def _get_qdrant():
        try:
            pdfs = await asyncio.to_thread(get_unique_documents)
            return [
                {
                    "id": p["document_id"],
                    "name": p["source"],
                    "description": p.get("description", p["title"]),
                    "type": "Unstructured (PDF)",
                    "created_at": p.get("created_at", "")
                }
                for p in pdfs
            ]
        except Exception as e:
            log.error(f"Failed to fetch PDF datasets for management: {e}")
            return []

    sql_datasets, pdf_datasets = await asyncio.gather(_get_sql(), _get_qdrant())

    return {
        "sql": sql_datasets,
        "qdrant": pdf_datasets
    }

@router.delete("/sql/{table_id}")
async def delete_sql_dataset(request: Request, table_id: str):
    """
    Delete a structured dataset (SQL Table) and its registry entry by ID.
    """
    engine = request.app.state.db_engine
    result = await asyncio.to_thread(delete_supabase_table, table_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return {"status": "success", "message": result.get("message")}

@router.delete("/qdrant/{document_id}")
async def delete_pdf_dataset(document_id: str):
    """
    Delete an unstructured dataset (PDF chunks) from Qdrant.
    """
    success = await asyncio.to_thread(delete_chunks_by_document_id, document_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete PDF from Qdrant.")
    return {"status": "success", "message": f"Deleted PDF document {document_id}"}
