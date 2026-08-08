"""
LangGraph ↔ LiveKit adapter.

This file connects LiveKit's STT to our AgentOrchestrator using the 
same _run_chat_pipeline logic used by the REST API, ensuring voice users 
benefit from the guardrail, decision graph, and memory caching.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Optional

from loguru import logger
from fastapi import BackgroundTasks

from livekit.agents import (
    APIConnectOptions,
    DEFAULT_API_CONNECT_OPTIONS,
)
from livekit.agents.llm import (
    ChatChunk,
    ChatContext,
    ChoiceDelta,
    LLM,
    LLMStream,
    Tool,
)

from src.agents.orchestrator import AgentOrchestrator
from src.api.routers.chat import _run_chat_pipeline
from src.api.schemas import ChatRequest


class LangGraphLLMAdapter(LLM):
    """Wrap AgentOrchestrator so it satisfies LiveKit's LLM interface."""

    def __init__(
        self,
        orchestrator: AgentOrchestrator,
        user_id: str = "voice-user",
        session_id: str = "voice-session",
    ) -> None:
        super().__init__()
        self._orchestrator = orchestrator
        self._user_id = user_id
        self._session_id = session_id
        self._current_task: Optional[asyncio.Task] = None

    def chat(
        self,
        *,
        chat_ctx: ChatContext,
        tools: list[Tool] | None = None,
        tool_choice: Any | None = None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> "LangGraphLLMStream":
        """Called by LiveKit after STT produces a final transcript."""
        return LangGraphLLMStream(
            llm=self,
            chat_ctx=chat_ctx,
            tools=tools or [],
            tool_choice=tool_choice,
            conn_options=conn_options,
            orchestrator=self._orchestrator,
            user_id=self._user_id,
            session_id=self._session_id,
        )

    def cancel_current(self) -> None:
        """Cancel any in-flight agent task. Called on barge-in."""
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            logger.info("Cancelled in-flight agent task (barge-in)")

    def update_identity(self, user_id: str, session_id: str) -> None:
        """Update caller identity."""
        self._user_id = user_id
        self._session_id = session_id


class LangGraphLLMStream(LLMStream):
    """Async iterator that runs the agent and yields its answer."""

    def __init__(
        self,
        llm: LangGraphLLMAdapter,
        *,
        chat_ctx: ChatContext,
        tools: list[Tool],
        tool_choice: Any | None = None,
        conn_options: APIConnectOptions,
        orchestrator: AgentOrchestrator,
        user_id: str,
        session_id: str,
    ) -> None:
        super().__init__(
            llm=llm,
            chat_ctx=chat_ctx,
            tools=tools,
            conn_options=conn_options,
        )
        self._orchestrator = orchestrator
        self._user_id = user_id
        self._session_id = session_id
        self._adapter = llm

    async def _run(self) -> None:
        # 1. Extract the latest user message from the chat context
        items = getattr(self._chat_ctx, "items", None)
        if items is None:
            messages = getattr(self._chat_ctx, "messages", None)
            items = messages() if callable(messages) else (messages or [])

        user_text = ""
        for msg in reversed(list(items)):
            if getattr(msg, "role", None) != "user":
                continue
            content = getattr(msg, "content", None)
            if isinstance(content, str):
                user_text = content
            elif isinstance(content, list):
                user_text = " ".join(p for p in content if isinstance(p, str)).strip()
            if user_text:
                break

        if not user_text:
            return

        logger.info(f'Voice → Agent: "{user_text}"')
        t0_in = time.perf_counter()

        try:
            self._adapter._current_task = asyncio.current_task()
            
            chunk_idx = 0
            
            # This emit function streams tokens back to LiveKit for TTS
            async def _livekit_emit(event: dict[str, Any]) -> None:
                nonlocal chunk_idx
                if event.get("type") == "token":
                    content = event.get("content", "")
                    if content:
                        self._event_ch.send_nowait(
                            ChatChunk(
                                id=f"lg-{chunk_idx}",
                                delta=ChoiceDelta(role="assistant", content=content),
                            )
                        )
                        chunk_idx += 1

            req = ChatRequest(
                message=user_text,
                user_id=self._user_id,
                session_id=self._session_id,
            )
            bg_tasks = BackgroundTasks()

            # 2. Get answer from the centralized chat pipeline 
            # (handles decision graph, memory, tools, and streaming)
            final_response = await _run_chat_pipeline(
                req=req,
                orchestrator=self._orchestrator,
                background=bg_tasks,
                emit=_livekit_emit,
            )
            
            # Fire and forget background tasks (memory saving)
            asyncio.create_task(bg_tasks())
            
            total_ms = int((time.perf_counter() - t0_in) * 1000)
            answer_preview = (final_response.answer[:80] + "...") if final_response.answer else "[No Answer]"
            logger.success(f"📊 Agent answered in {total_ms}ms: \"{answer_preview}\"")

        except asyncio.CancelledError:
            logger.info("🛑 Agent task cancelled (barge-in).")
            raise

        except Exception:
            logger.exception("Agent processing failed")
            # Graceful fallback so the user hears something
            self._event_ch.send_nowait(
                ChatChunk(
                    id="lg-error",
                    delta=ChoiceDelta(
                        role="assistant",
                        content="I'm sorry, I had a problem processing that. Could you please try again?",
                    ),
                )
            )

        finally:
            self._adapter._current_task = None