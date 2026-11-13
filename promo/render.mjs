// node promo/render.mjs <project-dir> [--parts 4] [--scale 1.3333] [--fps 60] [--name Promo]
//
// Renders <project>/site/index.html frame by frame in headless Chrome and encodes it with ffmpeg.
// - The page must expose window.ready (Promise), window.seek(t) (async) and window.DURATION.
// - <project>/timeline.json is injected as window.TIMELINE before the page loads.
// - Frames are captured at --fps (60) and blended in pairs to 30 fps for natural motion blur,
//   with light film grain. --scale 4/3 turns the 1080x1920 page into 1440x2560 ("2K").
// - The video is split into --parts segments rendered in parallel, then joined.
// - If <project>/audio/mix.wav exists it is muxed in; audio/voice_only.wav gives a second file.
// - A 1080p copy is made for sharing (the 2K master is large).
import { chromium } from 'playwright-core';
import { spawn, execFileSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const args = process.argv.slice(2);
const dir = path.resolve(args[0] || '.');
const opt = (k, d) => { const i = args.indexOf('--' + k); return i > -1 ? args[i + 1] : d; };
const PARTS = +opt('parts', 4), SCALE = +opt('scale', 4 / 3), FPS = +opt('fps', 60), NAME = opt('name', 'Promo');
const W = 1080, H = 1920;

const tlPath = path.join(dir, 'timeline.json');
const TLJ = fs.readFileSync(tlPath, 'utf8');
const total = JSON.parse(TLJ).total;
const out = path.join(dir, 'out'); fs.mkdirSync(out, { recursive: true });

const run = (cmd, a) => execFileSync(cmd, a, { stdio: ['ignore', 'inherit', 'inherit'] });

async function renderPart(i, t0, t1, browser) {
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: SCALE });
  await page.addInitScript(`window.TIMELINE=${TLJ};`);
  page.on('pageerror', e => console.error(`[part ${i}] PAGE ERROR`, e.message));
  await page.goto('file://' + path.join(dir, 'site', 'index.html'));
  await page.evaluate(() => window.ready);
  const file = path.join(out, `part${i}.mp4`);
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-vf', "tmix=frames=2:weights='1 1',fps=30,noise=alls=3:allf=t,format=yuv420p",
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-profile:v', 'high', file], { stdio: ['pipe', 'inherit', 'inherit'] });
  const f0 = Math.round(t0 * FPS), f1 = Math.round(t1 * FPS);
  for (let f = f0; f < f1; f++) {
    await page.evaluate(t => window.seek(t), f / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - f0) % 300 === 0) console.log(`part ${i}: ${Math.round((f - f0) / (f1 - f0) * 100)}%`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await page.close();
  return file;
}

const browser = await chromium.launch({ channel: 'chrome' });
// Cut points snapped to whole frames so the parts join without a gap.
const cuts = Array.from({ length: PARTS + 1 }, (_, k) => Math.round(total * k / PARTS * FPS) / FPS);
const parts = await Promise.all(cuts.slice(0, -1).map((t, i) => renderPart(i + 1, t, cuts[i + 1], browser)));
await browser.close();

const list = path.join(out, 'parts.txt');
fs.writeFileSync(list, parts.map(p => `file '${p}'`).join('\n'));
const silent = path.join(out, 'video_silent.mp4');
run('ffmpeg', ['-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', silent]);
parts.forEach(p => fs.rmSync(p)); fs.rmSync(list);

const res = SCALE === 1 ? '1080p' : `${Math.round(W * SCALE)}x${Math.round(H * SCALE)}`;
const mux = (audio, dest) => run('ffmpeg', ['-y', '-v', 'error', '-i', silent, '-i', audio, '-map', '0:v', '-map', '1:a',
  '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', dest]);
const master = path.join(out, `${NAME}_9x16_${res}.mp4`);
const mix = path.join(dir, 'audio', 'mix.wav'), voice = path.join(dir, 'audio', 'voice_only.wav');
if (fs.existsSync(mix)) mux(mix, master); else fs.renameSync(silent, master);
if (fs.existsSync(voice) && fs.existsSync(silent)) mux(voice, path.join(out, `${NAME}_9x16_${res}_voice_only.mp4`));
if (fs.existsSync(silent)) fs.rmSync(silent);
if (SCALE > 1)
  run('ffmpeg', ['-y', '-v', 'error', '-i', master, '-vf', 'scale=1080:1920:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow',
    '-crf', '19', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart', path.join(out, `${NAME}_9x16_1080p.mp4`)]);
console.log('Done:', fs.readdirSync(out).filter(f => f.endsWith('.mp4')).map(f => path.join('out', f)).join(', '));
