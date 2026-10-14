# voiceover-studio

Make narrated product-demo videos in **Bangla**, using a **cloned voice**. Everything runs on your own machine: no cloud TTS service and no per-minute fees.

You provide a script, some screenshots and a short voice recording. You get back a 1080p MP4 with:

- narration in the cloned voice (IndicF5 zero-shot cloning; nothing is trained)
- highlight boxes that light up as each element is mentioned
- burned-in Bangla captions, synced phrase by phrase
- title and closing cards, step-by-step process diagrams and picture-in-picture insets

```
pitch.md ──narrate──▶ narration/*.wav + timings.json ─┐
project.json ──cards──▶ cards/*.png ──────────────────┼──build──▶ video.mp4
shots/*.jpg + cues.json ──────────────────────────────┘
```

## Requirements

- macOS (Apple Silicon recommended) or Linux. On Windows, use WSL.
- Python 3.10
- ffmpeg built with **libass** (needed for captions). Homebrew's ffmpeg includes it.
- Google Chrome (renders the cards so Bangla text shapes correctly)
- the [Kalpurush](https://www.omicronlab.com/bangla-fonts.html) font
- about 4 GB of disk space for the model and Python packages

## Install

```bash
git clone <this repo> voiceover-studio && cd voiceover-studio
brew install python@3.10 ffmpeg     # macOS; on Linux use your package manager
./setup.sh
```

`setup.sh` creates `.venv/`, installs pinned packages and downloads the IndicF5 weights into `models/`. It fetches them from a public mirror. To use the official gated repo instead, accept its terms on Hugging Face, run `hf auth login`, then run `INDICF5_REPO=ai4bharat/IndicF5 ./setup.sh`. Set `WITH_ASR=0` to skip the optional Bengali Whisper download.

## Quick start

**1. Make a voice.** You need the speaker's consent (see below) and 8-12 s of clean speech.

```bash
.venv/bin/python -m studio.make_voice recording.m4a voices/alice                        # lists segments + draft transcripts
.venv/bin/python -m studio.make_voice recording.m4a voices/alice --start 3.9 --end 14.1 # cuts the reference clip
# now edit voices/alice/reference.txt so it matches the clip word for word
.venv/bin/python -m studio.speak voices/alice "আসসালামু আলাইকুম।" test.wav               # listen
```

**2. Start a project.**

```bash
cp -r projects/_template projects/my-demo
```

Then fill in the project:
- In `project.json`, set `"voice": "voices/alice"`.
- Write `pitch.md`, with numbers written in words.
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
voices/         one folder per voice: reference.wav + reference.txt + README.txt
projects/       one folder per video; _template/ is the starter
docs/           GUIDE.md (full workflow), MODELS.md (models, links, licences)
claude-skill/   optional Claude Code skill that drives this workflow
setup.sh, requirements.txt
```

## Not in the repo

`.gitignore` keeps these out:

- `.venv/`, `models/`, `data/`: `setup.sh` recreates them.
- **Voice audio** (`voices/**/*.wav|m4a|mp3`). A voice belongs to a person. Share voice folders privately, and only with the speaker's agreement.
- **`voices/user-voice/`**, a colleague's voice used for our own demos. He agreed to that use, not to publishing his voice, transcript or name, so the whole folder stays local.

The one voice that **is** included is `voices/speaker-00737`. It comes from the open SLR37 corpus (CC BY-SA 4.0), so it can be shared as long as the credit is kept. The template uses it, so a fresh clone works out of the box. The template's `project.json` already carries the credit line.
- **Projects** other than `_template`: they usually hold client screenshots, scripts and output.
- `*.mp4` output.

## Consent and attribution

- Clone a real person's voice **only with their explicit consent**, and record it in `voices/<name>/README.txt`: who they are, when they agreed and for what use.
- Don't use a cloned voice to make someone appear to say something they haven't approved.
- Don't present cloned speech as a live recording of them.
- Voices built from a licensed corpus must carry its credit line. For OpenSLR SLR37 (CC BY-SA 4.0), set `"credit": "Voice based on Google SLR37 Bengali speech data, CC BY-SA 4.0"` in `project.json`; the closing card prints it.

## Using with Claude Code

```bash
cp -r claude-skill/narrated-demo-video ~/.claude/skills/
```

Then ask Claude for "a narrated demo video of …". It follows the workflow: pitch, then voice, narration, screenshots, cues, preview and full build. It checks preview frames before the full build.

## Credits

Built on [IndicF5](https://github.com/AI4Bharat/IndicF5) (AI4Bharat, MIT), [F5-TTS](https://github.com/SWivid/F5-TTS) (MIT) and [Vocos](https://huggingface.co/charactr/vocos-mel-24khz) (MIT). Optional: [Bengali Whisper](https://huggingface.co/bengaliAI/tugstugi_bengaliai-asr_whisper-medium) for draft transcripts, and [OpenSLR SLR37](https://openslr.org/37/) for stock voices. Details are in [docs/MODELS.md](docs/MODELS.md).
