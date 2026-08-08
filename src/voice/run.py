"""
Voice worker entrypoint.
Run this script to start the FinVox LiveKit agent worker.
"""

from __future__ import annotations

import os
import sys

# Ensure project root is in sys.path so 'src' imports work
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv(usecwd=True))

from livekit.agents import WorkerOptions, cli
from loguru import logger

from src.voice.agent import entrypoint, prewarm
from src.voice.config import load_voice_config, validate_voice_env

def main() -> None:
    # Load configuration
    cfg = load_voice_config()

    # Print a nice startup banner
    print()
    print("  FinVox — Voice AI Worker")
    print(f"  {'-' * 48}")
    print(f"  LiveKit URL  : {cfg.livekit_url or '(unset)'}")
    print(f"  STT          : {cfg.stt_provider}/{cfg.stt_model}")
    print(f"  TTS          : {cfg.tts_provider}/{cfg.tts_model}")
    print(f"  VAD threshold: {cfg.vad_threshold}")
    print(f"  Silence      : {cfg.silence_threshold_ms} ms")
    print(f"  Endpointing  : {cfg.min_endpointing_delay} s")
    print(f"  Interruptions: {cfg.interruption_enabled}")
    print(f"  {'-' * 48}")
    print()

    # Validate that we have all API keys
    validate_voice_env()
    
    # Start the LiveKit worker
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            initialize_process_timeout=60.0,
            num_idle_processes=1,
        )
    )

if __name__ == "__main__":
    main()