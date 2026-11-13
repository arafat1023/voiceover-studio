# Motion promo reels

A second kind of video next to the narrated demo: a 9:16 motion-graphics promo for Reels, Shorts and TikTok. The scenes are a web page animated with GSAP, rendered frame by frame in headless Chrome and encoded with ffmpeg. Real app screens sit inside a phone mockup. The voice comes from ElevenLabs or a local clone.

| | Narrated demo (`studio.*`) | Motion promo (`promo/`) |
|---|---|---|
| Visuals | Screenshots with highlight boxes | Animated scenes, phone mockup, cards, chapter headers |
| Voice | Local clone (IndicF5 / Chatterbox) | ElevenLabs website, or a local clone |
| Length | 1–3 min walkthrough | 30–60 s ad |
| Tooling | Python | Node (Playwright + GSAP) + ffmpeg |

## 1. Setup (once)

Needs Node 20+, pnpm, ffmpeg and Google Chrome (Playwright drives the installed Chrome, so no browser download).

```bash
cd promo && pnpm install && cd ..
node promo/init.mjs myapp          # -> projects/myapp-promo/ (git-ignored, like all projects)
```

A project contains `timeline.json` (everything about the video), `site/` (the scene page, fonts, GSAP, images), `vo/` (voice takes), `audio/` (mixes), `rec/` (screen-recording frames), `qa/` (still sheets) and `out/` (videos).

## 2. Story and script

Short ads follow one beat sheet. Name the app early. A long setup buys attention but not relevance.

| Beat | Time | Job |
|---|---|---|
| Hook | 0–5 s | A relatable tension or question the viewer recognises |
| Problem | 5–10 s | The pain, briefly |
| Reveal | ~10 s | The product name and logo |
| Proof | 10–45 s | 2–4 features, each shown in the real app |
| CTA | last 5–8 s | Where to get it, and a tagline |

- One idea per scene and one glowing object per scene. Busy frames read as cheap.
- Match the tone to the brand. A calm product (faith, health, finance) needs a calm voice and slow motion; never hype it.
- Write numbers the way the voice should say them. On ElevenLabs v4 write them normally.
- Agree the script with the user before generating any voice.

## 3. Screens

Real screens beat mock-ups. With an Android phone on adb (USB or Wi-Fi):

```bash
T=promo/tools/android.sh
$T devices                                   # two rows for one phone = USB + Wi-Fi: export ANDROID_SERIAL=<one>
$T launch com.example.app
$T dump                                      # what's on screen, with bounds
$T tap "Settings"                            # tap by visible text or label
$T shot shots/home.png && $T crop shots/home.png projects/myapp-promo/site/img/screen-1.jpg
$T rec rec.mp4 9   # …do the interaction… then: adb pull /sdcard/promo_rec.mp4 rec.mp4
$T frames rec.mp4 projects/myapp-promo/site/rec 0.9 7
```

- **Crop the status bar** (`crop`, default 128 px on a 1080×2400 phone). The mockup draws its own, and the real one shows personal notification icons.
- **Ask first if the phone is in use.** If `dump` shows another app, stop and ask; never tap inside someone's other apps.
- **Don't change real data.** Tapping a counter, saving or posting writes to the user's real account. Do it only if the user allows it, and dismiss "save?" prompts without saving.
- **Blur or replace real names** on public screens such as leaderboards and member lists. Demo cards with demo names are fine; say which numbers are demo data when you deliver.
- **Go one level deeper** than menus. A menu screen shows nothing; the reading page, the counter mid-use or the filled form sells it.
- **Recordings beat stills** for the hero feature: a real tap, with the animation happening.
- Without an Android phone, use the Claude in Chrome extension for web apps, or ask the user for screenshots and list each screen and the state it should show.

## 4. Voice

You can't hear audio. Check takes by transcript and timing; the user judges tone, accent and naturalness by ear. Say so every time you deliver.

### ElevenLabs (best emotion control)

