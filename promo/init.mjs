// node promo/init.mjs <name>
// Creates projects/<name>-promo/ from promo/template, with GSAP and the Bangla fonts copied in,
// so the scene page runs from file:// with no network access.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const name = process.argv[2];
if (!name) { console.error('usage: node promo/init.mjs <name>'); process.exit(1); }

const dest = path.join(here, '..', 'projects', `${name}-promo`);
if (fs.existsSync(dest)) { console.error(`${dest} already exists; not overwriting it.`); process.exit(1); }

const nm = path.join(here, 'node_modules');
if (!fs.existsSync(path.join(nm, 'gsap'))) {
  console.error('promo dependencies are missing: run `pnpm install` inside promo/ first.');
  process.exit(1);
}

fs.cpSync(path.join(here, 'template'), dest, { recursive: true });
for (const d of ['shots', 'rec', 'audio', 'vo', 'out', 'qa']) fs.mkdirSync(path.join(dest, d), { recursive: true });

const site = path.join(dest, 'site');
fs.copyFileSync(path.join(nm, 'gsap/dist/gsap.min.js'), path.join(site, 'gsap.min.js'));
const fonts = [
  ['@fontsource/anek-bangla/files', 'anek-bangla-bengali', [600, 700, 800]],
  ['@fontsource/anek-bangla/files', 'anek-bangla-latin', [600, 700, 800]],
  ['@fontsource/hind-siliguri/files', 'hind-siliguri-bengali', [500, 600, 700]],
  ['@fontsource/hind-siliguri/files', 'hind-siliguri-latin', [500, 600, 700]],
];
fs.mkdirSync(path.join(site, 'fonts'), { recursive: true });
for (const [dir, base, weights] of fonts)
  for (const w of weights)
    fs.copyFileSync(path.join(nm, dir, `${base}-${w}-normal.woff2`), path.join(site, 'fonts', `${base}-${w}-normal.woff2`));

console.log(`Created ${path.relative(process.cwd(), dest)}
Next:
  1. Put the logo at site/img/logo.png and app screens in site/img/ (see docs/PROMO.md, "Screens").
  2. Write the voice-over lines into timeline.json and the voice into audio/ (see "Voice").
  3. Check stills:  node promo/stills.mjs ${path.relative(process.cwd(), dest)} 2 8 15
  4. Render:        node promo/render.mjs ${path.relative(process.cwd(), dest)}`);
