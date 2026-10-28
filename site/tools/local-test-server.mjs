// 내 컴퓨터에서 사이트+주문 서버를 통째로 돌려 보는 시험용 서버.
// 진짜 결제·이메일·깃허브 대신 가짜를 쓰고, 결과 작성은 python -m saju.order 를 초안 모드(SAJU_DRAFT=1, API 비용 없음)로 돌린다.
// 예) node site/tools/local-test-server.mjs 8787  → http://localhost:8787
import http from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { makeApi, memoryStore } from '../netlify/functions/lib/api.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const site = path.resolve(here, '..'), repo = path.resolve(site, '..');
const port = Number(process.argv[2] || 8787);
const outDir = process.env.OUT_DIR || path.join(site, '.local-mail');
const env = { TOSS_CLIENT_KEY: 'test_ck_local', TOSS_SECRET_KEY: 'test_sk_local', GH_DISPATCH_TOKEN: 'local', WORKER_SECRET: 'local-secret', RESEND_API_KEY: 'local' };
const TYPES = { '.html': 'text/html; charset=utf-8', '.jpg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.css': 'text/css' };

const services = {
  tossConfirm: async a => { console.log('[가짜 토스] 결제 승인', a.orderId, a.amount); return { ok: true }; },
  startWorker: async orderId => {
    console.log('[가짜 깃허브] 작업 시작', orderId);
    const p = spawn('python3', ['-m', 'saju.order', orderId], { cwd: repo, stdio: 'inherit',
      env: { ...process.env, SITE_URL: `http://localhost:${port}`, WORKER_SECRET: env.WORKER_SECRET, SAJU_DRAFT: '1' } });
    p.on('exit', code => console.log('[작업 끝]', code));
  },
  sendEmail: async (order, pdf) => {
    await mkdir(outDir, { recursive: true });
    const file = path.join(outDir, `${order.id}.pdf`);
    await writeFile(file, pdf);
    console.log('[가짜 이메일]', order.email, file);
  },
  notifyOwner: async (order, note) => console.log('[사장님 알림]', order.id, note),
};
const store = memoryStore();
// 재구매 할인 링크 화면을 볼 때: DEMO_COUPON=UNM-XXXXXX 로 띄우면 그 코드를 쓸 수 있는 상태로 넣어 둔다.
if (process.env.DEMO_COUPON) await store.set(`coupons/${process.env.DEMO_COUPON}`, { code: process.env.DEMO_COUPON, kind: 'rebuy', percent: 10, createdAt: new Date().toISOString(), expiresAt: new Date(Date.now() + 30 * 864e5).toISOString() });
const api = makeApi({ store, services, env });

http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${port}`);
  if (url.pathname.startsWith('/api/')) {
    const chunks = []; for await (const c of req) chunks.push(c);
    const body = ['GET', 'HEAD'].includes(req.method) ? undefined : Buffer.concat(chunks);
    const r = await api(new Request(url, { method: req.method, headers: req.headers, body }));
    res.writeHead(r.status, Object.fromEntries(r.headers)); res.end(Buffer.from(await r.arrayBuffer()));
    return;
  }
  const rel = url.pathname === '/' ? 'index.html' : decodeURIComponent(url.pathname.slice(1));
  const file = path.join(site, 'public', rel);
  if (!file.startsWith(path.join(site, 'public'))) { res.writeHead(403); return res.end(); }
  try { const data = await readFile(file); res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' }); res.end(data); }
  catch { res.writeHead(404); res.end('not found'); }
}).listen(port, () => console.log(`http://localhost:${port}`));
