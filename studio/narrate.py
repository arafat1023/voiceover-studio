"""Generate the narration: one clip per scene, spoken one phrase at a time, with exact timings.

    .venv/bin/python -m studio.narrate projects/<name> [--only 7,10]

Reads "### Scene N: ... **Narration:**" blocks from the project's pitch.md. Each scene is split into
phrases (at the end of each sentence and at colons), each phrase is spoken separately and joined with
a short gap, so the start and end of every phrase is known. Writes narration/scene-NN.wav,
narration/timings.json (used for synced captions and highlights) and narration/captions.json (the
original text).

project.json keys used (all optional):
    language         "bn" (default, IndicF5) or "en" (Chatterbox)
    voice            voice folder (default voices/speaker-00737); "builtin" = English model's own voice
    speed            below 1 is slower (default 0.9)
    voice_spellings  {"সিএসভি": "সি-এস-ভি"}: the voice gets the right side, captions keep the left
    fixed_seconds    {"আসসালামু আলাইকুম।": 1.8}: force the length of short phrases
    pause_before     {"1": "অনেকটাই স্বয়ংক্রিয়"}: split that scene's phrase there with a longer pause
    pause_seconds    length of that pause (default 0.5)
    sentence_gap / colon_gap            gaps after a sentence / a colon (0.32 / 0.18)
    comma_scenes + comma_gap            scenes whose lists are spoken item by item (pause after each)
    slow_scenes + slow_gap              scenes with a longer pause between sentences
    require_word_numbers                refuse digits in narration (default: true for bn, false for en)
    retakes          extra takes per phrase when Whisper hears different words (default 0 = off)
"""
import argparse
import json
import re
import unicodedata
from typing import TYPE_CHECKING

import numpy as np
import soundfile as sf

from studio.config import Project

if TYPE_CHECKING:
    from studio.tts import Voice

# Sentence ends, and the words that join the last two items of a list, per language.
SENTENCE_END = {'bn': '।?!:', 'en': '.?!:'}
LIST_JOINERS = {'bn': '(?:এবং|আর)', 'en': '(?:and|or)'}
# Speech recognisers used to check takes (only when "retakes" is set).
ASR_MODELS = {'bn': 'bengaliAI/tugstugi_bengaliai-asr_whisper-medium', 'en': 'openai/whisper-small'}
GOOD_ENOUGH = 0.1


def read_scenes(pitch) -> dict[int, str]:
    text = pitch.read_text(encoding='utf-8')
    scenes = {}
    for match in re.finditer(r'### Scene (\d+):.*?\*\*Narration:\*\*\n(.+?)(?=\n\n|\n###|\Z)', text, re.S):
        scenes[int(match.group(1))] = match.group(2).strip()
    return scenes


def split_phrases(project: Project, number: int, text: str) -> list[tuple[str, float]]:
    """Phrases with the silence that follows each one."""
    language = project.language
    sentence_gap = project.get('sentence_gap', 0.32)
    colon_gap = project.get('colon_gap', 0.18)
    comma_gap = project.get('comma_gap', 0.8) if number in project.get('comma_scenes', []) else None
    slow_gap = project.get('slow_gap', 1.0) if number in project.get('slow_scenes', []) else None
    parts = []
    for match in re.finditer(rf'.+?(?:[{SENTENCE_END[language]}]|$)(?=\s|$)', text):
        phrase = match.group(0).strip()
        if not phrase:
            continue
        gap = colon_gap if phrase.endswith(':') else (slow_gap or sentence_gap)
        if comma_gap is None:
            parts.append((phrase, gap))
            continue
        items = [item.strip() for item in re.split(rf'(?<=,)\s+|\s+(?={LIST_JOINERS[language]}\s)', phrase) if item.strip()]
        parts += [(item, comma_gap) for item in items[:-1]] + [(items[-1], gap)]
    marker = project.get('pause_before', {}).get(str(number))
    if marker:
        for index, (phrase, gap) in enumerate(parts):
            if marker in phrase:
                first, second = phrase.split(marker, 1)
                parts[index:index + 1] = [(first.rstrip(' ,'), project.get('pause_seconds', 0.5)), (marker + second, gap)]
                break
    return parts


def for_voice(project: Project, text: str) -> str:
    for plain, spoken in project.get('voice_spellings', {}).items():
        text = text.replace(plain, spoken)
    if project.get('require_word_numbers', project.language == 'bn') and re.search(r'[0-9০-৯]', text):
        raise ValueError(f'digits in narration (write numbers in words): {text[:60]}')
    return text


