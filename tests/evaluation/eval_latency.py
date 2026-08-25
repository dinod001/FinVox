"""
FinVox - Latency Evaluation
============================
Measures wall-clock response latency per agent type:
    Cashflow, RAG, Tax, Investment, General

Usage:
    python tests/evaluation/eval_latency.py

Requirements:
    No extra dependencies (stdlib only).
"""

import sys
import os
import time
import json
import statistics
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from tests.evaluation.eval_setup import ensure_eval_users, EVAL_USER_LATENCY, EVAL_SESSION_LATENCY

LATENCY_TESTS = {
    "cashflow": [
        "What is the total net cashflow for July 2026?",
        "How much did we spend on salaries last month?",
        "What is my current burn rate?",
    ],
    "rag": [
        "What are the VAT filing deadlines for Sri Lankan SMEs?",
        "Summarize the invoice INV-2026-0842.",
        "What is the withholding tax rate on dividends?",
    ],
    "tax": [
        "What is the corporate income tax rate in Sri Lanka for 2026?",
        "What are my estimated advance income tax payments for Q3?",
        "Explain the APIT obligations for our payroll.",
    ],
    "investment": [
        "What short-term investment options suit a 1 million rupee surplus?",
        "Compare Treasury Bills vs Fixed Deposits for a 6-month horizon.",
    ],
    "general": [
        "Hello, what can you help me with?",
        "Can you give me a brief overview of FinVox?",
    ],
}

USER_ID = EVAL_USER_LATENCY
SESSION_ID = EVAL_SESSION_LATENCY


def measure_latency(orchestrator, queries: list, label: str) -> dict:
    """Runs queries and records response latency."""
    timings = []
    print(f"\n  [{label}] ({len(queries)} queries)")
    for q in queries:
        try:
            t0 = time.perf_counter()
            orchestrator.chat(q, USER_ID, SESSION_ID)
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            timings.append(elapsed_ms)
            print(f"    {elapsed_ms:>5}ms - {q[:65]}...")
        except Exception as e:
            print(f"    ERROR: {e}")

    if not timings:
        return {"label": label, "error": "All queries failed"}

    return {
        "label":     label,
        "avg_ms":    int(statistics.mean(timings)),
        "median_ms": int(statistics.median(timings)),
        "min_ms":    min(timings),
        "max_ms":    max(timings),
    }


def run_latency_evaluation() -> list:
    ensure_eval_users()
    print("\n[INFO] Loading FinVox Orchestrator...")
    from src.agents.orchestrator import AgentOrchestrator
    orchestrator = AgentOrchestrator()
    print("[OK] Orchestrator loaded.")

    results = []
    for agent_type, queries in LATENCY_TESTS.items():
        result = measure_latency(orchestrator, queries, agent_type)
        results.append(result)
        time.sleep(0.5)
    return results


def print_report(results: list):
    print("\n" + "=" * 60)
    print("  FinVox - Latency Evaluation Report")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    print(f"\n  {'Agent':<15} {'Avg':>8} {'Median':>8} {'Min':>8} {'Max':>8}")
    print("  " + "-" * 52)

    avgs = []
    for r in results:
        if "error" in r:
            print(f"  {r['label']:<15}  ERROR")
            continue
        print(f"  {r['label']:<15} {r['avg_ms']:>6}ms {r['median_ms']:>6}ms {r['min_ms']:>6}ms {r['max_ms']:>6}ms")
        avgs.append(r["avg_ms"])

    if avgs:
        print(f"\n  Overall Average Latency: {int(statistics.mean(avgs))}ms")

    print("\n  Benchmarks: <4000ms = Excellent, 4-8s = Acceptable, >8s = Needs optimization")

    report_path = os.path.join(os.path.dirname(__file__), "latency_report.json")
    with open(report_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "overall_avg_ms": int(statistics.mean(avgs)) if avgs else 0,
            "results": results
        }, f, indent=2)
    print(f"  Report saved: {report_path}")
    print("=" * 60)


if __name__ == "__main__":
    print("\n" + "#" * 60)
    print("#  FinVox - End-to-End Latency Evaluation")
    print("#" * 60)
    results = run_latency_evaluation()
    print_report(results)
