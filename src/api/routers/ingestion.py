import os
import uuid
import asyncio
from pathlib import Path
import tempfile
import aiofiles

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from src.services.ingest_service.pipeline import IngestionPipeline
from src.api.schemas import IngestionResponse
from src.infrastructure.log import log

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
    file: UploadFile = File(...),
    user_id: str = Form(..., description="User uploading the file"),
    description: str = Form(None, description="Description of the file contents"),
    company: str = Form(None, description="Associated company name"),
    year: str = Form(None, description="Relevant financial year")
):
    """
    Upload and ingest a file (PDF, CSV, Excel).
    - PDFs are chunked, embedded, and stored in Qdrant (Vector DB) for RAG.
    - CSV/Excel files are cleaned and dynamically created as tables in Supabase (Relational DB) for Text-to-SQL.
    """
    
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
        "description": description or "No description",
        "company": company or "Unknown",
        "year": year or "Unknown"
    }
    
    def _run_pipeline():
        pipeline = get_pipeline()
        return pipeline.run(
            file_path=temp_path,
            document_id=document_id,
            base_metadata=base_metadata
        )
        
    try:
        # Run blocking ingestion tasks in a background thread
        result = await asyncio.to_thread(_run_pipeline)
        
        # 3. Format the response
        response = IngestionResponse(
            success=result.get("success", False),
            document_id=document_id,
            message=result.get("message", "Ingestion completed") if result.get("success") else "Ingestion failed",
            error=result.get("error")
        )
        
        if response.success:
            if "upserted_count" in result:
                # Vector DB results
                response.chunks_processed = result.get("chunks_processed", 0)
                response.upserted_count = result.get("upserted_count", 0)
                response.message = f"Successfully vectorized {response.upserted_count} chunks to Qdrant."
            elif "supabase_table" in result:
                # Relational DB results
                response.supabase_table = result.get("supabase_table")
                response.rows_inserted = result.get("rows_inserted", 0)
                response.message = f"Successfully created table {response.supabase_table} with {response.rows_inserted} rows."
                
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
