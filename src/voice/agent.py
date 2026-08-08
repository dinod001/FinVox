"""
LiveKit voice agent entrypoint for FinVox.
Connects VAD, STT, TTS, and our LangGraph adapter.
"""
import asyncio
import os
from loguru import logger

from livekit import rtc
from livekit.agents import AutoSubscribe, JobContext, JobProcess, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero

from src.agents.orchestrator import AgentOrchestrator
from src.voice.adapter import LangGraphLLMAdapter
from src.voice.config import load_voice_config
from src.voice.stt import get_stt
from src.voice.tts import get_tts

# Global orchestrator instance so we don't reload it per call
_orchestrator = None

async def _get_orchestrator() -> AgentOrchestrator:
    """Lazy-init the AgentOrchestrator (Main Brain)."""
    global _orchestrator
    if _orchestrator is None:
        logger.info("Initializing FinVox AgentOrchestrator...")
        # Run sync initialization in a background thread so it doesn't block
        _orchestrator = await asyncio.to_thread(AgentOrchestrator)
        logger.success("FinVox AgentOrchestrator ready.")
    return _orchestrator

def prewarm(process: JobProcess):
    """
    Called by LiveKit worker BEFORE accepting any jobs.
    We load the orchestrator and models here so the first user doesn't wait.
    """
    logger.info("🔥 Running Voice Agent Warmup...")
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    logger.success("✅ Voice Agent Warmup Complete. Ready for low-latency connections!")

async def entrypoint(ctx: JobContext):
    """
    LiveKit worker entrypoint for FinVox Voice Agent.
    """
    logger.info(f"Connecting to room {ctx.room.name}...")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the user to join
    participant = await ctx.wait_for_participant()
    user_id = participant.identity or "voice-user"
    session_id = ctx.room.name

    logger.info(f"User {user_id} joined session {session_id}")

    # Load Config & Orchestrator
    cfg = load_voice_config()
    orchestrator = await _get_orchestrator()

    # Create the LLM Adapter (The Bridge to our logic)
    adapter = LangGraphLLMAdapter(
        orchestrator=orchestrator,
        user_id=user_id,
        session_id=session_id
    )

    # Initialize LiveKit Plugins
    vad = silero.VAD.load(
        min_silence_duration=cfg.silence_threshold_ms / 1000.0,
        activation_threshold=cfg.vad_threshold,
    )
    stt = get_stt(cfg)
    tts = get_tts(cfg)

    # Build the Voice Agent
    agent = Agent(
        instructions=(
            "You are FinVox, a specialized SME Financial Assistant. "
            "You are communicating with the user through a voice interface. "
            "Keep your answers conversational, concise, and easy to understand when spoken out loud. "
            "Speak naturally."
        ),
        stt=stt,
        llm=adapter,
        tts=tts,
        vad=vad,
        allow_interruptions=cfg.interruption_enabled,
        min_endpointing_delay=cfg.min_endpointing_delay,
    )

    # Start the session
    agent_session = AgentSession()
    
    # Handle barge-in cancellation if user interrupts AI
    @agent_session.on("agent_speech_interrupted")
    def _on_interrupted(_ev):
        logger.info("User interrupted the agent (barge-in detected)")
        adapter.cancel_current()

    await agent_session.start(agent, room=ctx.room)
    logger.info("FinVox Voice Agent started successfully.")

    # Greet the user
    await agent_session.say("Hi! Welcome to FinVox. How can I help you with your business today?", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))