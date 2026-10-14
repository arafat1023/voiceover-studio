"""Bangla text-to-speech in a cloned voice with IndicF5 (F5-TTS), fully local.

A voice is a folder with `reference.wav` (5-12 s of clean speech) and `reference.txt` (exactly
what that clip says, English words written in Bangla script as spoken). Nothing is trained: every
call imitates the reference. Write numbers out in words; the model was not trained on digits.

    from studio.tts import Voice
    voice = Voice('voices/speaker-00737')
    audio, rate = voice.speak('আসসালামু আলাইকুম।', speed=0.9)
"""
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from f5_tts.infer.utils_infer import infer_process, load_model, load_vocoder, preprocess_ref_audio_text
from f5_tts.model import DiT
from safetensors.torch import load_file

from studio.config import STUDIO_ROOT

MODEL_DIR = STUDIO_ROOT / 'models' / 'indicf5-base'
# IndicF5's architecture (from its model.py).
DIT_CONFIG = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)
SAMPLE_RATE = 24000


def pick_device(requested: str = 'auto') -> str:
    if requested != 'auto':
        return requested
    if torch.backends.mps.is_available():
        return 'mps'
    return 'cuda' if torch.cuda.is_available() else 'cpu'


def load_tts(device: str):
    model = load_model(DiT, DIT_CONFIG, mel_spec_type='vocos',
                       vocab_file=str(MODEL_DIR / 'checkpoints' / 'vocab.txt'), device=device)
    # The weights are saved from a compiled EMA copy; strip that prefix and load strictly so a
    # mismatch fails loudly instead of quietly producing a different voice. The file also bundles
    # the vocoder's weights; only the EMA model's are loaded here.
    weights = load_file(str(MODEL_DIR / 'model.safetensors'), device='cpu')
    prefix = 'ema_model._orig_mod.'
    state = {k[len(prefix):]: v for k, v in weights.items() if k.startswith(prefix)}
    for key in ['mel_spec.mel_stft.mel_scale.fb', 'mel_spec.mel_stft.spectrogram.window']:
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    vocoder = load_vocoder(vocoder_name='vocos', is_local=False, device=device)
    return model.to(device).eval(), vocoder


class Voice:
    """A loaded model plus one reference voice. Load once, speak many lines."""

    def __init__(self, voice_dir: str | Path, device: str = 'auto'):
        voice = Path(voice_dir)
        if not voice.is_absolute():
            voice = STUDIO_ROOT / voice
        self.device = pick_device(device)
        self.model, self.vocoder = load_tts(self.device)
        self.ref_audio, self.ref_text = preprocess_ref_audio_text(
            str(voice / 'reference.wav'), (voice / 'reference.txt').read_text(encoding='utf-8').strip())
        self.ref_seconds = sf.info(self.ref_audio).duration

    def speak(self, text: str, speed: float = 0.9, seconds: float | None = None) -> tuple[np.ndarray, int]:
        """`seconds` forces the clip length; use it for short phrases the model rushes."""
        with torch.inference_mode():
            audio, rate, _ = infer_process(
                self.ref_audio, self.ref_text, text, self.model, self.vocoder, mel_spec_type='vocos',
                speed=speed, device=self.device, fix_duration=self.ref_seconds + seconds if seconds else None)
        audio = np.asarray(audio, dtype=np.float32)
        return audio / (float(np.max(np.abs(audio))) or 1.0) * 0.89, rate or SAMPLE_RATE
