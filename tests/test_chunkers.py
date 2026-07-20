import os
import sys

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.ingest_service.chunkers import chunk_json_rows, chunk_markdown_parent_child
from scripts.ingest_file import IngestFile

def run_integration_test():
    print("="*60)
    print("Integration Test: Data Ingestion -> Chunkers")
    print("="*60)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "sample_test.csv")
    pdf_path = os.path.join(current_dir, "AXZIO_AI_B2B_Strategy_Report.pdf")
    
    ingester = IngestFile()
    
    # ---------------------------------------------------------
    # 1. Test CSV Ingestion -> JSON Chunker
    # ---------------------------------------------------------
    print("\n--- 1. Testing CSV Pipeline ---")
    csv_data = ingester.process_file(csv_path)
    
    if "error" in csv_data:
        print(f"Error ingesting CSV: {csv_data['error']}")
    else:
        csv_chunks = chunk_json_rows(
            data=csv_data,
            document_id="doc-csv-123",
            source_name="sample_test.csv",
            base_metadata={"company": "Test SME"}
        )
        print(f"Generated {len(csv_chunks)} chunks from CSV.")
        for i, chunk in enumerate(csv_chunks):
            print(f"  -> Chunk {i}: {chunk['text']}")
            
    # ---------------------------------------------------------
    # 2. Test PDF Ingestion -> Markdown + JSON Chunkers
    # ---------------------------------------------------------
    print("\n--- 2. Testing PDF Pipeline ---")
    pdf_data = ingester.process_file(pdf_path)
    
    if "error" in pdf_data:
        print(f"Error ingesting PDF: {pdf_data['error']}")
    else:
        pdf_text = pdf_data.get("text", "")
        pdf_tables = pdf_data.get("tables", [])
        
        # 2a. Chunk Markdown Text
        md_chunks = chunk_markdown_parent_child(
            md_text=pdf_text,
            document_id="doc-pdf-456",
            source_name="AXZIO_AI_B2B_Strategy_Report.pdf"
        )
        print(f"Generated {len(md_chunks)} text chunks from PDF Markdown.")
        
        # 2b. Chunk PDF Tables
        table_chunks = []
        for table_data in pdf_tables:
            chunks = chunk_json_rows(
                data=table_data,
                document_id="doc-pdf-456",
                source_name="AXZIO_AI_B2B_Strategy_Report.pdf"
            )
            table_chunks.extend(chunks)
            
        print(f"Generated {len(table_chunks)} table row chunks from PDF.")
        
        # Display some PDF chunks
        print("\n--- Sample Text Chunk (Index 1) ---")
        if len(md_chunks) > 1:
            print(md_chunks[1]['text'])
            print("Metadata:", md_chunks[1])
            
        print("\n--- Sample Table Chunk (Index 0) ---")
        if len(table_chunks) > 0:
            print(table_chunks[0]['text'])
            print("Metadata:", table_chunks[0])

if __name__ == "__main__":
    run_integration_test()
