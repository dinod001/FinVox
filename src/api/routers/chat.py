import asyncio
import json
import time
from typing import Any, Awaitable, Callable, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from src.api.schemas import ChatRequest, ChatResponse
from src.api.deps import get_orchestrator
from src.agents.orchestrator import AgentOrchestrator
from src.api.routers.chat_sessions import touch_session_sync
from src.api.event_labs import stage_label, tool_label
from src.infrastructure.observability import observe, update_current_trace, update_current_observation
from langfuse.langchain import CallbackHandler

router = APIRouter(prefix="/chat", tags=["Chat & Agents"])

OUT_OF_SCOPE_REPLY = "I'm a specialized financial assistant for FinVox. I can help you with cash flow, investments, market data, tax regulations, and business documents. I cannot help with that request."

# Type alias for the event emitter
EmitFn = Callable[[Dict[str, Any]], Awaitable[None]]

async def _noop_emit(_event: Dict[str, Any]) -> None:
    """Default emitter for the non-streaming path."""
    return None

def _ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)

def _save_memory_bg(orchestrator: AgentOrchestrator, user_id: str, session_id: str, message: str, answer: str) -> None:
    """Helper to save both user message and assistant reply to memory."""
    try:
        orchestrator.memory_manager.process_user_message(user_id, session_id, message)
        orchestrator.memory_manager.save_assistant_message(user_id, session_id, answer)
    except Exception as e:
        logger.error(f"Failed to save memory in background: {e}")

