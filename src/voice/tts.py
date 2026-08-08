"""
Text-to-Speech (TTS) provider instantiation.
"""
from livekit.plugins import elevenlabs, deepgram
from src.voice.config import VoiceConfig

def get_tts(cfg: VoiceConfig):
    """
    Return the configured TTS instance for the Voice Pipeline.
    Supports ElevenLabs (default) and Deepgram as fallback.
    """
    if cfg.tts_provider == "elevenlabs":
        return elevenlabs.TTS(
            model=cfg.tts_model,
            voice_id=cfg.tts_voice_id,
            api_key=cfg.eleven_api_key
        )
    elif cfg.tts_provider == "deepgram":
        return deepgram.TTS(
            model=cfg.tts_model,
            api_key=cfg.deepgram_api_key
        )
    else:
        raise ValueError(f"Unsupported TTS provider: {cfg.tts_provider}")
