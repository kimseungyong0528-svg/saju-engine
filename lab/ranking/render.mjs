// 대본 시간표(plan.json)대로 ../ranking/ranking.html 을 한 장면씩 찍어 mp4 로 만든다. node render.mjs plan.json out.mp4 [audio.mp3]
import { chromium } from '/opt/node-tools/node_modules/playwright/index.mjs';
import { spawn } from 'node:child_process';
import { readFileSync } from 'node:fs';
import path from 'node:path';
const [planPath, out, audio] = process.argv.slice(2);
const plan = JSON.parse(readFileSync(planPath, 'utf8'));
const FPS = 30, here = path.dirname(new URL(import.meta.url).pathname);
const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
await pg.goto('file://' + path.join(here, '../ranking/ranking.html')); await pg.evaluate(p => document.fonts.ready.then(() => window.setPlan(p)), plan);
await pg.waitForTimeout(500);
const args = ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-'];
if (audio) args.push('-i', audio);
args.push('-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'medium', '-crf', '20', '-r', String(FPS));
if (audio) args.push('-c:a', 'aac', '-b:a', '160k', '-shortest');
args.push(out);
const ff = spawn('ffmpeg', args, { stdio: ['pipe', 'inherit', 'inherit'] });
const n = Math.ceil(plan.total * FPS); const t0 = Date.now();
for (let i = 0; i < n; i++) {
  await pg.evaluate(t => window.render(t), i / FPS);
  const buf = await pg.screenshot({ type: 'jpeg', quality: 90 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
}
ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close();
console.log(`frames ${n}, ${((Date.now() - t0) / 1000).toFixed(1)}s`);
