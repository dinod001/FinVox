import os
import uuid
import asyncio
import time
from pathlib import Path
import tempfile
import aiofiles

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from sqlalchemy import text
from src.services.ingest_service.pipeline import IngestionPipeline
from src.api.schemas import IngestionResponse
from src.infrastructure.log import log
from src.infrastructure.db.table_manager import sanitize_table_name
from src.infrastructure.db.qdrant_client import get_unique_documents

router = APIRouter(prefix="/ingestion", tags=["Data Ingestion"])

# It's better to instantiate the pipeline once if possible, but it loads models.
# To avoid slowing down startup or if models need to be lazy-loaded, we can instantiate it lazily.
_pipeline = None

def get_pipeline() -> IngestionPipeline:
    global _pipeline
    if _pipeline is None:
        log.info("Initializing Ingestion Pipeline...")
        _pipeline = IngestionPipeline()
    return _pipeline


@router.post("/upload", response_model=IngestionResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    user_id: str = Form(..., description="User uploading the file"),
    description: str = Form(..., description="Description of the file contents")
):
    """
    Upload and ingest a file (PDF, CSV, Excel).
    - PDFs are chunked, embedded, and stored in Qdrant (Vector DB) for RAG.
    - CSV/Excel files are cleaned and dynamically created as tables in Supabase (Relational DB) for Text-to-SQL.
    """
    
    # 0. Check if a dataset with this filename already exists
    filename = file.filename
    engine = request.app.state.db_engine
    try:
        # Check Structured (Supabase)
        table_name = sanitize_table_name(filename)
        def _check_sql():
            if not engine: return False
            with engine.connect() as conn:
                res = conn.execute(text("SELECT 1 FROM table_registry WHERE table_name = :t"), {"t": table_name})
                return res.fetchone() is not None
        
        sql_exists = await asyncio.to_thread(_check_sql)
        if sql_exists:
            raise HTTPException(status_code=409, detail=f"A structured dataset named '{filename}' already exists. Please delete it first or use a different file name.")
            
        # Check Unstructured (Qdrant)
        pdfs = await asyncio.to_thread(get_unique_documents)
        pdf_exists = any(p["source"] == filename for p in pdfs)
        if pdf_exists:
            raise HTTPException(status_code=409, detail=f"An AI document named '{filename}' already exists. Please delete it first or use a different file name.")
            
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error checking dataset existence: {e}")
    
    # 1. Save uploaded file to a temporary location
    try:
        suffix = Path(file.filename).suffix
        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        
        async with aiofiles.open(temp_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
            
    except Exception as e:
        log.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # 2. Run the ingestion pipeline
    document_id = str(uuid.uuid4())
    base_metadata = {
        "user_id": user_id,
        "description": description or "No description"
    }
    
    def _run_pipeline():
        pipeline = get_pipeline()
        return pipeline.run(
            file_path=temp_path,
            document_id=document_id,
            base_metadata=base_metadata,
            original_filename=file.filename
        )
        
    try:
        # Run blocking ingestion tasks in a background thread
        start_time = time.time()
        result = await asyncio.to_thread(_run_pipeline)
        end_time = time.time()
        time_taken_ms = int((end_time - start_time) * 1000)
        
        # 3. Format the response
        response = IngestionResponse(
            success=result.get("success", False),
            document_id=document_id,
            file_name=file.filename,
            time_taken_ms=time_taken_ms,
            message=result.get("message", "Ingestion completed") if result.get("success") else "Ingestion failed",
            error=result.get("error")
        )
        
        if response.success:
            if "supabase_table" in result and result.get("supabase_table"):
                # Relational DB results (CSV/Excel)
                response.supabase_table = result.get("supabase_table")
                response.rows_inserted = result.get("rows_inserted", 0)
                response.message = f"Successfully created table '{response.supabase_table}' with {response.rows_inserted} rows."
            elif "upserted_count" in result:
                # Vector DB results (PDFs)
                response.chunks_processed = result.get("chunks_processed", 0)
                response.upserted_count = result.get("upserted_count", 0)
                response.message = f"Successfully vectorized {response.upserted_count} chunks to Qdrant."
                
        else:
            raise HTTPException(status_code=400, detail=response.error)
            
        return response
        
    except Exception as e:
        log.error(f"Pipeline execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion pipeline failed: {str(e)}")
        
    finally:
        # 4. Clean up temp file
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception as e:
            log.warning(f"Failed to remove temp file {temp_path}: {e}")
