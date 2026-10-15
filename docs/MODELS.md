# Models, data and licences

Everything runs locally. Nothing is sent to a cloud TTS service. Licences below are as stated on each model's Hugging Face card or repository.

| Part | What it does | Source | Licence |
|------|--------------|--------|---------|
| IndicF5 | Bangla (and 10 other Indian languages) TTS with zero-shot voice cloning | https://huggingface.co/ai4bharat/IndicF5 (gated; accept the terms) · code https://github.com/AI4Bharat/IndicF5, pinned at commit `13f7c4d627cc10111aea8fe9c0039462cacacdc7` · public mirror of the weights used by setup.sh: https://huggingface.co/rsolanki1822/IndicF5-mirror | MIT |
| F5-TTS | the architecture IndicF5 is trained on (DiT + flow matching) | https://github.com/SWivid/F5-TTS | MIT (code) |
| Vocos | turns IndicF5's mel spectrogram into audio | https://huggingface.co/charactr/vocos-mel-24khz | MIT |
| Chatterbox Turbo | English TTS with zero-shot voice cloning | https://huggingface.co/ResembleAI/chatterbox-turbo · code https://github.com/resemble-ai/chatterbox (`chatterbox-tts==0.1.7`) | MIT |
| Perth | inaudible watermark Chatterbox adds to every clip | https://github.com/resemble-ai/perth | MIT |
| Whisper small (optional) | English transcripts: drafts in `make_voice`, take checks in `narrate` | https://huggingface.co/openai/whisper-small | Apache 2.0 |
| Bengali Whisper (optional) | Bangla transcripts: drafts in `make_voice`, take checks in `narrate` | https://huggingface.co/bengaliAI/tugstugi_bengaliai-asr_whisper-medium | Apache 2.0 |
| SLR37 (optional) | Bangladeshi Bangla speech corpus for stock voices | https://openslr.org/37/ | CC BY-SA 4.0. Credit any voice made from it, e.g. "Voice based on Google SLR37 Bengali speech data, CC BY-SA 4.0" |
| Kalpurush | Bangla font for captions and cards | https://www.omicronlab.com/bangla-fonts.html | free font |

## Why Chatterbox for English

The requirements were local, zero-shot cloning, a licence that allows commercial use (videos made with this go to clients), Apple Silicon support, and running in the same environment as IndicF5.
- **Disqualified by licence:** several strong models (F5-TTS's English weights, XTTS-v2, Fish Speech / OpenAudio, Spark-TTS) have non-commercial weights.
- **No cloning:** Kokoro (Apache 2.0) has excellent preset voices but can't clone.
- **Untested alternatives:** Zonos and CosyVoice2 (Apache 2.0) are possible alternatives but haven't been tried with this pipeline.

Engines are separate classes in `studio/tts.py`, so adding another is a small change.

## Notes

- **IndicF5 weights layout.** `models/indicf5-base/` holds `model.safetensors`, `config.json`, `model.py` and `checkpoints/vocab.txt`. The safetensors file stores a compiled EMA copy (`ema_model._orig_mod.*`); `studio/tts.py` strips that prefix and loads strictly, so a wrong file fails loudly instead of giving a different voice.
- **Digits.** IndicF5 was trained on normalised text and does not read digits; write numbers in words (the narrator refuses digits in Bangla projects). Chatterbox reads digits, but words are safer for prices and dates.
- **Speed.**
  - About 5-10 s of compute per sentence on Apple Silicon (`mps`) or an NVIDIA GPU. CPU works, but a long video takes hours.
  - Chatterbox has no speed control, so `speed` and `fixed_seconds` are applied afterwards with a pitch-preserving time stretch (ffmpeg `atempo`).
- **Reference clips.** IndicF5 needs the clip's exact transcript (`reference.txt`). Chatterbox ignores it but needs the clip to be longer than 5 s.
- **Ethics.** Voice cloning needs the speaker's consent. Record it in `voices/<name>/README.txt`. Don't present cloned speech as a live recording of the person.