@observe(name="chat_pipeline")
async def _run_chat_pipeline(
    req: ChatRequest,
    orchestrator: AgentOrchestrator,
    background: BackgroundTasks,
    emit: EmitFn,
) -> ChatResponse:
    update_current_trace(
        user_id=req.user_id,
        session_id=req.session_id,
        tags=["chat"]
    )

    t_total = time.perf_counter()
    timings: Dict[str, int] = {}
    
    # ── Phase 1: Retrieve Memory Context ─────────────────────────────────────
    t0 = time.perf_counter()
    await emit({"type": "stage_start", "stage": "recall_st", "label": "Loading conversation history"})
    try:
        memory_context = await asyncio.to_thread(
            orchestrator.memory_manager.get_memory_context, 
            req.user_id, 
            req.session_id, 
            req.message
        )
    except Exception as e:
        logger.warning(f"Memory context retrieval failed: {e}")
        memory_context = ""
    timings["recall_st"] = _ms(t0)
    await emit({"type": "stage_done", "stage": "recall_st", "ms": timings["recall_st"]})
    
    # ── Phase 2: Decision Graph (Guardrail + Router) ──────────────────────────
    t0 = time.perf_counter()
    await emit({"type": "stage_start", "stage": "router", "label": stage_label("router")})
    
    # Run the decision graph parallel nodes
    handler = CallbackHandler()
    decision_state = await orchestrator.decision_graph.ainvoke(
        {
            "message": req.message,
            "memory_context": memory_context
        },
        config={"callbacks": [handler]}
    )
    
    verdict = decision_state.get("verdict", "proceed")
    primary_route = decision_state.get("primary_route", "general")
    route_decisions = decision_state.get("route_decisions", [])
    
    timings["decision"] = _ms(t0)
    await emit({"type": "stage_done", "stage": "router", "ms": timings["decision"]})
    
    # ── Phase 2a: Guardrail Short-Circuit ─────────────────────────────────────
    if verdict == "out_of_scope":
        await emit({"type": "tool_invoke", "route": "out_of_scope", "action": None, "label": tool_label("out_of_scope")})
        await emit({"type": "tool_done", "route": "out_of_scope", "action": None, "ms": 0, "summary": "Declined by guardrail"})
        
        # Emitting tokens for the frontend to show the message immediately
        for word in OUT_OF_SCOPE_REPLY.split(" "):
            await emit({"type": "token", "content": word + " "})
            await asyncio.sleep(0.02)  # Tiny delay for smooth typing effect
            
        # Background Memory Save
        background.add_task(_save_memory_bg, orchestrator, req.user_id, req.session_id, req.message, OUT_OF_SCOPE_REPLY)
        background.add_task(touch_session_sync, req.user_id, req.session_id)
        
        return ChatResponse(
            session_id=req.session_id,
            answer=OUT_OF_SCOPE_REPLY,
            routes=["out_of_scope"],
            tool_output=None,
            latency_ms=_ms(t_total)
        )

    # ── Phase 3: Tool Dispatch (Parallel Fan-Out) ─────────────────────────────
    t0 = time.perf_counter()
    routes_taken = []
    
    # Check if we need KPIs for any route before dispatching
    from src.services.kpi_service import get_kpis_for_user
    user_kpis_str = ""
    if any(d.get("route") in ["cashflow", "rag"] for d in route_decisions):
        user_kpis_str = await get_kpis_for_user(req.user_id)
    
    async def _dispatch_one(decision: Dict[str, Any]) -> str:
        route = decision.get("route", "general")
        query = decision.get("rewritten_query", req.message)
        routes_taken.append(route)
        
        await emit({"type": "tool_invoke", "route": route, "action": None, "label": tool_label(route)})
        t_sub = time.perf_counter()
        
        out = ""
        try:
            if route == "cashflow" and orchestrator.cashflow_tool:
                out = await asyncio.to_thread(orchestrator.cashflow_tool.analyze, query, user_kpis_str)
            elif route == "rag" and orchestrator.rag_tool:
                out = await asyncio.to_thread(orchestrator.rag_tool.search, query)
            elif route == "market" and orchestrator.market_tool:
                # In a real system, extract tickers via LLM. Here we use defaults for demonstration.
                out = str(await asyncio.to_thread(orchestrator.market_tool.fetch_data, ["^GSPC", "LKR=X"]))
            elif route == "investment" and orchestrator.investment_tool:
                out = str(await asyncio.to_thread(orchestrator.investment_tool.search, query))
            elif route == "tax" and orchestrator.tax_tool:
                results = await asyncio.to_thread(orchestrator.tax_tool.search, query)
                out = "\n\n".join([
                    f"Source: {r.get('url', 'Official Source')}\n{r.get('content', '')}"
                    for r in results if not r.get("error")
                ]) or "No results from official tax portals."
        except Exception as e:
            logger.warning(f"Tool dispatch failed for route {route}: {e}")
            out = f"Error running tool: {e}"
            
        ms = _ms(t_sub)
        summary = out.splitlines()[0][:100] if out else "No tool output"
        await emit({"type": "tool_done", "route": route, "action": None, "ms": ms, "summary": summary})
        
        if out:
            return f"=== {route.upper()} RESULT ===\n{out}"
        return ""

    if len(route_decisions) > 1:
        await emit({"type": "tool_invoke", "route": "multi", "action": None, "label": tool_label("multi")})
        # Fan-out: Run multiple tools concurrently
        outs = await asyncio.gather(*[_dispatch_one(d) for d in route_decisions])
        tool_output = "\n\n".join(filter(None, outs))
        await emit({"type": "tool_done", "route": "multi", "action": None, "ms": _ms(t0), "summary": "Multiple tools completed"})
    elif len(route_decisions) == 1:
        tool_output = await _dispatch_one(route_decisions[0])
    else:
        tool_output = ""
        routes_taken = [primary_route]

    timings["tool"] = _ms(t0)

    # ── Phase 4: Synthesis (with Streaming Support) ───────────────────────────
    t0 = time.perf_counter()
    await emit({"type": "stage_start", "stage": "synth", "label": "Composing your financial response"})
    
    chart_instruction = """
=== CHART GENERATION ===
If the user asks for a chart, graph, or visual representation, OR if you believe the numerical data is best presented visually (e.g. expenses, trends), output a JSON block wrapped in ```chart
Format EXACTLY like this:
```chart
{
  "type": "bar",
  "title": "Chart Title",
  "data": [
    {"name": "Label1", "value": 100},
    {"name": "Label2", "value": 200}
  ]
}
```
Valid types: "bar", "line", "pie". The "name" field is the label.
"""

    active_routes = routes_taken
    
    kpi_context = ""
    if ("cashflow" in active_routes or "rag" in active_routes) and user_kpis_str:
        kpi_context = f"\n\n=== COMPANY KPIs ===\n{user_kpis_str}\n\nCRITICAL RULE: DO NOT invent or assume any business KPIs or targets. You MUST ONLY evaluate performance against the specific KPIs listed above. If no KPIs are listed, just provide the facts without judging performance."

    report_instruction = """
=== REPORT GENERATION ===
If the user explicitly asks to generate a report, document, or summary, format your ENTIRE response as a formal, highly detailed professional report. Use Markdown to structure it with an 'Executive Summary', clear bold headings (##, ###), bullet points, and data tables. Be comprehensive, analytical, and synthesize all available tool data.
"""

    system_prompt = (
        "You are FinVox, an expert SME Financial Assistant.\n"
        "IMPORTANT FORMATTING RULES: Whenever you present numerical data, breakdowns, financial projections, or comparative information, ALWAYS format it using clean Markdown Tables to make it easy for the user to read.\n\n"
        f"{report_instruction}\n\n"
        f"=== MEMORY CONTEXT ===\n{memory_context}{kpi_context}\n\n{chart_instruction}"
    )
    if "tax" in active_routes and tool_output:
        system_prompt += (
            "\n\n=== TAX COMPLIANCE INSTRUCTIONS ===\n"
            "You have been provided with LIVE, OFFICIAL data fetched directly from the Sri Lanka Inland Revenue Department (ird.gov.lk) and other government tax portals. "
            "Always cite the source URL when referencing a specific rate or rule. "
            "If the data does not contain a direct answer, say so clearly and direct the user to https://www.ird.gov.lk."
        )
    if tool_output:
        system_prompt += f"\n\n=== TOOL OUTPUT ===\n{tool_output}\n\nCRITICAL RULE: Use the tool output above to accurately answer the user's query. If the TOOL OUTPUT contradicts any information found in the MEMORY CONTEXT (e.g. from previous chat history), ALWAYS trust the TOOL OUTPUT. The tool output is the absolute ground truth. Do not combine old numbers from memory with new numbers from the tool output."
        
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=req.message)
    ]
    
    answer_chunks = []
    try:
        # astream allows us to yield tokens as they arrive
        handler = CallbackHandler()
        async for chunk in orchestrator.llm_chat.astream(messages, config={"callbacks": [handler]}):
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            if content:
                answer_chunks.append(content)
                # Emit token event for letter-by-letter streaming
                await emit({"type": "token", "content": content})
                
    except Exception as exc:
        logger.exception("Synth LLM failed: {}", exc)
        raise HTTPException(status_code=500, detail=f"Synth error: {exc}")
        
    final_answer = "".join(answer_chunks)
    timings["synth"] = _ms(t0)
    await emit({"type": "stage_done", "stage": "synth", "ms": timings["synth"]})

    # ── Phase 5: Background Tasks (Zero Latency Impact) ───────────────────────
    # Memory saving is completely offloaded to the background
    background.add_task(_save_memory_bg, orchestrator, req.user_id, req.session_id, req.message, final_answer)
    background.add_task(touch_session_sync, req.user_id, req.session_id)

    return ChatResponse(
        session_id=req.session_id,
        answer=final_answer,
        routes=routes_taken,
        tool_output=tool_output if tool_output else None,
        latency_ms=_ms(t_total)
    )

