from typing import Dict, Any, List
import json
import re
from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate

from src.infrastructure.db.crm_client import engine
from src.infrastructure.log import log
from src.infrastructure.llm.llm_provider import get_chat_llm
from sqlalchemy import text

def _get_table_context() -> str:
    """
    Fetches all dynamic tables from table_registry and formats their descriptions and schemas
    into a context string for the LLM.
    """
    if not engine:
        return "Database engine not initialized."
        
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT table_name, description, schema_info FROM table_registry"))
            rows = result.fetchall()
            
            if not rows:
                return "No user-uploaded data tables are currently available in the database."
                
            context_parts = []
            for row in rows:
                table_name = row[0]
                description = row[1] or "No description provided"
                schema_json = row[2] or "{}"
                
                # Format schema nicely
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


@tool
def analyze_cashflow(query: str) -> str:
    """
    Use this tool to answer numerical, statistical, or data-driven questions about the user's 
    uploaded financial data, cashflow, liquidity, and expenses. 
    It automatically queries the underlying PostgreSQL database.
    
    Args:
        query: The user's specific numerical/analytical question.
    """
    log.info(f"CashFlow Tool triggered for query: {query}")
    
    context = _get_table_context()
    if "No user-uploaded data" in context or "Error" in context:
        return context
        
    llm = get_chat_llm(temperature=0)
    
    # ---------------------------------------------------------
    # STEP 1: Generate SQL Query
    # ---------------------------------------------------------
    sql_prompt = PromptTemplate.from_template(
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
"""
    )
    
    sql_chain = sql_prompt | llm
    
    try:
        log.info("Generating SQL query via LLM...")
        raw_llm_response = sql_chain.invoke({"context": context, "query": query})
        
        # Clean the response just in case the LLM ignored instructions and used markdown
        sql_query = raw_llm_response.content.strip()
        sql_query = re.sub(r"^```sql", "", sql_query, flags=re.IGNORECASE)
        sql_query = re.sub(r"^```postgres", "", sql_query, flags=re.IGNORECASE)
        sql_query = re.sub(r"^```", "", sql_query)
        sql_query = re.sub(r"```$", "", sql_query)
        sql_query = sql_query.strip()
        
        log.info(f"Generated SQL: {sql_query}")
        
    except Exception as e:
        log.error(f"Failed to generate SQL: {e}")
        return "Sorry, I encountered an error while trying to generate the SQL query."

    # ---------------------------------------------------------
    # STEP 2: Validate SQL Query (SECURITY)
    # ---------------------------------------------------------
    if not sql_query.upper().startswith("SELECT"):
        log.warning(f"Blocked non-SELECT query: {sql_query}")
        return "Security Error: I am only allowed to execute SELECT queries. The generated query was blocked."

    # ---------------------------------------------------------
    # STEP 3: Execute SQL Query
    # ---------------------------------------------------------
    try:
        log.info("Executing SQL query...")
        with engine.connect() as conn:
            # Enforce read-only transaction as an extra safety net
            conn.execute(text("SET TRANSACTION READ ONLY;"))
            result = conn.execute(text(sql_query))
            rows = result.fetchall()
            
            # Format results
            if not rows:
                db_results = "No data found matching the query."
            else:
                # Convert rows to a list of dicts for the LLM
                columns = result.keys()
                db_results = str([dict(zip(columns, row)) for row in rows])
                
            log.info(f"Query returned {len(rows)} rows.")
            
    except Exception as e:
        log.error(f"SQL Execution Error: {e}")
        return f"I encountered a database error while executing the query: {str(e)}"

    # ---------------------------------------------------------
    # STEP 4: Format Final Answer
    # ---------------------------------------------------------
    answer_prompt = PromptTemplate.from_template(
        """You are a helpful Financial Advisor answering a user's question.
        
User's Question: "{query}"

I executed a database query to find the answer. Here are the raw results from the database:
{db_results}

Based on these results, provide a clear, natural, and concise answer to the user's question. 
If the results say "No data found", inform the user politely. Do not mention SQL or databases in your final answer.
"""
    )
    
    answer_chain = answer_prompt | llm
    
    try:
        log.info("Formatting final answer via LLM...")
        final_answer_response = answer_chain.invoke({"query": query, "db_results": db_results})
        return final_answer_response.content.strip()
    except Exception as e:
        log.error(f"Failed to format final answer: {e}")
        return f"Raw Data Results: {db_results}"

