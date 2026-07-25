"""
Friendly labels for the chain-of-thought timeline.

Maps internal stage / tool identifiers to human-readable strings the
UI shows users while their request is in flight. Keeps the wording
in one place so the chain-of-thought never says "cashflow" but
"Analyzing your cash flow and financial data".
"""

from typing import Optional, Tuple

STAGE_LABELS: dict[str, str] = {
    "router":          "Routing your question to the right financial expert",
    "guardrail":       "Checking if the question is within financial scope",
    "merge_responses": "Consolidating insights into a final report",
    "save_memory":     "Saving context for future reference",
}

# Tool-level labels keyed by (route, action). action is None for routes
# without a sub-action.
_TOOL_LABELS: dict[Tuple[str, Optional[str]], str] = {
    ("cashflow", None):     "Analyzing your cash flow and financial database",
    ("rag", None):          "Searching your uploaded company documents and notes",
    ("market", None):       "Fetching real-time stock and currency market data",
    ("investment", None):   "Searching trusted sources for investment opportunities",
    ("general", None):      "Composing a general financial response",
    ("out_of_scope", None): "Politely declining — outside the financial domain",
    ("multi", None):        "Running multiple specialized agents in parallel",
}

def tool_label(route: str, action: Optional[str] = None) -> str:
    """Friendly label for a single tool/agent invocation."""
    return (
        _TOOL_LABELS.get((route, action))
        or _TOOL_LABELS.get((route, None))
        or f"Running {route}{' / ' + action if action else ''}"
    )

def stage_label(stage: str) -> str:
    """Friendly label for a pipeline stage."""
    return STAGE_LABELS.get(stage, stage.replace("_", " ").title())