def _words(text: str) -> list[str]:
    # NFC first: Bangla letters like য় can be one code point or two (য + nukta), and the script and
    # the recogniser often store the same word in different forms.
    text = unicodedata.normalize('NFC', text).lower()
    return re.sub(r'[^\wঀ-৿]+', ' ', text).split()


def _same(expected: str, heard: str) -> bool:
    # A number in digits matches any one word: recognisers write "10" for "ten", which is not a
    # mistake in the take.
    return expected == heard or bool(re.fullmatch(r'[0-9০-৯]+', heard) or re.fullmatch(r'[0-9০-৯]+', expected))


def word_error(expected: str, heard: str) -> float:
    ref, hyp = _words(expected), _words(heard)
    if ''.join(ref) == ''.join(hyp):  # only the spacing differs, e.g. "ভয়েসওভার" heard as "ভয়েস ওভার"
        return 0.0
    row = list(range(len(hyp) + 1))
    for i in range(1, len(ref) + 1):
        diagonal, row[0] = row[0], i
        for j in range(1, len(hyp) + 1):
            cost = 0 if _same(ref[i - 1], hyp[j - 1]) else 1
            diagonal, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, diagonal + cost)
    return row[len(hyp)] / max(len(ref), 1)


class TakeChecker:
    """Transcribes a take and scores it against the text it should say."""

    def __init__(self, language: str):
        import librosa
        from transformers import pipeline
        self.librosa = librosa
        self.asr = pipeline('automatic-speech-recognition', model=ASR_MODELS[language], device='cpu')

    def score(self, text: str, audio: np.ndarray, rate: int) -> float:
        heard = self.asr({'raw': self.librosa.resample(audio, orig_sr=rate, target_sr=16000),
                          'sampling_rate': 16000})['text']
        return word_error(text, heard)


def best_take(voice: 'Voice', checker: TakeChecker | None, retakes: int, text: str, spoken: str,
              speed: float, seconds: float | None) -> tuple[np.ndarray, int]:
    best = None
    for _ in range(1 + (retakes if checker else 0)):
        audio, rate = voice.speak(spoken, speed=speed, seconds=seconds)
        if checker is None:
            return audio, rate
        error = checker.score(spoken, audio, rate)
        if best is None or error < best[0]:
            best = (error, audio, rate)
        if error <= GOOD_ENOUGH:
            break
    if best[0] > GOOD_ENOUGH:
        print(f'  (best take still differs: {text[:50]})', flush=True)
    return best[1], best[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('project')
    parser.add_argument('--only', default='', help='comma-separated scene numbers')
    parser.add_argument('--voice', help='override the project voice folder')
    parser.add_argument('--speed', type=float, help='override the project speed')
    args = parser.parse_args()

    project = Project.load(args.project)
    scenes = read_scenes(project.pitch)
    wanted = {int(n) for n in args.only.split(',') if n} or set(scenes)
    for number in wanted:
        for phrase, _ in split_phrases(project, number, scenes[number]):
            for_voice(project, phrase)  # fail on digits before loading the model

    out = project.narration
    out.mkdir(parents=True, exist_ok=True)
    (out / 'captions.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding='utf-8')
    from studio.tts import Voice  # imported here so the text logic above works without PyTorch
    voice = Voice(args.voice or project.voice, language=project.language)
    speed = args.speed or project.get('speed', 0.9)
    fixed = project.get('fixed_seconds', {})
    retakes = project.get('retakes', 0)
    checker = TakeChecker(project.language) if retakes else None

    timings_path = out / 'timings.json'
    timings = json.loads(timings_path.read_text(encoding='utf-8')) if timings_path.exists() else {}
    for number in sorted(wanted):
        pieces, phrases, clock, rate = [], [], 0.0, 24000
        for phrase, gap in split_phrases(project, number, scenes[number]):
            audio, rate = best_take(voice, checker, retakes, phrase, for_voice(project, phrase), speed, fixed.get(phrase))
            phrases.append({'text': phrase, 'start': round(clock, 3), 'end': round(clock + len(audio) / rate, 3)})
            pieces += [audio, np.zeros(int(rate * gap), dtype=np.float32)]
            clock += len(audio) / rate + gap
        audio = np.concatenate(pieces[:-1])
        path = out / f'scene-{number:02d}.wav'
        sf.write(str(path), audio, rate)
        timings[str(number)] = phrases
        timings_path.write_text(json.dumps(timings, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'scene {number:2d}: {len(audio) / rate:5.1f}s in {len(phrases)} phrases -> {path.name}', flush=True)


if __name__ == '__main__':
    main()
