"""Render the project's cards to 1920x1080 PNGs in cards/, using headless Chrome so Bangla text
is shaped correctly (ordinary image libraries break Bangla conjuncts).

    .venv/bin/python -m studio.cards projects/<name>

project.json "cards" (all optional):
    "font": "Kalpurush" (Bangla) / "Arial" (English), "logo": "assets/logo.png",
    "colors": {"bg1": "#1f4a73", "bg2": "#12304f", "bg3": "#0b2038", "accent": "#e2483d", "muted": "#cfe0f1"},
    "title":   {"heading": "...", "subtitle": "..."}          -> cards/title.png
    "closing": {"heading": "...", "subtitle": "ধন্যবাদ"}       -> cards/closing.png
    "process_map": {"title": "...", "steps": ["...", ...]}    -> cards/map-00.png .. map-NN.png
        (frame k has the first k steps lit, step k highlighted; use them one per narration cue)
    "extra": {"name": {"heading": "...", "subtitle": "..."}}   -> cards/<name>.png
project.json "credit": a small line at the bottom of the closing card (e.g. a voice licence credit).
project.json "insets": {"9": {"image": "shots/scene-09-inset.png", "label": "..."}}
    -> cards/inset-09.png, a framed strip faded into the bottom of that scene's last shot.
Cues refer to cards as "card/<name>" (e.g. "card/title", "card/map-03").
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

from studio.config import Project

CHROMES = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 'google-chrome', 'google-chrome-stable',
           'chromium', 'chromium-browser', 'chrome']
BN_DIGITS = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')


def chrome() -> str:
    for candidate in CHROMES:
        if Path(candidate).exists() or shutil.which(candidate):
            return candidate
    sys.exit('Google Chrome is needed to render the cards')


def base_css(project: Project) -> str:
    cards = project.get('cards', {})
    c = {'bg1': '#1f4a73', 'bg2': '#12304f', 'bg3': '#0b2038', 'accent': '#e2483d', 'muted': '#cfe0f1',
         **cards.get('colors', {})}
    font = cards.get('font', project.font)
    return f'''
html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; }}
body {{ font-family: '{font}', 'Bangla Sangam MN', 'Noto Sans Bengali', 'Helvetica Neue', 'DejaVu Sans', sans-serif; color: #fff;
  background: radial-gradient(circle at 50% 35%, {c['bg1']} 0%, {c['bg2']} 55%, {c['bg3']} 100%); }}
.center {{ display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; }}
.logo {{ background: #fff; border-radius: 28px; padding: 28px 40px; box-shadow: 0 18px 50px rgba(0,0,0,.35); }}
.logo img {{ width: 330px; display: block; }}
h1 {{ font-size: 76px; margin: 56px 0 0; font-weight: 700; letter-spacing: .5px; }}
h2 {{ font-size: 44px; margin: 22px 0 0; font-weight: 400; color: {c['muted']}; }}
.rule {{ width: 160px; height: 5px; background: {c['accent']}; border-radius: 3px; margin-top: 34px; }}
.off {{ background: rgba(255,255,255,.06); color: rgba(255,255,255,.35); border: 2px solid rgba(255,255,255,.12); }}
.on {{ background: #ffffff; color: {c['bg2']}; border: 2px solid #ffffff; }}
.credit {{ position: absolute; top: 36px; width: 100%; text-align: center; font: 22px sans-serif; color: {c['muted']}; opacity: .75; }}
.now {{ background: {c['accent']}; color: #fff; border-color: #ff8a80; box-shadow: 0 0 40px rgba(226,72,61,.6); }}
'''


def card_html(project: Project, heading: str, subtitle: str = '', credit: str = '') -> str:
    logo = project.get('cards', {}).get('logo')
    logo_html = f'<div class="logo"><img src="file://{project.asset(logo)}"></div>' if logo else ''
    sub = f'<div class="rule"></div><h2>{subtitle}</h2>' if subtitle else ''
    foot = f'<div class="credit">{credit}</div>' if credit else ''
    return f'<div class="center">{logo_html}<h1>{heading}</h1>{sub}</div>{foot}'


def map_html(title: str, steps: list[str], lit: int, language: str = 'bn') -> str:
    half = (len(steps) + 1) // 2
    boxes = []
    for index, label in enumerate(steps):
        state = 'on' if index < lit else 'off'
        current = ' now' if index == lit - 1 else ''
        number = str(index + 1).translate(BN_DIGITS) if language == 'bn' else str(index + 1)
        boxes.append(f'<div class="step {state}{current}"><span class="n">{number}</span>{label}</div>')
    row1 = '<div class="arrow">→</div>'.join(boxes[:half])
    row2 = '<div class="arrow">←</div>'.join(boxes[half:])
    return f'''<style>
.map {{ padding: 120px 90px 0; }}
.title {{ text-align: center; font-size: 58px; font-weight: 700; margin-bottom: 90px; }}
.row {{ display: flex; align-items: center; justify-content: center; gap: 14px; }}
.turn {{ text-align: right; font-size: 64px; color: #7fa6cc; margin: 18px 160px 18px 0; }}
.step {{ width: 270px; height: 150px; border-radius: 22px; display: flex; flex-direction: column;
  align-items: center; justify-content: center; text-align: center; font-size: 34px; line-height: 1.25;
  padding: 0 14px; box-sizing: border-box; }}
.step .n {{ font-size: 24px; opacity: .8; margin-bottom: 6px; }}
.arrow {{ font-size: 46px; color: #7fa6cc; }}
</style>
<div class="map"><div class="title">{title}</div><div class="row">{row1}</div>
<div class="turn">↓</div><div class="row" style="flex-direction: row-reverse">{row2}</div></div>'''


def render(project: Project, html: str, out: Path, size: str = '1920,1080') -> None:
    work = project.cards / 'html'
    work.mkdir(parents=True, exist_ok=True)
    page = work / (out.stem + '.html')
    page.write_text(f'<!doctype html><meta charset="utf-8"><style>{base_css(project)}</style>{html}', encoding='utf-8')
    # Chrome refuses to start as root (e.g. in a Linux container) unless its sandbox is off.
    sandbox = ['--no-sandbox'] if hasattr(os, 'geteuid') and os.geteuid() == 0 else []
    subprocess.run([chrome(), *sandbox, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--allow-file-access-from-files',
                    '--force-device-scale-factor=1', f'--window-size={size}', f'--screenshot={out}',
                    f'file://{page}'], check=True, capture_output=True)


def render_inset(project: Project, scene: str, spec: dict) -> None:
    image = project.asset(spec['image']).resolve()
    html = f'''<style>html, body {{ width: 1540px; height: 176px; background: #0b2038; }}
.box {{ padding: 12px 20px; }} .label {{ font-size: 30px; color: #fff; margin: 0 0 8px 4px; }}
.box img {{ width: 1500px; display: block; border-radius: 6px; }}</style>
<div class="box"><div class="label">{spec.get('label', '')}</div><img src="file://{image}"></div>'''
    render(project, html, project.cards / f'inset-{int(scene):02d}.png', '1540,176')


def main() -> None:
    project = Project.load(sys.argv[1])
    project.cards.mkdir(parents=True, exist_ok=True)
    cards = project.get('cards', {})
    for name in ('title', 'closing'):
        if name in cards:
            render(project, card_html(project, cards[name]['heading'], cards[name].get('subtitle', ''),
                             project.get('credit', '') if name == 'closing' else ''),
                   project.cards / f'{name}.png')
    for name, spec in cards.get('extra', {}).items():
        render(project, card_html(project, spec['heading'], spec.get('subtitle', '')), project.cards / f'{name}.png')
    process_map = cards.get('process_map')
    if process_map:
        for lit in range(len(process_map['steps']) + 1):
            render(project, map_html(process_map['title'], process_map['steps'], lit, project.language), project.cards / f'map-{lit:02d}.png')
    for scene, spec in project.get('insets', {}).items():
        render_inset(project, scene, spec)
    print('cards written to', project.cards)


if __name__ == '__main__':
    main()
