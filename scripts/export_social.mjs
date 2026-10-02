// Export the Meta/LinkedIn ads (1080x1080, 1200x628) to flat PNGs in dist/social-static/.
// Uses your installed Chrome. Override with CHROME_PATH; extra flags via CHROME_ARGS (space separated).
import puppeteer from 'puppeteer-core';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const chrome = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const args = (process.env.CHROME_ARGS || '').split(' ').filter(Boolean);
const FREEZE_MS = 6000; // all text and CTA are in place, background push-in mid-way
const sizes = { '1080x1080': [1080, 1080], '1200x628': [1200, 628] };
const out = path.join(root, 'dist', 'social-static');
fs.mkdirSync(out, { recursive: true });

const browser = await puppeteer.launch({ executablePath: chrome, headless: 'shell', args });
let count = 0;
for (const set of ['A', 'B', 'C', 'D']) {
  for (const [size, [w, h]] of Object.entries(sizes)) {
    for (const variant of ['button', 'link']) {
      const file = path.join(root, 'docs', 'ads', `${set}_${size}`, `${variant}.html`);
      const page = await browser.newPage();
      await page.setViewport({ width: w, height: h, deviceScaleFactor: 1 });
      await page.goto(pathToFileURL(file).href, { waitUntil: 'networkidle0' });
      await page.evaluate(() => document.fonts.ready);
      await page.evaluate((t) => document.getAnimations().forEach(a => { a.pause(); a.currentTime = t; }), FREEZE_MS);
      await new Promise(r => setTimeout(r, 200));
      await page.screenshot({ path: path.join(out, `${set}_${size}_${variant}.png`) });
      await page.close(); count++;
    }
  }
}
await browser.close();
console.log(`exported ${count} PNGs to dist/social-static/`);
