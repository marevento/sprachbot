"""
Deutscher Sprachbot - Sprachmodus
Pipeline: Mikrofon -> Silence-VAD -> faster-whisper STT -> Ollama LLM -> Piper TTS

Verwendung:
    python main_voice.py
    SPEAK=0 python main_voice.py   # ohne TTS-Ausgabe
"""
import sys
import os
import json
import pathlib
import tempfile
import wave
import requests
import numpy as np
from datetime import datetime
from loguru import logger

import pyaudio

from config import OLLAMA_MODEL, OLLAMA_BASE_URL, TRANSCRIPT_DIR, SAMPLE_RATE, WHISPER_MODEL, PIPER_MODEL
from knowledge_base import SYSTEM_PROMPT
from tts_service import speak_piper

logger.remove(0)
logger.add(sys.stderr, level="WARNING")

os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

SPEAK = os.getenv("SPEAK", "1") == "1"
CHUNK = 1024
SILENCE_THRESHOLD = int(os.getenv("SILENCE_THRESHOLD", "400"))   # RMS; raise if noisy
SILENCE_SECONDS = float(os.getenv("SILENCE_SECONDS", "1.5"))
IDLE_TIMEOUT = float(os.getenv("IDLE_TIMEOUT", "30"))

END_MARKER = "[ENDE]"


def load_whisper():
    from faster_whisper import WhisperModel
    model_dir = pathlib.Path(f"models/whisper-{WHISPER_MODEL}")
    if not (model_dir / "model.bin").exists():
        print(f"[FEHLER] Whisper-Modell '{WHISPER_MODEL}' nicht gefunden in {model_dir}/")
        print("Bitte zuerst ./setup.sh ausführen.")
        sys.exit(1)
    print(f"[STT] Lade Whisper '{WHISPER_MODEL}'...", end=" ", flush=True)
    model = WhisperModel(str(model_dir), device="cpu", compute_type="int8")
    print("bereit.")
    return model


def record_utterance(p) -> bytes | str | None:
    """Record from mic until silence. Returns raw PCM bytes or None on error."""
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )
    frames = []
    silent_chunks = 0
    total_chunks = 0
    speaking = False
    silence_limit = int(SILENCE_SECONDS * SAMPLE_RATE / CHUNK)
    idle_limit = int(IDLE_TIMEOUT * SAMPLE_RATE / CHUNK)
    min_speech_chunks = int(0.3 * SAMPLE_RATE / CHUNK)  # ignore < 0.3s blips

    print("[Mikrofon] Bitte sprechen Sie...", end=" ", flush=True)
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            total_chunks += 1
            audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            rms = np.sqrt(np.mean(audio_data ** 2))

            if rms > SILENCE_THRESHOLD:
                speaking = True
                silent_chunks = 0
            elif speaking:
                silent_chunks += 1
                if silent_chunks >= silence_limit:
                    break
            elif total_chunks >= idle_limit:
                print("(Zeitüberschreitung)")
                return "timeout"
    finally:
        stream.stop_stream()
        stream.close()

    if not speaking or len(frames) < min_speech_chunks:
        print("(kein Ton erkannt)")
        return None

    print("(aufgenommen)")
    return b"".join(frames)


def transcribe(model, pcm: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_path = f.name
        with wave.open(f, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # int16 = 2 bytes
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(pcm)

    try:
        segments, _ = model.transcribe(tmp_path, language="de", beam_size=5)
        text = " ".join(s.text for s in segments).strip()
        return text
    finally:
        os.unlink(tmp_path)


def ollama_chat(messages: list) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.7},
    }
    try:
        r = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["message"]["content"].strip()
    except Exception as e:
        return f"Entschuldigung, es gab einen Fehler: {e}"


def check_end(response: str) -> tuple[str, bool]:
    """Check if LLM signalled end. Returns (clean_response, should_end)."""
    if END_MARKER in response:
        return response.replace(END_MARKER, "").strip(), True
    return response, False


def speak(text: str):
    if SPEAK:
        speak_piper(text)


def _check_setup():
    """Check all prerequisites, exit with hint to run setup.sh if anything is missing."""
    missing = []
    piper_path = pathlib.Path(PIPER_MODEL)
    whisper_dir = pathlib.Path(f"models/whisper-{WHISPER_MODEL}")
    if not piper_path.exists():
        missing.append(f"Piper-Stimmmodell nicht gefunden: {piper_path}")
    if not (whisper_dir / "model.bin").exists():
        missing.append(f"Whisper-Modell nicht gefunden: {whisper_dir}/")
    try:
        requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3).raise_for_status()
    except Exception:
        missing.append(f"Ollama nicht erreichbar auf {OLLAMA_BASE_URL}")
    if missing:
        print("[FEHLER] Setup unvollständig:")
        for m in missing:
            print(f"  - {m}")
        print("\nBitte zuerst ./setup.sh ausführen.")
        sys.exit(1)


def run():
    print("\n" + "=" * 55)
    print("  DEUTSCHER SPRACHBOT")
    print("  (Strg+C zum Beenden)")
    print("=" * 55 + "\n")

    _check_setup()

    whisper = load_whisper()
    p = pyaudio.PyAudio()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    start_time = datetime.now()
    end_reason = "manual"
    entries = []

    def log(role, text):
        entries.append({"timestamp": datetime.now().isoformat(), "role": role, "text": text})

    # Greeting
    greeting = "Willkommen, wie kann ich Ihnen helfen?"
    messages.append({"role": "assistant", "content": greeting})
    log("assistant", greeting)
    print(f"Sprachbot: {greeting}\n")
    speak(greeting)

    try:
        while True:
            pcm = record_utterance(p)
            if pcm == "timeout":
                end_reason = "timeout"
                goodbye = "Auf Wiederhören!"
                log("assistant", goodbye)
                print(f"Sprachbot: {goodbye}\n")
                speak(goodbye)
                print("[Info] Keine Eingabe — Gespräch beendet.")
                break
            if pcm is None:
                continue

            user_text = transcribe(whisper, pcm)
            if not user_text:
                continue

            print(f"Sie:      {user_text}")
            log("user", user_text)
            messages.append({"role": "user", "content": user_text})

            response = ollama_chat(messages)
            response, should_end = check_end(response)
            messages.append({"role": "assistant", "content": response})
            log("assistant", response)
            print(f"Sprachbot: {response}\n")
            speak(response)

            if should_end:
                end_reason = "farewell"
                print("[Info] Gespräch beendet.")
                break

    except KeyboardInterrupt:
        end_reason = "manual"
        print("\n[Info] Abgebrochen.")
    finally:
        p.terminate()

    duration = round((datetime.now() - start_time).total_seconds(), 1)
    path = os.path.join(TRANSCRIPT_DIR, f"transcript_{session_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "session_id": session_id,
            "duration_seconds": duration,
            "end_reason": end_reason,
            "transcript": entries,
        }, f, ensure_ascii=False, indent=2)

    print("\n=== GESPRÄCHSTRANSKRIPT ===")
    for e in entries:
        role = "Nutzer   " if e["role"] == "user" else "Sprachbot"
        print(f"[{e['timestamp']}] {role}: {e['text']}")
    print(f"Gespeichert: {path}\n")


if __name__ == "__main__":
    run()
