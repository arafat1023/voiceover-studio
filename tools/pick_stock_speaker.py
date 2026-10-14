"""Pick a stock voice from an open speech corpus when no real person's voice is to be cloned.

    .venv/bin/python tools/pick_stock_speaker.py data/slr37-bn-bd

Prints a rough profile per speaker of an OpenSLR-style corpus (line_index.tsv + wavs/): median
pitch (female if above ~165 Hz), pitch spread (lower = calmer, steadier) and speaking rate. Listen
to the shortlisted speakers, then build the voice from 2-3 of their clips joined to 8-12 s:
reference.txt is their lines from line_index.tsv. Keep the corpus licence's credit line (SLR37 is
CC BY-SA 4.0: "Voice based on Google SLR37 Bengali speech data, CC BY-SA 4.0").
"""
import csv
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import librosa
import numpy as np

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'data/slr37-bn-bd')
lines = {}
with open(root / 'line_index.tsv', encoding='utf-8') as f:
    for row in csv.reader(f, delimiter='\t'):
        lines[row[0]] = row[-1]

by_speaker = defaultdict(list)
for key in lines:
    by_speaker[key.split('_')[1]].append(key)

random.seed(7)
for speaker, keys in sorted(by_speaker.items()):
    medians, spreads, rates = [], [], []
    for key in random.sample(keys, min(20, len(keys))):
        y, sr = librosa.load(root / 'wavs' / f'{key}.wav', sr=16000)
        f0, voiced, _ = librosa.pyin(y, fmin=70, fmax=400, sr=sr)
        f0 = f0[voiced]
        if len(f0) < 20:
            continue
        medians.append(float(np.median(f0)))
        spreads.append(float(np.std(np.log2(f0)) * 12))
        speech = librosa.effects.trim(y, top_db=30)[0]
        rates.append(len(lines[key].replace(' ', '')) / (len(speech) / sr))
    if medians:
        print(f'{speaker}: clips={len(keys):4d}  F0={statistics.median(medians):6.1f} Hz  '
              f'spread={statistics.median(spreads):4.2f} st  rate={statistics.median(rates):5.1f} chars/s')
