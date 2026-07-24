from pydantic import BaseModel, Field
from typing import Literal
from langchain_core.prompts import PromptTemplate
from src.infrastructure.llm.llm_provider import get_router_llm
from src.infrastructure.log import log

# Define valid routes
VALID_ROUTES = ["general", "cashflow", "rag", "investment", "market"]

class RouteItem(BaseModel):
    """A single routing decision for a specific agent."""
    route: Literal["general", "cashflow", "rag", "investment", "market"] = Field(
        description="The agent to route the query to. Use 'general' for normal conversation."
    )
    rewritten_query: str = Field(
        description="The contextualized, standalone query optimized specifically for the target agent. "
                    "CRITICAL: If the route is 'rag', the query MUST be a search query extracting specific facts (e.g., 'Extract total amounts, due dates, and vendor names from the invoice' instead of 'Can you analyze my PDF'). "
                    "Resolve any pronouns (it, that, he, she) using Memory Context."
    )
    reasoning: str = Field(
        description="Brief reasoning for why this route was selected."
    )

class RouteDecision(BaseModel):
    """Schema for the LLM to output its routing decision(s)."""
    routes: list[RouteItem] = Field(
        description="A list of route items. Can be multiple if the user's query requires multiple tools."
    )

from langchain_core.output_parsers import PydanticOutputParser

class AgentRouter:
    """
    Intelligent router that decides which sub-agent should handle the user's query.
    Uses a fast LLM (e.g., Llama 3.1 8B or 3.3 70B via Groq) for classification and query rewriting.
    """
    def __init__(self):
        # We use temperature=0.0 for deterministic routing
        self.llm = get_router_llm(temperature=0.0)
        self.parser = PydanticOutputParser(pydantic_object=RouteDecision)
        
        self.prompt = PromptTemplate(
            template="""You are the master Orchestrator Router for an AI Financial Advisory System (FinVox).
Your job is to read the User Message and the available Memory Context, then route the user to the correct specialized agent.
CRITICAL: You must rewrite the user's query to be a standalone sentence if it contains pronouns (it, that, he) referring to past context.
CRITICAL: The rewritten query MUST be optimized for the specific tool. For example, if routing to 'rag' (Vector Search), rewrite "Can you analyze my PDF" to "Extract total amounts, due dates, and vendor names from the invoice."
CRITICAL: If routing to data-driven tools (cashflow, market, investment), you MUST replace relative time expressions (e.g., "this month") with absolute dates (e.g., "July 2026") using the Current Date provided. However, for 'general' conversation, keep natural words like "tomorrow" or "next week" as they are.

Valid Routes:
- general    : For greetings, small talk, normal conversation, or if the user is just answering a question.
- cashflow   : For questions about future cash flow, liquidity, income/expense predictions, or upcoming bills.
- rag        : For questions asking to read, analyze, or summarize uploaded documents, invoices, or past PDF reports.
- investment : For questions about how to invest surplus money, risk management, or portfolio advice.
- market     : For live stock market data, forex rates, or current economic news (e.g., Yahoo Finance, CSE).

{format_instructions}

Current Date and Time:
{current_time}

Memory Context (may be empty):
{memory_context}

User Message:
{user_message}

Analyze the message and context, then output the routes, rewritten queries, and reasoning.
""",
            input_variables=["memory_context", "user_message", "current_time"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )

    def route_query(self, user_message: str, memory_context: str = "") -> dict:
        """
        Routes the query to the appropriate agent and rewrites the query using memory context.
        """
        from datetime import datetime
        try:
            chain = self.prompt | self.llm | self.parser
            result: RouteDecision = chain.invoke({
                "user_message": user_message,
                "memory_context": memory_context if memory_context else "No memory available yet.",
                "current_time": datetime.now().strftime("%A, %B %d, %Y %H:%M:%S")
            })
            
            # Fallback check just in case LLM hallucinates a route
            final_decisions = []
            for item in result.routes:
                if item.route in VALID_ROUTES:
                    final_decisions.append({
                        "route": item.route,
                        "rewritten_query": item.rewritten_query,
                        "reasoning": item.reasoning
                    })
            
            if not final_decisions:
                final_decisions = [{"route": "general", "rewritten_query": user_message, "reasoning": "Fallback"}]
            
            log.info(f"Router Decisions: {final_decisions}")
            
            return {
                "route_decisions": final_decisions
            }
            
        except Exception as e:
            log.error(f"Router LLM failed, defaulting to 'general'. Error: {e}")
            return {
                "route_decisions": [{"route": "general", "rewritten_query": user_message, "reasoning": "LLM Error"}]
            }
