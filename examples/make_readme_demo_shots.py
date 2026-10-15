"""Render the screenshots for the README demo videos (examples/readme-demo-en and -bn).

    .venv/bin/python examples/make_readme_demo_shots.py

Each screen is an editor or terminal mock-up drawn in HTML and captured with headless Chrome at
1920x936 (the video's shot area, so highlight boxes need no scaling). Lines sit on a fixed grid, so
the highlight boxes in each project's cues.json are exact: see box() below.
"""
import html
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))  # the repo root, for studio.*

from studio.cards import chrome  # noqa: E402

W, H = 1920, 936
LEFT, TOP, LINE = 150, 150, 50  # text grid: first line's top edge and line height, in pixels
PANEL_W = 1620

TEXT = {
    'en': {
        'pitch': ['### Scene 2: The list page',
                  '**On screen:** the course list; highlight the add button.',
                  '**Narration:**',
                  'The course list shows every course in one place.',
                  'Click the new course button to open the form.',
                  '',
                  '### Scene 3: Closing'],
        'cue_at': ['The course list', 'new course button'],
    },
    'bn': {
        'pitch': ['### Scene 2: The list page',
                  '**On screen:** the course list; highlight the add button.',
                  '**Narration:**',
                  'কোর্স তালিকায় সব কোর্স একসাথে দেখা যায়।',
                  'উপরের নতুন কোর্স বাটনে ক্লিক করলে ফর্ম খোলে।',
                  '',
                  '### Scene 3: Closing'],
        'cue_at': ['কোর্স তালিকায়', 'নতুন কোর্স বাটনে'],
    },
}


def box(first_line: int, last_line: int, width: int = PANEL_W - 60) -> list[int]:
    """[x, y, w, h] around text lines first_line..last_line (0-based) of a screen."""
    return [LEFT - 14, TOP + first_line * LINE - 8, width, (last_line - first_line + 1) * LINE + 8]


def page(title: str, lines: list[tuple[str, str]], terminal: bool = False) -> str:
    rows = ''.join(f'<div class="ln {cls}" style="top:{TOP + i * LINE}px">{html.escape(text) or "&nbsp;"}</div>'
                   for i, (text, cls) in enumerate(lines))
    background = '#0c0f14' if terminal else '#161b22'
    return f'''<!doctype html><meta charset="utf-8"><style>
html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: #0b2038; }}
.win {{ position: absolute; left: {LEFT - 40}px; top: 60px; width: {PANEL_W + 30}px; height: {H - 110}px;
  background: {background}; border-radius: 14px; box-shadow: 0 20px 60px rgba(0,0,0,.45); }}
.bar {{ position: absolute; left: 0; right: 0; top: 0; height: 52px; border-bottom: 1px solid #2a313c;
  font: 24px 'SF Mono', Menlo, 'DejaVu Sans Mono', monospace; color: #9aa7b6; padding: 12px 0 0 120px; box-sizing: border-box; }}
.dot {{ position: absolute; top: 18px; width: 16px; height: 16px; border-radius: 50%; }}
.ln {{ position: absolute; left: {LEFT}px; height: {LINE}px; line-height: {LINE}px; white-space: pre;
  font: 28px 'SF Mono', Menlo, 'DejaVu Sans Mono', 'Kalpurush', monospace; color: #d6dde6; }}
.h {{ color: #79c0ff; font-weight: 600; }} .k {{ color: #ffa657; }} .s {{ color: #a5d6ff; }}
.c {{ color: #7d8590; }} .p {{ color: #7ee787; }} .ok {{ color: #7ee787; }}
.bn {{ font-family: 'Kalpurush', sans-serif; font-size: 32px; }}
</style><div class="win"><div class="dot" style="left:22px;background:#ff5f57"></div>
<div class="dot" style="left:48px;background:#febc2e"></div><div class="dot" style="left:74px;background:#28c840"></div>
<div class="bar">{html.escape(title)}</div></div>{rows}'''


def render(markup: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    source = out.with_suffix('.html')
    source.write_text(markup, encoding='utf-8')
    subprocess.run([chrome(), '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                    f'--window-size={W},{H}', f'--screenshot={out}', f'file://{source}'], check=True, capture_output=True)
    source.unlink()


def main() -> None:
    boxes = {}
    for language, text in TEXT.items():
        shots = ROOT / f'readme-demo-{language}' / 'shots'
        narration_cls = 'bn' if language == 'bn' else ''
        pitch = [(text['pitch'][0], 'h'), (text['pitch'][1], 'c'), (text['pitch'][2], 'k'),
                 (text['pitch'][3], narration_cls), (text['pitch'][4], narration_cls), ('', ''), (text['pitch'][6], 'h')]
        render(page('pitch.md', pitch), shots / 'scene-02.png')

        at1, at2 = text['cue_at']
        cues = [('"2": [', ''),
                ('  { "at": null, "shot": "scene-02a" },', 'c'),
                (f'  {{ "at": "{at1}", "box": [40, 120, 1480, 520] }},', narration_cls),
                (f'  {{ "at": "{at2}", "box": [1340, 60, 190, 44] }}', narration_cls),
                ('],', '')]
        render(page('cues.json', cues), shots / 'scene-03.png')

        terminal = [('$ .venv/bin/python -m studio.narrate projects/my-demo', 'p'),
                    ('scene  1:   6.2s in 2 phrases -> scene-01.wav', 'c'),
                    ('scene  2:   9.2s in 3 phrases -> scene-02.wav', 'c'),
                    ('$ .venv/bin/python -m studio.cards projects/my-demo', 'p'),
                    ('$ .venv/bin/python -m studio.build projects/my-demo', 'p'),
                    ('scene  2:  10.6s, 2 shots, 3 highlights', 'c'),
                    ('wrote my-demo.mp4 (0.4 min)', 'ok')]
        render(page('terminal', terminal, terminal=True), shots / 'scene-04.png')

        boxes[language] = {'narration': box(3, 4), 'cue_lines': box(2, 3), 'commands_narrate': box(0, 2),
                           'commands_build': box(3, 6), 'result': box(6, 6, 640)}
    print(json.dumps(boxes, indent=1))


if __name__ == '__main__':
    main()
