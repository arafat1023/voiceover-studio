#!/usr/bin/env bash
# Fresh install of voiceover-studio: Python venv, IndicF5 + pinned deps, model weights, vocoder.
# Usage: ./setup.sh            (macOS or Linux; about 3 GB of downloads)
set -euo pipefail
cd "$(dirname "$0")"

need() { command -v "$1" >/dev/null 2>&1 || { echo "missing: $1 ($2)"; exit 1; }; }
need ffmpeg "brew install ffmpeg  (needs libass for captions: ffmpeg -filters | grep ' ass ')"
ffmpeg -hide_banner -filters 2>/dev/null | grep -q ' ass ' || { echo "ffmpeg has no libass (captions need it)"; exit 1; }
if [ ! -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ] && ! command -v google-chrome >/dev/null && ! command -v chromium >/dev/null; then
  echo "missing: Google Chrome (cards are rendered with headless Chrome)"; exit 1
fi

PY=${PYTHON:-python3.10}
need "$PY" "install Python 3.10, e.g. 'brew install python@3.10' or 'uv python install 3.10'"
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# IndicF5 weights. The official repo (ai4bharat/IndicF5) is gated; accept its terms on Hugging Face
# and run 'hf auth login' to use it, or use the public mirror below (same files, MIT licence).
REPO=${INDICF5_REPO:-rsolanki1822/IndicF5-mirror}
if [ ! -f models/indicf5-base/model.safetensors ]; then
  .venv/bin/python - "$REPO" <<'PY'
import sys
from huggingface_hub import snapshot_download
snapshot_download(sys.argv[1], local_dir='models/indicf5-base',
                  allow_patterns=['model.safetensors', 'config.json', 'model.py', 'checkpoints/vocab.txt'])
PY
fi

# Vocoder (cached by Hugging Face) and, optionally, the Bengali Whisper used for draft transcripts.
.venv/bin/python -c "from huggingface_hub import snapshot_download as d; d('charactr/vocos-mel-24khz')"
if [ "${WITH_ASR:-1}" = 1 ]; then
  .venv/bin/python -c "from huggingface_hub import snapshot_download as d; d('bengaliAI/tugstugi_bengaliai-asr_whisper-medium')"
fi

fc-list 2>/dev/null | grep -qi kalpurush || ls ~/Library/Fonts /Library/Fonts 2>/dev/null | grep -qi kalpurush \
  || echo "note: install the Kalpurush font (captions and cards use it), or set another font in project.json"

echo "ready. Test: .venv/bin/python -m studio.speak voices/<name> 'আসসালামু আলাইকুম।' test.wav"
