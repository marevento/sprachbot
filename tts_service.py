"""
TTS-Wrapper: Piper TTS (deutsche Thorsten-Stimme, vollständig lokal).
"""
import re
import pyaudio
from loguru import logger
from config import PIPER_MODEL

_DIGIT_WORDS = {
    "0": "null", "1": "eins", "2": "zwei", "3": "drei", "4": "vier",
    "5": "fünf", "6": "sechs", "7": "sieben", "8": "acht", "9": "neun",
}


def _normalize_phone(match: re.Match) -> str:
    """Convert a phone number to spoken German digits."""
    raw = match.group(0)
    raw = raw.replace("+49", "0")
    parts = raw.split()
    spoken = []
    for part in parts:
        digits = [_DIGIT_WORDS.get(d, d) for d in part if d.isdigit()]
        if digits:
            spoken.append(" ".join(digits))
    return ", ".join(spoken)


def normalize_for_tts(text: str) -> str:
    """Normalize text for better TTS pronunciation."""
    # Phone numbers: +49 ... or 0xxxx patterns with grouped digits
    text = re.sub(r"(?:\+49|0)\s*\d[\d\s]{6,}", _normalize_phone, text)
    return text

_piper_voice = None


def _get_piper():
    global _piper_voice
    if _piper_voice is None:
        from piper import PiperVoice
        print(f"[TTS] Lade Piper-Stimme '{PIPER_MODEL}'...", end=" ", flush=True)
        _piper_voice = PiperVoice.load(PIPER_MODEL)
        print("bereit.")
    return _piper_voice


_pyaudio = None


def _get_pyaudio():
    global _pyaudio
    if _pyaudio is None:
        _pyaudio = pyaudio.PyAudio()
    return _pyaudio


def speak_piper(text: str):
    """Piper TTS — hochwertige deutsche Stimme, vollständig lokal."""
    try:
        voice = _get_piper()
        p = _get_pyaudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=voice.config.sample_rate,
            output=True,
        )
        text = normalize_for_tts(text)
        for chunk in voice.synthesize(text):
            stream.write(chunk.audio_int16_bytes)
        stream.stop_stream()
        stream.close()
    except Exception as e:
        logger.error(f"[TTS Piper] Fehler: {e}")
        print(f"[TTS FALLBACK TEXT] {text}")
