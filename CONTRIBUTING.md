# Contributing

Thanks for helping. Issues and pull requests are welcome, especially for more languages and voice engines, Bangla text handling, and Linux/GPU reports.

## Setup

Follow **Install** in the [README](README.md#install). For the tests alone you don't need the models:

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
```

## Before you open a pull request

```bash
.venv/bin/ruff check studio tests examples tools    # lint (settings in pyproject.toml)
.venv/bin/python -m pytest -q                       # unit tests, no models needed
```

CI runs both on every push and pull request.

The unit tests cover the text, timing, caption and setup logic. Anything that touches the voice engines, setup.sh or the video build also needs a real run, because CI doesn't download the models (~6 GB):

1. `./setup.sh` (or `LANGUAGES=bn` / `en`), then `.venv/bin/python -m studio.device`
2. Build both demo projects (see [examples/README.md](examples/README.md)) and watch the result.
3. Say in the pull request what you ran it on (macOS / Linux, CPU / GPU, languages).

## Guidelines

- Keep changes small and focused. Match the existing style (see `pyproject.toml`).
- New engines: a class in `studio/tts.py` with the same `speak()` contract, a `requirements-<lang>.txt`, setup.sh support, and the licence in `docs/MODELS.md`. Models must allow commercial use and run locally.
- **Voices and consent:** never commit a real person's voice recording or transcript without their written consent. Corpus voices need their licence and credit (see `voices/speaker-00737/README.txt`).
- Don't commit client material, generated videos or narration (the `.gitignore` covers the usual paths).
