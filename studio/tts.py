"""Text-to-speech in a cloned voice, fully local. One `Voice` class, two engines:

    bn  IndicF5 (F5-TTS trained on Indian languages). Needs reference.wav + reference.txt.
    en  Chatterbox Turbo (Resemble AI). Needs only reference.wav (at least 5 s), or the folder
        name "builtin" for the model's own voice. Its output carries Resemble's inaudible Perth
        watermark, which marks the audio as AI-generated.

A voice is a folder with `reference.wav` (8-12 s of clean speech) and, for Bangla, `reference.txt`
(exactly what that clip says, English words written in Bangla script as spoken). Nothing is
trained: every call imitates the reference, so any voice can speak either language.

    from studio.tts import Voice
    voice = Voice('voices/speaker-00737', language='bn')
    audio, rate = voice.speak('আসসালামু আলাইকুম।', speed=0.9)
"""
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

from studio.config import STUDIO_ROOT

MODEL_DIR = STUDIO_ROOT / 'models' / 'indicf5-base'
# IndicF5's architecture (from its model.py).
DIT_CONFIG = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)
SAMPLE_RATE = 24000
BUILTIN = 'builtin'


def pick_device(requested: str = 'auto') -> str:
    if requested != 'auto':
        return requested
    if torch.backends.mps.is_available():
        return 'mps'
    return 'cuda' if torch.cuda.is_available() else 'cpu'


def resolve_voice(voice_dir: str | Path) -> Path | None:
    """The voice folder, or None for the English engine's built-in voice."""
    if str(voice_dir) == BUILTIN or Path(voice_dir).name == BUILTIN:
        return None
    voice = Path(voice_dir)
    return voice if voice.is_absolute() else STUDIO_ROOT / voice


def stretch(audio: np.ndarray, rate: int, factor: float) -> np.ndarray:
    """Change tempo without changing pitch (ffmpeg atempo); factor < 1 is slower."""
    if abs(factor - 1.0) < 0.01:
        return audio
    filters = []
    while factor < 0.5 or factor > 2.0:  # atempo takes 0.5-2.0 per stage
        step = 0.5 if factor < 0.5 else 2.0
        filters.append(f'atempo={step}')
        factor /= step
    filters.append(f'atempo={factor:.4f}')
    out = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'f32le', '-ar', str(rate), '-ac', '1', '-i', 'pipe:0',
                          '-af', ','.join(filters), '-f', 'f32le', 'pipe:1'],
                         input=audio.astype(np.float32).tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def normalise(audio: np.ndarray) -> np.ndarray:
    audio = np.asarray(audio, dtype=np.float32)
    return audio / (float(np.max(np.abs(audio))) or 1.0) * 0.89


class IndicF5Engine:
    def __init__(self, voice: Path | None, device: str):
        from f5_tts.infer.utils_infer import load_model, load_vocoder, preprocess_ref_audio_text
        from f5_tts.model import DiT
        from safetensors.torch import load_file
        if voice is None:
            raise SystemExit('Bangla needs a voice folder with reference.wav + reference.txt (no built-in voice)')
        self.device = device
        self.model = load_model(DiT, DIT_CONFIG, mel_spec_type='vocos',
                                vocab_file=str(MODEL_DIR / 'checkpoints' / 'vocab.txt'), device=device)
        # The weights are saved from a compiled EMA copy; strip that prefix and load strictly so a
        # mismatch fails loudly instead of quietly producing a different voice. The file also bundles
        # the vocoder's weights; only the EMA model's are loaded here.
        weights = load_file(str(MODEL_DIR / 'model.safetensors'), device='cpu')
        prefix = 'ema_model._orig_mod.'
        state = {k[len(prefix):]: v for k, v in weights.items() if k.startswith(prefix)}
        for key in ['mel_spec.mel_stft.mel_scale.fb', 'mel_spec.mel_stft.spectrogram.window']:
            state.pop(key, None)
        self.model.load_state_dict(state, strict=True)
        self.model = self.model.to(device).eval()
        self.vocoder = load_vocoder(vocoder_name='vocos', is_local=False, device=device)
        self.ref_audio, self.ref_text = preprocess_ref_audio_text(
            str(voice / 'reference.wav'), (voice / 'reference.txt').read_text(encoding='utf-8').strip())
        self.ref_seconds = sf.info(self.ref_audio).duration

    def speak(self, text: str, speed: float, seconds: float | None) -> tuple[np.ndarray, int]:
        from f5_tts.infer.utils_infer import infer_process
        with torch.inference_mode():
            audio, rate, _ = infer_process(
                self.ref_audio, self.ref_text, text, self.model, self.vocoder, mel_spec_type='vocos',
                speed=speed, device=self.device, fix_duration=self.ref_seconds + seconds if seconds else None)
        return normalise(audio), rate or SAMPLE_RATE


class ChatterboxEngine:
    """Chatterbox Turbo has no speed or length control, so both are applied afterwards with a
    pitch-preserving time stretch."""

    def __init__(self, voice: Path | None, device: str):
        import librosa
        from chatterbox.tts_turbo import ChatterboxTurboTTS
        self.librosa = librosa
        self.model = ChatterboxTurboTTS.from_pretrained(device=device)
        if voice is not None:
            reference = voice / 'reference.wav'
            if sf.info(str(reference)).duration <= 5.0:
                raise SystemExit(f'{reference} must be longer than 5 s for the English engine')
            self.model.prepare_conditionals(str(reference))

    def speak(self, text: str, speed: float, seconds: float | None) -> tuple[np.ndarray, int]:
        with torch.inference_mode():
            audio = self.model.generate(text).squeeze(0).cpu().numpy()
        rate = self.model.sr
        audio, _ = self.librosa.effects.trim(audio, top_db=40)
        if seconds:
            audio = stretch(audio, rate, len(audio) / rate / seconds)
        else:
            audio = stretch(audio, rate, speed)
        return normalise(audio), rate


ENGINES = {'bn': IndicF5Engine, 'en': ChatterboxEngine}


class Voice:
    """A loaded model plus one reference voice. Load once, speak many lines."""

    def __init__(self, voice_dir: str | Path, language: str = 'bn', device: str = 'auto'):
        if language not in ENGINES:
            raise SystemExit(f'language must be one of {", ".join(ENGINES)}, not {language!r}')
        self.language = language
        self.engine = ENGINES[language](resolve_voice(voice_dir), pick_device(device))

    def speak(self, text: str, speed: float = 0.9, seconds: float | None = None) -> tuple[np.ndarray, int]:
        """`speed` below 1 is slower. `seconds` forces the clip length (short phrases the model rushes)."""
        return self.engine.speak(text, speed, seconds)
