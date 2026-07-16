"""Quick smoke test for the IngestFile pipeline."""

import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.ingest_file import IngestFile


def main():
    ingestor = IngestFile()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_csv = os.path.join(current_dir, "sample_test.csv")
    test_pdf = os.path.join(current_dir, "AXZIO_AI_B2B_Strategy_Report.pdf")

    print("=" * 50)
    print("Testing CSV Ingestion Pipeline...")
    print("=" * 50)

    result_csv = ingestor.process_file(test_csv)
    print("\n--- CSV Final JSON Output ---")
    print(json.dumps(result_csv, indent=2, default=str))

    print("\n" + "=" * 50)
    print("Testing PDF Ingestion Pipeline...")
    print("=" * 50)

    result_pdf = ingestor.process_file(test_pdf)
    
    # We truncate the page content for display purposes so the console doesn't overflow
    print("\n--- PDF Final JSON Output (Truncated Content) ---")
    if isinstance(result_pdf, dict) and "error" not in result_pdf:
        for key in result_pdf:
            if isinstance(result_pdf[key], dict) and "page_content" in result_pdf[key]:
                content = result_pdf[key]["page_content"]
                # Truncate content to 100 characters for terminal output readability
                result_pdf[key]["page_content"] = content[:100].replace('\n', ' ') + "... [TRUNCATED]"
                
    print(json.dumps(result_pdf, indent=2, default=str))


if __name__ == "__main__":
    main()
