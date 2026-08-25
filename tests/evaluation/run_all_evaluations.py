"""
FinVox - Master Evaluation Runner
===================================
Runs all evaluation scripts and produces a consolidated summary report.

Evaluations:
    1. WER     - Voice STT accuracy (English + Singlish)
    2. RAGAS   - RAG faithfulness, answer relevance, context precision
    3. Latency - Per-agent end-to-end response time

Usage:
    python tests/evaluation/run_all_evaluations.py
    python tests/evaluation/run_all_evaluations.py --wer-only
    python tests/evaluation/run_all_evaluations.py --skip-ragas
    python tests/evaluation/run_all_evaluations.py --skip-latency
"""

import sys
import os
import json
import argparse
from datetime import datetime

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(EVAL_DIR, '..', '..'))
sys.path.insert(0, ROOT_DIR)


def run_wer():
    print("\n" + "=" * 60)
    print("  [1/3] WER Evaluation")
    print("=" * 60)
    try:
        from tests.evaluation.eval_wer import WER_DATASET, evaluate_wer, print_report
        results = evaluate_wer(WER_DATASET)
        print_report(results)
        report_path = os.path.join(EVAL_DIR, "wer_report.json")
        if os.path.exists(report_path):
            with open(report_path) as f:
                return json.load(f)
    except Exception as e:
        print(f"  [ERROR] WER failed: {e}")
    return None


def run_ragas():
    print("\n" + "=" * 60)
    print("  [2/3] RAGAS Evaluation")
    print("=" * 60)
    try:
        from tests.evaluation.eval_ragas import EVAL_DATASET, generate_answers_and_contexts, run_ragas_evaluation, print_report
        results = generate_answers_and_contexts(EVAL_DATASET)
        scores = run_ragas_evaluation(results)
        print_report(scores, results)
        report_path = os.path.join(EVAL_DIR, "ragas_report.json")
        if os.path.exists(report_path):
            with open(report_path) as f:
                return json.load(f)
    except Exception as e:
        print(f"  [ERROR] RAGAS failed: {e}")
    return None


def run_latency():
    print("\n" + "=" * 60)
    print("  [3/3] Latency Evaluation")
    print("=" * 60)
    try:
        from tests.evaluation.eval_latency import run_latency_evaluation, print_report
        results = run_latency_evaluation()
        print_report(results)
        report_path = os.path.join(EVAL_DIR, "latency_report.json")
        if os.path.exists(report_path):
            with open(report_path) as f:
                return json.load(f)
    except Exception as e:
        print(f"  [ERROR] Latency failed: {e}")
    return None


def print_summary(wer_data, ragas_data, latency_data):
    print("\n" + "#" * 60)
    print("#  FinVox - Consolidated Evaluation Summary")
    print(f"#  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("#" * 60)

    print(f"\n  {'Metric':<30} {'Result':>15}")
    print("  " + "-" * 48)

    if ragas_data and ragas_data.get("scores"):
        s = ragas_data["scores"]
        avg = (s.get("faithfulness", 0) + s.get("answer_relevancy", 0) + s.get("context_precision", 0)) / 3
        print(f"  {'RAGAS Faithfulness':<30} {s.get('faithfulness', 0):>14.3f}")
        print(f"  {'RAGAS Answer Relevance':<30} {s.get('answer_relevancy', 0):>14.3f}")
        print(f"  {'RAGAS Context Precision':<30} {s.get('context_precision', 0):>14.3f}")
        print(f"  {'RAGAS Overall':<30} {avg:>14.3f}")
    else:
        print(f"  {'RAGAS':<30} {'Not run':>15}")

    if wer_data:
        print(f"  {'WER (English)':<30} {wer_data.get('english_wer', 0)*100:>13.1f}%")
        print(f"  {'WER (Singlish)':<30} {wer_data.get('singlish_wer', 0)*100:>13.1f}%")
    else:
        print(f"  {'WER':<30} {'Not run':>15}")

    if latency_data:
        print(f"  {'Avg Query Latency':<30} {latency_data.get('overall_avg_ms', 0):>12}ms")
    else:
        print(f"  {'Latency':<30} {'Not run':>15}")

    master_path = os.path.join(EVAL_DIR, "master_report.json")
    with open(master_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "ragas": ragas_data,
            "wer": wer_data,
            "latency": latency_data,
        }, f, indent=2)
    print(f"\n  Master report saved: {master_path}")
    print("#" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinVox Master Evaluation Runner")
    parser.add_argument("--skip-ragas", action="store_true")
    parser.add_argument("--skip-latency", action="store_true")
    parser.add_argument("--wer-only", action="store_true")
    args = parser.parse_args()

    print("\n" + "#" * 60)
    print("#  FinVox - Master Evaluation Suite")
    print("#" * 60)

    wer_data = run_wer()
    ragas_data = None if (args.skip_ragas or args.wer_only) else run_ragas()
    latency_data = None if (args.skip_latency or args.wer_only) else run_latency()

    print_summary(wer_data, ragas_data, latency_data)
