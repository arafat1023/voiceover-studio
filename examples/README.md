# Examples

`readme-demo-en/` and `readme-demo-bn/` are the projects behind the demo videos in the main README
(`docs/media/`). They are complete, working projects: copy one to start your own.

| Project | Language | Voice |
|---------|----------|-------|
| `readme-demo-en` | English | `builtin` (Chatterbox Turbo's own voice) |
| `readme-demo-bn` | Bangla | `voices/speaker-00737` (SLR37, CC BY-SA 4.0, credited on the closing card) |

Their screenshots are editor and terminal mock-ups drawn by `make_readme_demo_shots.py`, so the
highlight boxes in `cues.json` are exact. To rebuild a demo (needs that language installed):

```bash
.venv/bin/python examples/make_readme_demo_shots.py          # only if you change the screens
.venv/bin/python -m studio.narrate examples/readme-demo-en
.venv/bin/python -m studio.cards   examples/readme-demo-en
.venv/bin/python -m studio.build   examples/readme-demo-en      # -> examples/readme-demo-en/video.mp4
```
