// node promo/stills.mjs <project-dir> <t1> <t2> ... [--cols 4]
// Renders the scene page at the given seconds (half size) and tiles them into <project>/qa/sheet.jpg,
// so layout, captions and overlaps can be checked before the full render.
import { chromium } from 'playwright-core';
import { execFileSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const args = process.argv.slice(2);
const dir = path.resolve(args[0]);
const ci = args.indexOf('--cols'); const cols = ci > -1 ? +args[ci + 1] : 4;
const times = args.slice(1).filter((a, i, all) => a !== '--cols' && all[i - 1] !== '--cols').map(Number);
if (!times.length) { console.error('usage: node promo/stills.mjs <project-dir> <t1> <t2> ... [--cols 4]'); process.exit(1); }

const qa = path.join(dir, 'qa'); fs.rmSync(qa, { recursive: true, force: true }); fs.mkdirSync(qa, { recursive: true });
const TLJ = fs.readFileSync(path.join(dir, 'timeline.json'), 'utf8');
const b = await chromium.launch({ channel: 'chrome' });
const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 0.5 });
await p.addInitScript(`window.TIMELINE=${TLJ};`);
p.on('pageerror', e => console.error('PAGE ERROR', e.message));
await p.goto('file://' + path.join(dir, 'site', 'index.html'));
await p.evaluate(() => window.ready);
for (const [i, t] of times.entries()) {
  await p.evaluate(t => window.seek(t), t);
  await p.screenshot({ path: path.join(qa, `s${String(i).padStart(3, '0')}.jpg`), quality: 85 });
}
await b.close();
const rows = Math.ceil(times.length / cols);
execFileSync('ffmpeg', ['-y', '-v', 'error', '-framerate', '1', '-i', path.join(qa, 's%03d.jpg'),
  '-vf', `tile=${cols}x${rows}:padding=6:color=black`, '-frames:v', '1', path.join(qa, 'sheet.jpg')]);
console.log(`Wrote ${path.join(qa, 'sheet.jpg')} (${times.join('s, ')}s)`);
