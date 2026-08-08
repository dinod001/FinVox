"""
Voice pipeline configuration.
Settings are loaded centrally from infrastructure.config to avoid duplication.
"""
import os
from dataclasses import dataclass
from typing import Optional
from loguru import logger
from src.infrastructure import config as infra_cfg

@dataclass
class VoiceConfig:
    """Resolved voice pipeline settings."""
    # STT
    stt_provider: str = infra_cfg.VOICE_STT_PROVIDER
    stt_model: str = infra_cfg.VOICE_STT_MODEL
    stt_language: str = infra_cfg.VOICE_STT_LANGUAGE

    # LLM
    llm_provider: str = infra_cfg.VOICE_LLM_PROVIDER
    llm_model: str = infra_cfg.VOICE_LLM_MODEL

    # TTS
    tts_provider: str = infra_cfg.VOICE_TTS_PROVIDER
    tts_model: str = infra_cfg.VOICE_TTS_MODEL
    tts_voice_id: str = infra_cfg.VOICE_TTS_VOICE_ID

    # VAD & Logic
    vad_threshold: float = float(infra_cfg.VOICE_VAD_THRESHOLD)
    silence_threshold_ms: int = int(infra_cfg.VOICE_SILENCE_THRESHOLD_MS)
    min_endpointing_delay: float = float(infra_cfg.VOICE_MIN_ENDPOINTING_DELAY)
    interruption_enabled: bool = bool(infra_cfg.VOICE_INTERRUPTION_ENABLED)
    sample_rate: int = int(infra_cfg.VOICE_SAMPLE_RATE)

    # Credentials
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    deepgram_api_key: Optional[str] = os.getenv("DEEPGRAM_API_KEY")
    eleven_api_key: Optional[str] = os.getenv("ELEVEN_API_KEY")
    livekit_url: Optional[str] = infra_cfg.LIVEKIT_URL
    livekit_api_key: Optional[str] = infra_cfg.LIVEKIT_API_KEY
    livekit_api_secret: Optional[str] = infra_cfg.LIVEKIT_API_SECRET

def load_voice_config() -> VoiceConfig:
    """Return the loaded voice configuration."""
    cfg = VoiceConfig()
    logger.debug(f"Voice config: STT={cfg.stt_provider}/{cfg.stt_model}, LLM={cfg.llm_provider}/{cfg.llm_model}, TTS={cfg.tts_provider}")
    return cfg

def validate_voice_env() -> None:
    """Validate required environment variables for the voice pipeline."""
    cfg = load_voice_config()
    required = [
        "OPENAI_API_KEY", 
        "DEEPGRAM_API_KEY", 
        "LIVEKIT_URL", 
        "LIVEKIT_API_KEY", 
        "LIVEKIT_API_SECRET"
    ]
    
    if cfg.tts_provider == "elevenlabs":
        required.append("ELEVEN_API_KEY")

    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise EnvironmentError(f"Missing voice env vars: {', '.join(missing)}")
    
    logger.success(f"Voice env vars OK (TTS: {cfg.tts_provider})")