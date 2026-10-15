"""Make a reusable voice from a recording of the speaker (with their consent).

    .venv/bin/python -m studio.make_voice <recording.m4a|wav> voices/<name>            # step 1: list segments
    .venv/bin/python -m studio.make_voice <recording> voices/<name> --start 3.9 --end 14.1   # step 2: cut
    add --language en for an English recording (drafts the transcript with English Whisper)

Step 1 finds the pauses and prints each speech segment with a draft transcript (Whisper, offline,
if the model is in the Hugging Face cache), so you can pick 8-12 seconds of clean speech
that ends on a sentence boundary. Step 2 cuts that span to voices/<name>/reference.wav (24 kHz mono)
and writes a draft reference.txt. EDIT reference.txt so it matches the audio word for word, with
English words written in Bangla script as spoken (e.g. "ম্যানেজমেন্ট"). A wrong transcript is the
most common cause of a poor Bangla clone. (The English engine does not read reference.txt; it only
needs reference.wav to be longer than 5 s.) Any voice can speak either language. Then test with
studio.speak.
"""
import argparse
import os
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

ASR_MODELS = {'bn': 'bengaliAI/tugstugi_bengaliai-asr_whisper-medium', 'en': 'openai/whisper-small'}


def to_wav16(src: Path, dst: Path) -> None:
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(src), '-ac', '1', '-ar', '16000', str(dst)], check=True)


def segments(wav: Path, noise: str = '-30dB', min_pause: float = 0.18) -> list[tuple[float, float]]:
    out = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(wav), '-af', f'silencedetect=noise={noise}:d={min_pause}',
                          '-f', 'null', '-'], capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', out)]
    ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', out)]
    total = sf.info(str(wav)).duration
    edges, spans, cursor = sorted(zip(starts, ends)), [], 0.0
    for s, e in edges:
        if s - cursor > 0.4:
            spans.append((round(cursor, 2), round(s, 2)))
        cursor = e
    if total - cursor > 0.4:
        spans.append((round(cursor, 2), round(total, 2)))
    return spans


def transcriber(language: str):
    try:
        os.environ.setdefault('HF_HUB_OFFLINE', '1')
        from transformers import pipeline
        return pipeline('automatic-speech-recognition', model=ASR_MODELS[language], device='cpu')
    except Exception as error:  # noqa: BLE001 - optional helper
        print(f'(no draft transcripts: {str(error)[:80]})')
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('recording')
    parser.add_argument('voice_dir')
    parser.add_argument('--start', type=float)
    parser.add_argument('--end', type=float)
    parser.add_argument('--language', default='bn', choices=sorted(ASR_MODELS), help='language of the recording')
    args = parser.parse_args()
    src, voice = Path(args.recording), Path(args.voice_dir)
    voice.mkdir(parents=True, exist_ok=True)
    wav16 = voice / 'original-16k.wav'
    to_wav16(src, wav16)
    audio, rate = sf.read(str(wav16), dtype='float32')
    asr = transcriber(args.language)

    def draft(a: float, b: float) -> str:
        if not asr:
            return ''
        return asr({'raw': audio[int(max(a - 0.05, 0) * rate):int((b + 0.05) * rate)], 'sampling_rate': rate})['text']

    if args.start is None:
        for a, b in segments(wav16):
            print(f'{a:6.2f}-{b:6.2f} ({b - a:4.1f}s) {draft(a, b)}', flush=True)
        print('\nPick a span of 8-12 s of whole sentences, then run again with --start and --end.')
        return
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(args.start), '-to', str(args.end), '-i', str(src),
                    '-ac', '1', '-ar', '24000', '-af', f'afade=t=in:d=0.05,afade=t=out:st={args.end - args.start - 0.1:.2f}:d=0.1',
                    str(voice / 'reference.wav')], check=True)
    text = ' '.join(draft(a, b) for a, b in segments(wav16) if a >= args.start - 0.2 and b <= args.end + 0.2)
    (voice / 'reference.txt').write_text(text.strip() + '\n', encoding='utf-8')
    print(f'wrote {voice}/reference.wav ({args.end - args.start:.1f}s) and a DRAFT reference.txt:\n  {text}')
    print('Edit reference.txt to match the audio exactly, then test: python -m studio.speak', voice, '"..." test.wav')


if __name__ == '__main__':
    main()
