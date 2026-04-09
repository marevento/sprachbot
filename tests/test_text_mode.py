"""
Automatisierte Tests für LLM-Wissensbasis — kein Audio-Hardware nötig.
Ausführen: python tests/test_text_mode.py
Voraussetzung: Ollama muss laufen
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
from config import OLLAMA_MODEL, OLLAMA_BASE_URL
from knowledge_base import SYSTEM_PROMPT


def chat(user_msg: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]
    r = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7},
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


def test_ollama_running():
    r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
    assert r.status_code == 200, "Ollama muss laufen: ollama serve"
    print("PASS: Ollama erreichbar")


def test_german_response():
    response = chat("What do you do?")
    german_words = ["wir", "die", "der", "das", "und", "ist", "ich", "bin"]
    assert any(w in response.lower() for w in german_words), (
        f"Antwort nicht auf Deutsch: {response}"
    )
    print(f"PASS: Deutsch — {response[:80]}...")


def test_short_response():
    response = chat("Erzähl mir etwas über dich.")
    sentences = [s for s in response.split(".") if s.strip()]
    assert len(sentences) <= 3, (
        f"Antwort zu lang ({len(sentences)} Sätze): {response}"
    )
    print(f"PASS: Kurze Antwort — {response[:80]}...")


def test_farewell_detection():
    response = chat("Auf Wiedersehen, danke für Ihre Hilfe!")
    has_ende = "[ENDE]" in response
    farewell_words = ["wiedersehen", "tschüss", "gerne", "schönen", "auf wiederhören"]
    has_farewell = any(w in response.lower() for w in farewell_words)
    assert has_ende or has_farewell, (
        f"Verabschiedung nicht erkannt (kein [ENDE] und keine Abschiedsworte): {response}"
    )
    print(f"PASS: Verabschiedung — {response[:80]}...")


if __name__ == "__main__":
    print("=== Starte LLM-Tests (Ollama muss laufen) ===\n")
    test_ollama_running()
    test_german_response()
    test_short_response()
    test_farewell_detection()
    print("\nAlle Tests bestanden!")
