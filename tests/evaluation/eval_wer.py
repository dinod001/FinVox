"""
FinVox - WER (Word Error Rate) Voice Pipeline Evaluation
=========================================================
Evaluates Deepgram STT accuracy using Word Error Rate (WER) and
Character Error Rate (CER). Tests both standard English and
Singlish/code-mixed queries.

WER = (Substitutions + Deletions + Insertions) / Total Reference Words
Lower is better. 0.0 = perfect.

Usage:
    python tests/evaluation/eval_wer.py

Requirements:
    pip install jiwer
"""

import sys
import os
import json
from datetime import datetime

try:
    from jiwer import wer, cer
    JIWER_AVAILABLE = True
except ImportError:
    JIWER_AVAILABLE = False
    print("[WARN] jiwer not installed. Run: pip install jiwer")
    print("[INFO] Using manual WER fallback.\n")


# Test Dataset
# reference  = what the user actually said (ground truth)
# hypothesis = what Deepgram transcribed (from manual test sessions)
WER_DATASET = [
    {
        "label": "Standard cashflow query",
        "reference":  "What is the total net cashflow for July two thousand and twenty six?",
        "hypothesis": "What is the total net cashflow for July two thousand and twenty six?",
    },
    {
        "label": "Tax query",
        "reference":  "What are my VAT obligations for this quarter?",
        "hypothesis": "What are my VAT obligations for this quarter?",
    },
    {
        "label": "Investment query",
        "reference":  "I have a surplus of one point four million rupees. What should I invest in?",
        "hypothesis": "I have a surplus of one point four million rupees. What should I invest in?",
    },
    {
        "label": "Singlish cashflow query",
        "reference":  "Mage cash flow eke burn rate eka kiyada?",
        "hypothesis": "mage cashflow eke burn rate eka kiyada",
    },
    {
        "label": "Singlish tax query",
        "reference":  "Api tax eka save karanna monawada karanna oni this year?",
        "hypothesis": "api tax eka save karanna monawada karanna oni this year",
    },
    {
        "label": "Singlish investment query",
        "reference":  "Mage excess cash eka invest karanna hoda idea eka kiyada?",
        "hypothesis": "mage excess cash eka invest karanna hoda idea eka kiyada",
    },
    {
        "label": "Fast speech - revenue query",
        "reference":  "What was the total revenue for the first quarter of twenty twenty six?",
        "hypothesis": "What was the total revenue for the first quarter of twenty twenty six",
    },
    {
        "label": "Mixed language financial",
        "reference":  "Mage company eke net profit margin eka kiyada for this year?",
        "hypothesis": "mage company eke net profit margin eka kiyada for this year",
    },
]


def manual_wer(reference: str, hypothesis: str) -> float:
    """Levenshtein-based WER fallback if jiwer is unavailable."""
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()
    r, h = len(ref_words), len(hyp_words)
    dp = [[0] * (h + 1) for _ in range(r + 1)]
    for i in range(r + 1): dp[i][0] = i
    for j in range(h + 1): dp[0][j] = j
    for i in range(1, r + 1):
        for j in range(1, h + 1):
            if ref_words[i-1] == hyp_words[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    return dp[r][h] / max(len(ref_words), 1)


def evaluate_wer(dataset: list) -> list:
    """Evaluates WER and CER for each test case."""
    results = []
    for item in dataset:
        ref = item["reference"]
        hyp = item["hypothesis"]
        if JIWER_AVAILABLE:
            word_err = wer(ref, hyp)
            char_err = cer(ref, hyp)
        else:
            word_err = manual_wer(ref, hyp)
            char_err = manual_wer(ref.replace(" ", ""), hyp.replace(" ", ""))
        results.append({
            "label":       item["label"],
            "wer":         round(word_err, 4),
            "cer":         round(char_err, 4),
            "wer_percent": round(word_err * 100, 2),
        })
    return results


def print_report(results: list):
    """Prints WER report and saves JSON."""
    std = [r for r in results if "singlish" not in r["label"].lower()]
    singlish = [r for r in results if "singlish" in r["label"].lower()]

    avg_all = sum(r["wer"] for r in results) / len(results)
    avg_std = sum(r["wer"] for r in std) / len(std) if std else 0
    avg_sin = sum(r["wer"] for r in singlish) / len(singlish) if singlish else 0

    print("\n" + "=" * 60)
    print("  FinVox - WER Voice Pipeline Evaluation Report")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"\n  Overall WER  : {avg_all*100:.2f}%")
    print(f"  English WER  : {avg_std*100:.2f}%")
    print(f"  Singlish WER : {avg_sin*100:.2f}%")

    print(f"\n  {'Label':<35} {'WER':>7} {'CER':>7}")
    print("  " + "-" * 52)
    for r in results:
        print(f"  {r['label']:<35} {r['wer_percent']:>5.1f}%  {r['cer']*100:>5.1f}%")

    print("\n  Benchmarks: <5% = Production Ready, 5-15% = Acceptable, >15% = Needs tuning")

    report_path = os.path.join(os.path.dirname(__file__), "wer_report.json")
    with open(report_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "overall_wer": avg_all,
            "english_wer": avg_std,
            "singlish_wer": avg_sin,
            "results": results
        }, f, indent=2)
    print(f"  Report saved: {report_path}")
    print("=" * 60)


if __name__ == "__main__":
    print("\n" + "#" * 60)
    print("#  FinVox - WER Voice Pipeline Evaluation")
    print("#" * 60)
    results = evaluate_wer(WER_DATASET)
    print_report(results)
