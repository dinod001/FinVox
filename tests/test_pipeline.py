import os
import sys

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.ingest_service.pipeline import IngestionPipeline
from datetime import datetime

def generate_doc_id(file_name: str) -> str:
    # Remove extension and space for a clean ID
    clean_name = os.path.splitext(file_name)[0].replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{clean_name}_{timestamp}"

def test_pipeline():
    print("="*60)
    print("Integration Test: End-to-End Pipeline (with HuggingFace)")
    print("="*60)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Setup CSV
    csv_file = "sample_test.csv"
    csv_path = os.path.join(current_dir, csv_file)
    csv_doc_id = generate_doc_id(csv_file)
    
    # 2. Setup PDF
    pdf_file = "AXZIO_AI_B2B_Strategy_Report.pdf"
    pdf_path = os.path.join(current_dir, pdf_file)
    pdf_doc_id = generate_doc_id(pdf_file)
    
    pipeline = IngestionPipeline()
    
    print(f"\n--- Testing CSV Ingestion [Doc ID: {csv_doc_id}] ---")
    result_csv = pipeline.run(
        file_path=csv_path,
        document_id=csv_doc_id,
        base_metadata={"author": "Test Agent", "type": "csv"}
    )
    print("\nCSV Pipeline Result:", result_csv)

    print(f"\n--- Testing PDF Ingestion [Doc ID: {pdf_doc_id}] ---")
    result_pdf = pipeline.run(
        file_path=pdf_path,
        document_id=pdf_doc_id,
        base_metadata={"author": "Test Agent", "type": "pdf"}
    )
    print("\nPDF Pipeline Result:", result_pdf)

if __name__ == "__main__":
    test_pipeline()
