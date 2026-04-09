**[Deutsche Version](README.md)**

# German Voicebot

Fully local German voicebot. Answers questions based on a configurable knowledge base. No cloud services required — the entire pipeline runs self-hosted.

---

## Features

- **Fully local** — no cloud services, no API keys, no data leaves the machine
- **German end-to-end** — speech recognition, reasoning and speech output in German
- **Natural speech output** — Thorsten voice via Piper TTS
- **Phone number normalization** — digits are automatically converted to spoken German
- **Semantic end-of-conversation detection** — LLM recognizes farewells in context, no rigid keyword matching
- **Idle timeout** — conversation ends automatically after 30 seconds of silence
- **Transcript logging** — every conversation saved as JSON with timestamps, duration and end reason
- **Text mode** — test without audio
- **Interactive setup** — `./setup.sh` with model selection (Whisper base/small, LLM model)
- **Configurable knowledge base** — add your own content in `knowledge_base.py`

---

## Architecture

```
Microphone
  |
[Silence-VAD]              RMS-based speech detection (no cloud)
  |
[faster-whisper STT]       transcribes German locally
  |
[Ollama LLM]               local LLM with embedded knowledge base
  |
[Farewell detection]       LLM detects farewells semantically
  |
[Piper TTS]                German TTS (Thorsten voice), local
  |
Speaker
  |
[JSON transcript]          saves conversation as JSON file
```

---

## Example Dialog

```
Bot:  Welcome, how can I help you?

User: What can you do for me?

Bot:  We offer consulting, development and training.

User: How can I reach you?

Bot:  You can reach us by email at info at example dot com or
      by phone at zero one two three, four five six, seven eight nine.

User: Thanks, bye!

Bot:  You're welcome! Goodbye and have a nice day!
```

---

## Knowledge Base

The knowledge base is defined as a system prompt in `knowledge_base.py`. The bot can only answer questions covered there. Simply add your own content — company info, products, FAQ, contact details, etc.

---

## Component Decisions

| Component | Technology | Model | Rationale |
|---|---|---|---|
| VAD | RMS threshold (custom) | — | Simple, no dependencies, configurable via `SILENCE_THRESHOLD` |
| STT | faster-whisper | `base`/`small` | Best German OSS ASR, fully local, faster than original Whisper |
| LLM | Ollama | `llama3.2:3b` | Local model management, good German support |
| TTS | Piper TTS | `de_DE-thorsten-high` | German voice, fully local, fast on CPU |
| Transcript | JSON file | — | Human-readable, no database needed |

---

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) >= 0.1.0 installed and running
- PortAudio: `brew install portaudio` (macOS) or `apt install portaudio19-dev` (Linux)
- Microphone + speakers (for voice mode `main_voice.py`)
- RAM: at least 8 GB recommended (LLM ~4–5 GB, Whisper ~1–2 GB, Piper TTS minimal)

**Platform note:** Developed and tested on Linux. macOS should work. Windows requires additional PortAudio setup and is not officially tested.

---

## Setup and Usage

**Automatic (recommended):**
```
./setup.sh
```

The script creates a virtual environment, installs all Python packages, downloads Piper and Whisper models, and checks Ollama.

**Run:**

Voice mode (microphone + speakers):
```
python main_voice.py
```

Text mode (no audio, ideal for testing):
```
python main_text.py
```

---

## Project Structure

```
├── setup.sh               Installation script (all dependencies)
├── main_voice.py          Voice mode (Mic -> STT -> LLM -> TTS -> Speaker)
├── main_text.py           Text mode (terminal chat with optional TTS)
├── config.py              Configuration via environment variables / .env
├── knowledge_base.py      System prompt with knowledge base (customize here!)
├── tts_service.py         Piper TTS wrapper with phone number normalization
├── requirements.txt       Python dependencies
├── models/                Local models (Whisper, Piper)
├── transcripts/           Saved conversation transcripts (JSON)
└── tests/                 Tests (LLM, TTS)
```

---

## Tests

### `tests/test_text_mode.py` — LLM Tests

Tests basic LLM functionality. No audio needed, but Ollama must be running.

| Test | Checks |
|---|---|
| `test_ollama_running` | Ollama server reachable |
| `test_german_response` | Response is in German (even for English input) |
| `test_short_response` | Response is short (max 2–3 sentences) |
| `test_farewell_detection` | Farewell is detected ([ENDE] marker or farewell words) |

```
python tests/test_text_mode.py
```

### `tests/test_tts.py` — TTS Output Test

Plays a test sentence through the speakers. Requires audio.

```
python tests/test_tts.py
```

---

## Transcripts

Each conversation session is automatically saved under:

```
transcripts/transcript_YYYYMMDD_HHMMSS.json
```

Example:

```json
{
  "session_id": "20260405_143022",
  "duration_seconds": 45.3,
  "end_reason": "farewell | timeout | manual",
  "transcript": [
    {
      "timestamp": "2026-04-05T14:30:22.123456",
      "role": "assistant",
      "text": "Willkommen, wie kann ich Ihnen helfen?"
    },
    {
      "timestamp": "2026-04-05T14:30:35.654321",
      "role": "user",
      "text": "Was bietet ihr an?"
    }
  ]
}
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `WHISPER_MODEL` | `base` | Whisper model size (`base`, `small`) — chosen during setup |
| `OLLAMA_MODEL` | `llama3.2:3b` | Ollama model name |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `PIPER_MODEL` | `models/de_DE-thorsten-high.onnx` | Path to Piper voice model |
| `SILENCE_THRESHOLD` | `400` | RMS threshold for speech detection (lower = more sensitive) |
| `SILENCE_SECONDS` | `1.5` | Seconds of silence until recording stops |
| `SPEAK` | `1` (voice) / `0` (text) | TTS output on/off |
| `IDLE_TIMEOUT` | `30` | Seconds of silence until conversation ends automatically |

---

## Self-Hosted

All components run fully without cloud:

| Component | License |
|---|---|
| faster-whisper | MIT |
| Ollama + llama3.2 | Meta Llama Community License |
| Piper TTS | MIT |
