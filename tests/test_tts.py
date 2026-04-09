"""Test TTS-Ausgabe — benötigt Lautsprecher."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tts_service import speak_piper


def test_piper():
    speak_piper(
        "Hallo, ich bin ein deutscher Sprachbot. "
        "Dieser Test prüft die Sprachausgabe."
    )
    print("PASS: Piper TTS — Sprachausgabe sollte hörbar sein")


if __name__ == "__main__":
    print("=== TTS Test ===")
    test_piper()
    print("Test beendet.")
