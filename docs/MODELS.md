# Models, data and licences

Everything runs locally. Nothing is sent to a cloud TTS service.

| Part | What it does | Source | Licence |
|------|--------------|--------|---------|
| IndicF5 | Bangla (and 10 other Indian languages) TTS with zero-shot voice cloning | https://huggingface.co/ai4bharat/IndicF5 (gated; accept the terms) · code https://github.com/AI4Bharat/IndicF5, pinned at commit `13f7c4d627cc10111aea8fe9c0039462cacacdc7` · public mirror of the weights used by setup.sh: https://huggingface.co/rsolanki1822/IndicF5-mirror | MIT |
| F5-TTS | the architecture IndicF5 is trained on (DiT + flow matching) | https://github.com/SWivid/F5-TTS | MIT (code) |
| Vocos | turns the model's mel spectrogram into audio | https://huggingface.co/charactr/vocos-mel-24khz | MIT |
| Bengali Whisper (optional) | drafts transcripts in `make_voice` | https://huggingface.co/bengaliAI/tugstugi_bengaliai-asr_whisper-medium | see the model card |
| SLR37 (optional) | Bangladeshi Bangla speech corpus for stock voices | https://openslr.org/37/ | CC BY-SA 4.0. Credit any voice made from it, e.g. "Voice based on Google SLR37 Bengali speech data, CC BY-SA 4.0" |
| Kalpurush | Bangla font for captions and cards | https://www.omicronlab.com/bangla-fonts.html | free font |

## Notes

- **Weights layout.** `models/indicf5-base/` holds `model.safetensors`, `config.json`, `model.py` and `checkpoints/vocab.txt`. The safetensors file stores a compiled EMA copy (`ema_model._orig_mod.*`); `studio/tts.py` strips that prefix and loads strictly, so a wrong file fails loudly instead of giving a different voice.
- **Digits.** IndicF5 was trained on normalised text and does not read digits. Write numbers in words.
- **Speed.** About 5-10 s of compute per sentence on Apple Silicon (`mps`). CPU works, but slowly.
- **Ethics.** Voice cloning needs the speaker's consent. Record it in `voices/<name>/README.txt`. Don't present cloned speech as a live recording of the person.
