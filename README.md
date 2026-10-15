# voiceover-studio

Make narrated product-demo videos in **Bangla or English**, using a **cloned voice**. Everything runs on your own machine: no cloud TTS service and no per-minute fees.

You provide a script, some screenshots and a short voice recording. You get back a 1080p MP4 with:

- narration in the cloned voice (zero-shot cloning; nothing is trained)
- highlight boxes that light up as each element is mentioned
- burned-in captions, synced phrase by phrase
- title and closing cards, step-by-step process diagrams and picture-in-picture insets

```
pitch.md ──narrate──▶ narration/*.wav + timings.json ─┐
project.json ──cards──▶ cards/*.png ──────────────────┼──build──▶ video.mp4
shots/*.jpg + cues.json ──────────────────────────────┘
```

| Language | Engine | Voice cloning | Licence |
|----------|--------|---------------|---------|
| Bangla (`"language": "bn"`, the default) | [IndicF5](https://github.com/AI4Bharat/IndicF5) | from 8-12 s of speech **plus its exact transcript** | MIT |
| English (`"language": "en"`) | [Chatterbox Turbo](https://github.com/resemble-ai/chatterbox) | from 5+ s of speech, no transcript; or its built-in voice | MIT |

Any voice can speak either language. A Bangla speaker's clip can narrate in English, and the reverse.

## Requirements

- macOS (Apple Silicon recommended) or Linux (an NVIDIA GPU is optional; CPU works, just much slower). On Windows, use WSL2 with Ubuntu and follow the Linux steps.
- **Python 3.12**, a recent patch release (3.12.13 or later is known to work)
- ffmpeg with libass, and Google Chrome or Chromium
- about 12 GB of free disk space (6 GB for Bangla only) and 8 GB of RAM (16 GB recommended)

## Install

### 1. Clone

```bash
git clone https://github.com/arafat1023/voiceover-studio.git
cd voiceover-studio
```

### 2. Install the system tools

**macOS** (with [Homebrew](https://brew.sh)):

```bash
brew install python@3.12 ffmpeg
brew install --cask google-chrome      # skip if Chrome is already installed
```

**Ubuntu 24.04+ / Debian / WSL2:**

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv ffmpeg fontconfig curl git
# Ubuntu 22.04 has no python3.12: first run  sudo add-apt-repository ppa:deadsnakes/ppa
# Debian 12 has no python3.12: use  uv python install 3.12  (https://docs.astral.sh/uv/) or pyenv
# Chrome (x86_64):
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb
# ...or Chromium on Debian or ARM: sudo apt install chromium
```

**Fedora:** `sudo dnf install python3.12 chromium`, plus ffmpeg from [RPM Fusion](https://rpmfusion.org/Configuration).

### 3. Run the setup script

```bash
./setup.sh                    # macOS, or Linux with an NVIDIA GPU
TORCH_CPU=1 ./setup.sh        # Linux without an NVIDIA GPU (much smaller PyTorch download)
```

If a system tool is missing, `setup.sh` stops and prints the exact install command for your OS. Fix it and run the script again; it skips anything already done. If `python3.12` isn't on your PATH (pyenv, uv), point at it: `PYTHON=/path/to/python3.12 ./setup.sh`.

### What gets downloaded

You never download any of these by hand; `setup.sh` handles each one.

| What | Size | From | Where it goes |
|------|------|------|---------------|
| Python packages (PyTorch, IndicF5 code, Chatterbox, …) | ~1-3 GB | PyPI, GitHub, pytorch.org | `.venv/` |
| IndicF5 model weights (Bangla) | 1.3 GB | [rsolanki1822/IndicF5-mirror](https://huggingface.co/rsolanki1822/IndicF5-mirror) | `models/indicf5-base/` |
| Vocos vocoder (Bangla) | 50 MB | [charactr/vocos-mel-24khz](https://huggingface.co/charactr/vocos-mel-24khz) | `~/.cache/huggingface/` |
| Chatterbox Turbo (English) | ~4 GB | [ResembleAI/chatterbox-turbo](https://huggingface.co/ResembleAI/chatterbox-turbo) | `~/.cache/huggingface/` |
| Bengali Whisper (optional) | 3 GB | [bengaliAI/tugstugi_bengaliai-asr_whisper-medium](https://huggingface.co/bengaliAI/tugstugi_bengaliai-asr_whisper-medium) | `~/.cache/huggingface/` |
| Whisper small (optional, English) | 1 GB | [openai/whisper-small](https://huggingface.co/openai/whisper-small) | `~/.cache/huggingface/` |
| Kalpurush font (only if missing) | 300 KB | [omicronlab.com](https://www.omicronlab.com/bangla-fonts.html) | `~/Library/Fonts` (macOS), `~/.local/share/fonts` (Linux) |

The Whisper models are optional helpers. They draft the transcript when you make a voice, and they check each narrated phrase when a project sets `"retakes"`.

Options, set before `./setup.sh`:

| Variable | Effect |
|----------|--------|
| `TORCH_CPU=1` | CPU-only PyTorch (Linux) |
| `WITH_EN=0` | Bangla only: skip the English engine (saves ~4 GB) |
| `WITH_ASR=0` | skip the Whisper models |
| `INDICF5_REPO=ai4bharat/IndicF5` | use the official model instead of the mirror. It's gated: first accept its terms on [the model page](https://huggingface.co/ai4bharat/IndicF5), then run `.venv/bin/hf auth login` |
| `PYTHON=/path/to/python3.12` | use a specific Python 3.12 |

Optional, downloaded by hand only if you need them:

- **OpenSLR SLR37** (560 MB): only needed to pick a *different* Bangla stock voice. Download it with `curl -LO https://www.openslr.org/resources/37/bn_bd.zip && unzip -q bn_bd.zip -d data/slr37-bn-bd`, then run `.venv/bin/python tools/pick_stock_speaker.py data/slr37-bn-bd`. The guide explains how to turn a speaker into a voice.
- **[Claude in Chrome](https://claude.ai/chrome)**: only if you want Claude Code to take the screenshots for you (see the guide).

### 4. Test it

```bash
.venv/bin/python -m studio.speak voices/speaker-00737 "আসসালামু আলাইকুম।" test-bn.wav
.venv/bin/python -m studio.speak builtin "Welcome to the demo." test-en.wav --language en
```

The first run loads the model, which takes about 30 s. After that, a sentence takes about 5-10 s on Apple Silicon or a GPU, and 20-60 s on a CPU.

## Quick start

**1. Make a voice.** You need the speaker's consent (see below) and 8-12 s of clean speech. You can skip this step and use a bundled voice: `voices/speaker-00737` (Bangla stock voice) or `builtin` (English model's own voice).

```bash
.venv/bin/python -m studio.make_voice recording.m4a voices/alice                        # lists segments + draft transcripts
.venv/bin/python -m studio.make_voice recording.m4a voices/alice --start 3.9 --end 14.1 # cuts the reference clip
# Bangla: edit voices/alice/reference.txt so it matches the clip word for word
.venv/bin/python -m studio.speak voices/alice "আসসালামু আলাইকুম।" test.wav               # listen
```

Add `--language en` to both commands for an English recording.

**2. Start a project.**

```bash
cp -r projects/_template    projects/my-demo     # Bangla
cp -r projects/_template-en projects/my-demo     # English
```

Then fill in the project:
- In `project.json`, set `"voice"`.
- Write the script in `pitch.md`.
- Put screenshots in `shots/` and a logo at `assets/logo.png`.
- In `cues.json`, set which words trigger which highlight box.

**3. Build.**

```bash
.venv/bin/python -m studio.narrate projects/my-demo        # voice, scene by scene
.venv/bin/python -m studio.build   projects/my-demo --check
.venv/bin/python -m studio.cards   projects/my-demo
.venv/bin/python -m studio.build   projects/my-demo --only 2   # preview one scene
.venv/bin/python -m studio.build   projects/my-demo            # the full video
```

**[docs/GUIDE.md](docs/GUIDE.md)** walks through the whole process in detail:
- choosing a good voice clip
- writing a script the voice reads well
- fixing pacing and pronunciation
- capturing screenshots and measuring highlight boxes
- cards, process maps and insets
- which step to re-run after which change

## Repo layout

```
studio/         the pipeline: tts, narrate, cards, build, speak, make_voice, config
tools/          pick_stock_speaker.py: choose a voice from an open speech corpus
voices/         one folder per voice: reference.wav (+ reference.txt for Bangla) + README.txt
projects/       one folder per video; _template/ (Bangla) and _template-en/ (English) are the starters
docs/           GUIDE.md (full workflow), MODELS.md (models, links, licences)
claude-skill/   optional Claude Code skill that drives this workflow
setup.sh, requirements.txt, requirements-en.txt
```

## Not in the repo

`.gitignore` keeps these out:

- `.venv/`, `models/`, `data/`: `setup.sh` recreates them.
- **Voice audio** (`voices/**/*.wav|m4a|mp3`). A voice belongs to a person. Share voice folders privately, and only with the speaker's agreement.
- **`voices/user-voice/`**, a colleague's voice used for our own demos. He agreed to that use, not to publishing his voice, transcript or name, so the whole folder stays local.
- **Projects** other than the two templates: they usually hold client screenshots, scripts and output.
- `*.mp4` output.

One voice **is** included: `voices/speaker-00737`. It comes from the open SLR37 corpus (CC BY-SA 4.0), so it can be shared as long as the credit is kept. The Bangla template uses it, and its `project.json` already carries the credit line. The English template uses `builtin`, which ships with the model.

## Package versions

Every Python package is pinned to its newest release that works with the rest. A few are held back on purpose, each with a comment in `requirements.txt` saying why. The root cause is numpy: IndicF5 requires numpy 1.26 or older, and its repo has been inactive since September 2025. That keeps:
- **Python at 3.12:** numpy 1.26 has no wheels for 3.13 or later.
- **`librosa`, `scipy` and `pyarrow` one step behind:** their newest releases need numpy 2.

`huggingface_hub` stays on 1.x because `cached-path` and `diffusers` require it. When IndicF5 supports numpy 2, those holds can be lifted. Chatterbox is installed with `--no-deps` because its own pins (torch 2.6, transformers 5.2) are older than what IndicF5 needs; it runs fine on the newer versions.

## Consent and attribution

- Clone a real person's voice **only with their explicit consent**, and record it in `voices/<name>/README.txt`: who they are, when they agreed and for what use.
- Don't use a cloned voice to make someone appear to say something they haven't approved.
- Don't present cloned speech as a live recording of them.
- English output from Chatterbox carries Resemble AI's inaudible [Perth watermark](https://github.com/resemble-ai/perth), so it can later be identified as AI-generated. Leave it in.
- Voices built from a licensed corpus must carry its credit line. For OpenSLR SLR37 (CC BY-SA 4.0), set `"credit": "Voice based on Google SLR37 Bengali speech data, CC BY-SA 4.0"` in `project.json`; the closing card prints it.

## Using with Claude Code

```bash
cp -r claude-skill/narrated-demo-video ~/.claude/skills/
```

Then ask Claude for "a narrated demo video of …". It follows the workflow: pitch, then voice, narration, screenshots, cues, preview and full build. It checks preview frames before the full build.

## Licence

The code in this repo is MIT-licensed (see [LICENSE](LICENSE)). The models and the bundled voice keep their own licences; see [docs/MODELS.md](docs/MODELS.md).

## Credits

Built on:
- [IndicF5](https://github.com/AI4Bharat/IndicF5) (AI4Bharat, MIT)
- [F5-TTS](https://github.com/SWivid/F5-TTS) (MIT)
- [Vocos](https://huggingface.co/charactr/vocos-mel-24khz) (MIT)
- [Chatterbox](https://github.com/resemble-ai/chatterbox) (Resemble AI, MIT)

Optional:
- [Whisper](https://huggingface.co/openai/whisper-small) and [Bengali Whisper](https://huggingface.co/bengaliAI/tugstugi_bengaliai-asr_whisper-medium) for transcripts and take checks
- [OpenSLR SLR37](https://openslr.org/37/) for stock voices

Details are in [docs/MODELS.md](docs/MODELS.md).
