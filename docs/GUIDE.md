# The full guide: from a recording to a finished video

Run every command from the repo root. `projects/my-demo` stands for your project folder.

```
pitch.md ──narrate──▶ narration/*.wav + timings.json ─┐
project.json ──cards──▶ cards/*.png ──────────────────┼──build──▶ video.mp4
shots/*.jpg + cues.json ──────────────────────────────┘
```

The whole cycle, in order:

1. [Setup](#1-setup-once)
2. [Make a voice](#2-make-a-voice-once-per-voice)
3. [Start a project](#3-start-a-project)
4. [Write the pitch](#4-write-the-pitch-pitchmd)
5. [Narrate](#5-narrate)
6. [Capture screenshots](#6-capture-the-screenshots)
7. [Cues and highlight boxes](#7-cues-and-highlight-boxes-cuesjson)
8. [Cards, process maps and insets](#8-cards-process-maps-and-insets)
9. [Build and iterate](#9-build-and-iterate)

At the end are a [project.json reference](#projectjson-reference), [troubleshooting](#troubleshooting) and the [repo layout](#layout).

`projects/_template` (Bangla) and `projects/_template-en` (English) are complete three-scene examples: add two screenshots and a logo and they build.

**Language.** Set `"language": "bn"` (the default) or `"en"` in project.json:
- **Bangla** uses IndicF5, which needs a reference clip **and** its exact transcript.
- **English** uses Chatterbox Turbo, which needs only a clip longer than 5 s, or the voice name `builtin` for the model's own voice.

Any voice can speak either language. Where the rules differ, this guide says so.

## 1. Setup (once)

Follow **Install** in the [README](../README.md#install). It lists the system tools for macOS and Linux, everything `setup.sh` downloads, and the optional manual downloads. Model sources and licences are in [MODELS.md](MODELS.md).

The device is picked automatically: `mps` on Apple Silicon, `cuda` with an NVIDIA GPU, otherwise `cpu`. Check that everything works:

```bash
.venv/bin/python -m studio.speak voices/speaker-00737 "আসসালামু আলাইকুম।" test-bn.wav
.venv/bin/python -m studio.speak builtin "Welcome to the demo." test-en.wav --language en
```

## 2. Make a voice (once per voice)

A voice is just a folder under `voices/`. Nothing is trained; every line imitates the reference clip.

```
voices/<name>/reference.wav   8-12 s of clean speech, 24 kHz mono
voices/<name>/reference.txt   exactly what that clip says (Bangla only; English ignores it)
voices/<name>/README.txt      who it is, where it came from, consent / licence
```

**Get consent first.** Clone a real person's voice only with their explicit agreement, and record it in `README.txt`: who, when they agreed, and for what use. Never use a clone to make someone appear to say things they would not stand behind.

### From a recording

A voice message is fine. Record in a quiet room with no music, one speaker, at a natural pace. Any format ffmpeg reads works (m4a, mp3, wav, ogg, …).

```bash
.venv/bin/python -m studio.make_voice ~/Downloads/voice.m4a voices/alice
#   step 1: lists speech segments (start-end, length) with draft transcripts
.venv/bin/python -m studio.make_voice ~/Downloads/voice.m4a voices/alice --start 3.9 --end 14.1
#   step 2: cuts that span to reference.wav and writes a DRAFT reference.txt
```

To choose the span:
- Pick 8-12 s made of whole sentences.
- Start and end in a pause.
- Choose the calmest, most evenly paced part. The clone copies the clip's pace and mood.

The draft transcripts come from Bengali Whisper, or from English Whisper if you add `--language en` to both commands. `setup.sh` downloads both unless you set `WITH_ASR=0`. Without them, step 1 still lists the segments; you just type the text yourself.

**For Bangla, fix `reference.txt` by hand** so it matches the audio word for word. English skips this step, because Chatterbox doesn't use the transcript.
- Write English words in Bangla script as they are spoken (ম্যানেজমেন্ট).
- Write numbers in words.

A wrong transcript is the most common cause of a bad Bangla clone: you get mumbles, skipped words or the wrong accent.

Test it:

```bash
.venv/bin/python -m studio.speak voices/alice "আসসালামু আলাইকুম। আজ আমরা নতুন ফিচারটি দেখব।" test.wav
.venv/bin/python -m studio.speak voices/alice "আসসালামু আলাইকুম।" test.wav --speed 0.85 --seconds 1.8
```

For English, add `--language en`:

```bash
.venv/bin/python -m studio.speak voices/alice "Welcome to the demo." test.wav --language en
```

If it sounds off, try a different span. `--speed` below 1 is slower. `--seconds` forces the clip length, which helps short phrases the model rushes.

### No real person's voice?

For English, use `"voice": "builtin"`, the Chatterbox model's own voice (MIT). For Bangla, use `voices/speaker-00737`, which ships with the repo. Or pick another speaker from the open SLR37 corpus (Bangladeshi Bangla, CC BY-SA 4.0):

```bash
curl -LO https://www.openslr.org/resources/37/bn_bd.zip          # 560 MB
unzip -q bn_bd.zip -d data/slr37-bn-bd
.venv/bin/python tools/pick_stock_speaker.py data/slr37-bn-bd    # pitch / calmness / pace per speaker
grep ban_00737 data/slr37-bn-bd/line_index.tsv | head            # a speaker's clips and their text
mkdir -p voices/speaker-00737b
ffmpeg -i data/slr37-bn-bd/wavs/<clip1>.wav -i data/slr37-bn-bd/wavs/<clip2>.wav \
  -filter_complex "[0][1]concat=n=2:v=0:a=1" -ac 1 -ar 24000 voices/speaker-00737b/reference.wav
# reference.txt = the two clips' lines from line_index.tsv, joined with a space
```

How to read the profile:
- A pitch above about 165 Hz is usually a female voice.
- A lower spread means a calmer, steadier delivery.

Aim for 8-12 s in total. A corpus voice needs its credit line: set `"credit"` in project.json and it is printed on the closing card.

## 3. Start a project

```bash
cp -r projects/_template    projects/my-demo     # Bangla
cp -r projects/_template-en projects/my-demo     # English
```

| File | What it is |
|------|------------|
| `project.json` | voice, speed, pronunciation and pacing fixes, cards, output path ([reference](#projectjson-reference)) |
| `pitch.md` | the script: `### Scene N: ...` blocks, each with a `**Narration:**` paragraph |
| `shots/` | screenshots, named `scene-02a.jpg`, `scene-02b.jpg`, ... (jpg or png, any size; 16:9-ish fits best) |
| `assets/` | logo and inset images for the cards |
| `cues.json` | per scene: which shot to show, and what to highlight on which words |

These are generated, so you can delete them at any time: `narration/`, `cards/` and `work/`.

## 4. Write the pitch (`pitch.md`)

Each scene looks like this:

```markdown
### Scene 2: The list page
**On screen:** the course list; highlight the add button, then the new row.
**Narration:**
কোর্স তালিকায় সব কোর্স একসাথে দেখা যায়। উপরের নতুন কোর্স বাটনে ক্লিক করলে ফর্ম খোলে।
```

Only the paragraph right after `**Narration:**` is spoken. It ends at the first blank line. Everything else in the file is notes for you and any reviewer.

Writing rules:

- **One scene, one screen.** Show the process: what the user does, step by step, and where the result appears. If a result lands on another page, show it as an [inset](#insets) rather than cutting away.
- **Numbers in words (Bangla).** Write চার হাজার টাকা, not ৪,০০০ টাকা. In a Bangla project the narrator refuses digits, so the mistake shows up before any audio is generated. English reads digits, but words are still safer for prices and dates ("four thousand taka").
- **Abbreviations.** Write them normally (সিএসভি). Add `"voice_spellings": {"সিএসভি": "সি-এস-ভি"}` so the voice spells them out, while captions keep the normal spelling. The same trick fixes any word the voice gets wrong: map it to a spelling that sounds right.
- **Sentences** end with `।` `?` `!` in Bangla, or `.` `?` `!` in English; a `:` also splits. Each one is spoken separately, which is what keeps captions and highlights in sync. Keep sentences short. In English, avoid abbreviations with a dot inside a sentence ("e.g.", "Dr."), because the dot splits it.

Pacing controls, all in project.json:

| Problem | Fix |
|---------|-----|
| a short phrase is rushed | `"fixed_seconds": {"আসসালামু আলাইকুম।": 1.8}` |
| a list is read too fast | add the scene number to `"comma_scenes"`: it pauses after each comma, and before এবং / আর (Bangla) or "and" / "or" (English) |
| a dense scene | add it to `"slow_scenes"` for longer pauses between sentences |
| a dramatic pause | `"pause_before": {"1": "অনেকটাই স্বয়ংক্রিয়"}`: in scene 1, pause before those words |
| everything too fast or slow | `"speed"` (0.85 is calmer, 1.0 is the model's natural pace) |

Get the pitch reviewed before narrating. Text changes are cheap now; later they cost re-narration and re-timing.

## 5. Narrate

```bash
.venv/bin/python -m studio.narrate projects/my-demo              # all scenes
.venv/bin/python -m studio.narrate projects/my-demo --only 4,7   # only these scenes
.venv/bin/python -m studio.narrate projects/my-demo --voice voices/alice --speed 0.85   # one-off override
```

This writes:
- `narration/scene-NN.wav`
- `narration/timings.json`: start and end of every phrase, used to sync highlights and captions
- `narration/captions.json`: the caption text

Timing: about 10-20 s per scene on Apple Silicon or a GPU. On a CPU it's several times slower, so use `--only` while iterating.

Listen to every clip. Any phrase can come out odd: a garbled word, a strange stress or a cut-off ending. Every run is a fresh take, so re-run that scene. If one word keeps failing, change its spelling in `voice_spellings`.

**Automatic retakes.** Set `"retakes": 2` in project.json. Whisper then transcribes every phrase as it's generated. If more than 1 word in 10 differs from the script, the phrase is regenerated, up to 2 more times, and the closest take is kept. A phrase that is still off gets a "(best take still differs: …)" line in the output, so you know what to listen to. Digits in the transcript are ignored, so "10" for "ten" doesn't count as an error. This roughly doubles narration time, and it needs the Whisper models (`WITH_ASR=1`, the default). The English template has it on.

## 6. Capture the screenshots

Set the app up in the exact state each scene describes, with clean demo data seeded first. Never use real customer data. Then save one screenshot per screen state into `shots/`, named after the scene (`scene-04.jpg`, or `scene-04a.jpg` and `scene-04b.jpg` when a scene changes screens).

Ways to capture:

- **Claude Code + [Claude in Chrome](https://claude.ai/chrome):** ask Claude to open each page, get it into the right state and save a screenshot to disk. Keep the browser window the same size for the whole session; a size change mid-way moves every box.
- **macOS:** Cmd-Shift-4 then Space, then click the window. Or `screencapture -o -l <windowid> shots/scene-04.png`.
- **Linux:** `gnome-screenshot -w` (GNOME), Spectacle (KDE), or `import -window root shots/scene-04.png` (ImageMagick).
- **Headless, for public pages:** `google-chrome --headless=new --window-size=1920,936 --screenshot=shots/scene-02a.png <url>`. Use `chromium` on Linux, or the full path on macOS: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"`.

The video area is 1920×936 above the caption bar. Shots are scaled to its width, then cropped or padded in height. The best fit is a wide browser window with no dev tools open.

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

Every scene needs an entry. The first event is always `"at": null` with the shot the scene opens on.

| Event | Effect |
|-------|--------|
| `"shot": "scene-02b"` | switch to `shots/scene-02b.jpg` (0.3 s before the word) |
| `"box": [x, y, w, h]` | highlight that area: the rest dims and an orange frame glows. It replaces the previous box. |
| `"clear": true` | remove the highlight |
| `"inset": true` | fade in this scene's inset strip (see [insets](#insets)) |
| `"shot": "card/title"` | show a generated card (`card/closing`, `card/map-03`, `card/<extra name>`) |

- `at` is a piece of the scene's narration text, copied exactly. The event fires when that word is spoken; highlights appear 0.1 s early. Anchors are searched in order, so a repeated word matches its next occurrence after the previous anchor.
- `box` is in **that screenshot's own pixels**: x and y of the top-left corner, then width and height. Ways to measure:
  - **Preview (macOS):** drag a selection; Tools ▸ Show Inspector shows its position and size.
  - **GIMP (Linux):** the rectangle-select tool shows position and size.
  - **In the browser:** `el.getBoundingClientRect()` × (screenshot width ÷ `innerWidth`).
  - **Claude:** ask it to read the coordinates off the screenshot.
- Keys starting with `_` (such as `"_help"`) are ignored, so use them for notes.

Check every anchor without rendering anything:

```bash
.venv/bin/python -m studio.build projects/my-demo --check     # "all N scenes ok", or each phrase not found
```

## 8. Cards, process maps and insets

```bash
.venv/bin/python -m studio.cards projects/my-demo
```

This renders everything under `cards` and `insets` in project.json to `cards/*.png` with headless Chrome, so Bangla conjuncts shape correctly. Re-run it after any card change.

### Title, closing and extra cards

```json
"cards": {
  "logo": "assets/logo.png",
  "font": "Kalpurush",
  "colors": { "bg1": "#1f4a73", "bg2": "#12304f", "bg3": "#0b2038", "accent": "#e2483d", "muted": "#cfe0f1" },
  "title":   { "heading": "সিজদাহ একাডেমি", "subtitle": "অ্যাডমিন প্যানেল" },
  "closing": { "heading": "আপনার প্রতিষ্ঠান, আপনার নিয়ন্ত্রণে", "subtitle": "ধন্যবাদ" },
  "extra":   { "part2": { "heading": "দ্বিতীয় অংশ", "subtitle": "লাইভ পরিবর্তন" } }
}
```

Use them in cues as `card/title`, `card/closing` and `card/part2`. Colours are optional:
- `bg1`, `bg2` and `bg3` make the background gradient.
- `accent` is the rule under the heading and the current step on a process map.

`"credit"` (top level) prints a small line at the top of the closing card.

### Process map

A diagram whose steps light up one by one as the narration names them:

```json
"cards": {
  "process_map": { "title": "পুরো প্রক্রিয়া এক নজরে",
                   "steps": ["শিক্ষার্থীর পেমেন্ট", "আয়", "ওয়ালেট", "খরচ", "মুনাফা", "ফান্ড"] }
}
```

This makes frames `map-00` (nothing lit) to `map-06` (all lit; the newest step is in the accent colour). Steps run in two rows. Up to 10 steps fit. Cue them on the words that name each step:

```json
"2": [
  { "at": null, "shot": "card/map-00" },
  { "at": "শিক্ষার্থী পেমেন্ট করলে", "shot": "card/map-01" },
  { "at": "আয় নিজে থেকেই", "shot": "card/map-02" }
]
```

### Insets

A picture-in-picture strip faded into the bottom of a scene. Use it to show where a result lands (for example, a log on another page) without leaving the current screen:

```json
"insets": { "9": { "image": "shots/scene-09-inset.png", "label": "ওয়ালেট অ্যাক্টিভিটি লগ" } }
```

The image should be a wide, short crop (about 1500×120). Trigger it in scene 9's cues with `{ "at": "...", "inset": true }`.

## 9. Build and iterate

```bash
.venv/bin/python -m studio.build projects/my-demo --only 2,3   # preview -> projects/my-demo/work/preview.mp4
.venv/bin/python -m studio.build projects/my-demo              # full video -> project.json "output"
.venv/bin/python -m studio.build projects/my-demo --out ~/Desktop/v2.mp4
```

The output is 1080p H.264 at 30 fps, with AAC audio loudness-normalised to -16 LUFS. Captions are burned in and split into short lines (`caption_max` characters). The video fades in at the start and out at the end.

Check before you share:
- Pull frames from the preview and look at them: is every box on the right element, and is nothing cut off at the edges?
  ```bash
  ffmpeg -ss 12 -i projects/my-demo/work/preview.mp4 -frames:v 1 frame.jpg
  ```
- Watch the whole video once with sound.

When you change something, redo only the step that depends on it:

| You changed | Re-run |
|-------------|--------|
| narration text of a scene | `narrate --only N`, `build --check`, then `build` |
| a screenshot or a box | `build --only N` to preview, then `build` |
| card text, colours, map steps or an inset | `cards`, then `build` |
| the voice or speed | `narrate` (all scenes), then `build` |
| a cue anchor (`at`) | `build --check`, then `build` |

## project.json reference

All keys are optional except where noted.

| Key | Default | Meaning |
|-----|---------|---------|
| `name` | | label for you |
| `language` | `bn` | `bn` (Bangla, IndicF5) or `en` (English, Chatterbox); also picks the default font, sentence ends and list words |
| `voice` | `voices/speaker-00737` | voice folder (relative to the repo root, or absolute); `builtin` = the English model's own voice |
| `speed` | `0.9` | below 1 is slower |
| `voice_spellings` | `{}` | `{"as written": "as spoken"}`: the voice reads the right side, captions keep the left |
| `fixed_seconds` | `{}` | `{"exact phrase।": 1.8}`: force a phrase's length |
| `pause_before` / `pause_seconds` | `{}` / `0.5` | `{"scene": "words"}`: pause before those words |
| `sentence_gap` / `colon_gap` | `0.32` / `0.18` | silence after a sentence / after a `:` |
| `comma_scenes` / `comma_gap` | `[]` / `0.8` | scenes read item by item, and the pause after each item |
| `slow_scenes` / `slow_gap` | `[]` / `1.0` | scenes with longer pauses between sentences |
| `require_word_numbers` | `true` for bn, `false` for en | refuse digits in the narration |
| `retakes` | `0` | extra takes per phrase when Whisper hears different words ([narrate](#5-narrate)) |
| `cards` | | `logo`, `font`, `colors`, `title`, `closing`, `extra`, `process_map` ([cards](#8-cards-process-maps-and-insets)) |
| `insets` | `{}` | `{"scene": {"image": ..., "label": ...}}` ([insets](#insets)) |
| `credit` | | small line at the top of the closing card |
| `video` | | `fps` 30; `lead` 0.5 / `tail` 0.9 (silence before/after each scene); `last_hold` 1.5; `caption_font` "Kalpurush" (bn) / "Arial" (en); `caption_size` 50; `caption_max` 68 (characters per line); `bar` "0x0b2038" (caption bar colour); `highlight` "255,106,48" (box colour, RGB) |
| `output` | `<project>/video.mp4` | where the full build goes; `~` works |
| `pitch` / `cues` | `pitch.md` / `cues.json` | other file names, e.g. to keep two cuts in one project |

## Troubleshooting

| Message or symptom | Cause and fix |
|--------------------|---------------|
| `digits in narration (write numbers in words)` | a digit in `pitch.md`; write it as words (or map it in `voice_spellings`) |
| `cue phrase not found in narration: …` | the `at` text isn't in that scene's narration exactly, or it comes before the previous anchor; copy it from `pitch.md` |
| `scene N: no cues` | add an entry for scene N to `cues.json` |
| `shot not found: …` | no `shots/<name>.jpg|.png`, or for `card/…` run `studio.cards` first |
| `KeyError` for a scene number in `narrate` | `--only` names a scene that isn't in `pitch.md` (check the `### Scene N:` heading) |
| Missing `timings.json` / scene wav in `build` | run `studio.narrate` (for the scenes you are building) |
| Captions show boxes or the wrong font | Kalpurush isn't installed; re-run `./setup.sh` or set `video.caption_font` / `cards.font` |
| `No such filter: 'ass'` | your ffmpeg lacks libass; install Homebrew's or your distro's ffmpeg |
| `Google Chrome is needed to render the cards` | install Chrome or Chromium (`setup.sh` prints the command) |
| Mumbling, skipped words, wrong accent (Bangla) | `reference.txt` doesn't match `reference.wav`; fix it word for word, or choose a cleaner span |
| `… must be longer than 5 s for the English engine` | the voice's `reference.wav` is too short for Chatterbox; cut a longer span with `make_voice` |
| `No module named 'chatterbox'` | the English engine isn't installed; run `./setup.sh` without `WITH_EN=0` |
| `.venv was made with another Python version` | `rm -rf .venv` and run `./setup.sh` again (the project needs Python 3.12) |
| English garbles a word or skips one | set `"retakes": 2`; respell names in `voice_spellings` (e.g. `"bKash": "bee-cash"`) |
| One word always wrong | respell it in `voice_spellings` (hyphenate, or write it how it sounds) |
| Voice too fast or flat | lower `speed`; use a calmer reference clip; add `slow_scenes` or `comma_scenes` |
| A highlight is offset | the box was measured on a different-size screenshot; re-measure on the shot you're using |
| Slow on Linux | no GPU means CPU inference; use `--only` while iterating, and do the full narration once at the end |

## Layout

```
studio/         the pipeline
  tts.py          the two engines (IndicF5 for bn, Chatterbox for en) + a voice; Voice.speak()
  narrate.py      pitch.md -> narration/ (wavs, timings, captions)
  cards.py        project.json -> cards/ (title, closing, extra, process map, insets)
  build.py        narration + shots + cards + cues -> video
  speak.py        one line, for testing a voice or a word
  make_voice.py   recording -> voices/<name>/
  config.py       project folder + project.json loader
tools/          pick_stock_speaker.py
voices/         one folder per voice (audio git-ignored, except the bundled speaker-00737)
projects/       one folder per video; _template/ (bn) and _template-en/ (en) to copy (others git-ignored)
docs/           this guide and MODELS.md (models, links, licences)
claude-skill/   the Claude Code skill
models/ .venv/  created by setup.sh (git-ignored)
```

## Using Claude Code

Install the skill with `cp -r claude-skill/narrated-demo-video ~/.claude/skills/`. Then ask Claude for "a narrated demo video of …". It works through this guide:

1. drafts the pitch for your review
2. narrates
3. takes the screenshots through Claude in Chrome
4. writes `cues.json`, measuring boxes from the screenshots
5. checks preview frames
6. builds the full video
