"""
Chunking strategies for FinVox ingestion pipeline.
Handles JSON (CSV/Tables) and Markdown (PDF) files.
"""

from typing import Dict, Any, List
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from src.infrastructure.config import PARENT_CHUNK_SIZE, CHILD_OVERLAP

def chunk_json_rows(
    data: Dict[str, Any],
    document_id: str,
    source_name: str,
    base_metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Chunk JSON rows extracted from CSVs or PDF tables.
    Each row (JSON object) becomes exactly ONE chunk to prevent data loss.
    """
    chunks = []
    base_meta = base_metadata or {}

    for row_idx, row_data in data.items():
        if not isinstance(row_data, dict):
            continue

        # Convert dictionary to a semantic string (Key: Value)
        semantic_text_parts = []
        for k, v in row_data.items():
            if v is not None and v != "":
                # Replace underscores with spaces in keys for better LLM comprehension
                clean_key = str(k).replace("_", " ").title()
                semantic_text_parts.append(f"{clean_key}: {v}")
        
        chunk_text = ", ".join(semantic_text_parts)
        
        if not chunk_text.strip():
            continue

        # Build chunk payload
        chunk = {
            "text": chunk_text,
            "document_id": document_id,
            "source": source_name,
            "title": base_meta.get("title", source_name),
            "strategy": "json_row",
            "chunk_index": int(row_idx) if str(row_idx).isdigit() else 0,
        }
        
        # Add any other metadata from the row itself or base_meta
        for k, v in base_meta.items():
            if k not in chunk:
                chunk[k] = v
                
        chunks.append(chunk)

    return chunks

def chunk_markdown_parent_child(
    md_text: str,
    document_id: str,
    source_name: str,
    base_metadata: Dict[str, Any] = None,
    chunk_size: int = PARENT_CHUNK_SIZE,
    chunk_overlap: int = CHILD_OVERLAP,
) -> List[Dict[str, Any]]:
    """
    Chunk Markdown text using a Parent-Child strategy.
    It first splits by Markdown headers to preserve structural context,
    then uses RecursiveCharacterTextSplitter for sections that are too long.
    """
    chunks = []
    base_meta = base_metadata or {}

    # Define headers to split on
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
    ]

    # 1. Split by headers
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False
    )
    md_header_splits = markdown_splitter.split_text(md_text)

    # 2. Split large sections further if needed
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    
    final_splits = text_splitter.split_documents(md_header_splits)

    for idx, doc in enumerate(final_splits):
        # Extract header metadata to prepend to the text for context
        header_context = " > ".join(
            [doc.metadata.get(f"Header {i}", "") for i in range(1, 5) if doc.metadata.get(f"Header {i}")]
        )
        
        # Prepend context to the text
        if header_context:
            chunk_text = f"[{header_context}]\n{doc.page_content}"
        else:
            chunk_text = doc.page_content

        chunk = {
            "text": chunk_text,
            "document_id": document_id,
            "source": source_name,
            "title": base_meta.get("title", source_name),
            "strategy": "markdown_parent_child",
            "chunk_index": idx,
        }

        # Merge base metadata
        for k, v in base_meta.items():
            if k not in chunk:
                chunk[k] = v
                
        # Merge header metadata explicitly as well
        for k, v in doc.metadata.items():
            if k not in chunk:
                chunk[k] = v

        chunks.append(chunk)

    return chunks