What works on which plan, as found in Nov 2026:

| Route | Free plan | Notes |
|---|---|---|
| **Website** Text to Speech with a library voice | ✅ | How most people use it. The free route for voices like "Shahriar" |
| API or MCP connector with a **library** voice | ❌ | "Free users cannot use library voices via the API" |
| API with an output format above 128 kbps | ❌ | `mp3_44100_192` needs Creator; use `mp3_44100_128` |
| Connector `creative_generate_speech` | ⚠️ | Often refuses with "Free generations are busy right now". Retrying doesn't help; use the website |
| **Instant Voice Clone** (save) | ❌ | Needs Starter or above; the upload works but saving shows an upgrade screen |
| Voice Design (your own designed voice) | ✅ | Designed voices belong to you, so they also work via the API |

**Website workflow** (in the user's Chrome, with their go-ahead):
1. Text to Speech: pick the voice and the **Eleven v4** model.
2. Generate **one line at a time**, with 2 takes each. Per-line takes make re-timing and redoing a single line easy.
3. Download both takes, then file them with `promo/tools/file_takes.sh projects/myapp-promo L03 <VoiceName>`. It refuses to mix takes from different generations.
4. Keep the tab open; the user may want to listen in the History tab.

**v4 audio tags** are free-form words in square brackets placed before the words they colour: `[softly]`, `[warmly]`, `[sighs]`, `[short pause]`, `[pause]`, `[long pause]`. A tag holds until the next one. Describe how the words are spoken, not actions. Older models (Multilingual v2, Flash, Turbo) read tags aloud, so don't use tags there.

Filenames encode the settings: `…_gen_s50_sim75_v4.mp3` means a designed (`gen`) voice, stability 50, similarity 75, model v4. `pvc` means a professional voice clone.

### Local clones

- **voiceover-studio (IndicF5 / Chatterbox):** `studio.make_voice` and `studio.speak`, see [GUIDE.md](GUIDE.md). The clone copies the **mood of its reference clip**: a casual WhatsApp note clones casual. For promo energy, record a 15–25 s *performance* (standing, smiling, quiet room) and keep one reference per mood (calm, warm, upbeat).
- **VoiceStudio / OmniVoice** (debpalash/VoiceStudio): good Bangla cloning, but the OmniVoice weights are **CC-BY-NC**, so they're for testing only, not published promos. It has no emotion control in Bangla; only `[pause]`, `[sigh]` and `[laughter]`.
- **Licences:** check them before publishing. A model card's MIT label doesn't cover its training data (IndicF5 descends from F5-TTS, trained on CC-BY-NC Emilia data).
- **Consent:** clone a real person only with their consent, and record it in the voice's README.txt.

### Checking takes

- Transcribe each take and compare it with the script. The Bangla Whisper used by `studio.narrate` / `studio.make_voice` works: step 1 of `make_voice` prints the segments with text. Pick the take with the closest match, and flag words that came back odd for the user to check by ear.
- Short or melodic clips (recitation, single words) confuse small speech models. Prove cuts by timing instead: transcribe the part before the cut, and cut inside a measured silence (`ffmpeg -af silencedetect`).

### Placing the voice

Put each chosen take on its scene in `timeline.json`, `"voice": "vo/L05-a.mp3", "gapBefore": 0.8`, then run:

```bash
python3 promo/tools/assemble_vo.py projects/myapp-promo
```

It trims and masters each line, writes the real `start`, `dur` and `total` into the timeline, and builds `audio/voice_only.wav` and `audio/mix.wav` at −14 LUFS, the Reels standard. Put a sound-effects bed at `audio/sfx.wav` and it is ducked under the voice. Longer `gapBefore` values (1.0–1.2 s) around a reveal or a quote give the moment room.

**Sacred and quoted text:** copy Arabic, Quran and hadith text verbatim from its source (for example the app's own data), never from memory. Never have an AI or cloned voice recite the Quran; use a real qari's recording, after checking its licence.

## 5. Scenes (`timeline.json`)

```json
{ "total": 30, "digits": "bangla",
  "brand": { "name": "My App", "logo": "img/logo.png", "colors": { "bg1": "#16365A", "bg2": "#081424", "accent": "#C9A227", "accent2": "#E7C766", "card": "#FFFDF6", "cardInk": "#0D2137" } },
  "captionHighlights": ["My App"],
  "scenes": [ { "type": "hook", "start": 0.6, "dur": 4, "text": "voice line…", … } ] }
```

Every scene has `type`, `start`, `dur` and `text` (the voice line, used for captions). `"caption": false` hides captions where the screen already shows the words (reveal, quote, end). Times inside a scene (`at`) are seconds from the scene's `start`.

| Type | Fields |
|---|---|
| `hook` | `cards: [{icon, label, value, plus}]` count up; `big` = the punch word, at `bigAt` |
| `text` | `title`, `sub` |
| `quote` | `main` (word-by-word reveal), `rtl`, `font`, `meaning`, `ref`, `wordsAt`, `wordGap`, `meaningAt` |
| `reveal` | logo burst; `tagline`, `sub` |
| `feature` | `title`, `sub` (chapter header "০১ / ০৪", auto-numbered); `screen` or `screens: [{src, at}]` crossfade, or `frames: {dir, count, fps, startAt}` for a recording; `highlights: [{box:[x,y,w,h], at, hold}]` and `taps: [{xy:[x,y], at}]` in the screenshot's own pixels (`shotWidth`, default 1080); `chips: [{text, xy, at}]`; `toast: {text, at}`; `phone` = CSS overrides; `chapter: false` |
| `end` | `tagline`, `sub`, `features: [{icon, label}]`, `stores: ["play","appstore"]`, `storeLabel`, `site` |

For a one-off scene, add a builder to `build` in `site/index.html`. Everything must be driven by the paused timeline or `frame(t)`, never by real time, so any frame renders identically in any order.

**Look:** dark, minimal and premium. That means a deep background with a soft glow and slow dust, one glass object or phone per scene, a bold Anek Bangla headline with a chapter counter at top-left, the logo pill at top-right, and captions in a dark pill at the bottom. Keep captions on: most viewers watch muted.

## 6. Check, then render

```bash
node promo/stills.mjs projects/myapp-promo 2 6 11 15 21 26   # -> qa/sheet.jpg; look at it
node promo/render.mjs projects/myapp-promo --name MyApp       # 4 parts in parallel
```

Look at the still sheet before every full render. Check for captions over the phone, labels hidden behind cards, cut-off edges and text widows.

- **Output:** `out/<Name>_9x16_1440x2560.mp4` (with `audio/mix.wav`), `…_voice_only.mp4` and `…_1080p.mp4`. Send the 1080p copy for review and WhatsApp; the 2K master is 170–360 MB.
- **Speed:** frames are captured at 60 fps and blended to 30 for motion blur. On an M4 Pro a 53 s reel at 2K takes about 6–8 min with 4 parts. `--scale 1` renders 1080p directly and faster.
- After rendering, pull a few frames from the final file (`ffmpeg -ss T -i out.mp4 -frames:v 1 x.jpg`) and look at them. You can't watch the motion or hear the mix, so ask the user for timecodes.

## 7. Gotchas

- **Emoji:** some don't exist in Chrome's emoji font (👣 rendered blank). Check them in a still, or use SVG.
- **Phone size:** at full size the phone runs under the caption. The template scales it to `.85`.
- **Labels behind cards:** anything floating over the phone or cards needs a `z-index`.
- **Re-timing a new voice:** run `assemble_vo.py` again. Scene timing follows the voice, so a voice swap is a re-render, not a rebuild.
- **Background renders:** `window.seek` awaits image decoding, so recording frames never flash blank. Keep that if you change it.
- **File delivery:** some chat apps silently cut uploads over about 64 MB. Send the 1080p file, or split at silent moments.
