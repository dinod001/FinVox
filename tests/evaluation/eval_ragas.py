"""
FinVox - RAGAS Evaluation Script
=================================
Evaluates the RAG pipeline using the RAGAS framework across three key metrics:
    1. Faithfulness      - hallucination check (does answer stay grounded in context?)
    2. Answer Relevance  - is the answer on-topic and direct?
    3. Context Precision - did Qdrant retrieve the right chunks?

Usage:
    python tests/evaluation/eval_ragas.py

Requirements:
    pip install ragas datasets langchain-openai

Prerequisites:
    - PDF documents already ingested into Qdrant
    - OPENAI_API_KEY set in .env
"""

import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from tests.evaluation.eval_setup import ensure_eval_users, EVAL_USER_RAGAS, EVAL_SESSION_RAGAS

# Ground Truth Dataset
EVAL_DATASET = [
    {
        "question": "What is the total net cashflow for July 2026?",
        "ground_truth": "The total net cashflow for July 2026 is LKR 2,450,000.",
    },
    {
        "question": "What are the VAT obligations for a Sri Lankan SME with revenue over LKR 60 million?",
        "ground_truth": "Sri Lankan SMEs with annual revenue exceeding LKR 60 million are required to register for VAT with the Inland Revenue Department (IRD) and charge 18% VAT on taxable supplies.",
    },
    {
        "question": "What is the invoice INV-2026-0842 net payable amount and due date?",
        "ground_truth": "Invoice INV-2026-0842 has a net payable amount of LKR 1,136,780 and is due on 29 July 2026.",
    },
    {
        "question": "What are the best short-term investment options for an SME with LKR 1 million surplus?",
        "ground_truth": "For a Sri Lankan SME with a LKR 1 million surplus, recommended short-term options include Treasury Bills, Fixed Deposits with licensed commercial banks, and money market funds.",
    },
    {
        "question": "How much did we spend on salaries in July 2026?",
        "ground_truth": "The total salary expenditure for July 2026 was LKR 850,000.",
    },
]


def generate_answers_and_contexts(dataset: list) -> list:
    """Runs each question through the FinVox orchestrator."""
    ensure_eval_users()
    print("\n[INFO] Loading FinVox Orchestrator...")
    from src.agents.orchestrator import AgentOrchestrator
    orchestrator = AgentOrchestrator()

    USER_ID = EVAL_USER_RAGAS
    SESSION_ID = EVAL_SESSION_RAGAS

    results = []
    for i, item in enumerate(dataset):
        q = item["question"]
        gt = item["ground_truth"]

        print(f"  [{i+1}/{len(dataset)}] Q: {q[:80]}...")
        t0 = time.perf_counter()
        try:
            res = orchestrator.chat(q, USER_ID, SESSION_ID)
            answer = res.get("answer", "")
            tool_output = res.get("tool_output", "")
            latency_ms = int((time.perf_counter() - t0) * 1000)
            context = tool_output if tool_output else answer

            results.append({
                "question": q,
                "answer": answer,
                "contexts": [context],
                "ground_truth": gt,
                "latency_ms": latency_ms,
            })
            print(f"  Answer ({latency_ms}ms): {answer[:120]}...")
        except Exception as e:
            print(f"  [ERROR] Failed: {e}")
            results.append({
                "question": q,
                "answer": "",
                "contexts": [""],
                "ground_truth": gt,
                "latency_ms": 0,
            })

    return results


def run_ragas_evaluation(results: list):
    """Runs the RAGAS scoring framework on collected results."""
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    except ImportError:
        print("\n[ERROR] RAGAS not installed. Run: pip install ragas datasets langchain-openai")
        return None

    print("\n[INFO] Running RAGAS Evaluation...")

    eval_data = {
        "question":     [r["question"] for r in results],
        "answer":       [r["answer"] for r in results],
        "contexts":     [r["contexts"] for r in results],
        "ground_truth": [r["ground_truth"] for r in results],
    }

    dataset = Dataset.from_dict(eval_data)

    scores = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision],
        llm=ChatOpenAI(model="gpt-4o-mini"),
        embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
    )

    return scores


def print_report(scores, results: list):
    """Prints evaluation report and saves JSON summary."""
    print("\n" + "=" * 60)
    print("  FinVox RAGAS Evaluation Report")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if scores:
        avg = (scores['faithfulness'] + scores['answer_relevancy'] + scores['context_precision']) / 3
        print(f"\n  Faithfulness     : {scores['faithfulness']:.4f} / 1.0")
        print(f"  Answer Relevance : {scores['answer_relevancy']:.4f} / 1.0")
        print(f"  Context Precision: {scores['context_precision']:.4f} / 1.0")
        print(f"  Overall Average  : {avg:.4f} / 1.0")

    avg_latency = sum(r["latency_ms"] for r in results) / len(results) if results else 0
    print(f"  Avg Query Latency: {avg_latency:.0f} ms")

    report_path = os.path.join(os.path.dirname(__file__), "ragas_report.json")
    report = {
        "timestamp": datetime.now().isoformat(),
        "scores": {k: float(v) for k, v in scores.items()} if scores else {},
        "avg_latency_ms": avg_latency,
        "results": results,
    }
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report saved: {report_path}")
    print("=" * 60)


if __name__ == "__main__":
    print("\n" + "#" * 60)
    print("#  FinVox - RAGAS RAG Pipeline Evaluation")
    print("#" * 60)

    results = generate_answers_and_contexts(EVAL_DATASET)
    scores = run_ragas_evaluation(results)
    print_report(scores, results)
