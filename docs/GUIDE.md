# The full guide: from a recording to a finished video

Run every command from the repo root.

```
pitch.md ──narrate──▶ narration/*.wav + timings.json ─┐
project.json ──cards──▶ cards/*.png ──────────────────┼──build──▶ video.mp4
shots/*.jpg + cues.json ──────────────────────────────┘
```

Start from `projects/_template`: it is a complete, buildable three-scene example once you add two screenshots and a logo.

## 1. Setup (once)

Requirements:
- macOS (Apple Silicon uses `mps`) or Linux (CUDA or CPU)
- Python 3.10
- ffmpeg built with libass
- Google Chrome
- the Kalpurush font

```bash
brew install python@3.10 ffmpeg      # macOS
./setup.sh                           # venv + pinned packages + model weights (~3 GB)
```

`setup.sh` does the following:
- installs IndicF5 at a pinned commit, plus `requirements.txt`
- downloads the IndicF5 weights to `models/indicf5-base/` from a public mirror (the official repo is gated)
- caches the Vocos vocoder
- caches Bengali Whisper, which drafts transcripts for new voices. Skip it with `WITH_ASR=0`.

Model sources and licences are listed in [MODELS.md](MODELS.md).

## 2. Make a voice (once per voice)

A voice is just a folder under `voices/`. Nothing is trained; every line imitates the reference clip.

```
voices/<name>/reference.wav   8-12 s of clean speech, 24 kHz mono
voices/<name>/reference.txt   exactly what that clip says
voices/<name>/README.txt      who it is, where it came from, consent / licence
```

**Get consent first.** Clone a real person's voice only with their explicit agreement, and record it in `README.txt`. Never use a clone to make someone appear to say things they would not stand behind.

From a recording (a voice message works; a quiet room, no music):

```bash
.venv/bin/python -m studio.make_voice ~/Downloads/voice.m4a voices/alice
#   lists speech segments with draft transcripts; pick 8-12 s of whole sentences
.venv/bin/python -m studio.make_voice ~/Downloads/voice.m4a voices/alice --start 3.9 --end 14.1
#   writes reference.wav and a DRAFT reference.txt
```

**Then fix `reference.txt` by hand** so it matches the audio word for word. Write English words in Bangla script as they are spoken (ম্যানেজমেন্ট). A wrong transcript is the most common cause of a bad clone: you get mumbles, skipped words or the wrong accent.

Test the voice:

```bash
.venv/bin/python -m studio.speak voices/alice "আসসালামু আলাইকুম। আজ আমরা নতুন ফিচারটি দেখব।" test.wav
```

If it sounds off, try a different 8-12 s span. A calm, evenly paced clip gives calm narration. You can also lower `--speed` (0.85 is slower).

**No real person's voice?** Use a speaker from an open corpus. `tools/pick_stock_speaker.py` profiles every speaker in OpenSLR SLR37 (Bangladeshi Bangla, CC BY-SA 4.0); `voices/speaker-00737` came from it. Keep the licence's credit line by setting `"credit"` in project.json, which prints it on the closing card.

## 3. Start a project

```bash
cp -r projects/_template projects/my-demo
```

| File | What it is |
|------|------------|
| `project.json` | voice, speed, pronunciation fixes, cards, output path |
| `pitch.md` | the script: `### Scene N: ...` blocks, each with a `**Narration:**` paragraph |
| `shots/` | screenshots, `scene-02a.jpg`, `scene-02b.jpg`, ... (any size; 16:9-ish fits best) |
| `assets/` | logo etc. for the cards |
| `cues.json` | per scene: which shot to show, and what to highlight on which words |

## 4. Write the pitch (`pitch.md`)

- **One scene, one screen.** Show the process: what the user does, step by step, and where the result appears. If a result lands on another page, show it as an inset (see `insets` in `studio/cards.py`) rather than cutting away.
- **Numbers in words.** Write চার হাজার টাকা, not ৪,০০০ টাকা. The narrator refuses digits, so the mistake shows up before any audio is generated.
- **Abbreviations.** Write them normally (সিএসভি). Add `"voice_spellings": {"সিএসভি": "সি-এস-ভি"}` so the voice spells them out, while captions keep the normal spelling.
- **Short phrases rushed?** Use `"fixed_seconds": {"আসসালামু আলাইকুম।": 1.8}`.
- **A list read too fast?** Add the scene to `"comma_scenes"`, which pauses after each item.
- **A dense scene?** Add it to `"slow_scenes"` for longer pauses between sentences.
- **A dramatic pause?** Use `"pause_before": {"1": "অনেকটাই স্বয়ংক্রিয়"}`.
- Sentences end with `।` `?` `!`. Each one is spoken separately, which is what keeps captions and highlights in sync.

