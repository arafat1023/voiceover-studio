---
name: narrated-demo-video
description: Make a narrated product-demo video (Bangla by default) with a locally cloned voice, synced highlight boxes and burned-in captions, using the voiceover-studio repo. Use when the user asks for a demo/walkthrough/pitch video with voiceover, to clone a voice for narration, or to re-voice or edit an existing demo video.
---

# Narrated demo video

Tooling lives in the voiceover-studio repo (default location `~/Documents/Workspace/voiceover-studio`; adjust if cloned elsewhere). Its README.md is the full manual, so read it first. Run everything from that folder as `.venv/bin/python -m studio.<module> projects/<name>`. If `.venv` or `models/` is missing, run `./setup.sh`.

## Workflow

1. **Agree on the story.** Before writing anything, settle the audience, the features, the length and the language. Seed clean demo data in the product so the shots tell one consistent story. Never use real customer data.
2. **Pick a voice.**
   - Use an existing folder in `voices/`, or build a new one with `studio.make_voice` (step 1 lists the segments, step 2 runs with `--start/--end`).
   - Clone a real person **only with their explicit consent**, and record it in `voices/<name>/README.txt`.
   - Hand-correct `reference.txt` so it matches the audio word for word, with English words in Bangla script.
   - Test with `studio.speak`.
   - For a corpus voice (SLR37), set `"credit"` in project.json.
3. **Start the project** with `cp -r projects/_template projects/<name>`. Write `pitch.md`:
   - one scene per screen
   - show the process step by step
   - numbers written in words
   - normal spelling for abbreviations, with hyphenated versions in `voice_spellings`
   
   Show the pitch to the user and apply their edits before narrating.
4. **Narrate** with `studio.narrate` (use `--only N` to redo scenes). Pacing fixes go in project.json: `fixed_seconds`, `comma_scenes`, `slow_scenes`, `pause_before`, `speed`.
5. **Capture screenshots** into `shots/scene-NNx.jpg`. With Claude in Chrome, save screenshots to disk. Keep one window size for the whole session. Ask before any download.
6. **Write `cues.json`**: per scene, `{"at": null, "shot": ...}` first, then events anchored on narration words, with `box` as `[x, y, w, h]` in the screenshot's own pixels. Run `studio.build --check` until every anchor resolves.
7. **Make cards** with `studio.cards` (title, closing, process map frames, insets).
8. **Preview scenes** with `studio.build --only 2,3`. Pull frames with ffmpeg and look at them: is each highlight on the right element, are the captions readable, is anything clipped? Then run the full `studio.build`.
9. **Report** the output path and length, and what to listen for. Iterate per the README's "re-run" table.

## Gotchas

- Digits in the narration stop `narrate` early. Write them as words.
- A wrong `reference.txt` is the top cause of a bad clone.
- Each run is a new take; re-run a scene that has a garbled phrase.
- Box coordinates follow the screenshot size. If the window was resized, re-measure.
- Captions need ffmpeg with libass; cards need Google Chrome and the Kalpurush font.
- Voice audio and client projects are git-ignored. Don't commit or share them without consent.
