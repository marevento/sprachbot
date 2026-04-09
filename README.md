**[English version](README.en.md)**

# Deutscher Voicebot

Vollständig lokal betreibbarer deutscher Voicebot. Beantwortet Fragen auf Basis einer konfigurierbaren Wissensbasis. Kein Cloud-Dienst erforderlich — die gesamte Pipeline läuft self-hosted.

---

## Features

- **Vollständig lokal** — kein Cloud-Dienst, keine API-Keys, keine Daten verlassen den Rechner
- **Deutschsprachig** — Spracherkennung, Reasoning und Sprachausgabe auf Deutsch
- **Natürliche Sprachausgabe** — Thorsten-Stimme via Piper TTS
- **Telefonnummern-Normalisierung** — Ziffern werden automatisch in gesprochenes Deutsch umgewandelt
- **Semantische Gesprächsende-Erkennung** — LLM erkennt Verabschiedungen im Kontext, kein starres Keyword-Matching
- **Idle-Timeout** — Gespräch wird nach 30 Sekunden Stille automatisch beendet
- **Transkript-Logging** — jedes Gespräch als JSON mit Timestamps, Dauer und Beendigungsgrund
- **Textmodus** — Testen ohne Audio möglich
- **Interaktives Setup** — `./setup.sh` mit Modellauswahl (Whisper base/small, LLM-Modell)
- **Konfigurierbare Wissensbasis** — eigene Inhalte in `knowledge_base.py` eintragen

---

## Architektur

```
Mikrofon
  |
[Silence-VAD]              RMS-basierte Sprecherkennung (kein Cloud)
  |
[faster-whisper STT]       transkribiert Deutsch lokal
  |
[Ollama LLM]               lokales LLM mit eingebetteter Wissensbasis
  |
[Farewell-Erkennung]       LLM erkennt Verabschiedungen semantisch
  |
[Piper TTS]                deutsches TTS (Thorsten-Voice), lokal
  |
Lautsprecher
  |
[JSON-Transkript]          speichert Gespräch als JSON-Datei
```

---

## Beispiel-Dialog

```
Bot:  Willkommen, wie kann ich Ihnen helfen?

User: Was könnt ihr für mich tun?

Bot:  Wir bieten Beratung, Entwicklung und Schulungen an.

User: Wie erreiche ich euch?

Bot:  Sie erreichen uns per E-Mail an info at musterfirma punkt de oder
      telefonisch unter null eins zwei drei, vier fünf sechs, sieben acht neun.

User: Danke, tschüss!

Bot:  Gerne! Auf Wiederhören und einen schönen Tag noch!
```

---

## Wissensbasis

Die Wissensbasis wird in `knowledge_base.py` als System-Prompt definiert. Der Bot kann nur Fragen beantworten, die dort hinterlegt sind. Eigene Inhalte einfach eintragen — Firmeninfos, Produkte, FAQ, Kontaktdaten etc.

---

## Komponentenentscheidungen

| Komponente | Technologie | Modell | Begründung |
|---|---|---|---|
| VAD | RMS-Schwellwert (custom) | — | Einfach, keine Abhängigkeit, konfigurierbar via `SILENCE_THRESHOLD` |
| STT | faster-whisper | `base`/`small` | Beste deutsche OSS-ASR, vollständig lokal, schneller als Original-Whisper |
| LLM | Ollama | `llama3.2:3b` | Lokales Modell-Management, gute Deutschunterstützung |
| TTS | Piper TTS | `de_DE-thorsten-high` | Deutsche Stimme, vollständig lokal, schnell auf CPU |
| Transkript | JSON-Datei | — | Menschenlesbar, keine Datenbank nötig |

---

## Voraussetzungen

