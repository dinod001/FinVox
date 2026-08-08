"""
Speech-to-Text (STT) provider instantiation.
"""
from livekit.plugins import deepgram
from src.voice.config import VoiceConfig

def get_stt(cfg: VoiceConfig):
    """
    Return the configured STT instance for the Voice Pipeline.
    In FinVox, we use Deepgram for low-latency streaming STT.
    """
    # Initialize and return Deepgram STT plugin with configuration
    return deepgram.STT(
        model=cfg.stt_model,
        language=cfg.stt_language,
        api_key=cfg.deepgram_api_key
    )
