// Renders index.html frame by frame and encodes a 1080x1920 MP4.
// Usage: node render.js [out.mp4]
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const FPS = 30;
const out = process.argv[2] || path.join(__dirname, 'car-x-claude.mp4');
const framesDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'frames-'));

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.join(__dirname, 'index.html'), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  const duration = await page.evaluate(() => window.DURATION);
  const total = Math.round(duration * FPS);
  for (let f = 0; f < total; f++) {
    await page.evaluate((t) => window.render(t), f / FPS);
    await page.screenshot({ path: path.join(framesDir, `f${String(f).padStart(5, '0')}.png`) });
  }
  await browser.close();
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS),
    '-i', path.join(framesDir, 'f%05d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
    '-crf', '18', '-movflags', '+faststart', out]);
  fs.rmSync(framesDir, { recursive: true });
  console.log('wrote', out);
})();
