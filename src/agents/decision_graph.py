from typing import Dict, Any, Literal, TypedDict
from langgraph.graph import StateGraph, START, END
from loguru import logger

from src.agents.guardrail import check_guardrail
from src.agents.router import AgentRouter

# ── State Schema ─────────────────────────────────────────────────────────────

DecisionVerdict = Literal["out_of_scope", "proceed"]

class DecisionState(TypedDict, total=False):
    """Mutable state passed between parallel decision nodes."""
    
    # ── Inputs ─────────────────────────────────────────────────────────────
    message: str
    memory_context: str
    
    # ── Parallel node outputs ──────────────────────────────────────────────
    guardrail_in_scope: bool
    route_decisions: list
    
    # ── Final verdict (set by decide_node) ─────────────────────────────────
    verdict: DecisionVerdict
    primary_route: str


# ── Node Implementations ─────────────────────────────────────────────────────

def guardrail_node(state: DecisionState) -> Dict[str, Any]:
    """Runs the guardrail check."""
    logger.info("Running guardrail check...")
    try:
        is_in_scope = check_guardrail(state["message"])
    except Exception as e:
        logger.warning(f"Guardrail failed, defaulting to in-scope: {e}")
        is_in_scope = True
    return {"guardrail_in_scope": is_in_scope}

def make_router_node(router: AgentRouter):
    """Closure factory to bind the existing AgentRouter instance."""
    def router_node(state: DecisionState) -> Dict[str, Any]:
        logger.info("Running LLM router...")
        try:
            routing_result = router.route_query(state["message"], state.get("memory_context", ""))
            decisions = routing_result.get("route_decisions", [])
        except Exception as e:
            logger.warning(f"Router failed, defaulting to general: {e}")
            decisions = [{"route": "general", "rewritten_query": state["message"], "reasoning": "Fallback"}]
        return {"route_decisions": decisions}
    return router_node

def decide_node(state: DecisionState) -> Dict[str, Any]:
    """Pure logic node: synthesizes parallel outputs into a final verdict."""
    in_scope = state.get("guardrail_in_scope", True)
    decisions = state.get("route_decisions", [])
    
    primary = decisions[0] if decisions else {"route": "general"}
    primary_route = primary.get("route", "general")
    
    if not in_scope:
        verdict = "out_of_scope"
        primary_route = "out_of_scope"
    else:
        verdict = "proceed"
        
    return {"verdict": verdict, "primary_route": primary_route}

# ── Graph Builder ────────────────────────────────────────────────────────────

def build_decision_graph(router: AgentRouter):
    """
    Builds a compiled LangGraph runnable that runs Guardrail and Router in parallel.
    """
    g = StateGraph(DecisionState)
    
    # Add nodes
    g.add_node("guardrail", guardrail_node)
    g.add_node("router", make_router_node(router))
    g.add_node("decide", decide_node)
    
    # Parallel execution from START
    g.add_edge(START, "guardrail")
    g.add_edge(START, "router")
    
    # Fan-in to decide node
    g.add_edge("guardrail", "decide")
    g.add_edge("router", "decide")
    
    g.add_edge("decide", END)
    
    return g.compile()
