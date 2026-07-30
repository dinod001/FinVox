from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.infrastructure.llm.llm_provider import get_router_llm
from src.infrastructure.log import log

# ── 1. System Prompt & Examples for Guardrail ───────────────────────────────

_GUARDRAIL_SYSTEM = """\
You are a strict scope filter for FinVox, an AI-Powered SME Financial Advisory System.
Your job is to decide whether the user's message is within the assistant's domain.

IN-SCOPE — the assistant should help with ANY of the following, even if implicitly implied:
  • SME finance, cash flow, revenue, expenses, budgets, taxes, accounting, and ROI calculations.
  • Tax rates, VAT rates, income tax, corporate tax, withholding tax, customs duties — for Sri Lanka OR any country. Knowing tax rates is a core business need.
  • General business operations, purchasing equipment, cost savings, production, and hiring (as these affect business finances).
  • Investments, stock market, fixed deposits, wealth management, and economic trends.
  • Data analysis, summarizing datasets, identifying highest/lowest values, and formatting data into tables or charts.
  • Analyzing financial documents (invoices, receipts, financial reports, ledgers).
  • Greetings, small talk, thanks (these are still in-scope; the main assistant handles them).
  • Short confirmations, replies, or selections made in the context of an ongoing conversation (e.g., "yes", "no", "confirm", "proceed", "cancel").
  • Brief fragments consisting of dates, quarters, amounts, currency, or any terms (e.g., "Q1 2026", "LKR 100,000", "what about expenses?", "next month").
  • Conversational fillers, thinking words, and pauses (e.g., "umm", "let me check", "wait a second", "I don't know").
  • Be highly permissive: if a query can be even loosely interpreted as analyzing business data, making a business decision, or exploring business concepts, it is IN-SCOPE.

CRITICAL CONTEXT RULE:
If the user's message is a short fragment or follow-up question (e.g., "can you give me number", "what about the other one", "show it to me"), you MUST read the "RECENT CONVERSATION CONTEXT". If the ongoing conversation is about finance or data analysis, you MUST classify the fragment as IN-SCOPE. Do not reject fragments as gibberish if they make sense in context.

OUT-OF-SCOPE — politely refuse ONLY IF it is completely unrelated to business, data, or finance:
  • General world knowledge (presidents, capitals, celebrities, politics, general science trivia).
  • Medical advice, generic weather, sports scores.
  • Coding help (unrelated to data analysis), jokes, riddles, role-play, story generation.
  • Gibberish or random non-questions.
Answer with ONE WORD ONLY: `in_scope` or `out_of_scope`.
No explanation, no punctuation, no other tokens.
"""

_GUARDRAIL_EXAMPLES = """\
Examples:
  USER: "What is my total cash inflow for Q1 2026?"       → in_scope
  USER: "Analyze this invoice for me."                    → in_scope
  USER: "Hey there, FinVox!"                              → in_scope
  USER: "Should I invest my surplus in FDs or stocks?"    → in_scope
  USER: "What are the financial trends for retail?"       → in_scope
  USER: "How is inflation affecting small businesses?"    → in_scope
  USER: "Calculate the ROI and payback period for a new machine." → in_scope
  USER: "What is my profit margin if I buy an oven for $5000?" → in_scope
  USER: "Give me a table summarizing the total expenses grouped by Category." → in_scope
  USER: "can u tell me the current tax of sri lanka today ?" → in_scope
  USER: "What is the current VAT rate in Sri Lanka?"      → in_scope
  USER: "What is the corporate income tax rate in Sri Lanka 2024?" → in_scope
  USER: "Who is the president of the USA?"                → out_of_scope
  USER: "What's the weather in Colombo today?"            → out_of_scope
  USER: "Write a python script for machine learning."     → out_of_scope
  USER: "Tell me a joke about a duck."                    → out_of_scope
  USER: "machna ape market, and invesrmen atharin lankawe tax sambadna hiyana kiyana hoda ekkena kawuda ??" → in_scope
  USER: "Who are the best tax consultants in Sri Lanka?"  → in_scope
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
    template="{system}\n\n{examples}\n\n=== RECENT CONVERSATION CONTEXT ===\n{memory_context}\n\nUSER: \"{query}\"\nDECISION:",
    input_variables=["query", "memory_context"],
    partial_variables={
        "system": _GUARDRAIL_SYSTEM,
        "examples": _GUARDRAIL_EXAMPLES
    }
)

def check_guardrail(user_message: str, memory_context: str = "") -> bool:
    """
    Checks if the user's message is within the FinVox domain.
    Returns True if in-scope, False if out-of-scope.
    """
    log.info(f"Running guardrail check for message: '{user_message}'")
    try:
        llm = get_router_llm()
        
        chain = GUARDRAIL_PROMPT | llm | StrOutputParser()
        
        result: str = chain.invoke({"query": user_message, "memory_context": memory_context})
        
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