- Python 3.10+
- [Ollama](https://ollama.com) >= 0.1.0 installiert und gestartet
- PortAudio: `brew install portaudio` (macOS) bzw. `apt install portaudio19-dev` (Linux)
- Mikrofon + Lautsprecher (für Sprachmodus `main_voice.py`)
- RAM: mindestens 8 GB empfohlen (LLM ~4–5 GB, Whisper ~1–2 GB, Piper TTS minimal)

**Plattform-Hinweis:** Entwickelt und getestet unter Linux. macOS sollte funktionieren. Windows erfordert zusätzliches PortAudio-Setup und ist nicht offiziell getestet.

---

## Setup und Start

**Automatisch (empfohlen):**
```
./setup.sh
```

Das Skript erstellt eine virtuelle Umgebung, installiert alle Python-Pakete, lädt Piper- und Whisper-Modelle herunter und prüft Ollama.

**Starten:**

Sprachmodus (Mikrofon + Lautsprecher):
```
python main_voice.py
```

Textmodus (kein Audio, ideal zum Testen):
```
python main_text.py
```

---

## Projektstruktur

```
├── setup.sh               Installations-Skript (alle Abhängigkeiten)
├── main_voice.py          Sprachmodus (Mic -> STT -> LLM -> TTS -> Speaker)
├── main_text.py           Textmodus (Terminal-Chat mit optionalem TTS)
├── config.py              Konfiguration via Umgebungsvariablen / .env
├── knowledge_base.py      System-Prompt mit Wissensbasis (hier anpassen!)
├── tts_service.py         Piper-TTS-Wrapper mit Telefonnummern-Normalisierung
├── requirements.txt       Python-Abhängigkeiten
├── models/                Lokale Modelle (Whisper, Piper)
├── transcripts/           Gespeicherte Gesprächstranskripte (JSON)
└── tests/                 Tests (LLM, TTS)
```

---

## Tests

### `tests/test_text_mode.py` — LLM-Tests

Testet Grundfunktionen des LLM. Kein Audio nötig, aber Ollama muss laufen.

| Test | Prüft |
|---|---|
| `test_ollama_running` | Ollama-Server erreichbar |
| `test_german_response` | Antwort erfolgt auf Deutsch (auch bei englischer Frage) |
| `test_short_response` | Antwort ist kurz (max 2–3 Sätze) |
| `test_farewell_detection` | Verabschiedung wird erkannt ([ENDE]-Marker oder Abschiedsworte) |

```
python tests/test_text_mode.py
```

### `tests/test_tts.py` — TTS-Ausgabetest

Spielt einen Testsatz über die Lautsprecher ab. Benötigt Audio.

```
python tests/test_tts.py
```

---

## Transkripte

Jede Gesprächssession wird automatisch gespeichert unter:

```
transcripts/transcript_YYYYMMDD_HHMMSS.json
```

Beispiel:

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

## Konfiguration

| Variable | Standard | Beschreibung |
|---|---|---|
| `WHISPER_MODEL` | `base` | Whisper-Modellgröße (`base`, `small`) — wird im Setup gewählt |
| `OLLAMA_MODEL` | `llama3.2:3b` | Ollama-Modellname |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama-Server-URL |
| `PIPER_MODEL` | `models/de_DE-thorsten-high.onnx` | Pfad zum Piper-Stimmmodell |
| `SILENCE_THRESHOLD` | `400` | RMS-Schwellwert für Sprecherkennung (niedriger = empfindlicher) |
| `SILENCE_SECONDS` | `1.5` | Sekunden Stille bis Aufnahme endet |
| `SPEAK` | `1` (voice) / `0` (text) | TTS-Ausgabe ein/aus |
| `IDLE_TIMEOUT` | `30` | Sekunden Stille bis Gespräch automatisch endet |

---

## Self-Hosted-Betrieb

Alle Komponenten laufen vollständig ohne Cloud:

| Komponente | Lizenz |
|---|---|
| faster-whisper | MIT |
| Ollama + llama3.2 | Meta Llama Community License |
| Piper TTS | MIT |
