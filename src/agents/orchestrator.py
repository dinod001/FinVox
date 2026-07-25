import time
from typing import Dict, Any, List, Union
from loguru import logger
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END

from src.agents.state import AgentState
from src.agents.router import AgentRouter
from src.memory.memory_manager import MemoryManager
from src.infrastructure.llm.llm_provider import get_chat_llm
from src.infrastructure.db.crm_client import engine
from src.infrastructure.llm.embeddings import get_embeddings

from src.agents.tools.cashflow_tools import CashflowTool
from src.agents.tools.rag_tools import RAGTool
from src.agents.tools.market_tools import MarketTool
from src.agents.tools.investment_tools import InvestmentTool

class AgentOrchestrator:
    """
    Orchestrates the multi-agent system using a LangGraph StateGraph.
    Supports single-route and multi-route (fan-out) queries.
    """

    def __init__(self):
        self.llm_chat = get_chat_llm(temperature=0.0)
        self.router = AgentRouter()
        self.memory_manager = MemoryManager()
        
        # Instantiate Tool Singletons
        self.cashflow_tool = CashflowTool(engine=engine, llm=self.llm_chat)
        self.rag_tool = RAGTool(embedder=get_embeddings(), llm=self.llm_chat)
        self.market_tool = MarketTool()
        self.investment_tool = InvestmentTool()
        
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Constructs the LangGraph state machine with fan-out support."""
        workflow = StateGraph(AgentState)

        # 1. Define Nodes
        workflow.add_node("router", self.router_node)
        workflow.add_node("cashflow_agent", self.cashflow_agent)
        workflow.add_node("rag_agent", self.rag_agent)
        workflow.add_node("investment_agent", self.investment_agent)
        workflow.add_node("market_agent", self.market_agent)
        workflow.add_node("general_agent", self.general_agent)
        workflow.add_node("merge_responses", self.merge_responses_node)
        workflow.add_node("save_memory", self.save_memory_node)

        # 2. Define Edges (The Pipeline)
        workflow.set_entry_point("router")

        # Conditional routing from router (supports fan-out)
        workflow.add_conditional_edges(
            "router",
            self.route_classifier,
            {
                "cashflow": "cashflow_agent",
                "rag": "rag_agent",
                "investment": "investment_agent",
                "market": "market_agent",
                "general": "general_agent"
            }
        )

        # All agents converge to merge_responses (fan-in point)
        for agent_node in ["cashflow_agent", "rag_agent", "investment_agent", "market_agent", "general_agent"]:
            workflow.add_edge(agent_node, "merge_responses")

        # Merge -> Save -> END
        workflow.add_edge("merge_responses", "save_memory")
        workflow.add_edge("save_memory", END)

        return workflow.compile()

    # ── Node Implementations ────────────────────────────────────────

    def router_node(self, state: AgentState) -> Dict:
        """Retrieves memory context, then classifies the user's intent."""
        user_message = state["messages"][0].content
        user_id = state["user_id"]
        session_id = state["session_id"]
        
        # Get memory context
        try:
            memory_context = self.memory_manager.get_memory_context(user_id=user_id, session_id=session_id, query=user_message)
        except Exception as e:
            logger.warning(f"Memory context retrieval failed: {e}")
            memory_context = ""

        # Route query
        routing_result = self.router.route_query(user_message, memory_context)
        route_decisions = routing_result.get("route_decisions", [])
        
        return {
            "memory_context": memory_context,
            "route_decisions": route_decisions,
            "route_decision": route_decisions[0] if route_decisions else {"route": "general"}
        }

    def route_classifier(self, state: AgentState) -> Union[str, List[str]]:
        """Maps route decisions to actual graph nodes (Fan-Out)."""
        decisions = state.get("route_decisions", [])
        if not decisions:
            return "general"
        
        routes = []
        for d in decisions:
            route = d.get("route", "general")
            if route not in ["cashflow", "rag", "investment", "market", "general"]:
                route = "general"
            if route not in routes:
                routes.append(route)
        
        if len(routes) == 1:
            return routes[0]
        return routes

    def _generate_agent_response(self, state: AgentState, system_prompt: str, target_route: str, tool_output: str = "") -> str:
        """Standard LLM call for sub-agents."""
        # Find the specific rewritten query for this agent
        decisions = state.get("route_decisions", [])
        decision = next((d for d in decisions if d.get("route") == target_route), None)
        query = decision.get("rewritten_query") if decision else state["messages"][0].content
        
        memory_context = state.get("memory_context", "")

        system_content = f"{system_prompt}\n\n=== MEMORY CONTEXT ===\n{memory_context}"
        if tool_output:
            system_content += f"\n\n=== TOOL OUTPUT ===\n{tool_output}"

        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=query)
        ]
        
        response = self.llm_chat.invoke(messages)
        return response.content

    def cashflow_agent(self, state: AgentState) -> Dict:
        """Specialized Agent for Cashflow and Liquidity."""
        decisions = state.get("route_decisions", [])
        decision = next((d for d in decisions if d.get("route") == "cashflow"), {})
        query = decision.get("rewritten_query", state["messages"][0].content)
        
        try:
            tool_output = self.cashflow_tool.analyze(query)
        except Exception as e:
            logger.error(f"Cashflow tool error: {e}")
            tool_output = "Unable to fetch cashflow data."

        system_prompt = "You are a financial analyst specializing in SME cash flow. Analyze the tool output and provide clear predictions and insights."
        answer = self._generate_agent_response(state, system_prompt, "cashflow", tool_output)
        
        return {
            "agent_outputs": [{"route": "cashflow", "tool_output": tool_output, "answer": answer}]
        }

    def rag_agent(self, state: AgentState) -> Dict:
        """Specialized Agent for Document Analysis."""
        decisions = state.get("route_decisions", [])
        decision = next((d for d in decisions if d.get("route") == "rag"), {})
        query = decision.get("rewritten_query", state["messages"][0].content)
        
        try:
            tool_output = self.rag_tool.search(query)
        except Exception as e:
            logger.error(f"RAG tool error: {e}")
            tool_output = "Unable to fetch document data."

        system_prompt = "You are a document processing assistant. Extract the precise numerical details and entities from the provided document context."
        answer = self._generate_agent_response(state, system_prompt, "rag", tool_output)
        
        return {
            "agent_outputs": [{"route": "rag", "tool_output": tool_output, "answer": answer}]
        }

    def investment_agent(self, state: AgentState) -> Dict:
        """Specialized Agent for Investment Advice."""
        decisions = state.get("route_decisions", [])
        decision = next((d for d in decisions if d.get("route") == "investment"), {})
        query = decision.get("rewritten_query", state["messages"][0].content)
        
        try:
            tool_output = str(self.investment_tool.search(query))
        except Exception as e:
            logger.error(f"Investment tool error: {e}")
            tool_output = "Unable to fetch investment data."
            
        system_prompt = "You are an expert investment advisor for SMEs. Provide risk-assessed investment advice based on the user's query and the provided search results."
        answer = self._generate_agent_response(state, system_prompt, "investment", tool_output)
        return {
            "agent_outputs": [{"route": "investment", "tool_output": tool_output, "answer": answer}]
        }

    def market_agent(self, state: AgentState) -> Dict:
        """Specialized Agent for Market Data."""
        decisions = state.get("route_decisions", [])
        decision = next((d for d in decisions if d.get("route") == "market"), {})
        query = decision.get("rewritten_query", state["messages"][0].content)
        
        # Note: In a real system, we'd extract tickers from the query using another LLM call or regex.
        # For this refactor, we just pass a default to show the plumbing is wired correctly.
        try:
            tool_output = str(self.market_tool.fetch_data(["^GSPC", "LKR=X"]))
        except Exception as e:
            logger.error(f"Market tool error: {e}")
            tool_output = "Unable to fetch market data."
            
        system_prompt = "You are a live stock market analyst. Provide up-to-date information on the market based on the fetched data."
        answer = self._generate_agent_response(state, system_prompt, "market", tool_output)
        return {
            "agent_outputs": [{"route": "market", "tool_output": tool_output, "answer": answer}]
        }

    def general_agent(self, state: AgentState) -> Dict:
        """Specialized Agent for General Chat."""
        system_prompt = "You are FinVox, a friendly and professional financial AI assistant for SMEs in Sri Lanka. Answer general questions directly."
        answer = self._generate_agent_response(state, system_prompt, "general", "")
        return {
            "agent_outputs": [{"route": "general", "tool_output": "", "answer": answer}]
        }

    def merge_responses_node(self, state: AgentState) -> Dict:
        """Fan-in node: merges outputs from parallel agent nodes."""
        agent_outputs = state.get("agent_outputs", [])

        if len(agent_outputs) <= 1:
            # Single route: passthrough
            answer = agent_outputs[0]["answer"] if agent_outputs else "I'm sorry, I couldn't process that."
            tool_output = agent_outputs[0].get("tool_output", "") if agent_outputs else ""
            return {
                "final_answer": answer,
                "tool_output": tool_output,
                "messages": [AIMessage(content=answer)]
            }

        # Multi-route: synthesize
        logger.info(f"Merging {len(agent_outputs)} agent outputs into unified response")
        user_message = state["messages"][0].content
        
        combined_tool_output = ""
        for out in agent_outputs:
            route = out.get("route", "unknown").upper()
            answer = out.get("answer", "")
            combined_tool_output += f"=== {route} AGENT RESULT ===\n{answer}\n\n"

        system_prompt = "You are FinVox. Consolidate the following agent responses into a single, cohesive, and natural reply to the user. Do not explicitly say 'Agent X said this', just provide a unified financial answer."
        system_content = f"{system_prompt}\n\n=== AGENT RESULTS TO MERGE ===\n{combined_tool_output}"

        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=user_message)
        ]

        response = self.llm_chat.invoke(messages)
        merged_answer = response.content
        
        all_tool_output = "\n---\n".join(out.get("tool_output", "") for out in agent_outputs if out.get("tool_output"))

        return {
            "final_answer": merged_answer,
            "tool_output": all_tool_output,
            "messages": [AIMessage(content=merged_answer)]
        }

    def save_memory_node(self, state: AgentState) -> Dict:
        """Dedicated node to save short-term and long-term memory."""
        user_message = state["messages"][0].content
        answer = state.get("final_answer", "")
        user_id = state["user_id"]
        session_id = state["session_id"]
        
        try:
            # Save User Message to ST & Distill LT
            self.memory_manager.process_user_message(user_id=user_id, session_id=session_id, content=user_message)
            # Save Assistant Reply to ST
            self.memory_manager.save_assistant_message(user_id=user_id, session_id=session_id, content=answer)
            logger.info("Successfully updated memory context.")
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            
        return {}

    # ── Entry Point ───────────────────────────────────────────────

    def chat(self, user_message: str, user_id: str, session_id: str) -> Dict:
        """Run the graph for one interaction."""
        t0 = time.time()

        initial_state = {
            "messages": [HumanMessage(content=user_message)],
            "user_id": user_id,
            "session_id": session_id,
            "agent_outputs": [],
        }

        final_state = self.graph.invoke(initial_state)
        latency = int((time.time() - t0) * 1000)
        
        return {
            "answer": final_state.get("final_answer", ""),
            "routes": [d.get("route", "general") for d in final_state.get("route_decisions", [])],
            "tool_output": final_state.get("tool_output", ""),
            "latency_ms": latency
        }
