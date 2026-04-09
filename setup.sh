#!/usr/bin/env bash
set -e

PIPER_MODEL="de_DE-thorsten-high"
PIPER_BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/high"
WHISPER_FILES="config.json model.bin tokenizer.json vocabulary.txt"

download() {
    curl -# -L -o "$2" "$1"
}

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║   Deutscher Sprachbot — Setup                 ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# --- Whisper model selection ---
echo "Welches Whisper-Modell für Spracherkennung?"
echo ""
echo "  1) base   — schnell, ~145 MB RAM, gute Erkennung"
echo "  2) small  — langsamer, ~460 MB RAM, bessere Erkennung"
echo ""
read -rp "Auswahl [1]: " whisper_choice
case "${whisper_choice}" in
    2) WHISPER_MODEL="small" ;;
    *) WHISPER_MODEL="base" ;;
esac
echo "  → Whisper '${WHISPER_MODEL}' ausgewählt."
echo ""

# --- Ollama model selection ---
echo "Welches LLM-Modell für Antworten?"
echo ""
echo "  1) llama3.2:3b  — schnell, ~2 GB, Standard"
echo "  2) llama3:8b    — langsamer, ~5 GB, bessere Qualität"
echo "  3) qwen2.5:7b   — langsamer, ~5 GB, gutes Deutsch"
echo ""
read -rp "Auswahl [1]: " llm_choice
case "${llm_choice}" in
    2) OLLAMA_MODEL="llama3:8b" ;;
    3) OLLAMA_MODEL="qwen2.5:7b" ;;
    *) OLLAMA_MODEL="llama3.2:3b" ;;
esac
echo "  → ${OLLAMA_MODEL} ausgewählt."
echo ""

WHISPER_REPO="Systran/faster-whisper-${WHISPER_MODEL}"
WHISPER_DIR="models/whisper-${WHISPER_MODEL}"

# --- Installation ---
echo "════════════════════════════════════════════════"
echo ""

# 1. Python venv
if [ ! -d ".venv" ]; then
    echo "[1/5] Erstelle virtuelle Umgebung..."
    python3 -m venv .venv
else
    echo "[1/5] Virtuelle Umgebung vorhanden."
fi

# 2. Pip install
echo "[2/5] Installiere Python-Abhängigkeiten..."
.venv/bin/pip install --progress-bar on -r requirements.txt

# 3. Piper model
mkdir -p models
if [ ! -f "models/${PIPER_MODEL}.onnx" ]; then
    echo "[3/5] Lade Piper-Stimmmodell herunter..."
    echo "  [1/2] ${PIPER_MODEL}.onnx"
    download "${PIPER_BASE}/${PIPER_MODEL}.onnx" "models/${PIPER_MODEL}.onnx"
    echo "  [2/2] ${PIPER_MODEL}.onnx.json"
    download "${PIPER_BASE}/${PIPER_MODEL}.onnx.json" "models/${PIPER_MODEL}.onnx.json"
else
    echo "[3/5] Piper-Stimmmodell vorhanden."
fi

# 4. Whisper model
if [ ! -f "${WHISPER_DIR}/model.bin" ]; then
    echo "[4/5] Lade Whisper '${WHISPER_MODEL}' herunter..."
    mkdir -p "${WHISPER_DIR}"
    CURRENT=0
    FILE_COUNT=4
    for fname in ${WHISPER_FILES}; do
        CURRENT=$((CURRENT + 1))
        if [ ! -s "${WHISPER_DIR}/${fname}" ]; then
            echo "  [${CURRENT}/${FILE_COUNT}] ${fname}"
            download "https://huggingface.co/${WHISPER_REPO}/resolve/main/${fname}" "${WHISPER_DIR}/${fname}"
        else
            echo "  [${CURRENT}/${FILE_COUNT}] ${fname} (vorhanden)"
        fi
    done
else
    echo "[4/5] Whisper '${WHISPER_MODEL}' vorhanden."
fi

# 5. Ollama
echo "[5/5] Prüfe Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "  FEHLER: Ollama nicht installiert. Siehe https://ollama.com"
    exit 1
fi

if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  Starte Ollama..."
    ollama serve &
    sleep 3
fi

if ! ollama list | grep -q "${OLLAMA_MODEL}"; then
    echo "  Lade Modell ${OLLAMA_MODEL}..."
    ollama pull "${OLLAMA_MODEL}"
else
    echo "  Modell ${OLLAMA_MODEL} vorhanden."
fi

# --- Write selected config ---
cat > .env <<EOF
WHISPER_MODEL=${WHISPER_MODEL}
OLLAMA_MODEL=${OLLAMA_MODEL}
EOF

echo ""
echo "════════════════════════════════════════════════"
echo ""
echo "Setup abgeschlossen!"
echo ""
echo "  Whisper:  ${WHISPER_MODEL}"
echo "  LLM:      ${OLLAMA_MODEL}"
echo "  Konfig:   .env"
echo ""
echo "Starten mit:"
echo "  .venv/bin/python main_voice.py    # Sprachmodus"
echo "  .venv/bin/python main_text.py     # Textmodus"
echo ""
