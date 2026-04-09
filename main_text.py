"""
Deutscher Sprachbot - Textmodus (kein Mikrofon nötig)
Zum Testen von LLM, Wissensbasis und Transkript ohne Audio-Hardware.

Verwendung:
    python main_text.py
"""
import sys
import json
import requests
from datetime import datetime
from loguru import logger
import os

from config import OLLAMA_MODEL, OLLAMA_BASE_URL, TRANSCRIPT_DIR
from knowledge_base import SYSTEM_PROMPT

os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

SPEAK = os.getenv("SPEAK", "0") == "1"

def speak(text: str):
    if not SPEAK:
        return
    from tts_service import speak_piper
    speak_piper(text)

logger.remove(0)
logger.add(sys.stderr, level="WARNING")

END_MARKER = "[ENDE]"


def ollama_chat(messages: list) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.7},
    }
    try:
        r = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["message"]["content"].strip()
    except Exception as e:
        return f"Fehler: {e}"


def check_end(response: str) -> tuple[str, bool]:
    """Check if LLM signalled end. Returns (clean_response, should_end)."""
    if END_MARKER in response:
        return response.replace(END_MARKER, "").strip(), True
    return response, False


def run():
    print("\n" + "=" * 55)
    print("  DEUTSCHER SPRACHBOT -- TEXTMODUS")
    print("  (Tippen Sie 'exit' zum Beenden)")
    print("=" * 55 + "\n")

    try:
        requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3).raise_for_status()
    except Exception:
        print(f"[FEHLER] Ollama nicht erreichbar auf {OLLAMA_BASE_URL}")
        print("Bitte zuerst ./setup.sh ausführen.")
        sys.exit(1)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    start_time = datetime.now()
    end_reason = "manual"
    entries = []

    def log_entry(role, text):
        entries.append({
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "text": text,
        })

    # Greeting
    greeting = "Willkommen, wie kann ich Ihnen helfen?"
    messages.append({"role": "assistant", "content": greeting})
    log_entry("assistant", greeting)
    print(f"Sprachbot: {greeting}\n")
    speak(greeting)

    while True:
        try:
            user_input = input("Sie: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input or user_input.lower() == "exit":
            break

        log_entry("user", user_input)
        messages.append({"role": "user", "content": user_input})

        response = ollama_chat(messages)
        response, should_end = check_end(response)
        messages.append({"role": "assistant", "content": response})
        log_entry("assistant", response)

        print(f"Sprachbot: {response}\n")
        speak(response)

        if should_end:
            end_reason = "farewell"
            print("[Info] Gespräch beendet.")
            break

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
