"""
FinVox — Comprehensive Orchestrator Test Suite
Tests the full pipeline: Data Ingestion + Multi-Agent Orchestrator

Test Phases:
    Phase 0: Ingest sample CSV (cashflow data) -> Supabase
    Phase 1: Ingest sample PDF (invoice)       -> Qdrant
    Phase 2: General conversation
    Phase 3: Cashflow analysis (uses ingested CSV)
    Phase 4: RAG query (uses ingested PDF invoice)
    Phase 5: Investment advice
    Phase 6: Multi-route fan-out (Cashflow + Market)
    Phase 7: Complex multi-route (RAG + Cashflow + Investment)
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.orchestrator import AgentOrchestrator

# ── File Paths ────────────────────────────────────────────────────────────────
CSV_PATH     = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample', 'sme_cashflow_sample.csv')
PDF_PATH     = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample', 'sample_invoice.pdf')
USER_ID      = "test_user_finvox"
SESSION_ID   = "22222222-2222-2222-2222-222222222222"

# ── Helpers ───────────────────────────────────────────────────────────────────
def header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_result(res: dict):
    print(f"  Routes  : {res['routes']}")
    if res.get('tool_output'):
        preview = res['tool_output'][:300].replace('\n', ' ')
        print(f"  Tool Out: {preview}...")
    print(f"  Answer  : {res['answer'][:500]}")
    print(f"  Latency : {res['latency_ms']} ms")

def check_data_ready() -> bool:
    """
    Lightweight pre-flight check.
    Verifies that the CSV and PDF sample files exist on disk.
    Actual DB-level check (Supabase table / Qdrant points) is done
    inside test_ingest.py — run that first if this is a fresh environment.
    """
    csv_ok = os.path.exists(os.path.abspath(CSV_PATH))
    pdf_ok = os.path.exists(os.path.abspath(PDF_PATH))

    if not csv_ok or not pdf_ok:
        print("\n[WARN] Sample data files not found!")
        if not csv_ok:
            print(f"  Missing: {CSV_PATH}  ->  run: python generate_dataset.py")
        if not pdf_ok:
            print(f"  Missing: {PDF_PATH}  ->  run: python generate_invoice.py")
        print("  Then run: python tests/test_ingest.py")
        print("  Orchestrator tests will continue but RAG/Cashflow results may be empty.\n")
        return False

    print("  [OK] Sample files found. Assuming data is ingested.")
    print("  [TIP] If DB is fresh, run 'python tests/test_ingest.py' first.\n")
    return True


# ── Phase 2–7: Orchestrator Tests ─────────────────────────────────────────────
def run_orchestrator_tests():

    orchestrator = AgentOrchestrator()

    # ── Phase 2: General Conversation ─────────────────────────────────────
    header("PHASE 2: General Conversation")
    msg = "Hello FinVox! I'm the owner of LankaTech Solutions. What can you help me with?"
    print(f"  User: {msg}")
    print_result(orchestrator.chat(msg, USER_ID, SESSION_ID))

    time.sleep(1)

    # ── Phase 3: Cashflow Analysis (SQL on ingested CSV) ──────────────────
    header("PHASE 3: Cashflow Analysis (Ingested CSV)")
    msg = "What is the total net cashflow for July 2026? How much did we spend on Salaries?"
    print(f"  User: {msg}")
    print_result(orchestrator.chat(msg, USER_ID, SESSION_ID))

    time.sleep(1)

    # ── Phase 4: RAG — Invoice Query (uses Qdrant) ────────────────────────
    header("PHASE 4: RAG Document Query (Invoice PDF)")
    msg = "I uploaded invoice INV-2026-0842. What is the net payable amount, due date, and which client is it billed to?"
    print(f"  User: {msg}")
    print_result(orchestrator.chat(msg, USER_ID, SESSION_ID))

    time.sleep(1)

    # ── Phase 5: Investment Advice ────────────────────────────────────────
    header("PHASE 5: Investment Advice")
    msg = "We have a surplus of LKR 1.4 million this year. What are the best short-term investment options for an IT company in Sri Lanka?"
    print(f"  User: {msg}")
    print_result(orchestrator.chat(msg, USER_ID, SESSION_ID))

    time.sleep(1)

    # ── Phase 6: Multi-Route Fan-Out (Cashflow + Market) ─────────────────
    header("PHASE 6: Multi-Route Fan-Out (Cashflow + Market)")
    msg = "Give me a cashflow summary for Q2 2026 (April–June) and also tell me the current market status of the CSE."
    print(f"  User: {msg}")
    print_result(orchestrator.chat(msg, USER_ID, SESSION_ID))

    time.sleep(1)

    # ── Phase 7: Complex (RAG + Cashflow + Investment) ────────────────────
    header("PHASE 7: Complex Multi-Route (RAG + Cashflow + Investment)")
    msg = ("I have an invoice INV-2026-0842 for LKR 1,136,780 due on 29 July 2026. "
           "Based on my cashflow data for July 2026, can I cover this payment? "
           "If I have a surplus after paying it, what should I invest in?")
    print(f"  User: {msg}")
    print_result(orchestrator.chat(msg, USER_ID, SESSION_ID))

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "#" * 60)
    print("#   FinVox — Full System Test Suite")
    print("#   LankaTech Solutions (Pvt) Ltd — Test Run")
    print("#" * 60)

    # Pre-flight: verify sample files exist (ingestion done via test_ingest.py)
    check_data_ready()

    # Run orchestrator tests
    run_orchestrator_tests()

    print("\n" + "#" * 60)
    print("#   All Tests Completed!")
    print("#" * 60 + "\n")
