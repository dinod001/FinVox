from typing import Any, Optional
import json
import re
import time
from langchain_core.prompts import PromptTemplate
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.infrastructure.log import log

# ── Module-level schema cache ─────────────────────────────────────────────────
# Avoids hitting Supabase on every cashflow query.
# Invalidated by ingest pipeline after a new table is uploaded.
_TABLE_CONTEXT_CACHE: Optional[str] = None
_TABLE_CONTEXT_TTL: float = 0.0  # epoch seconds
_TABLE_CONTEXT_TTL_SECS: int = 300  # 5-minute TTL

def invalidate_table_context_cache() -> None:
    """Call this from the ingest pipeline after a new dataset is uploaded."""
    global _TABLE_CONTEXT_CACHE, _TABLE_CONTEXT_TTL
    _TABLE_CONTEXT_CACHE = None
    _TABLE_CONTEXT_TTL = 0.0
    log.info("Table context cache invalidated.")


class CashflowTool:
    """
    Encapsulates all cashflow/SQL intelligence as a singleton-friendly class.
    The DB engine and LLM are injected once at startup and reused across calls.
    """

    def __init__(self, engine: Engine, llm: Any):
        self.engine = engine
        self.llm = llm

        self._sql_prompt = PromptTemplate.from_template(
            """You are a PostgreSQL expert Data Analyst.

Here are the available tables in the database, along with their descriptions and column schemas:
{context}

{kpis}

The user is asking: "{query}"

Based on the tables available, write a PostgreSQL query that will answer the user's question.
IMPORTANT RULES:
1. ONLY return the raw SQL query. Do not include markdown formatting like ```sql. Do not include any explanations.
2. The query MUST start with SELECT.
3. Be mindful of PostgreSQL syntax for casting strings to numeric if necessary.
4. When searching for specific categories or types (e.g. 'salary', 'rent'), ALWAYS check the appropriate categorical columns (like `category`, `transaction_type`, `type`, `status`) using ILIKE (e.g. `category ILIKE '%salary%'`).
   - CRITICAL SQL SYNTAX: If you use multiple `OR` conditions for categories, you MUST wrap them in parentheses BEFORE applying `AND` conditions like dates. Example: `WHERE (category ILIKE '%a%' OR category ILIKE '%b%') AND date >= ...`
5. DO NOT search in free-text `description` columns unless the user explicitly asks to search by description or note. Rely on the categorical columns to filter data.
6. CRITICAL DATE RULE: If the user asks for a specific year, month, or date range (e.g., 'for the year 2026', 'in Jan 2026'), you MUST apply a DATE filter using `>=` and `<` (e.g., `WHERE date >= '2026-01-01' AND date < '2027-01-01'`). NEVER assume the data is already filtered for that year.
7. DO NOT return thousands of raw rows. ALWAYS aggregate data (e.g. SUM, COUNT, GROUP BY) when analyzing large periods, or use LIMIT for top N queries.
8. NEVER calculate totals or perform arithmetic yourself! You MUST write SQL to do the math.
   - Carefully inspect the schema and data types.
   - When ordering to find the 'top' or 'highest' expenses (which are stored as negative numbers), you MUST use `ORDER BY SUM(amount_column) ASC`.
9. CRITICAL KPI RULE: If the user asks about a business metric or KPI, you MUST use the exact formula provided in the 'COMPANY KPIs' section above.
   - VERY IMPORTANT: If a formula instructs you to subtract expenses (e.g. `Total Income - Total Expenses`), you MUST translate the minus sign (`-`) to a plus sign (`+`) in your SQL logic (e.g. `SUM(Income) + SUM(Expenses)`) because expenses are already stored as NEGATIVE numbers. If you use a minus sign, you will double-subtract!
   - The easiest way to calculate Net Profit or Net Income is to just use `SUM([amount_column])` across all rows without splitting by Credit/Debit.
10. COMPOUND KPI FORMULAS: If a KPI formula uses other business terms (e.g. `(Operating Income / Total Revenue)`), you MUST look for the definitions of those terms in the 'COMPANY KPIs' section. Do not guess what 'Operating Income' means—find its formula in the list and substitute it. 
    - For example, if Operating Income is defined as `Total Income - Total Expenses`, substitute that as `(SUM(Credit) + SUM(Debit))` (Note the PLUS sign, as per Rule 9).
"""
        )

        self._answer_prompt = PromptTemplate.from_template(
            """You are a helpful Financial Advisor answering a user's question.

User's Question: "{query}"

I executed a database query to find the answer. Here are the raw results from the database:
{db_results}

Based on these results, provide a clear, natural, and concise answer to the user's question.
IMPORTANT RULES:
1. If the results say "No data found", inform the user politely. Do not mention SQL or databases.
2. If the result contains financial amounts, ALWAYS format them using 'LKR' or 'Rs.' (e.g., LKR 150,000). DO NOT use the $ symbol unless explicitly asked.
"""
        )

    # ── Private Helpers ───────────────────────────────────────────────────────

    def _get_table_context(self) -> str:
        """Fetches all dynamic tables from table_registry for the SQL prompt.
        Uses a module-level in-process cache (5-min TTL) to avoid DB round-trips
        on every cashflow tool call."""
        global _TABLE_CONTEXT_CACHE, _TABLE_CONTEXT_TTL

        # Return cached value if still valid
        if _TABLE_CONTEXT_CACHE and time.time() < _TABLE_CONTEXT_TTL:
            log.debug("Table context served from cache.")
            return _TABLE_CONTEXT_CACHE

        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT table_name, description, schema_info FROM table_registry")
                )
                rows = result.fetchall()

                if not rows:
                    return "No user-uploaded data tables are currently available in the database."

                context_parts = []
                for row in rows:
                    table_name = row[0]
                    description = row[1] or "No description provided"
                    schema_json = row[2] or "{}"
                    try:
                        schema_dict = json.loads(schema_json)
                        schema_str_parts = []
                        for k, v in schema_dict.items():
                            if k.lower() in ['category', 'transaction_type', 'type', 'status', 'label'] and 'str' in str(v).lower():
                                try:
                                    # Fetch sample distinct categories to help the LLM match exactly
                                    dist_res = conn.execute(text(f"SELECT DISTINCT \"{k}\" FROM {table_name} WHERE \"{k}\" IS NOT NULL LIMIT 30"))
                                    vals = [str(r[0]) for r in dist_res.fetchall() if r[0]]
                                    val_str = ", ".join(vals)
                                    if val_str:
                                        schema_str_parts.append(f"{k} (categorical values: [{val_str}])")
                                    else:
                                        schema_str_parts.append(f"{k} ({v})")
                                except Exception as inner_e:
                                    log.warning(f"Could not fetch distinct values for {k}: {inner_e}")
                                    schema_str_parts.append(f"{k} ({v})")
                            else:
                                schema_str_parts.append(f"{k} ({v})")
                        schema_str = ", ".join(schema_str_parts)
                    except Exception as exc:
                        log.warning(f"Error formatting schema: {exc}")
                        schema_str = schema_json

                    context_parts.append(
                        f"Table: {table_name}\n"
                        f"Description: {description}\n"
                        f"Columns: {schema_str}\n"
                    )
                result_str = "\n".join(context_parts)

                # Store in cache
                _TABLE_CONTEXT_CACHE = result_str
                _TABLE_CONTEXT_TTL = time.time() + _TABLE_CONTEXT_TTL_SECS
                log.info("Table context cache refreshed.")
                return result_str
        except Exception as e:
            log.error(f"Error fetching table context: {e}")
            return "Error fetching table schemas from database."

    # ── Public Interface ──────────────────────────────────────────────────────

    def analyze(self, query: str, kpis: str = "") -> str:
        """
        Full Text-to-SQL pipeline:
          1. Fetch available table schemas.
          2. LLM generates a SELECT query.
          3. Execute query against Supabase.
          4. LLM formats the raw DB result into a natural language answer.
        """
        log.info(f"CashflowTool.analyze called: '{query}'")

        context = self._get_table_context()
        if "No user-uploaded data" in context or "Error" in context:
            return context
            
        kpis_str = ""
        if kpis:
            kpis_str = f"=== COMPANY KPIs ===\n{kpis}"

        # ── Step 1: Generate SQL ──────────────────────────────────────────────
        sql_chain = self._sql_prompt | self.llm
        try:
            raw = sql_chain.invoke({"context": context, "kpis": kpis_str, "query": query})
            sql_query = raw.content.strip()
            # Strip any accidental markdown fences
            sql_query = re.sub(r"^```(sql|postgres)?", "", sql_query, flags=re.IGNORECASE)
            sql_query = re.sub(r"```$", "", sql_query).strip()
            log.info(f"Generated SQL: {sql_query}")
        except Exception as e:
            log.error(f"SQL generation failed: {e}")
            return "Sorry, I encountered an error while generating the SQL query."

        # ── Step 2: Security Validation ───────────────────────────────────────
        if not sql_query.upper().startswith("SELECT"):
            log.warning(f"Blocked non-SELECT query: {sql_query}")
            return "Security Error: Only SELECT queries are permitted."

        # ── Step 3: Execute SQL ───────────────────────────────────────────────
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SET TRANSACTION READ ONLY;"))
                result = conn.execute(text(sql_query))
                rows = result.fetchall()
                if not rows:
                    db_results = "No data found matching the query."
                else:
                    columns = result.keys()
                    max_rows = 50
                    dict_rows = [dict(zip(columns, row)) for row in rows[:max_rows]]
                    db_results = str(dict_rows)
                    if len(rows) > max_rows:
                        db_results += f"\n\n[NOTE: Output truncated. The query returned {len(rows)} rows, but only the first {max_rows} are shown here to prevent memory overload. Please refine the SQL query using aggregation (SUM, COUNT) or LIMIT.]"
                log.info(f"SQL returned {len(rows)} rows. Passed {min(len(rows), max_rows)} to LLM.")
        except Exception as e:
            log.error(f"SQL execution error: {e}")
            return f"Database error while executing the query: {str(e)}"

        # ── Step 4: Return Raw Results to Orchestrator ────────────────────────
        # We no longer use an LLM here to format the answer, because the Final 
        # Synthesis node in chat.py will do it (and it has the KPI context).
        # This prevents hallucinations like making up KPI targets.
        return f"The database successfully executed a query for: '{query}'\nResult: {db_results}"
