# Changelog

## v0.1.0 (2026-10-15)

First public release.

- **Narrated demo videos from a script and screenshots:**
  - cloned-voice narration, spoken phrase by phrase
  - highlight boxes timed to the words
  - burned-in captions
  - title and closing cards, process-map frames and picture-in-picture insets
- **Bangla:** IndicF5, zero-shot cloning from a 8-12 s clip and its transcript. Bundled stock voice `speaker-00737` (SLR37, CC BY-SA 4.0).
- **English:** Chatterbox Turbo, zero-shot cloning from a 5+ s clip, or its built-in voice.
- **Install only what you need:** `LANGUAGES=bn`, `en` or both, and add a language later.
- **Automatic retakes:** Whisper checks each phrase and regenerates wrong ones (`"retakes"`).
- **Voice tools:** `make_voice` cuts a reference clip from a recording, with a draft transcript.
- **Platforms:** macOS (Apple Silicon) and Linux. On Linux: CPU (`TORCH_CPU=1`), NVIDIA GPU with CUDA 13 (driver 580+) or CUDA 12.6 (`TORCH_CUDA=cu126`). `studio.device` reports what's in use.
- **Python 3.12,** with every package at its newest compatible release.
- **Claude Code skill:**
  - loaded automatically in the repo
  - guided, one-shot or custom checkpoints
- **Demos:** English and Bangla demo videos, built with the tool itself (`examples/`).
- **Tests and CI:** unit tests and lint on every push.

Tested on macOS (Apple Silicon) and on CPU-only Linux (Debian, Python 3.12). GPU on Linux uses the standard PyTorch CUDA builds but hasn't been tested on NVIDIA hardware yet.
