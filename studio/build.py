"""Assemble the video: screenshots and cards, highlights synced to the narration, burned-in captions.

    .venv/bin/python -m studio.build projects/<name> [--only 4,5,6] [--out file.mp4]

Inputs: narration/ (from studio.narrate), cards/ (from studio.cards), shots/, cues.json.

cues.json, per scene number, a list of events in narration order:
    {"at": null, "shot": "scene-04"}                 first event: what the scene opens on
    {"at": "ব্যাংক ওয়ালেট", "box": [x, y, w, h]}       highlight while this phrase is spoken
    {"at": "...", "shot": "scene-05b", "box": [...]} switch screenshot (0.3 s early) and highlight
    {"at": "...", "clear": true}                     drop the current highlight
    {"at": "...", "inset": true}                     fade in this scene's inset (project.json insets)
    {"at": "...", "shot": "card/map-03"}             show a card (cards/map-03.png)
"at" is a piece of the scene's narration text; anchors are searched in order, so a repeated word
matches its next occurrence. Boxes are in the pixels of that screenshot (any size). A box replaces
the previous one. Shots are shots/<name>.jpg (or .png).

project.json "video" (all optional): fps 30, lead 0.5, tail 0.9, last_hold 1.5, caption_font
"Kalpurush", caption_size 50, caption_max 68, bar "0x0b2038", highlight "255,106,48".
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter

from studio.config import Project

W, H = 1920, 1080
SHOT_W, SHOT_H = 1920, 936
SHOT_EARLY = 0.3
BOX_EARLY = 0.12
FADE = 0.25


class Builder:
    def __init__(self, project: Project):
        self.p = project
        v = project.get('video', {})
        self.fps = v.get('fps', 30)
        self.lead, self.tail, self.last_hold = v.get('lead', 0.5), v.get('tail', 0.9), v.get('last_hold', 1.5)
        self.bar = v.get('bar', '0x0b2038')
        self.caption_font = v.get('caption_font', 'Kalpurush')
        self.caption_size = v.get('caption_size', 50)
        self.caption_max = v.get('caption_max', 68)
        self.highlight = tuple(int(x) for x in v.get('highlight', '255,106,48').split(','))
        (project.work / 'hl').mkdir(parents=True, exist_ok=True)

    # ----- timing ---------------------------------------------------------------------------
    @staticmethod
    def anchor_time(phrases, anchor, after):
        start_phrase, start_char = after
        for index in range(start_phrase, len(phrases)):
            text = phrases[index]['text']
            position = text.find(anchor, start_char if index == start_phrase else 0)
            if position >= 0:
                phrase = phrases[index]
                share = position / max(len(text), 1)
                return phrase['start'] + share * (phrase['end'] - phrase['start']), (index, position + 1)
        raise ValueError(f'cue phrase not found in narration: {anchor}')

    def resolve_cues(self, cues, phrases, scene_seconds):
        timed, cursor = [], (0, 0)
        for cue in cues:
            if cue['at'] is None:
                at = 0.0
            else:
                voice_at, cursor = self.anchor_time(phrases, cue['at'], cursor)
                at = self.lead + voice_at
            timed.append({**cue, 'time': at})
        segments = []
        for cue in timed:
            if 'shot' in cue:
                start = 0.0 if cue['at'] is None else max(cue['time'] - SHOT_EARLY, 0.0)
                if segments:
                    segments[-1]['end'] = start
                segments.append({'shot': cue['shot'], 'start': start, 'boxes': [], 'inset': None})
            segment = segments[-1]
            box_start = max(cue['time'] - BOX_EARLY, segment['start'])
            if ('box' in cue or cue.get('clear')) and segment['boxes'] and segment['boxes'][-1]['end'] is None:
                segment['boxes'][-1]['end'] = box_start
            if 'box' in cue:
                segment['boxes'].append({'box': cue['box'], 'start': box_start, 'end': None})
            if cue.get('inset'):
                segment['inset'] = max(cue['time'], segment['start'])
        segments[-1]['end'] = scene_seconds
        for segment in segments:
            for box in segment['boxes']:
                if box['end'] is None:
                    box['end'] = segment['end']
        return segments

    # ----- pictures -------------------------------------------------------------------------
    def shot_path(self, name: str) -> Path:
        if name.startswith('card/'):
            return self.p.cards / f'{name[5:]}.png'
        for ext in ('.jpg', '.png', '.jpeg'):
            path = self.p.shots / f'{name}{ext}'
            if path.exists():
                return path
        raise FileNotFoundError(f'shot not found: {name}')

    def highlight_png(self, box, src_w):
        out = self.p.work / 'hl' / f'{src_w}-{"-".join(map(str, box))}.png'
        if out.exists():
            return out
        x, y, w, h = box
        pad, scale = 6, SHOT_W / src_w
        left, top = max(x * scale - pad, 2), max(y * scale - pad, 2)
        right, bottom = min((x + w) * scale + pad, SHOT_W - 3), min((y + h) * scale + pad, SHOT_H - 3)
        top = min(top, bottom - 24)
        hole = Image.new('L', (SHOT_W, SHOT_H), 120)
        ImageDraw.Draw(hole).rounded_rectangle([left, top, right, bottom], radius=12, fill=0)
        shade = Image.new('RGBA', (SHOT_W, SHOT_H), (6, 18, 34, 0))
        shade.putalpha(hole)
        glow = Image.new('RGBA', (SHOT_W, SHOT_H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).rounded_rectangle([left, top, right, bottom], radius=12,
                                               outline=(*self.highlight, 200), width=12)
        frame = Image.alpha_composite(shade, glow.filter(ImageFilter.GaussianBlur(8)))
        ImageDraw.Draw(frame).rounded_rectangle([left, top, right, bottom], radius=12,
                                                outline=(*self.highlight, 255), width=5)
        frame.save(out)
        return out

    def render_segment(self, number, segment, out):
        frames = max(round((segment['end'] - segment['start']) * self.fps), 1)
        length = f'{frames / self.fps:.3f}'
        shot = segment['shot']
        image = self.shot_path(shot)
        args = ['ffmpeg', '-y', '-loop', '1', '-framerate', str(self.fps), '-t', length, '-i', str(image)]
        is_card = shot.startswith('card/')
        src_w = 1920
        if is_card:
            graph = f'[0]scale={W}:{H}[v0]'
        else:
            # Any screenshot size: scale to the shot area's width, then crop or pad its height.
            src_w, src_h = Image.open(image).size
            scaled_h = round(src_h * SHOT_W / src_w / 2) * 2
            fit = f'crop={SHOT_W}:{SHOT_H}:0:0' if scaled_h >= SHOT_H else f'pad={SHOT_W}:{SHOT_H}:0:0:color={self.bar}'
            graph = f'[0]scale={SHOT_W}:{scaled_h},{fit}[v0]'
        last, inputs = 'v0', 1
        for box in segment['boxes']:
            overlay = self.highlight_png(box['box'], src_w)
            start, end = box['start'] - segment['start'], box['end'] - segment['start']
            fade_out = max(end - FADE, start + FADE)
            args += ['-loop', '1', '-framerate', str(self.fps), '-t', length, '-i', str(overlay)]
            graph += (f';[{inputs}]format=rgba,fade=in:st={start:.2f}:d={FADE}:alpha=1,'
                      f'fade=out:st={fade_out:.2f}:d={FADE}:alpha=1[h{inputs}];[{last}][h{inputs}]overlay=0:0[v{inputs}]')
            last, inputs = f'v{inputs}', inputs + 1
        if segment['inset'] is not None:
            start = segment['inset'] - segment['start']
            inset = self.p.cards / f'inset-{number:02d}.png'
            args += ['-loop', '1', '-framerate', str(self.fps), '-t', length, '-i', str(inset)]
            graph += (f';[{inputs}]format=rgba,fade=in:st={start:.2f}:d=0.4:alpha=1[ins];'
                      f'[{last}][ins]overlay=(W-w)/2:{SHOT_H}-h-28[v{inputs}]')
            last = f'v{inputs}'
        if not is_card:
            graph += f';[{last}]pad={W}:{H}:0:0:color={self.bar}[out]'
            last = 'out'
        subprocess.run(args + ['-filter_complex', graph, '-map', f'[{last}]', '-frames:v', str(frames),
                               '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                               '-r', str(self.fps), str(out)], check=True, capture_output=True)
        return frames / self.fps

    # ----- captions -------------------------------------------------------------------------
    def caption_lines(self, phrase):
        lines = []
        for piece in [p.strip() for p in re.split(r'(?<=,)\s+', phrase) if p.strip()]:
            line = ''
            for word in piece.split():
                if line and len(line) + 1 + len(word) > self.caption_max:
                    lines.append(line)
                    line = word
                else:
                    line = f'{line} {word}'.strip()
            if lines and len(lines[-1]) + 1 + len(line) <= self.caption_max:
                lines[-1] = f'{lines[-1]} {line}'
            else:
                lines.append(line)
        return lines

    def write_captions(self, timings, starts, out):
        def t(sec):
            cs = round(sec * 100)
            return f'{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}'
        lines = ['[Script Info]', 'ScriptType: v4.00+', f'PlayResX: {W}', f'PlayResY: {H}', 'WrapStyle: 0', '',
                 '[V4+ Styles]',
                 'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, '
                 'Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, '
                 'Alignment, MarginL, MarginR, MarginV, Encoding',
                 f'Style: Cap,{self.caption_font},{self.caption_size},&H00FFFFFF,&H00FFFFFF,&H00382010,&H80000000,'
                 '0,0,0,0,100,100,0,0,1,2.5,0,2,80,80,44,1', '', '[Events]',
                 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
        for number, phrases in timings.items():
            base = starts[number] + self.lead
            for phrase in phrases:
                chunks = self.caption_lines(phrase['text'])
                total = sum(len(c) for c in chunks)
                at, span = base + phrase['start'], phrase['end'] - phrase['start']
                for chunk in chunks:
                    length = span * len(chunk) / total
                    lines.append(f'Dialogue: 0,{t(at)},{t(at + length)},Cap,,0,0,0,,{chunk}')
                    at += length
        out.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    # ----- main -----------------------------------------------------------------------------
    def check(self, cues, timings):
        problems = []
        for number, phrases in timings.items():
            if str(number) not in cues:
                problems.append(f'scene {number}: no cues')
                continue
            try:
                self.resolve_cues(cues[str(number)], phrases, 999)
            except ValueError as error:
                problems.append(f'scene {number}: {error}')
        return problems

    def build(self, out, only=None):
        cues = json.loads(self.p.cues.read_text(encoding='utf-8'))
        timings = json.loads((self.p.narration / 'timings.json').read_text(encoding='utf-8'))
        timings = {int(k): v for k, v in sorted(timings.items(), key=lambda kv: int(kv[0]))
                   if only is None or int(k) in only}
        problems = self.check(cues, timings)
        if problems:
            raise SystemExit('cue problems:\n  ' + '\n  '.join(problems))
        last_scene = max(timings)
        audio_parts, segments_out, starts, clock, rate = [], [], {}, 0.0, 24000
        for number in timings:
            voice, rate = sf.read(str(self.p.narration / f'scene-{number:02d}.wav'), dtype='float32')
            scene_seconds = self.lead + len(voice) / rate + self.tail + (self.last_hold if number == last_scene else 0)
            segments = self.resolve_cues(cues[str(number)], timings[number], scene_seconds)
            rendered = 0.0
            for index, segment in enumerate(segments):
                path = self.p.work / f's{number:02d}-{index}.mp4'
                rendered += self.render_segment(number, segment, path)
                segments_out.append(path)
            starts[number] = clock
            pad = rendered - self.lead - len(voice) / rate
            audio_parts += [np.zeros(int(self.lead * rate), np.float32), voice,
                            np.zeros(max(int(pad * rate), 0), np.float32)]
            clock += rendered
            print(f'scene {number:2d}: {rendered:5.1f}s, {len(segments)} shots, '
                  f'{sum(len(s["boxes"]) for s in segments)} highlights', flush=True)
        work = self.p.work
        sf.write(str(work / 'narration.wav'), np.concatenate(audio_parts), rate)
        (work / 'list.txt').write_text(''.join(f"file '{s}'\n" for s in segments_out), encoding='utf-8')
        subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(work / 'list.txt'), '-c', 'copy',
                        str(work / 'silent.mp4')], check=True, capture_output=True)
        self.write_captions(timings, starts, work / 'captions.ass')
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['ffmpeg', '-y', '-i', str(work / 'silent.mp4'), '-i', str(work / 'narration.wav'),
                        '-vf', f"ass={work / 'captions.ass'},fade=in:st=0:d=0.6,fade=out:st={clock - 1.0:.2f}:d=1.0",
                        '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest',
                        '-movflags', '+faststart', str(out)], check=True, capture_output=True)
        print(f'wrote {out} ({clock / 60:.1f} min)')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('project')
    parser.add_argument('--only', default='', help='comma-separated scenes (for a quick check)')
    parser.add_argument('--out', help='output file (default: project.json output)')
    parser.add_argument('--check', action='store_true', help='only check that every cue phrase is in the narration')
    args = parser.parse_args()
    project = Project.load(args.project)
    builder = Builder(project)
    if args.check:
        cues = json.loads(project.cues.read_text(encoding='utf-8'))
        timings = {int(k): v for k, v in json.loads((project.narration / 'timings.json').read_text(encoding='utf-8')).items()}
        problems = builder.check(cues, timings)
        print('\n'.join(problems) if problems else f'all {len(timings)} scenes ok')
        return
    only = {int(n) for n in args.only.split(',') if n} or None
    out = Path(args.out).expanduser().resolve() if args.out else (project.work / 'preview.mp4' if only else project.output)
    builder.build(out, only)


if __name__ == '__main__':
    main()