# ── POST /chat — non-streaming (sync contract) ────────────────────────────────

@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    req: ChatRequest,
    background: BackgroundTasks,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
) -> ChatResponse:
    """Run the pipeline and return the full response in one shot."""
    logger.info(f"Incoming Chat Request - User: {req.user_id} | Session: {req.session_id}")
    return await _run_chat_pipeline(
        req, orchestrator=orchestrator, background=background, emit=_noop_emit
    )

# ── POST /chat/stream — chain-of-thought & letter-by-letter via SSE ───────────

@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    background: BackgroundTasks,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
) -> StreamingResponse:
    """
    Stream the chain of thought AND the generated answer letter-by-letter.
    The transport is SSE — one `data: {...}\\n\\n` event per transition.
    """
    logger.info(f"Incoming Stream Request - User: {req.user_id} | Session: {req.session_id}")
    queue: asyncio.Queue = asyncio.Queue()

    async def emit(event: Dict[str, Any]) -> None:
        await queue.put(event)

    async def run() -> None:
        try:
            final = await _run_chat_pipeline(
                req, orchestrator=orchestrator, background=background, emit=emit
            )
            await queue.put({
                "type": "final",
                "answer": final.answer,
                "routes": final.routes,
                "latency_ms": final.latency_ms,
            })
        except HTTPException as exc:
            await queue.put({"type": "error", "status": exc.status_code, "message": str(exc.detail)})
        except Exception as exc:
            logger.exception("Streaming chat failed: {}", exc)
            await queue.put({"type": "error", "status": 500, "message": str(exc)})
        finally:
            await queue.put(None)  # Sentinel to close the stream

    asyncio.create_task(run())

    async def event_generator():
        # Initial keep-alive comment so proxies open the stream immediately
        yield ": stream-open\n\n"
        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "cache-control": "no-cache",
            "x-accel-buffering": "no",  # Disable proxy buffering
            "connection": "keep-alive",
        },
    )
