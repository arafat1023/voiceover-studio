#!/usr/bin/env bash
# Fresh install of voiceover-studio on macOS or Linux.
#   ./setup.sh
# Checks the system tools (and prints the install command for anything missing), installs the
# Kalpurush font for the current user, creates .venv with the pinned Python packages, and downloads
# the IndicF5 weights, the Vocos vocoder and (optionally) Bengali Whisper. About 3-5 GB of downloads.
#
# Options (environment variables):
#   PYTHON=python3.10          the Python 3.10 interpreter to use
#   TORCH_CPU=1                Linux without an NVIDIA GPU: install the smaller CPU-only PyTorch
#   INDICF5_REPO=ai4bharat/IndicF5   use the official (gated) model repo instead of the mirror
#   WITH_ASR=0                 skip Bengali Whisper (only used to draft voice transcripts)
set -euo pipefail
cd "$(dirname "$0")"

OS=$(uname -s)
missing=()
hint() {
  if [ "$OS" = Darwin ]; then echo "$1"; elif command -v apt-get >/dev/null; then echo "$2"; elif command -v dnf >/dev/null; then echo "$3"; else echo "$4"; fi
}

PY=${PYTHON:-python3.10}
command -v "$PY" >/dev/null || missing+=("Python 3.10: $(hint 'brew install python@3.10' \
  'sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install python3.10 python3.10-venv' \
  'sudo dnf install python3.10' 'https://www.python.org/downloads/ (or: uv python install 3.10, then PYTHON=$(uv python find 3.10))')")

if ! command -v ffmpeg >/dev/null; then
  missing+=("ffmpeg: $(hint 'brew install ffmpeg' 'sudo apt install ffmpeg' 'sudo dnf install ffmpeg (RPM Fusion)' 'https://ffmpeg.org/download.html')")
elif ! grep -q ' ass ' <<<"$(ffmpeg -hide_banner -filters 2>/dev/null)"; then
  missing+=("ffmpeg with libass (captions need it): your ffmpeg lacks it; install the distro/Homebrew ffmpeg, which includes it")
fi

CHROME=""
for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" google-chrome google-chrome-stable chromium chromium-browser; do
  if [ -x "$c" ] || command -v "$c" >/dev/null; then CHROME=$c; break; fi
done
[ -n "$CHROME" ] || missing+=("Google Chrome or Chromium (renders the cards): $(hint 'https://www.google.com/chrome/ (or: brew install --cask google-chrome)' \
  'wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && sudo apt install ./google-chrome-stable_current_amd64.deb   (ARM: sudo apt install chromium)' \
  'sudo dnf install chromium' 'https://www.google.com/chrome/')")

if [ ${#missing[@]} -gt 0 ]; then
  echo "Install these first, then run ./setup.sh again:"
  printf '  - %s\n' "${missing[@]}"
  exit 1
fi

# Kalpurush (captions and cards). Installed for this user only; no sudo needed.
# (Command output is captured before grep -q: with pipefail, grep -q quitting early breaks the pipe.)
if ! grep -qi kalpurush <<<"$(fc-list 2>/dev/null; ls ~/Library/Fonts /Library/Fonts 2>/dev/null)"; then
  FONT_DIR=$([ "$OS" = Darwin ] && echo ~/Library/Fonts || echo ~/.local/share/fonts)
  mkdir -p "$FONT_DIR"
  echo "installing the Kalpurush font into $FONT_DIR"
  curl -fsSL https://www.omicronlab.com/download/fonts/kalpurush.ttf -o "$FONT_DIR/kalpurush.ttf"
  command -v fc-cache >/dev/null && fc-cache -f "$FONT_DIR" >/dev/null || true
fi

# Python packages.
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/pip install --upgrade pip
if [ "${TORCH_CPU:-0}" = 1 ]; then
  .venv/bin/pip install --index-url https://download.pytorch.org/whl/cpu \
    "$(grep '^torch==' requirements.txt)" "$(grep '^torchaudio==' requirements.txt)"
fi
.venv/bin/pip install -r requirements.txt

# IndicF5 weights. The official repo (ai4bharat/IndicF5) is gated: accept its terms on Hugging Face
# and run '.venv/bin/hf auth login' to use it. The default mirror has the same files (MIT licence).
REPO=${INDICF5_REPO:-rsolanki1822/IndicF5-mirror}
if [ ! -f models/indicf5-base/model.safetensors ]; then
  .venv/bin/python - "$REPO" <<'PY'
import sys
from huggingface_hub import snapshot_download
snapshot_download(sys.argv[1], local_dir='models/indicf5-base',
                  allow_patterns=['model.safetensors', 'config.json', 'model.py', 'checkpoints/vocab.txt'])
PY
fi

# Vocoder (Hugging Face cache) and, optionally, Bengali Whisper for draft transcripts.
.venv/bin/python -c "from huggingface_hub import snapshot_download as d; d('charactr/vocos-mel-24khz')"
if [ "${WITH_ASR:-1}" = 1 ]; then
  .venv/bin/python -c "from huggingface_hub import snapshot_download as d; d('bengaliAI/tugstugi_bengaliai-asr_whisper-medium')"
fi

echo
echo "ready. Test the bundled voice:"
echo "  .venv/bin/python -m studio.speak voices/speaker-00737 'আসসালামু আলাইকুম।' test.wav"
