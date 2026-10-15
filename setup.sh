#!/usr/bin/env bash
# Install voiceover-studio on macOS or Linux.
#   ./setup.sh                    Bangla and English (default)
#   LANGUAGES=bn ./setup.sh       Bangla only
#   LANGUAGES=en ./setup.sh       English only
# Run it again with more languages to add one later; what is already installed is kept.
#
# Checks the system tools (and prints the install command for anything missing), installs the
# Kalpurush font for Bangla, creates .venv with the pinned Python packages, and downloads the models
# for the chosen languages: IndicF5 + Vocos (Bangla, ~1.4 GB), Chatterbox Turbo (English, ~4 GB),
# and optionally a Whisper model per language for drafting voice transcripts and checking takes.
#
# Options (environment variables):
#   LANGUAGES=bn,en            which engines to install: bn (Bangla), en (English) or both (default)
#   PYTHON=python3.12          the Python 3.12 interpreter to use
#   TORCH_CPU=1                Linux without an NVIDIA GPU: install the smaller CPU-only PyTorch
#   TORCH_CUDA=cu126           Linux with an NVIDIA driver older than 580: PyTorch built for CUDA 12.6
#                              (the default Linux build targets CUDA 13, which needs driver 580+)
#   INDICF5_REPO=ai4bharat/IndicF5   use the official (gated) model repo instead of the mirror
#   WITH_ASR=0                 skip Whisper (drafts voice transcripts and checks takes; optional)
#   WITH_EN=0                  older spelling of LANGUAGES=bn
set -euo pipefail
cd "$(dirname "$0")"

LANGUAGES=${LANGUAGES:-$([ "${WITH_EN:-1}" = 0 ] && echo bn || echo bn,en)}
HAS_BN=0; HAS_EN=0
for lang in ${LANGUAGES//,/ }; do
  case "$lang" in
    bn) HAS_BN=1 ;;
    en) HAS_EN=1 ;;
    *) echo "LANGUAGES: unknown language '$lang' (use bn, en, or bn,en)"; exit 1 ;;
  esac
done
if [ $HAS_BN = 0 ] && [ $HAS_EN = 0 ]; then
  echo "LANGUAGES is empty (use bn, en, or bn,en)"; exit 1
fi
LANG_NAMES=""
if [ $HAS_BN = 1 ]; then LANG_NAMES="Bangla"; fi
if [ $HAS_EN = 1 ]; then LANG_NAMES="${LANG_NAMES:+$LANG_NAMES + }English"; fi
echo "installing: $LANG_NAMES"

OS=$(uname -s)
missing=()
hint() {
  if [ "$OS" = Darwin ]; then echo "$1"; elif command -v apt-get >/dev/null; then echo "$2"; elif command -v dnf >/dev/null; then echo "$3"; else echo "$4"; fi
}

PY=${PYTHON:-python3.12}
# Run it, not just look it up: a pyenv shim exists even when that version isn't active. Early 3.12
# patch releases (3.12.0) lack an RLock method that multiprocess (via IndicF5) calls at exit.
"$PY" -c 'import sys, _thread; sys.exit(sys.version_info[:2] != (3, 12) or not hasattr(_thread.RLock(), "_recursion_count"))' >/dev/null 2>&1 \
  || missing+=("a recent Python 3.12 (or set PYTHON=/path/to/python3.12; with pyenv: pyenv install 3.12, then PYTHON=\$(pyenv root)/versions/<3.12.x>/bin/python): $(hint 'brew install python@3.12' \
  'sudo apt install python3.12 python3.12-venv   (Ubuntu 24.04+; on 22.04 first: sudo add-apt-repository ppa:deadsnakes/ppa)' \
  'sudo dnf install python3.12' 'https://www.python.org/downloads/ (or: uv python install 3.12, then PYTHON=$(uv python find 3.12))')")

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

