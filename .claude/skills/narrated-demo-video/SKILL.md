---
name: narrated-demo-video
description: Make a narrated product-demo video in Bangla or English with a locally cloned voice, synced highlight boxes and burned-in captions, using the voiceover-studio repo. Use when the user asks for a demo/walkthrough/pitch video with voiceover, to clone a voice for narration, or to re-voice or edit an existing demo video.
---

# Narrated demo video

## Find the repo first

The tooling is the voiceover-studio repo (https://github.com/arafat1023/voiceover-studio). Its root has `setup.sh`, `studio/` and `projects/`. To locate it:
1. Use the current folder, or a parent of it, if it has those three.
2. Otherwise search: `find ~ -maxdepth 4 -type d -name voiceover-studio -not -path '*/.*' 2>/dev/null`.
3. If it isn't found, ask the user where it is, or offer to clone it (cloning is a download, so ask first).

Read its README.md and docs/GUIDE.md before starting; the guide is the full manual. Run every command from the repo root as `.venv/bin/python -m studio.<module> projects/<name>`.

If `.venv` is missing, run `./setup.sh` (Python 3.12):
- `LANGUAGES=bn` or `LANGUAGES=en` installs one language only; re-running with a language adds it.
- It downloads several GB, so tell the user before starting it.
- If narration stops with "The … engine is not installed", run the command it prints.

## What you can and can't do

- You can't hear audio. Check takes with `"retakes"` (Whisper), but the user judges voice, accent and pacing by ear.
- Screenshots of a web app need the Claude in Chrome extension. Without it, ask the user to provide the screenshots, and say which screens and states you need.
- Clone a real person's voice only with their explicit consent. Never use real customer data in a demo.

## Choose the mode first

The user decides how involved they want to be.

| Mode | Use when | Checkpoints |
|------|----------|-------------|
| **Guided** (default) | the user wants control, or nothing suggests otherwise after asking | three: agree the story (step 1), review the script (step 3), review a preview (step 8) |
| **One-shot** | the user says "just make it", "in one go", "don't ask me", "surprise me", or similar | none: decide everything, never wait |
| **Custom** | the user names their checkpoints, e.g. "just show me the script" | only those |

If the request doesn't make the mode clear, ask once, in one question: guided (you review the story, script and preview) or one-shot (I decide everything and report at the end). Don't ask again later.

**One-shot rules:**
- Pick sensible defaults and keep going. Language: from the request, else the language the user wrote in. Voice: `builtin` for English, `voices/speaker-00737` for Bangla, unless the user named one. Length: about 60 s. `"retakes": 2`. Title and closing cards from the product name.
- Write every assumption to `projects/<name>/DECISIONS.md`, one line each with how to change it (e.g. "Voice: builtin. To change: set `voice` in project.json, re-run narrate and build"). Point the user to it in the final report.
- Still stop and ask, in every mode, for things you must not decide alone:
  - cloning a real person's voice (consent)
  - large downloads (`setup.sh`, models)
  - logging into a site or entering credentials
  - screenshots you can't capture yourself

  Do everything else you can first, then ask all of these together in one message.

## Workflow

In guided mode, the steps marked ⏸ are where you stop for the user. In one-shot mode, decide and continue.

1. ⏸ **Agree on the story.** Before writing anything, settle the audience, the features, the length and the **language** (`bn` Bangla, the default, or `en` English). Seed clean demo data in the product so the shots tell one consistent story. Never use real customer data.
2. **Pick a voice.**
   - Use an existing folder in `voices/`, `builtin` (English only: the model's own voice), or build a new one with `studio.make_voice` (step 1 lists the segments, step 2 runs with `--start/--end`; add `--language en` for an English recording).
   - Clone a real person **only with their explicit consent**, and record it in `voices/<name>/README.txt`.
   - Bangla: hand-correct `reference.txt` so it matches the audio word for word, with English words in Bangla script.
   - English: the clip must be longer than 5 s; `reference.txt` isn't used.
   - Test with `studio.speak` (add `--language en` for English).
   - For a corpus voice (SLR37), set `"credit"` in project.json.
3. ⏸ **Start the project** by copying `projects/_template` (Bangla) or `projects/_template-en` (English) to `projects/<name>`. Write `pitch.md`:
   - one scene per screen
   - show the process step by step
   - Bangla: numbers written in words
   - normal spelling for abbreviations and names, with spoken versions in `voice_spellings`
   
   Guided: show the pitch to the user and apply their edits before narrating. One-shot: narrate straight away.
4. **Narrate** with `studio.narrate` (use `--only N` to redo scenes). Pacing fixes go in project.json: `fixed_seconds`, `comma_scenes`, `slow_scenes`, `pause_before`, `speed`. Set `"retakes": 2` so Whisper checks each phrase and regenerates wrong ones; read any "best take still differs" lines.
5. **Capture screenshots** into `shots/scene-NNx.png` (or `.jpg`):
   - With Claude in Chrome, open each screen and save a screenshot to disk. Keep one window size for the whole session, and ask before any download.
   - Without it, ask the user for the screenshots, listing each screen and the state it should show.
6. **Write `cues.json`**: per scene, `{"at": null, "shot": ...}` first, then events anchored on words copied exactly from the narration.
   - `box` is `[x, y, w, h]` in the screenshot's own pixels. Get the size with `sips -g pixelWidth -g pixelHeight` (macOS) or Python's PIL.
   - Measure boxes by looking at the screenshot. In a browser, `getBoundingClientRect()` × (screenshot width ÷ `innerWidth`) is exact.
   - Run `studio.build --check` until every anchor resolves.
7. **Make cards** with `studio.cards` (title, closing, process map frames, insets).
8. ⏸ **Preview scenes** with `studio.build --only 2,3`. Pull frames with ffmpeg and look at them: is each highlight on the right element, are the captions readable, is anything clipped? Fix what you find. Guided: show the user the preview path and wait. Then run the full `studio.build`.
9. **Report** the output path and length, what you checked, and what to listen for. In one-shot mode, also list the main decisions and point to `DECISIONS.md`. Iterate per the guide's "re-run" table. You can't hear the audio: say so, and let the user judge accent and naturalness.

## Gotchas

- Bangla: digits in the narration stop `narrate` early. Write them as words.
- A wrong `reference.txt` is the top cause of a bad Bangla clone.
- English: a dot inside a sentence ("e.g.", "Dr.") splits it into two phrases.
- Each run is a new take; re-run a scene that has a garbled phrase.
- Box coordinates follow the screenshot size. If the window was resized, re-measure.
- Captions need ffmpeg with libass; cards need Google Chrome. Bangla needs the Kalpurush font.
- English output carries Resemble's inaudible Perth watermark. Leave it in.
- Voice audio and client projects are git-ignored. Don't commit or share them without consent.
