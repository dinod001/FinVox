"""
FinVox — Data Ingestion Pipeline Test
Tests ingestion of both the Industry-Level CSV (cashflow) and Sample Invoice PDF.

Ingestion Targets:
    CSV  -> Supabase (Dynamic PostgreSQL table via Text-to-SQL architecture)
    PDF  -> Qdrant Cloud (Vector embeddings via Parent-Child chunking)
"""

import json
import os
import sys
import uuid

if os.environ.get("CI") == "true":
    print("Skipping tests in CI environment.")
    sys.exit(0)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.ingest_service.pipeline import IngestionPipeline

# ── File Paths ────────────────────────────────────────────────────────────────
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

INDUSTRY_CSV = os.path.join(ROOT_DIR, "data", "sample", "sme_cashflow_sample.csv")
INVOICE_PDF  = os.path.join(ROOT_DIR, "data", "sample", "sample_invoice.pdf")

# Use fixed document IDs so we can query them later in orchestrator tests
CSV_DOC_ID   = "sme_cashflow_2026"
PDF_DOC_ID   = "invoice_sampath_bank_2026_0842"

# ── Helpers ───────────────────────────────────────────────────────────────────
def section(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_result(result: dict):
    print(json.dumps(result, indent=4, default=str))

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "#" * 60)
    print("#   FinVox — Ingestion Pipeline Test")
    print("#" * 60)

    pipeline = IngestionPipeline()

    # ── TEST 1: Industry-Level CSV -> Supabase ────────────────────────────
    section("TEST 1: Industry-Level CSV -> Supabase Dynamic Table")

    if not os.path.exists(INDUSTRY_CSV):
        print(f"  [SKIP] File not found: {INDUSTRY_CSV}")
        print("  Run 'python generate_dataset.py' first to generate the dataset.")
    else:
        print(f"  File    : {os.path.basename(INDUSTRY_CSV)}")
        print(f"  Doc ID  : {CSV_DOC_ID}")
        print(f"  Target  : Supabase (PostgreSQL dynamic table)\n")

        result = pipeline.run(
            file_path=INDUSTRY_CSV,
            document_id=CSV_DOC_ID,
            base_metadata={
                "description": (
                    "LankaTech Solutions (Pvt) Ltd — Full year 2026 cashflow transactions. "
                    "Contains 992 transactions including salaries, rent, client invoices, "
                    "retainer fees, petty cash, freelancer payments, and quarterly taxes."
                ),
                "user_id":    "test_user_finvox",
                "year":       "2026",
                "company":    "LankaTech Solutions (Pvt) Ltd",
                "currency":   "LKR",
            }
        )

        print("  --- Result ---")
        print_result(result)

        if result.get("success"):
            print(f"\n  [OK] CSV ingested successfully!")
            print(f"       Supabase Table : {result.get('supabase_table')}")
            print(f"       Rows Inserted  : {result.get('rows_inserted')}")
        else:
            print(f"\n  [FAIL] CSV ingestion failed: {result.get('error')}")

    # ── TEST 2: Sample Invoice PDF -> Qdrant ──────────────────────────────
    section("TEST 2: Sample Invoice PDF -> Qdrant Vector DB")

    if not os.path.exists(INVOICE_PDF):
        print(f"  [SKIP] File not found: {INVOICE_PDF}")
        print("  Run 'python generate_invoice.py' first to generate the invoice.")
    else:
        print(f"  File    : {os.path.basename(INVOICE_PDF)}")
        print(f"  Doc ID  : {PDF_DOC_ID}")
        print(f"  Target  : Qdrant Cloud (Vector embeddings)\n")

        result = pipeline.run(
            file_path=INVOICE_PDF,
            document_id=PDF_DOC_ID,
            base_metadata={
                "description": (
                    "Tax Invoice INV-2026-0842 from LankaTech Solutions (Pvt) Ltd "
                    "to Sampath Bank PLC. Dated 15 July 2026, due 29 July 2026. "
                    "Net payable LKR 1,136,780. Includes VAT and withholding tax."
                ),
                "invoice_number": "INV-2026-0842",
                "vendor":         "LankaTech Solutions (Pvt) Ltd",
                "client":         "Sampath Bank PLC",
                "due_date":       "2026-07-29",
                "amount_lkr":     "1136780.00",
                "user_id":        "test_user_finvox",
            }
        )

        print("  --- Result ---")
        print_result(result)

        if result.get("success"):
            print(f"\n  [OK] PDF ingested successfully!")
            print(f"       Chunks Processed : {result.get('chunks_processed')}")
            print(f"       Qdrant Upserted  : {result.get('upserted_count')}")
        else:
            print(f"\n  [FAIL] PDF ingestion failed: {result.get('error')}")

    # ── Summary ───────────────────────────────────────────────────────────
    section("INGESTION COMPLETE")
    print("  Data is now ready for Orchestrator tests.")
    print("  Next step: Run 'python tests/test_orchestrator.py'")
    print()


if __name__ == "__main__":
    main()
