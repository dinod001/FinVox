from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.infrastructure.llm.llm_provider import get_router_llm
from src.infrastructure.log import log

# ── 1. System Prompt & Examples for Guardrail ───────────────────────────────

_GUARDRAIL_SYSTEM = """\
You are a strict scope filter for FinVox, an AI-Powered SME Financial Advisory System.
Your job is to decide whether the user's message is within the assistant's domain.

IN-SCOPE — the assistant should help with:
  • SME finance, cash flow, revenue, expenses, budgets, taxes, and accounting.
  • Investments, stock market (e.g., CSE), fixed deposits, treasury bills, and wealth management.
  • Analyzing financial documents (invoices, receipts, financial reports, ledgers).
  • Greetings, small talk, thanks (these are still in-scope; the main assistant handles them).
  • Short confirmations, replies, or selections made in the context of an ongoing financial conversation (e.g., "yes", "no", "confirm", "proceed", "cancel").
  • Brief fragments consisting of dates, quarters, amounts, currency, or financial terms (e.g., "Q1 2026", "LKR 100,000", "what about expenses?", "next month").
  • Conversational fillers, thinking words, and pauses (e.g., "umm", "let me check", "wait a second", "I don't know").
  • Be highly permissive: if a short phrase or single word could plausibly be an answer to a financial question the assistant just asked, always classify it as in_scope.

OUT-OF-SCOPE — politely refuse:
  • General world knowledge (presidents, capitals, sports, history, celebrities, politics, general science trivia).
  • Medical advice, generic weather, sports scores.
  • Coding help, non-financial math problems, jokes, riddles, role-play, story generation.
  • Gibberish or random non-questions.
  • Anything you can't confidently tie to SME finance, business operations, document analysis, or market research.

Answer with ONE WORD ONLY: `in_scope` or `out_of_scope`.
No explanation, no punctuation, no other tokens.
"""

_GUARDRAIL_EXAMPLES = """\
Examples:
  USER: "What is my total cash inflow for Q1 2026?"       → in_scope
  USER: "Analyze this invoice for me."                    → in_scope
  USER: "Hey there, FinVox!"                              → in_scope
  USER: "Should I invest my surplus in FDs or stocks?"    → in_scope
  USER: "Who is the president of the USA?"                → out_of_scope
  USER: "What's the weather in Colombo today?"            → out_of_scope
  USER: "Write a python script for machine learning."     → out_of_scope
  USER: "Tell me a joke about a duck."                    → out_of_scope
  USER: "100,000 rupees"                                  → in_scope
  USER: "yes, proceed"                                    → in_scope
  USER: "no, cancel that"                                 → in_scope
  USER: "what about expenses?"                            → in_scope
  USER: "umm let me check"                                → in_scope
  USER: "wait a second"                                   → in_scope
  USER: "Q2 2026"                                         → in_scope
  USER: "I have a headache, what medicine should I take?" → out_of_scope
"""

# Removed Pydantic Schema since we use StrOutputParser

# ── 3. Langchain Setup ────────────────────────────────────────────────────────

GUARDRAIL_PROMPT = PromptTemplate(
    template="{system}\n\n{examples}\n\nUSER: \"{query}\"\nDECISION:",
    input_variables=["query"],
    partial_variables={
        "system": _GUARDRAIL_SYSTEM,
        "examples": _GUARDRAIL_EXAMPLES
    }
)

def check_guardrail(user_message: str) -> bool:
    """
    Checks if the user's message is within the FinVox domain.
    Returns True if in-scope, False if out-of-scope.
    """
    log.info(f"Running guardrail check for message: '{user_message}'")
    try:
        llm = get_router_llm()
        
        chain = GUARDRAIL_PROMPT | llm | StrOutputParser()
        
        result: str = chain.invoke({"query": user_message})
        
        # Clean the output string
        result_clean = result.strip().lower()
        is_in_scope = "in_scope" in result_clean
        
        log.info(f"Guardrail Decision String: {result_clean}")
        return is_in_scope
        
    except Exception as e:
        log.error(f"Guardrail check failed: {e}. Defaulting to in_scope.")
        # If the guardrail fails for some reason (e.g., API timeout), 
        # default to True (in_scope) so we don't break the user experience.
        return True
