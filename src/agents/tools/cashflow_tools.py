from typing import Any
import json
import re
from langchain_core.prompts import PromptTemplate
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.infrastructure.log import log


class CashflowTool:
    """
    Encapsulates all cashflow/SQL intelligence as a singleton-friendly class.
    The DB engine and LLM are injected once at startup and reused across calls.
    """

    def __init__(self, engine: Engine, llm: Any):
        self.engine = engine
        self.llm = llm

        # Compile prompt templates once at init time — avoids re-parsing per call.
        self._sql_prompt = PromptTemplate.from_template(
            """You are a PostgreSQL expert Data Analyst.

Here are the available tables in the database, along with their descriptions and column schemas:
{context}

The user is asking: "{query}"

Based on the tables available, write a PostgreSQL query that will answer the user's question.
IMPORTANT RULES:
1. ONLY return the raw SQL query. Do not include markdown formatting like ```sql. Do not include any explanations.
2. The query MUST start with SELECT.
3. Be mindful of PostgreSQL syntax for casting strings to numeric if necessary.
4. Always use ILIKE or LOWER() for string comparisons to avoid case-sensitivity bugs (e.g. LOWER(transaction_type) = 'credit').
5. DO NOT return thousands of raw rows. ALWAYS aggregate data (e.g. SUM, COUNT, GROUP BY) when analyzing large periods, or use LIMIT for top N queries.
6. NEVER calculate totals or perform arithmetic yourself! You MUST write SQL to do the math (e.g., using SUM, COUNT, GROUP BY).
   - Carefully inspect the schema and data types. If expenses/debits are already stored as negative numbers, do not subtract them again when calculating net flows. 
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
        """Fetches all dynamic tables from table_registry for the SQL prompt."""
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
                        schema_str = ", ".join([f"{k} ({v})" for k, v in schema_dict.items()])
                    except Exception:
                        schema_str = schema_json

                    context_parts.append(
                        f"Table: {table_name}\n"
                        f"Description: {description}\n"
                        f"Columns: {schema_str}\n"
                    )
                return "\n".join(context_parts)
        except Exception as e:
            log.error(f"Error fetching table context: {e}")
            return "Error fetching table schemas from database."

    # ── Public Interface ──────────────────────────────────────────────────────

    def analyze(self, query: str) -> str:
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

        # ── Step 1: Generate SQL ──────────────────────────────────────────────
        sql_chain = self._sql_prompt | self.llm
        try:
            raw = sql_chain.invoke({"context": context, "query": query})
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

        # ── Step 4: Format Answer ─────────────────────────────────────────────
        answer_chain = self._answer_prompt | self.llm
        try:
            response = answer_chain.invoke({"query": query, "db_results": db_results})
            return response.content.strip()
        except Exception as e:
            log.error(f"Answer formatting failed: {e}")
            return f"Raw Data Results: {db_results}"
