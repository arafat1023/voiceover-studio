---
name: motion-promo-reel
description: Make a 9:16 motion-graphics promo reel (Reels/Shorts/TikTok) for an app or product, with real app screens in a phone mockup, animated scenes, synced captions and an ElevenLabs or locally cloned voice, using the voiceover-studio repo's promo/ pipeline (HTML/GSAP rendered frame by frame with Playwright + ffmpeg). Use when the user asks for a promo, ad, launch or feature reel, a "Vox-style" or "premium" motion video, or to re-voice or re-time an existing promo. For a narrated screen walkthrough, use narrated-demo-video instead.
---

# Motion promo reel

## Find the repo and set up

The tooling is the voiceover-studio repo (https://github.com/arafat1023/voiceover-studio); its root has `promo/`, `studio/` and `projects/`. Find it as the narrated-demo-video skill does: the current folder or a parent, else `find ~ -maxdepth 4 -type d -name voiceover-studio -not -path '*/.*'`, else ask.

Read **docs/PROMO.md** before starting; it is the full manual (scene fields, voice routes, gotchas). Then:
- If `promo/node_modules` is missing, run `cd promo && pnpm install`. It needs Node 20+, pnpm, ffmpeg and Google Chrome.
- Create the project: `node promo/init.mjs <name>` makes `projects/<name>-promo/`, which is git-ignored.

## What you can and can't do

- You can't hear audio or watch motion. Check voice takes by transcript, and visuals with still sheets and frames pulled from the final file. Tell the user what to listen and watch for, and ask for timecodes.
- Screens come from the user's phone (`promo/tools/android.sh`), the Claude in Chrome extension, or the user. Ask before touching a phone that may be in use. Never save, post or change real data unless the user allows it. Blur or replace real people's names.
- Downloads (voice takes, reference videos, recitations) and anything typed into a third-party site need the user's go-ahead. Never enter passwords or payment details, and never subscribe to a plan for the user.
- Clone a real person's voice only with their consent. Check a voice model's licence before its output is published (OmniVoice is non-commercial).
- Sacred text (Quran, hadith, dua): copy it verbatim from a source, never from memory. Never let an AI or cloned voice recite the Quran; use a real qari recording.

## Workflow

Steps marked ⏸ are checkpoints. Stop there unless the user asked for one-shot.

1. ⏸ **Story.** Agree the audience, language, length (30–60 s), tone and 2–4 features. Write the script on the hook → problem → reveal → proof → CTA beats in docs/PROMO.md §2, with mood notes per line. Show it and apply the user's edits before any voice is made.
2. **Screens.** Capture the real app screens and one screen recording of the hero interaction. Crop the status bar and put them in `site/img/` and `site/rec/` (§3).
3. ⏸ **Voice.** Default to the ElevenLabs **website**, one line at a time, 2 takes each, Eleven v4 with audio tags. The API and connector can't use library voices on a free plan. File the takes with `promo/tools/file_takes.sh`. Check each take by transcript, pick the best, and let the user listen. A local clone (`studio.make_voice`) works when the user prefers it (§4).
4. **Timeline.** Fill `timeline.json`: the brand, then one scene per beat with `voice` and `gapBefore`. Run `python3 promo/tools/assemble_vo.py <project>` to get the real start times and `audio/mix.wav` (§4, §5).
5. **Stills.** Run `node promo/stills.mjs <project> <times…>` and look at `qa/sheet.jpg`. Fix overlaps, hidden labels, cut-off edges and widowed words, and repeat until clean (§6).
6. ⏸ **Render.** Run `node promo/render.mjs <project> --name <Name>`, about 6–8 min for 50 s at 2K on an M4 Pro. Pull frames from the final MP4 and check them. Deliver the 1080p file for review and the 2K master on request, with file paths and length.
7. **Report.** Say what you checked and what you couldn't (sound, motion), and which numbers or names are demo data. Explain how to iterate: a new voice means `assemble_vo.py` plus a re-render, not a rebuild.

## Gotchas

- Look at a still sheet before every full render; most layout bugs only show there.
- Some emoji render blank in headless Chrome; check them in a still.
- Scene timing comes from the voice. Never hand-time scenes to a voice you will replace.
- Keep `promo/` generic. Client screens, logos, voices and renders live in `projects/` (git-ignored) and are never committed.
