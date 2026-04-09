import os
from pathlib import Path

# Load .env if present
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

# STT
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

# LLM
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# TTS
PIPER_MODEL = os.getenv("PIPER_MODEL", "models/de_DE-thorsten-high.onnx")

# Audio
SAMPLE_RATE = 16000

# Conversation
TRANSCRIPT_DIR = "transcripts"
