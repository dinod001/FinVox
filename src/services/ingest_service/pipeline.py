import os
import pandas as pd
from typing import Dict, Any, List

from src.infrastructure.log import log
from scripts.ingest_file import IngestFile
from src.services.ingest_service.chunkers import chunk_json_rows, chunk_markdown_parent_child
from src.infrastructure.llm.embeddings import get_embeddings
from src.infrastructure.db.qdrant_client import upsert_chunks, ensure_collection
from src.infrastructure.config import QDRANT_COLLECTION_NAME
from src.infrastructure.db.table_manager import save_dataframe_to_supabase

class IngestionPipeline:
    def __init__(self):
        self.ingester = IngestFile()
        self.embeddings_model = get_embeddings(show_progress=True)
        # Ensure the DB collection exists before inserting
        ensure_collection(collection_name=QDRANT_COLLECTION_NAME)

    def run(self, file_path: str, document_id: str, base_metadata: Dict[str, Any] = None, original_filename: str = None) -> Dict[str, Any]:
        """
        End-to-end ingestion pipeline:
        1. Ingest file to raw text/tables
        2. Chunk text and tables appropriately
        3. Embed the chunks
        4. Upsert to Qdrant Cloud
        """
        log.info("Starting ingestion pipeline for file: {}", file_path)
        source_name = original_filename if original_filename else os.path.basename(file_path)
        base_meta = base_metadata or {}
        
        # 1. INGEST
        log.info("Step 1: Extracting data from file...")
        extracted_data = self.ingester.process_file(file_path)
        
        if "error" in extracted_data:
            log.error("Ingestion failed: {}", extracted_data["error"])
            return {"success": False, "error": extracted_data["error"]}

        chunks = []
        
        # 2. CHUNK
        log.info("Step 2: Chunking data...")
        if file_path.lower().endswith(('.pdf')):
            # Handle PDF (Markdown text + Tables)
            pdf_text = extracted_data.get("text", "")
            pdf_tables = extracted_data.get("tables", [])
            
            # Chunk text
            if pdf_text.strip():
                text_chunks = chunk_markdown_parent_child(
                    md_text=pdf_text,
                    document_id=document_id,
                    source_name=source_name,
                    base_metadata=base_meta
                )
                chunks.extend(text_chunks)
                
            # Chunk tables
            for table_data in pdf_tables:
                table_chunks = chunk_json_rows(
                    data=table_data,
                    document_id=document_id,
                    source_name=source_name,
                    base_metadata=base_meta
                )
                chunks.extend(table_chunks)
        else:
            # Handle CSV/Excel (Pure Tables) -> Save dynamically to Supabase
            
            # Reconstruct the DataFrame from the extracted JSON rows
            # IngestFile returns a dict with row indices as keys: {"0": {...}, "1": {...}}
            if isinstance(extracted_data, dict):
                df = pd.DataFrame.from_dict(extracted_data, orient='index')
            else:
                df = pd.DataFrame(extracted_data)
            
            # Use base_metadata to get the description (or default to a generic one)
            description = base_meta.get("description", f"Table uploaded from {source_name}")
            
            log.info("Step 2 & 3 & 4: Saving CSV data directly to Supabase as a native table...")
            result = save_dataframe_to_supabase(df, filename=source_name, description=description)
            
            if not result.get("success"):
                return {"success": False, "error": result.get("error")}
                
            return {
                "success": True,
                "document_id": document_id,
                "chunks_processed": 0,
                "upserted_count": 0,
                "supabase_table": result.get("table_name"),
                "rows_inserted": result.get("rows_inserted")
            }
            
        if not chunks:
            log.warning("No chunks were generated from the document.")
            return {"success": False, "error": "No chunks generated"}
            
        log.info("Generated {} total chunks.", len(chunks))

        # 3. EMBED
        log.info("Step 3: Generating embeddings...")
        try:
            texts_to_embed = [chunk["text"] for chunk in chunks]
            vectors = self.embeddings_model.embed_documents(texts_to_embed)
            log.info("Successfully generated embeddings for {} chunks.", len(vectors))
        except Exception as e:
            log.error("Failed to generate embeddings: {}", e)
            return {"success": False, "error": str(e)}

        # 4. UPSERT TO QDRANT
        log.info("Step 4: Upserting into Qdrant database...")
        ensure_collection(collection_name=QDRANT_COLLECTION_NAME)
        
        try:
            upserted_count = upsert_chunks(
                chunks=chunks,
                embeddings=vectors,
                collection_name=QDRANT_COLLECTION_NAME
            )
            log.success("Pipeline completed! Upserted {} points for document '{}'", upserted_count, document_id)
            
            return {
                "success": True,
                "document_id": document_id,
                "chunks_processed": len(chunks),
                "upserted_count": upserted_count
            }
        except Exception as e:
            log.error("Failed to upsert chunks to Qdrant: {}", e)
            return {"success": False, "error": str(e)}
