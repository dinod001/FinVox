"""Quick smoke test for the IngestFile pipeline."""

import json
import os
import sys

if os.environ.get("CI") == "true":
    print("Skipping tests in CI environment.")
    sys.exit(0)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.ingest_service.pipeline import IngestionPipeline
import uuid


def main():
    pipeline = IngestionPipeline()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_csv = os.path.join(current_dir, "sample_test.csv")
    test_pdf = os.path.join(current_dir, "AXZIO_AI_B2B_Strategy_Report.pdf")

    print("=" * 50)
    print("Testing CSV Ingestion Pipeline...")
    print("=" * 50)

    # Pass metadata describing the table
    csv_meta = {"description": "Sample test data containing SME sales figures"}
    result_csv = pipeline.run(test_csv, document_id=str(uuid.uuid4()), base_metadata=csv_meta)
    print("\n--- CSV Pipeline Output ---")
    print(json.dumps(result_csv, indent=2, default=str))

    print("\n" + "=" * 50)
    print("Testing PDF Ingestion Pipeline...")
    print("=" * 50)

    pdf_meta = {"description": "AXZIO AI B2B Strategy Report"}
    result_pdf = pipeline.run(test_pdf, document_id=str(uuid.uuid4()), base_metadata=pdf_meta)
    print("\n--- PDF Pipeline Output ---")
    print(json.dumps(result_pdf, indent=2, default=str))


if __name__ == "__main__":
    main()