# Kalpurush (Bangla captions and cards). Installed for this user only; no sudo needed.
# (Command output is captured before grep -q: with pipefail, grep -q quitting early breaks the pipe.)
if [ $HAS_BN = 1 ] && ! grep -qi kalpurush <<<"$(fc-list 2>/dev/null; ls ~/Library/Fonts /Library/Fonts 2>/dev/null)"; then
  FONT_DIR=$([ "$OS" = Darwin ] && echo ~/Library/Fonts || echo ~/.local/share/fonts)
  mkdir -p "$FONT_DIR"
  echo "installing the Kalpurush font into $FONT_DIR"
  curl -fsSL https://www.omicronlab.com/download/fonts/kalpurush.ttf -o "$FONT_DIR/kalpurush.ttf"
  command -v fc-cache >/dev/null && fc-cache -f "$FONT_DIR" >/dev/null || true
fi

# Python packages.
if [ -e .venv ] && ! .venv/bin/python -c 'import sys; sys.exit(sys.version_info[:2] != (3, 12))' 2>/dev/null; then
  echo ".venv was made with another Python version. Remove it (rm -rf .venv) and run ./setup.sh again."
  exit 1
fi
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/pip install --upgrade pip
# PyTorch variant: the PyPI default (Apple Silicon on macOS, CUDA 13 on Linux), CPU-only, or another
# CUDA build. Installed first from PyTorch's own index; the pins in requirements.txt then match it.
TORCH_INDEX=""
if [ "${TORCH_CPU:-0}" = 1 ]; then
  TORCH_INDEX=cpu
elif [ -n "${TORCH_CUDA:-}" ]; then
  TORCH_INDEX=$TORCH_CUDA
fi
if [ -n "$TORCH_INDEX" ]; then
  .venv/bin/pip install --index-url "https://download.pytorch.org/whl/$TORCH_INDEX" \
    "$(grep "^torch==" requirements.txt)" "$(grep "^torchaudio==" requirements.txt)" "$(grep "^torchcodec==" requirements.txt)"
fi
.venv/bin/pip install -r requirements.txt
if [ $HAS_BN = 1 ]; then
  .venv/bin/pip install -r requirements-bn.txt
fi
if [ $HAS_EN = 1 ]; then
  .venv/bin/pip install -r requirements-en.txt
  # --no-deps: chatterbox-tts pins older torch/transformers than requirements.txt; it runs on these.
  .venv/bin/pip install --no-deps chatterbox-tts==0.1.7
fi

# IndicF5 weights. The official repo (ai4bharat/IndicF5) is gated: accept its terms on Hugging Face
# and run '.venv/bin/hf auth login' to use it. The default mirror has the same files (MIT licence).
REPO=${INDICF5_REPO:-rsolanki1822/IndicF5-mirror}
if [ $HAS_BN = 1 ] && [ ! -f models/indicf5-base/model.safetensors ]; then
  .venv/bin/python - "$REPO" <<'PY'
import sys
from huggingface_hub import snapshot_download
snapshot_download(sys.argv[1], local_dir='models/indicf5-base',
                  allow_patterns=['model.safetensors', 'config.json', 'model.py', 'checkpoints/vocab.txt'])
PY
fi

# The rest of each engine's models (Hugging Face cache), and optionally its Whisper model.
fetch() { .venv/bin/python -c "from huggingface_hub import snapshot_download as d; d('$1'${2:+, allow_patterns=$2})"; }
if [ $HAS_BN = 1 ]; then
  fetch charactr/vocos-mel-24khz
  if [ "${WITH_ASR:-1}" = 1 ]; then
    fetch bengaliAI/tugstugi_bengaliai-asr_whisper-medium
  fi
fi
if [ $HAS_EN = 1 ]; then
  fetch ResembleAI/chatterbox-turbo "['*.safetensors', '*.json', '*.txt', '*.pt', '*.model']"
  if [ "${WITH_ASR:-1}" = 1 ]; then
    fetch openai/whisper-small
  fi
fi

echo
.venv/bin/python -m studio.device
echo "ready ($LANG_NAMES). Test:"
if [ $HAS_BN = 1 ]; then
  echo "  .venv/bin/python -m studio.speak voices/speaker-00737 'আসসালামু আলাইকুম।' test-bn.wav"
fi
if [ $HAS_EN = 1 ]; then
  echo "  .venv/bin/python -m studio.speak builtin 'Welcome to the demo.' test-en.wav --language en"
fi