## 5. Narrate

```bash
.venv/bin/python -m studio.narrate projects/my-demo            # all scenes (~10-20 s per scene on an M-series Mac)
.venv/bin/python -m studio.narrate projects/my-demo --only 4,7 # redo some scenes after editing them
```

This writes `narration/scene-NN.wav` plus `timings.json` (start and end of every phrase). Listen to the clips. Any phrase can come out odd; re-run its scene, because every run is a fresh take.

## 6. Capture the screenshots

Set the app up in the exact state each scene describes (seed clean demo data first), then save one screenshot per screen state into `shots/`. You can capture them in any of these ways:

- **Claude Code + Claude in Chrome:** ask Claude to open each page and save a screenshot to disk. This is how both examples were made, at 1568×764. Keep the browser window the same size for the whole session; a size change mid-way moves every box.
- **macOS:** `screencapture -o -l <windowid>` or Cmd-Shift-4 then Space (window).
- **Headless, for public pages:** `chrome --headless=new --window-size=1920,936 --screenshot=shots/scene-02a.png <url>`.

The video area is 1920×936 above the caption bar. Wider or taller shots are scaled to the width and then cropped or padded.

## 7. Cues and highlight boxes (`cues.json`)

```json
"2": [
  { "at": null, "shot": "scene-02a" },
  { "at": "কোর্স তালিকায়", "box": [40, 120, 1480, 520] },
  { "at": "নতুন কোর্স বাটনে", "box": [1340, 60, 190, 44] },
  { "at": "সেভ করার পর", "shot": "scene-02b", "box": [40, 160, 1480, 60] },
  { "at": "রসিদ", "clear": true },
  { "at": "ওয়ালেটে", "inset": true }
]
```

- `at` is a piece of the narration text. The event fires when that word is spoken. Anchors are searched in order, so a repeated word matches its next occurrence.
- `box` is `[x, y, w, h]` in **that screenshot's own pixels**. Ways to get one:
  - In Preview, drag a selection and read the position and size from Tools ▸ Show Inspector.
  - In the browser, `el.getBoundingClientRect()` × (screenshot width ÷ `innerWidth`).
  - Ask Claude to read the coordinates off the screenshot.
- `shot: "card/map-03"` shows a generated card (process-map frame 3).

Check every anchor without rendering anything:

```bash
.venv/bin/python -m studio.build projects/my-demo --check
```

## 8. Cards

```bash
.venv/bin/python -m studio.cards projects/my-demo
```

This renders the title and closing cards, any `extra` cards, the `process_map` frames (one step lights up per frame) and the `insets` into `cards/`, using headless Chrome so Bangla conjuncts shape correctly. Colours and font are set in `cards` in project.json (see the docstring of `studio/cards.py`).

## 9. Build and iterate

```bash
.venv/bin/python -m studio.build projects/my-demo --only 2,3   # quick preview -> work/preview.mp4
.venv/bin/python -m studio.build projects/my-demo              # full video -> project.json "output"
```

The output is 1080p H.264 with loudness-normalised audio, burned-in Bangla captions, highlight boxes 0.1 s ahead of the word, and shot changes 0.3 s ahead.

When you change something, redo only the step that depends on it:

| You changed | Re-run |
|-------------|--------|
| narration text | `narrate --only N`, then `build --check`, then `build` |
| a screenshot or box | `build --only N` to preview, then `build` |
| card text or colours | `cards`, then `build` |
| the voice or speed | `narrate` (all scenes), then `build` |

Pull a frame to check a highlight: `ffmpeg -ss 12 -i work/preview.mp4 -frames:v 1 frame.jpg`.

## Layout

```
studio/         the pipeline (config, tts, narrate, cards, build, speak, make_voice)
tools/          pick_stock_speaker.py
voices/         one folder per voice (audio is git-ignored)
projects/       one folder per video; _template/ to copy
models/ .venv/  created by setup.sh (git-ignored)
docs/          this guide and MODELS.md (models, links, licences)
claude-skill/   the Claude Code skill
```

A Claude Code skill for this workflow is in `claude-skill/`. Install it with `cp -r claude-skill/narrated-demo-video ~/.claude/skills/`. Ask Claude for "a narrated demo video" and it follows these steps.
