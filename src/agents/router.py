from pydantic import BaseModel, Field
from typing import Literal
from langchain_core.prompts import PromptTemplate
from src.infrastructure.llm.llm_provider import get_router_llm
from src.infrastructure.log import log

# Define valid routes
VALID_ROUTES = ["general", "cashflow", "rag", "investment", "market", "tax"]

class RouteItem(BaseModel):
    """A single routing decision for a specific agent."""
    route: str = Field(
        description="CRITICAL: The agent to route the query to. MUST BE EXACTLY ONE OF: 'general', 'cashflow', 'rag', 'investment', 'market', 'tax'. DO NOT use table names like 'gusto_payroll'."
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
Your job is to read the User Message and the available Memory Context, then route the user to the correct specialized agent(s).
CRITICAL: If the user's query requires multiple different tools (e.g. checking a financial metric AND reading a document), you MUST return MULTIPLE routes in your list. Do NOT try to cram everything into one route. Split the question and rewrite the query for each specific agent.
CRITICAL: IMPORTANT CROSS-AGENT RULE: If a single sentence asks to combine or compare data across DIFFERENT domains (e.g., "Calculate the burn rate using the amount from the uploaded invoice"), you MUST split it into MULTIPLE routes (e.g., one 'rag' route for the invoice, one 'cashflow' route for the burn rate). However, if the query only involves ONE domain (e.g., "What is our burn rate?"), do NOT split it.
CRITICAL: You must rewrite the user's query to be a standalone sentence if it contains pronouns (it, that, he) referring to past context.
CRITICAL: The rewritten query MUST be optimized for the specific tool. For example, if routing to 'rag' (Vector Search), rewrite "Can you analyze my PDF" to "Extract total amounts, due dates, and vendor names from the invoice."
CRITICAL: If routing to data-driven tools (cashflow, market, investment), you MUST replace relative time expressions (e.g., "this month") with absolute dates (e.g., "July 2026") using the Current Date provided. However, for 'general' conversation, keep natural words like "tomorrow" or "next week" as they are.

Valid Routes:
- general    : For greetings, small talk, non-financial queries, or if the user is just answering a simple question. DO NOT use this for ANY financial explanations.
- cashflow   : For ANY questions about datasets, CSV tables, cash flow, ledgers, inflows, outflows, or SQL calculations. CRITICAL: Default to this route for ANY analytical questions about companies, EPS, or if you need to query a table. DO NOT output table names as routes (e.g. use 'cashflow', not 'gusto_payroll').
- rag        : For questions about specific entities, vendors, policies, contracts, or specific bills/invoices. DO NOT route here if the user is asking about a structured CSV dataset or table. Use this mainly for PDFs, documents, or knowledge retrieval.
- investment : For questions about how to invest surplus money, risk management, or portfolio advice.
- market     : STRICTLY ONLY for explicitly requested LIVE stock prices, current exchange rates (forex), gold prices, or breaking news from the internet (e.g., "What is the live price of Apple?", "Current USD to LKR rate?"). DO NOT route general questions about company EPS or Market Cap here; those belong in cashflow.
- tax        : STRICTLY for any questions about tax rates, VAT, income tax, corporate tax, withholding tax, customs duties, tax compliance, tax filing deadlines, or tax regulations in Sri Lanka or any other country. This searches official government tax portals (ird.gov.lk, treasury.gov.lk, customs.gov.lk) for live, accurate tax data.

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
                route_name = item.route.lower().strip()
                if route_name not in VALID_ROUTES:
                    log.warning(f"LLM hallucinated route '{route_name}'. Defaulting to 'cashflow'.")
                    route_name = "cashflow"
                
                final_decisions.append({
                    "route": route_name,
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
